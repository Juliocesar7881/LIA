# code_writer.py (Versão com IA para abrir em editor online e colar o código)

import webbrowser
import pyperclip
from gpt_bridge import gerar_codigo_com_gpt, alterar_codigo_com_gpt
import pyautogui
import time


async def gerar_codigo_e_abrir_no_navegador(descricao_pedido: str):
    """
    Usa a IA para gerar código Python, copia, abre um editor online e cola o código,
    substituindo qualquer conteúdo existente.
    """
    print(f"💻 Gerando código para: '{descricao_pedido}'...")
    try:
        codigo_gerado = await gerar_codigo_com_gpt(descricao_pedido)

        if not codigo_gerado or "não posso" in codigo_gerado.lower() or "desculpe" in codigo_gerado.lower():
            print("❌ A IA não conseguiu gerar um código válido.")
            return "Desculpe, não consegui gerar um código para isso.", None

        pyperclip.copy(codigo_gerado)
        print("✅ Código copiado para a área de transferência.")

        url_editor = "https://trinket.io/embed/python3"
        print(f"🌍 Abrindo o navegador em: {url_editor}...")
        webbrowser.open(url_editor)

        time.sleep(5)

        # --- INÍCIO DA LÓGICA SUGERIDA POR VOCÊ ---
        pyautogui.hotkey('ctrl', 'a')  # Seleciona todo o texto existente no editor
        time.sleep(0.2)  # Pequena pausa para garantir que o comando foi processado
        pyautogui.hotkey('ctrl', 'v')  # Cola o novo código, substituindo o antigo
        # --- FIM DA LÓGICA ---

        print("📋 Código colado no editor.")

        return "Ok, preparei o seu código e já colei no editor online para si.", codigo_gerado

    except Exception as e:
        print(f"🤯 Erro ao gerar o código ou abrir o navegador: {e}")
        return "Ocorreu um erro ao tentar preparar o seu ambiente de programação.", None


async def alterar_codigo_e_abrir_no_navegador(codigo_anterior: str, pedido_de_alteracao: str):
    """
    Pega um código existente, pede à IA para alterá-lo, e abre o resultado no navegador,
    substituindo qualquer conteúdo existente.
    """
    print(f"✍️  Modificando código com o pedido: '{pedido_de_alteracao}'...")
    try:
        novo_codigo = await alterar_codigo_com_gpt(codigo_anterior, pedido_de_alteracao)

        if not novo_codigo or "não posso" in novo_codigo.lower() or "desculpe" in novo_codigo.lower():
            print("❌ A IA não conseguiu alterar o código.")
            return "Desculpe, não consegui modificar o código como pediu.", None

        pyperclip.copy(novo_codigo)
        print("✅ Novo código copiado para a área de transferência.")

        url_editor = "https://trinket.io/embed/python3"
        print(f"🌍 Abrindo o navegador em: {url_editor}...")
        webbrowser.open(url_editor)

        time.sleep(5)

        # --- LÓGICA APLICADA AQUI TAMBÉM ---
        pyautogui.hotkey('ctrl', 'a')  # Seleciona tudo
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'v')  # Cola por cima
        # --- FIM DA LÓGICA ---

        print("📋 Código alterado colado no editor.")

        return "Ok, modifiquei o código e já colei a nova versão no editor para si.", novo_codigo

    except Exception as e:
        print(f"🤯 Erro ao alterar o código ou abrir o navegador: {e}")
        return "Ocorreu um erro ao tentar modificar o código.", None