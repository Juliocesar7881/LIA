# file_converter.py

import os
from moviepy.editor import VideoFileClip


def converter_video_para_audio(caminho_video: str, formato_saida: str = "mp3") -> str:
    """
    Converte um arquivo de vídeo para um arquivo de áudio (ex: .mp4 para .mp3).

    Args:
        caminho_video (str): O caminho completo para o arquivo de vídeo de entrada.
        formato_saida (str): O formato do áudio de saída (por exemplo, "mp3", "wav").

    Returns:
        str: Uma mensagem indicando o sucesso ou a falha da conversão.
    """
    try:
        if not os.path.exists(caminho_video):
            return f"Erro: O arquivo de entrada '{caminho_video}' não foi encontrado."

        # Define o nome do arquivo de saída na mesma pasta do original
        base, _ = os.path.splitext(caminho_video)
        caminho_saida = f"{base}.{formato_saida}"

        print(f"Iniciando conversão de '{os.path.basename(caminho_video)}' para '{os.path.basename(caminho_saida)}'...")

        with VideoFileClip(caminho_video) as video_clip:
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(caminho_saida)

        print("✅ Conversão concluída com sucesso.")
        return f"Arquivo convertido com sucesso! Salvei como {os.path.basename(caminho_saida)}."

    except Exception as e:
        print(f"🤯 Erro durante a conversão: {e}")
        return f"Ocorreu um erro durante a conversão. Verifique o console para mais detalhes."