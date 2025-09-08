# alarme_player.py

import sys
import asyncio
import os
import pygame
import edge_tts
import time


async def falar_alarme(texto: str):
    """
    Usa a biblioteca edge_tts para falar o texto do alarme.
    """
    try:
        nome_audio = "alarme_fala_temp.mp3"
        # --- MUDANÇA AQUI ---
        comunicador = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural")
        # --- FIM DA MUDANÇA ---
        await comunicador.save(nome_audio)

        pygame.mixer.music.load(nome_audio)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        if os.path.exists(nome_audio):
            os.remove(nome_audio)
    except Exception as e:
        print(f"Erro ao falar alarme: {e}")


def tocar_som_alarme():
    """
    Toca um som de alarme repetidamente.
    """
    try:
        # Você pode trocar 'alarme.mp3' pelo som que preferir
        caminho_som = os.path.join("audio_cache", "alarme.mp3")

        if not os.path.exists(caminho_som):
            caminho_som = os.path.join("audio_cache", "Ok.mp3")
            if not os.path.exists(caminho_som):
                print("Nenhum som de alarme encontrado.")
                return

        print(f"Tocando som: {caminho_som}")
        pygame.mixer.music.load(caminho_som)
        # Toca 3 vezes em loop
        for _ in range(3):
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            time.sleep(1)  # Pausa entre as repetições

    except Exception as e:
        print(f"Erro ao tocar som do alarme: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mensagem_alarme = " ".join(sys.argv[1:])
        print(f"Alarme disparado: {mensagem_alarme}")

        pygame.init()
        pygame.mixer.init()

        asyncio.run(falar_alarme(f"Alarme: {mensagem_alarme}"))
        tocar_som_alarme()

        pygame.quit()
    else:
        print("Nenhuma mensagem de alarme fornecida.")