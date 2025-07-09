# transcriber.py (versão simplificada)

import os
import pyperclip
from gpt_bridge import client


def transcrever_audio_copiado():
    """
    Pega o caminho JÁ LIMPO da área de transferência e transcreve o áudio.
    """
    try:
        caminho_arquivo = pyperclip.paste()

        # A limpeza de aspas não é mais necessária aqui
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Erro: O caminho '{caminho_arquivo}' não foi encontrado.")
            return "Erro: o arquivo copiado não foi encontrado. Tente copiar o caminho novamente."

        print(f"🎙️ Transcrevendo o arquivo: {caminho_arquivo}")

        with open(caminho_arquivo, "rb") as audio_file:
            transcricao = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        texto_transcrito = transcricao.text
        print("✅ Transcrição concluída.")
        pyperclip.copy(texto_transcrito)

        return "Transcrição concluída e copiada para a sua área de transferência!"

    except Exception as e:
        print(f"🤯 Ocorreu um erro inesperado durante a transcrição: {e}")
        return "Ocorreu um erro durante a transcrição. Verifique o console para mais detalhes."