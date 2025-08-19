# code_writer.py (Versão com IA para abrir em editor online)

import webbrowser
import urllib.parse
from gpt_bridge import gerar_codigo_com_gpt


def gerar_codigo_e_abrir_no_navegador(descricao_pedido: str) -> str:
    """
    Usa a IA para gerar código Python e o abre em um editor online (Trinket.io).

    Args:
        descricao_pedido (str): A descrição do que o código deve fazer.

    Returns:
        str: Uma mensagem de sucesso ou falha.
    """
    print(f"💻 Gerando código para: '{descricao_pedido}'...")
    try:
        # 1. Gera o código usando a IA
        codigo_gerado = gerar_codigo_com_gpt(descricao_pedido)

        if not codigo_gerado or "não posso" in codigo_gerado.lower() or "desculpe" in codigo_gerado.lower():
            print("❌ A IA não conseguiu gerar um código válido.")
            return "Desculpe, não consegui gerar um código para isso."

        # 2. Prepara o código para ser enviado via URL (URL Encoding)
        codigo_encodado = urllib.parse.quote(codigo_gerado)

        # 3. Monta a URL do Trinket.io com o código pré-carregado
        # O parâmetro 'run' faz com que o código seja inserido no editor
        url_final = f"https://trinket.io/embed/python3?run={codigo_encodado}"

        # 4. Abre o navegador com o link
        print(f"🌍 Abrindo o navegador em: https://trinket.io/...")
        webbrowser.open(url_final)

        return "Ok, preparei o seu código. Abri um editor online para você revisar e executar."

    except Exception as e:
        print(f"🤯 Erro ao gerar o código ou abrir o navegador: {e}")
        return "Ocorreu um erro ao tentar preparar o seu ambiente de programação."