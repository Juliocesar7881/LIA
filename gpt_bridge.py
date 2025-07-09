from openai import OpenAI
from dotenv import load_dotenv
import os

# Carrega a chave da API
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY não foi encontrada no .env")

client = OpenAI()

# Função principal para gerar resposta textual usando GPT-4o-mini
def perguntar_ao_gpt(mensagem_usuario):
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Você é a assistente LISA. Responda perguntas de forma direta e clara. Quando for um pedido de execução, tente retornar instruções ou comandos práticos."
                },
                {
                    "role": "user",
                    "content": mensagem_usuario
                }
            ],
            temperature=0.7
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro ao consultar GPT: {str(e)}"
