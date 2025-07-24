# transcriber.py (versão com retorno de sinal)

import os
import pyperclip
import whisper

print("Carregando modelo de transcrição Whisper (pode demorar na primeira vez)...")
try:
    model = whisper.load_model("base")
    print("✅ Modelo Whisper carregado com sucesso.")
except Exception as e:
    print(f"❌ Erro ao carregar o modelo Whisper: {e}")
    model = None


def transcrever_audio_copiado():
    """
    Transcreve o áudio e retorna um tuple: (sucesso, mensagem/nome_do_arquivo).
    """
    if not model:
        return (False, "Erro: O modelo de transcrição não pôde ser carregado.")

    try:
        caminho_arquivo = pyperclip.paste().strip()
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Erro: O caminho '{caminho_arquivo}' não foi encontrado.")
            return (False, "Erro: o arquivo copiado não foi encontrado.")

        print(f"🎙️ Transcrevendo o arquivo localmente: {caminho_arquivo}")
        result = model.transcribe(caminho_arquivo)
        texto_transcrito = result["text"]
        print("✅ Transcrição local concluída.")
        pyperclip.copy(texto_transcrito)

        # Retorna SUCESSO e o NOME do arquivo de áudio para a confirmação rápida
        return (True, "OkTransscrito.mp3")

    except Exception as e:
        print(f"🤯 Ocorreu um erro inesperado durante a transcrição local: {e}")
        return (False, "Ocorreu um erro durante a transcrição.")
