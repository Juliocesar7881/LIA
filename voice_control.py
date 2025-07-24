# voice_control.py (versão com fala "frase por frase" para baixa latência)

import speech_recognition as sr
import asyncio
import edge_tts
import os
import random
import threading
import time
import pygame
import re  # Importamos a biblioteca de expressões regulares

# --- Configurações Iniciais ---
pygame.mixer.init()
recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2

try:
    mic = sr.Microphone(device_index=1)  # Lembre-se de usar seu device_index
    with mic as source:
        print("🤫 Calibrando microfone... Por favor, fique em silêncio por 2 segundos.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"🎚️ Limiar de energia ajustado para: {recognizer.energy_threshold:.2f}.")
except Exception as e:
    print(f"❌ Microfone não encontrado ou não configurado: {e}")
    mic = None


# --- Funções de Controle de Áudio ---

def _tocar_audio(caminho_arquivo, deletar_depois=False):
    """Função interna (síncrona) para tocar um arquivo de áudio e opcionalmente deletá-lo."""
    try:
        pygame.mixer.music.load(caminho_arquivo)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"🤯 Erro ao tocar áudio: {e}")
    finally:
        pygame.mixer.music.unload()
        if deletar_depois and os.path.exists(caminho_arquivo):
            try:
                os.remove(caminho_arquivo)
            except PermissionError:
                print(f"⚠️ Não foi possível remover o arquivo temporário '{caminho_arquivo}' imediatamente.")


def parar_fala():
    """Para a reprodução de áudio imediatamente."""
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        print("🎤 Interrompendo a fala da LISA.")


# --- Funções de Geração de Voz ---

async def falar(texto):
    """
    MODIFICADO: Quebra o texto em frases e fala uma por uma para reduzir a latência inicial.
    """
    parar_fala()

    texto_limpo = re.sub(r'[\*#\_`%&()]', '', texto)
    print(f"LISA 🗣️: {texto_limpo}")

    # Usa regex para dividir o texto em frases de forma inteligente
    frases = re.split(r'(?<=[.!?])\s*', texto_limpo)
    frases_validas = [f for f in frases if f.strip()]

    if not frases_validas:
        return

    # Pega o loop de eventos do asyncio para rodar a função de tocar (que é síncrona) em uma thread
    loop = asyncio.get_running_loop()

    for i, frase in enumerate(frases_validas):
        # A verificação de interrupção acontece no main.py, que chama parar_fala().
        # Se a música não estiver tocando, é porque foi interrompida.
        # A exceção é a primeira frase (i == 0), onde a música ainda não começou.
        if i > 0 and not pygame.mixer.music.get_busy():
            print("▶️ Sequência de fala interrompida pelo usuário.")
            return  # Sai da função e não fala o resto das frases

        nome_audio = f"fala_temp_{random.randint(1000, 9999)}.mp3"
        try:
            # 1. Gera o áudio apenas para a frase atual (muito rápido)
            comunicador = edge_tts.Communicate(frase, "pt-BR-ThalitaMultilingualNeural")
            await comunicador.save(nome_audio)

            # 2. Toca o áudio em uma thread separada para não bloquear o programa
            await loop.run_in_executor(None, _tocar_audio, nome_audio, True)

        except Exception as e:
            print(f"🤯 Erro ao gerar ou tocar a fala para a frase: '{frase}'. Erro: {e}")
            if os.path.exists(nome_audio):
                os.remove(nome_audio)  # Limpa o arquivo que falhou
            return  # Para de falar o resto em caso de erro


def falar_rapido(nome_arquivo):
    """Toca um arquivo de áudio pré-gravado do cache de forma instantânea."""
    nome_seguro = nome_arquivo.replace("!", "").replace("?", "") + ".mp3"
    caminho_completo = os.path.join("audio_cache", nome_seguro)
    if os.path.exists(caminho_completo):
        print(f"⚡ Usando áudio do cache: '{nome_seguro}'")
        # Toca em uma thread separada para não bloquear
        playback_thread = threading.Thread(target=_tocar_audio, args=(caminho_completo, False), daemon=True)
        playback_thread.start()
    else:
        print(f"⚠️ Arquivo de cache de áudio não encontrado: {caminho_completo}")
