# whatsapp_bot.py (Versão Corrigida)

import pyautogui
import time
import webbrowser
import asyncio

# --- CORREÇÃO AQUI ---
# Importa as funções de visão e de clique dos locais corretos
from utils.vision import encontrar_elementos_por_texto
from screen_control import clicar_em_elemento


# --------------------

async def enviar_mensagem_whatsapp(nome: str, mensagem: str) -> str:
    """
    Abre o WhatsApp Web, procura por um contato e envia uma mensagem de forma visual.
    """
    try:
        print(f"📨 Preparando para enviar para {nome}: {mensagem}")
        webbrowser.open("https://web.whatsapp.com")

        print("Aguardando o WhatsApp Web carregar (15 segundos)...")
        await asyncio.sleep(15)

        # 1. Clica na barra de pesquisa de conversas
        print("🔎 Procurando a barra de pesquisa...")
        elementos_pesquisa = encontrar_elementos_por_texto("Pesquisar ou começar uma nova conversa")
        if not elementos_pesquisa:
            elementos_pesquisa = encontrar_elementos_por_texto("Search or start new chat")  # Fallback para inglês

        if not elementos_pesquisa:
            return "Não consegui encontrar a barra de pesquisa do WhatsApp. A página pode não ter carregado a tempo."

        clicar_em_elemento(elementos_pesquisa[0])
        await asyncio.sleep(1)

        # 2. Digita o nome do contato para filtrar
        print(f"⌨️  Digitando nome do contato: {nome}")
        pyautogui.write(nome, interval=0.05)
        await asyncio.sleep(3)  # Tempo para os resultados aparecerem

        # 3. Clica no contato na lista da esquerda
        print(f"🎯 Procurando pelo contato '{nome}' na lista para clicar...")
        elementos_contato = encontrar_elementos_por_texto(nome)
        if not elementos_contato:
            # Se não encontrar pelo nome exato, tenta selecionar o primeiro resultado
            pyautogui.press('down')
            await asyncio.sleep(0.5)
            pyautogui.press('enter')
            print("Contato não encontrado pelo nome, tentando selecionar o primeiro da lista.")
        else:
            clicar_em_elemento(elementos_contato[0])

        await asyncio.sleep(2)

        # 4. Digita a mensagem na caixa de texto
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