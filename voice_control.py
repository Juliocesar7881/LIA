# voice_control.py (Com trava de segurança para a sensibilidade do microfone)

import speech_recognition as sr
import asyncio
import edge_tts
import os
import random
import threading
import pygame
import re
import time


def encontrar_melhor_microfone():
    """
    Verifica todos os microfones e retorna o índice daquele que parece ser o melhor.
    """
    print("🎤 Procurando pelo melhor microfone...")
    nomes_mics = sr.Microphone.list_microphone_names()
    palavras_chave = ["usb", "headset", "externo"]
    for i, nome in enumerate(nomes_mics):
        nome_lower = nome.lower()
        for palavra in palavras_chave:
            if palavra in nome_lower:
                print(f"✅ Microfone preferencial encontrado no índice {i}: '{nome}'")
                return i
    print("⚠️ Nenhum microfone preferencial (USB, Headset) encontrado. Usando o padrão do sistema.")
    return None


# --- Configurações Iniciais ---
pygame.mixer.init()
recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2

try:
    indice_do_microfone = encontrar_melhor_microfone()
    mic = sr.Microphone(device_index=indice_do_microfone)

    with mic as source:
        print("🤫 Calibrando microfone... Por favor, fique em silêncio por 2 segundos.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"🎚️  Limiar de energia automático calculado: {recognizer.energy_threshold:.2f}.")

        # --- INÍCIO DA CORREÇÃO DE SEGURANÇA ---
        # Se a calibração automática resultar em um valor muito baixo, nós forçamos um valor mínimo.
        VALOR_MINIMO_DE_SENSIBILIDADE = 350
        if recognizer.energy_threshold < VALOR_MINIMO_DE_SENSIBILIDADE:
            print(f"⚠️ Limiar automático muito baixo. Forçando para o valor mínimo de {VALOR_MINIMO_DE_SENSIBILIDADE}.")
            recognizer.energy_threshold = VALOR_MINIMO_DE_SENSIBILIDADE
        # --- FIM DA CORREÇÃO DE SEGURANÇA ---

except Exception as e:
    print(f"❌ Microfone não encontrado ou não configurado: {e}")
    mic = None

# --- Controle de Estado da Fala ---
tts_is_active = threading.Event()


# --- Funções de Controle de Áudio ---
def _tocar_audio(caminho_arquivo, deletar_depois=False):
    """Função interna que apenas toca um áudio."""
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
            except Exception:
                pass


def parar_fala():
    """
    Para a reprodução de áudio imediatamente E limpa o sinalizador de atividade.
    """
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        print("🎤 Interrompendo a fala da LIA.")
    if tts_is_active.is_set():
        tts_is_active.clear()


# --- Funções de Geração de Voz ---
async def falar(texto):
    """
    Usa um sistema de produtor/consumidor otimizado.
    """
    if tts_is_active.is_set(): return

    parar_fala()
    texto_limpo = re.sub(r'[\*#\_`%&()]', '', str(texto))
    print(f"LIA 🗣️: {texto_limpo}")
    frases = re.split(r'(?<=[.!?])\s*', texto_limpo)
    frases_validas = [f for f in frases if f.strip()]
    if not frases_validas: return

    tts_is_active.set()
    loop = asyncio.get_event_loop()
    audio_queue = asyncio.Queue()

    async def produtor():
        try:
            for frase in frases_validas:
                if not tts_is_active.is_set():
                    print("▶️ Produção de áudio interrompida.")
                    break
                nome_audio = f"fala_temp_{random.randint(1000, 9999)}.mp3"
                # --- MUDANÇA AQUI ---
                comunicador = edge_tts.Communicate(frase, "pt-BR-FranciscaNeural")
                # --- FIM DA MUDANÇA ---
                await comunicador.save(nome_audio)
                await audio_queue.put(nome_audio)
        finally:
            await audio_queue.put(None)

    async def consumidor():
        while True:
            nome_audio = await audio_queue.get()
            if nome_audio is None:
                break
            if not tts_is_active.is_set():
                print("▶️ Fila de áudio descartada devido à interrupção.")
                if os.path.exists(nome_audio): os.remove(nome_audio)
                continue
            await loop.run_in_executor(None, _tocar_audio, nome_audio, True)

    try:
        await asyncio.gather(produtor(), consumidor())
    except Exception as e:
        print(f"🤯 Erro durante a fala otimizada: {e}")
    finally:
        if tts_is_active.is_set():
            tts_is_active.clear()


def _tocar_audio_rapido_thread(caminho):
    """Função auxiliar para a thread de áudio rápido gerenciar o semáforo."""
    tts_is_active.set()
    try:
        _tocar_audio(caminho, False)
    finally:
        if tts_is_active.is_set():
            tts_is_active.clear()


def falar_rapido(nome_arquivo):
    """Toca um arquivo de áudio curto em uma thread separada."""
    if tts_is_active.is_set():
        parar_fala()
        time.sleep(0.1)
    nome_seguro = nome_arquivo.replace("!", "").replace("?", "")
    if not nome_seguro.lower().endswith('.mp3'):
        nome_seguro += ".mp3"
    caminho_completo = os.path.join("audio_cache", nome_seguro)
    if os.path.exists(caminho_completo):
        print(f"⚡ Usando áudio do cache: '{nome_seguro}'")
        playback_thread = threading.Thread(target=_tocar_audio_rapido_thread, args=(caminho_completo,), daemon=True)
        playback_thread.start()
    else:
        print(f"⚠️ Arquivo de cache de áudio não encontrado: {caminho_completo}")