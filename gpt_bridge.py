# gpt_bridge.py (Com tratamento de respostas vazias/bloqueadas)

import os
import google.generativeai as genai
from dotenv import load_dotenv
import PIL.Image
import re

# Carrega as variáveis de ambiente
load_dotenv()

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Chave de API do Google (GOOGLE_API_KEY) não encontrada.")
        genai.configure(api_key="CHAVE_INVALIDA")
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    print(f"🤯 Erro ao configurar a API do Gemini: {e}")


def perguntar_ao_gpt(mensagem_usuario):
    """
    Envia um prompt de TEXTO para o modelo Gemini e trata respostas vazias.
    """
    print("🧠 Enviando prompt de texto para o Google Gemini...")
    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash-latest',
            system_instruction="Você é a assistente LISA. Responda perguntas de forma direta e clara."
        )
        response = model.generate_content(mensagem_usuario)

        if not response.parts:
            print("⚠️ Resposta do Gemini foi bloqueada ou retornou vazia (provavelmente filtro de segurança).")
            return "Não posso responder a isso."

        print("✅ Resposta de texto recebida do Gemini.")
        return response.text.strip()
    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini (texto): {e}")
        return "Desculpe, estou com problemas de conexão com minha IA."


def descrever_imagem(caminho_imagem, prompt_texto):
    """
    Envia uma IMAGEM e um prompt de texto para o Gemini e trata respostas vazias.
    """
    print(f"🖼️  Enviando imagem '{caminho_imagem}' para análise do Gemini...")
    try:
        img = PIL.Image.open(caminho_imagem)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content([prompt_texto, img])

        if not response.parts:
            print("⚠️ Análise de imagem do Gemini foi bloqueada ou retornou vazia.")
            return "Não consegui processar o conteúdo desta imagem."

        print("✅ Análise de imagem recebida do Gemini.")
        return response.text.strip()
    except FileNotFoundError:
        print(f"❌ Erro: Imagem não encontrada em '{caminho_imagem}'")
        return "Desculpe, não consegui encontrar o arquivo de imagem."
    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini (imagem): {e}")
        return "Desculpe, não consegui analisar a imagem."


def gerar_codigo_com_gpt(prompt_usuario: str) -> str:
    """
    Envia um prompt para o Gemini com foco em gerar apenas código Python.
    """
    print("🤖 Enviando prompt de geração de código para o Google Gemini...")
    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash-latest',
            system_instruction=(
                "Você é um assistente de programação especialista em Python. "
                "Sua tarefa é gerar APENAS o código Python funcional que resolve o pedido do usuário. "
                "Não inclua explicações, comentários desnecessários, ou a palavra 'python' no início do código. "
                "O código deve ser completo e pronto para ser executado."
            )
        )
        response = model.generate_content(f"Crie um script Python que faça o seguinte: {prompt_usuario}")

        if not response.parts:
            print("⚠️ Geração de código bloqueada ou retornou vazia.")
            return None

        # Limpa a resposta para remover ```python e ``` do início e fim
        codigo_limpo = re.sub(r'^```python\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)

        print("✅ Código recebido do Gemini.")
        return codigo_limpo
    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini (código): {e}")
        return None