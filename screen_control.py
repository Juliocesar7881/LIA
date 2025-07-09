# screen_control.py (Versão Canônica e Corrigida)

import pyautogui
import time
import os
import pyperclip
from utils.tools import listar_todos_apps_acessiveis, encontrar_app_por_nome
from utils.vision import clicar_em_palavra

def executar_acao_na_tela(comando):
    print(f"[DEBUG-SC] A função 'executar_acao_na_tela' foi chamada com o comando: '{comando}'")
    app_falado = comando.replace("abrir", "").strip().lower()

    # Se o nome do app ficar vazio, não faz nada
    if not app_falado:
        print("⚠️ Alvo para abrir não especificado.")
        return

    caminho_app = None
    # Tratamento especial para comandos que não são apps de um arquivo
    if "explorer" in app_falado or "arquivos" in app_falado:
        os.system("start explorer")
        caminho_app = "explorer"
    elif app_falado == "configurações":
        os.system("start ms-settings:")
        caminho_app = "configurações"
    else:
        # Lógica para encontrar e abrir outros aplicativos
        print(f"[DEBUG-SC] Procurando pelo app '{app_falado}'...")
        apps = listar_todos_apps_acessiveis()
        caminho_encontrado = encontrar_app_por_nome(app_falado, apps)
        if caminho_encontrado:
            os.startfile(caminho_encontrado)
            caminho_app = caminho_encontrado

    # Maximiza a janela se um app foi aberto
    if caminho_app:
        print(f"🟢 '{app_falado}' executado. Aguardando a janela aparecer...")
        time.sleep(3)
        try:
            janela_app = pyautogui.getActiveWindow()
            if janela_app:
                janela_app.maximize()
                print("✅ Janela maximizada.")
        except Exception as e:
            print(f"⚠️ Não foi possível maximizar a janela: {e}")
    else:
        print(f"❌ Nenhum aplicativo correspondente a '{app_falado}' encontrado.")


def copiar_arquivo_selecionado():
    """Simula um Ctrl+C para copiar o ARQUIVO selecionado."""
    try:
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        print("✅ Comando 'Copiar Arquivo' (Ctrl+C) executado.")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao tentar copiar o arquivo: {e}")
        return False

def copiar_caminho_selecionado():
    """Simula um Ctrl+Shift+C para copiar o CAMINHO do arquivo e limpa as aspas."""
    try:
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'shift', 'c')
        time.sleep(0.2)
        caminho_com_aspas = pyperclip.paste()
        caminho_sem_aspas = caminho_com_aspas.strip().strip('"')
        pyperclip.copy(caminho_sem_aspas)
        print("✅ Comando 'Copiar Caminho' executado e limpo.")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao tentar copiar o caminho: {e}")
        return False

def colar():
    """Simula um Ctrl+V para colar o que estiver na área de transferência."""
    try:
        pyautogui.hotkey('ctrl', 'v')
        print("📝 Conteúdo colado.")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao tentar colar: {e}")
        return False

def digitar_texto(texto):
    time.sleep(1)
    pyautogui.write(texto, interval=0.05)
    print("⌨️ Texto digitado.")

def apertar_tecla(comando):
    partes = comando.strip().split()
    if not partes: return
    tecla = partes[0].lower()
    equivalencias = { "enviar": "enter", "envia": "enter", "confirmar": "enter", "espaço": "space", "espaco": "space", "voltar": "backspace", "apagar": "delete", "escapar": "esc", "cima": "up", "baixo": "down", "direita": "right", "esquerda": "left" }
    tecla = equivalencias.get(tecla, tecla)
    pyautogui.press(tecla)
    print(f"⌨️ Apertando tecla: {tecla}")

def rolar_tela(sentido="baixo", quantidade=500):
    if sentido in ["baixo", "descer", "para baixo", "pra baixo"]:
        pyautogui.scroll(-quantidade)
        print("⬇️ Rolando para baixo.")
    elif sentido in ["cima", "subir", "para cima", "pra cima"]:
        pyautogui.scroll(quantidade)
        print("⬆️ Rolando para cima.")