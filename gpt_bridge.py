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


async def perguntar_ao_gpt(mensagem_usuario):
    """
    Envia um prompt de TEXTO para o modelo Gemini e trata respostas vazias.
    """
    print("🧠 Enviando prompt de texto para o Google Gemini...")
    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash-latest',
            system_instruction="Você é a assistente LISA. Responda perguntas de forma direta e clara."
        )
        response = await model.generate_content_async(mensagem_usuario)

        if not response.parts:
            print("⚠️ Resposta do Gemini foi bloqueada ou retornou vazia (provavelmente filtro de segurança).")
            return "Não posso responder a isso."

        print("✅ Resposta de texto recebida do Gemini.")
        return response.text.strip()
    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini (texto): {e}")
        return "Desculpe, estou com problemas de conexão com minha IA."


async def descrever_imagem(caminho_imagem, prompt_texto):
    """
    Envia uma IMAGEM e um prompt de texto para o Gemini e trata respostas vazias.
    """
    print(f"🖼️  Enviando imagem '{caminho_imagem}' para análise do Gemini...")
    try:
        img = PIL.Image.open(caminho_imagem)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = await model.generate_content_async([prompt_texto, img])

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


async def gerar_codigo_com_gpt(prompt_usuario: str) -> str:
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
        response = await model.generate_content_async(f"Crie um script Python que faça o seguinte: {prompt_usuario}")

        if not response.parts:
            print("⚠️ Geração de código bloqueada ou retornou vazia.")
            return None

        codigo_limpo = re.sub(r'^```python\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)

        print("✅ Código recebido do Gemini.")
        return codigo_limpo
    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini (código): {e}")
        return None


async def alterar_codigo_com_gpt(codigo_anterior: str, pedido_de_alteracao: str) -> str:
    """
    Envia um código existente e um pedido de alteração para a IA.
    """
    print("🤖 Enviando prompt de alteração de código para o Google Gemini...")
    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash-latest',
            system_instruction=(
                "Você é um assistente de programação especialista em Python. "
                "Sua tarefa é modificar o código Python fornecido de acordo com o pedido do usuário. "
                "Retorne APENAS o código Python completo e modificado. "
                "Não inclua explicações, comentários desnecessários, ou a palavra 'python' no início do código."
            )
        )
        prompt_completo = (
            f"Aqui está um código Python:\n\n```python\n{codigo_anterior}\n```\n\n"
            f"Por favor, modifique este código para fazer o seguinte: {pedido_de_alteracao}"
        )
        response = await model.generate_content_async(prompt_completo)

        if not response.parts:
            print("⚠️ Alteração de código bloqueada ou retornou vazia.")
            return None

        codigo_limpo = re.sub(r'^```python\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)

        print("✅ Código alterado recebido do Gemini.")
        return codigo_limpo
    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini (alteração de código): {e}")
        return None