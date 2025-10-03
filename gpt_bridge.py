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


def _definir_personalidade(humor: int, contexto_memoria: str = "") -> str:
    """Define a instrução de sistema com base no humor e no contexto da memória."""
    instrucao_base = "Você é a assistente LIA."
    if humor <= 25:
        personalidade = "Responda de forma direta, clara, concisa e mais séria, como uma assistente profissional."
    elif humor <= 75:
        personalidade = "Responda de forma amigável e prestativa, mantendo um tom equilibrado."
    else:  # humor > 75
        personalidade = "Responda de forma bem-humorada, criativa e um pouco engraçada, usando toques de ironia ou piadas quando apropriado, mas sem deixar de ser útil."

    instrucao_final = f"{instrucao_base} {personalidade}"

    if contexto_memoria:
        instrucao_final += f"\n\n--- CONTEXTO IMPORTANTE DE MEMÓRIAS RECENTES E FATOS SOBRE O USUÁRIO ---\n{contexto_memoria}\n--- FIM DO CONTEXTO ---"

    return instrucao_final


async def perguntar_ao_gpt(mensagem_usuario, humor_lia: int, contexto_memoria: str = ""):
    """
    Envia um prompt de TEXTO para o modelo Gemini, agora com contexto de memória.
    """
    print(
        f"🧠 Enviando prompt para o Google Gemini (Humor: {humor_lia}%, Contexto: {'Sim' if contexto_memoria else 'Não'})...")
    try:
        instrucao_sistema = _definir_personalidade(humor_lia, contexto_memoria)
        # --- USANDO O MODELO CORRETO E MODERNO ---
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash',
            system_instruction=instrucao_sistema
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


async def summarize_memories_with_gpt(memories_text: str):
    """Envia um bloco de texto de memórias para ser resumido pela IA."""
    try:
        system_instruction = (
            "Você é um especialista em análise de logs de conversas. Sua tarefa é ler a lista de eventos e conteúdos a seguir e "
            "resumi-la em 2 ou 3 pontos chave e concisos. Extraia apenas as informações mais importantes sobre os interesses, "
            "o contexto e os fatos principais sobre o usuário. Responda apenas com os pontos chave, de forma impessoal."
        )
        # --- USANDO O MODELO CORRETO E MODERNO ---
        model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=system_instruction)
        prompt = f"Analise e resuma os seguintes logs de interação com um usuário:\n\n{memories_text}"
        response = await model.generate_content_async(prompt)

        if not response.parts:
            return ""
        return response.text.strip()
    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini para resumir memórias: {e}")
        return ""


async def extrair_fatos_da_memoria(memories_text: str):
    """Envia um bloco de memórias para a IA e pede para extrair fatos permanentes."""
    try:
        system_instruction = (
            "Você é um analista de dados especialista em extrair informações nucleares de conversas. "
            "Sua tarefa é ler os logs de interação a seguir e extrair APENAS fatos que parecem ser permanentes ou de longo prazo sobre o usuário. "
            "Ignore informações temporárias (como perguntas sobre o tempo de hoje ou cotações de um dia específico). "
            "Se um fato for aprendido, retorne-o em uma lista, onde cada fato está em uma nova linha e começa com um hífen. "
            "Exemplos de BONS fatos a extrair: '- O nome do usuário é Loops', '- O usuário mora em Curitiba', '- O time de futebol do usuário é o Palmeiras'. "
            "Exemplos de informações RUINS para IGNORAR: '- O usuário pediu uma piada', '- O usuário perguntou as notícias'. "
            "Se nenhum fato permanente for encontrado, retorne uma resposta vazia."
        )
        # --- USANDO O MODELO CORRETO E MODERNO ---
        model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=system_instruction)
        prompt = f"Analise os seguintes logs e extraia os fatos permanentes:\n\n{memories_text}"
        response = await model.generate_content_async(prompt)

        if not response.parts:
            return []

        fatos = [line.strip().lstrip('-').strip() for line in response.text.strip().split('\n') if line.strip()]
        return fatos

    except Exception as e:
        print(f"🤯 Erro ao chamar a API do Gemini para extrair fatos: {e}")
        return []


async def descrever_imagem(caminho_imagem, prompt_texto):
    """
    Envia uma IMAGEM e um prompt de texto para o Gemini e trata respostas vazias.
    """
    print(f"🖼️  Enviando imagem '{caminho_imagem}' para análise do Gemini...")
    try:
        img = PIL.Image.open(caminho_imagem)
        # --- USANDO O MODELO CORRETO E MODERNO ---
        model = genai.GenerativeModel('models/gemini-2.5-flash')
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
        # --- USANDO O MODELO CORRETO E MODERNO ---
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash',
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
        # --- USANDO O MODELO CORRETO E MODERNO ---
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash',
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