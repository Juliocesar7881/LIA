# transcriber.py (Com verificação de tipo de arquivo)

import whisper
import pyperclip
import os
import re

print("Carregando modelo de transcrição Whisper (pode demorar na primeira vez)...")
try:
    model = whisper.load_model("base")
    print("✅ Modelo Whisper carregado com sucesso.")
except Exception as e:
    model = None
    print(f"❌ Falha ao carregar o modelo Whisper: {e}")

# --- INÍCIO DA MUDANÇA ---
# Lista de extensões de arquivo que o Whisper provavelmente consegue processar
EXTENSOES_VALIDAS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".mov", ".avi"}


# --- FIM DA MUDANÇA ---

def extrair_caminho_do_clipboard():
    """Pega o conteúdo da área de transferência e retorna um caminho de arquivo válido."""
    clipboard_content = pyperclip.paste()
    match = re.search(r'\"?([A-Z]:\\[^:\n\r"]+)\"?', clipboard_content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def transcrever_localmente(caminho_arquivo):
    """Transcreve um arquivo de áudio ou vídeo localmente usando Whisper."""
    if not model:
        return "O modelo de transcrição não está disponível."
    if not os.path.exists(caminho_arquivo):
        return "Arquivo não encontrado para transcrição."

    # --- INÍCIO DA MUDANÇA ---
    # Verifica se a extensão do arquivo é de áudio ou vídeo antes de tentar
    nome_arquivo, extensao = os.path.splitext(caminho_arquivo)
    if extensao.lower() not in EXTENSOES_VALIDAS:
        print(f"❌ Erro: Arquivo '{caminho_arquivo}' não é um formato de áudio/vídeo suportado.")
        return "Este não parece ser um arquivo de áudio ou vídeo."
    # --- FIM DA MUDANÇA ---

    try:
        print(f"🎙️ Transcrevendo o arquivo localmente: {caminho_arquivo}")
        result = model.transcribe(caminho_arquivo)
        texto_transcrito = result["text"].strip()
        print("✅ Transcrição local concluída.")
        return texto_transcrito
    except Exception as e:
        # A mensagem de erro agora será mais genérica, pois já filtramos o caso mais comum
        print(f"🤯 Erro durante a transcrição local: {e}")
        return f"Ocorreu um erro ao processar o arquivo."


def transcrever_audio_copiado():
    """Pega um caminho de arquivo da área de transferência e o transcreve."""
    caminho_do_arquivo = extrair_caminho_do_clipboard()
    if caminho_do_arquivo:
        texto = transcrever_localmente(caminho_do_arquivo)
        return texto
    else:
        return "Não encontrei um caminho de arquivo válido na sua área de transferência."