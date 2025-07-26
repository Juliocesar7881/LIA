# voice_control.py (Com o "freio de mão" na função parar_fala)

import speech_recognition as sr
import asyncio
import edge_tts
import os
import random
import threading
import pygame
import re

# --- Configurações Iniciais ---
pygame.mixer.init()
recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2

try:
    mic = sr.Microphone()
    with mic as source:
        print("🤫 Calibrando microfone... Por favor, fique em silêncio por 2 segundos.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"🎚️ Limiar de energia ajustado para: {recognizer.energy_threshold:.2f}.")
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
            # A verificação de interrupção agora é controlada pelo estado do mixer
            # Se parar_fala() for chamado, get_busy() se tornará False e o loop terminará.
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


# --- INÍCIO DA CORREÇÃO ---
def parar_fala():
    """
    Para a reprodução de áudio imediatamente E limpa o sinalizador de atividade,
    forçando a interrupção completa da sequência de fala.
    """
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        print("🎤 Interrompendo a fala da LISA.")

    # Esta é a parte crucial: avisa a todos os processos que a fala foi cancelada.
    if tts_is_active.is_set():
        tts_is_active.clear()


# --- FIM DA CORREÇÃO ---


# --- Funções de Geração de Voz ---
async def falar(texto):
    """
    Usa um sistema de produtor/consumidor otimizado.
    Agora respeita a interrupção imediata sinalizada por parar_fala().
    """
    if tts_is_active.is_set(): return

    parar_fala()
    texto_limpo = re.sub(r'[\*#\_`%&()]', '', str(texto))
    print(f"LISA 🗣️: {texto_limpo}")
    frases = re.split(r'(?<=[.!?])\s*', texto_limpo)
    frases_validas = [f for f in frases if f.strip()]
    if not frases_validas: return

    tts_is_active.set()
    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()

    async def produtor():
        try:
            for frase in frases_validas:
                # Se a fala foi cancelada no meio do caminho, para de gerar novos áudios.
                if not tts_is_active.is_set():
                    print("▶️ Produção de áudio interrompida.")
                    break
                nome_audio = f"fala_temp_{random.randint(1000, 9999)}.mp3"
                comunicador = edge_tts.Communicate(frase, "pt-BR-ThalitaMultilingualNeural")
                await comunicador.save(nome_audio)
                await audio_queue.put(nome_audio)
        finally:
            await audio_queue.put(None)

    async def consumidor():
        while True:
            nome_audio = await audio_queue.get()
            if nome_audio is None:
                break

            # Se a fala foi cancelada, não toca o próximo áudio da fila.
            if not tts_is_active.is_set():
                print("▶️ Fila de áudio descartada devido à interrupção.")
                if os.path.exists(nome_audio): os.remove(nome_audio)
                continue  # Pula para o próximo item da fila (para limpá-la)

            await loop.run_in_executor(None, _tocar_audio, nome_audio, True)

    try:
        await asyncio.gather(produtor(), consumidor())
    except Exception as e:
        print(f"🤯 Erro durante a fala otimizada: {e}")
    finally:
        # Garante que o sinalizador seja limpo, caso não tenha sido pela interrupção.
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
        # Se estiver falando, interrompe a fala longa para dar prioridade à resposta rápida
        parar_fala()
        time.sleep(0.1)  # Pequena pausa para garantir que a interrupção seja processada

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