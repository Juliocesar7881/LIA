# whatsapp_bot.py (Versão Robusta com Visão Computacional)

import pyautogui
import time
import webbrowser
import asyncio
from utils.vision import clicar_em_palavra


async def enviar_mensagem_whatsapp(nome: str, mensagem: str) -> str:
    """
    Abre o WhatsApp Web, procura por um contato e envia uma mensagem de forma visual.

    Args:
        nome (str): O nome do contato.
        mensagem (str): A mensagem a ser enviada.

    Returns:
        str: Uma mensagem indicando o resultado da operação.
    """
    try:
        print(f"📨 Preparando para enviar para {nome}: {mensagem}")
        webbrowser.open("https://web.whatsapp.com")

        print("Aguardando o WhatsApp Web carregar (15 segundos)...")
        await asyncio.sleep(15)

        # 1. Clica na barra de pesquisa de conversas
        print("🔎 Procurando a barra de pesquisa...")
        if not clicar_em_palavra("Pesquisar ou começar uma nova conversa")[0]:
            if not clicar_em_palavra("Search or start new chat")[0]:  # Fallback para inglês
                return "Não consegui encontrar a barra de pesquisa do WhatsApp. A página pode não ter carregado a tempo."

        await asyncio.sleep(1)

        # 2. Digita o nome do contato para filtrar (com velocidade aumentada)
        print(f"⌨️  Digitando nome do contato: {nome}")
        pyautogui.write(nome, interval=0.05)
        await asyncio.sleep(3)  # Tempo extra para os resultados aparecerem

        # 3. Clica no contato na lista da esquerda
        print(f"🎯 Procurando pelo contato '{nome}' na lista para clicar...")
        if not clicar_em_palavra(nome)[0]:
            # Se não encontrar pelo nome exato, tenta selecionar o primeiro resultado
            pyautogui.press('down')
            await asyncio.sleep(0.5)
            pyautogui.press('enter')
            print("Contato não encontrado pelo nome, tentando selecionar o primeiro da lista.")

        await asyncio.sleep(2)

        # 4. Digita a mensagem na caixa de texto (com velocidade aumentada)
        print(f"✍️  Digitando a mensagem...")
        pyautogui.write(mensagem, interval=0.02)
        await asyncio.sleep(1)

        # 5. Pressiona Enter para enviar
        pyautogui.press("enter")
        print("✅ Mensagem enviada com sucesso.")
        return "Mensagem enviada com sucesso."

    except Exception as e:
        print(f"⚠️ Erro ao enviar mensagem pelo WhatsApp: {e}")
        return "Ocorreu um erro, tente novamente..."