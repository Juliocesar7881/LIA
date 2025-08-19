# youtube_downloader.py (Versão com yt-dlp)

import os
import yt_dlp

def baixar_media_youtube(video_url: str, baixar_audio: bool = False) -> str:
    """
    Baixa um vídeo ou apenas o áudio de um link do YouTube usando yt-dlp.

    Args:
        video_url (str): O link completo do vídeo no YouTube.
        baixar_audio (bool): Se True, baixa apenas o áudio em formato mp3. Se False, baixa o vídeo completo.

    Returns:
        str: Uma mensagem de sucesso ou falha.
    """
    try:
        if baixar_audio:
            caminho_saida = os.path.join(os.path.expanduser('~'), 'Music', '%(title)s.%(ext)s')
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': caminho_saida,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': True,
            }
            pasta_destino = "Músicas"
            print("Configurado para baixar áudio em MP3...")
        else:
            caminho_saida = os.path.join(os.path.expanduser('~'), 'Videos', '%(title)s.%(ext)s')
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': caminho_saida,
                'noplaylist': True,
            }
            pasta_destino = "Vídeos"
            print("Configurado para baixar vídeo em MP4...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            titulo = info.get('title', 'título desconhecido')
            print(f"Iniciando download de: '{titulo}'")
            ydl.download([video_url])

        print(f"\n✅ Download de '{titulo}' concluído!")
        return f"Download de '{titulo}' concluído! Salvei na sua pasta de {pasta_destino}."

    except Exception as e:
        print(f"🤯 Erro durante o download com yt-dlp: {e}")
        if "is not a valid URL" in str(e):
            return "O link que você copiou não parece ser válido. Tente novamente."
        return "Ocorreu um erro ao tentar fazer o download. Verifique o console."