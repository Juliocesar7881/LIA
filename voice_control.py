# voice_control.py (versão com Modo de Audição de Alta Fidelidade)

import speech_recognition as sr
import asyncio
import edge_tts
import os
import random
import threading
import time
import pygame
import re

try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"⚠️ Erro ao inicializar o pygame.mixer: {e}")
    print("A funcionalidade de fala pode não funcionar.")


def parar_fala():
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        print("🎤 Interrompendo a fala da LISA.")
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()


def _tocar_e_limpar(nome_audio):
    if not pygame.mixer.get_init() or not os.path.exists(nome_audio):
        return
    try:
        pygame.mixer.music.load(nome_audio)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except pygame.error as e:
        print(f"Erro ao tocar áudio com pygame: {e}")
    finally:
        pygame.mixer.music.unload()
        if os.path.exists(nome_audio):
            try:
                os.remove(nome_audio)
            except (IOError, PermissionError):
                pass


async def falar(texto):
    parar_fala()
    texto_limpo = re.sub(r'[\*#\_`]', '', texto)
    print(f"LISA 🗣️: {texto_limpo}")
    frases = re.split(r'(?<=[.!?])\s*', texto_limpo)
    frases_validas = [f for f in frases if f.strip()]
    if not frases_validas:
        return
    loop = asyncio.get_event_loop()
    for frase in frases_validas:
        nome_audio = f"fala_parte_{random.randint(1000, 9999)}.mp3"
        try:
            comunicador = edge_tts.Communicate(frase, voice="pt-BR-ThalitaMultilingualNeural")
            await comunicador.save(nome_audio)
        except Exception as e:
            print(f"Erro ao gerar áudio: {e}")
            continue
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            print("Sequência de fala antiga cancelada por uma nova.")
            if os.path.exists(nome_audio):
                os.remove(nome_audio)
            break
        await loop.run_in_executor(None, _tocar_e_limpar, nome_audio)


# ===================================================================
# CONFIGURAÇÃO DE ESCUTA (MODO DE ALTA FIDELIDADE)
# ===================================================================
recognizer = sr.Recognizer()

# === MUDANÇA IMPORTANTE ===
# Desligamos o ajuste dinâmico. O threshold será fixo após a calibração inicial.
recognizer.dynamic_energy_threshold = False

# === PARÂMETROS MAIS 'PACIENTES' ===
recognizer.pause_threshold = 1  # Tempo de pausa para finalizar a frase.
recognizer.phrase_threshold = 0.3  # 'respiro' antes e depois da frase.
recognizer.non_speaking_duration = 0.4  # Tempo de silêncio para começar a escutar.
# ===================================================================

mic = None
try:
    # Lembre-se de usar o device_index correto para seu microfone!
    mic = sr.Microphone(device_index=1)

    # === CALIBRAÇÃO MAIS LONGA E IMPORTANTE ===
    print("🤫 Calibrando microfone... Por favor, fique em silêncio por 3 segundos.")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=3)
    print(
        f"🎚️ Limiar de energia fixo definido para: {recognizer.energy_threshold:.2f}. Tudo abaixo disso será ignorado.")

except Exception as e:
    print(f"⚠️ Erro ao iniciar o microfone: {e}")
    print("Verifique se o microfone (device_index=1) está correto e disponível.")