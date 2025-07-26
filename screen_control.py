# screen_control.py (Com a correção final para atalhos)

import pyautogui
import time
import os
import pyperclip
from utils.vision import clicar_em_palavra
from utils.tools import listar_todos_apps_acessiveis, encontrar_app_por_nome
from pywinauto import Desktop
from difflib import SequenceMatcher
from datetime import datetime

# --- DICIONÁRIO COMPLETO DE TECLAS E SINÔNIMOS ---
# (Seu KEY_MAP original, está perfeito e não foi alterado)
KEY_MAP = {
    'enter': 'enter', 'enviar': 'enter', 'confirma': 'enter', 'confirmar': 'enter',
    'espaço': 'space', 'space': 'space',
    'backspace': 'backspace', 'voltar': 'backspace', 'apagar': 'backspace', 'excluir': 'backspace',
    'tab': 'tab', 'tabulação': 'tab',
    'esc': 'esc', 'escape': 'esc', 'escapar': 'esc',
    'delete': 'delete', 'del': 'delete', 'deletar': 'delete',
    'shift': 'shift', 'shift esquerdo': 'shiftleft', 'shift direito': 'shiftright',
    'ctrl': 'ctrl', 'control': 'ctrl', 'control esquerdo': 'ctrlleft', 'control direito': 'ctrlright',
    'alt': 'alt', 'alt esquerdo': 'altleft', 'alt direito': 'altright',
    'windows': 'win', 'win': 'win', 'tecla windows': 'win', 'iniciar': 'win',
    'seta para cima': 'up', 'cima': 'up',
    'seta para baixo': 'down', 'baixo': 'down',
    'seta para esquerda': 'left', 'esquerda': 'left',
    'seta para direita': 'right', 'direita': 'right',
    'home': 'home', 'início': 'home',
    'end': 'end', 'fim': 'end',
    'page up': 'pageup', 'página para cima': 'pageup',
    'page down': 'pagedown', 'página para baixo': 'pagedown',
    'insert': 'insert', 'inserir': 'insert',
    'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4', 'f5': 'f5', 'f6': 'f6',
    'f7': 'f7', 'f8': 'f8', 'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
    'caps lock': 'capslock', 'fixar maiúsculas': 'capslock',
    'num lock': 'numlock',
    'scroll lock': 'scrolllock',
    'asterisco': '*', 'multiplicar': '*',
    'mais': '+', 'soma': '+',
    'menos': '-', 'subtrair': '-',
    'barra': '/', 'dividir': '/',
    'ponto': '.', 'vírgula': ',',
    **{chr(i): chr(i) for i in range(97, 123)},
    **{str(i): str(i) for i in range(10)},
}


# --- INÍCIO DA CORREÇÃO ---
def apertar_tecla(tecla_falada):
    """
    CORRIGIDO: Agora entende e executa atalhos (ex: 'ctrl+c')
    e também teclas únicas.
    """
    tecla_falada = tecla_falada.lower().strip()

    # 1. Verifica se é um atalho (contém '+')
    if '+' in tecla_falada:
        teclas_do_atalho = [key.strip() for key in tecla_falada.split('+')]
        try:
            # Usa a função hotkey, que é a correta para combinações
            pyautogui.hotkey(*teclas_do_atalho)
            print(f"⌨️  Atalho '{tecla_falada}' pressionado.")
            return True
        except Exception as e:
            print(f"❌ Erro ao pressionar atalho '{tecla_falada}': {e}")
            return False

    # 2. Se não for um atalho, procura a tecla no dicionário
    tecla_real = KEY_MAP.get(tecla_falada)
    if tecla_real:
        try:
            pyautogui.press(tecla_real)
            print(f"⌨️  Tecla '{tecla_real}' pressionada.")
            return True
        except Exception as e:
            print(f"❌ Erro ao pressionar tecla '{tecla_real}': {e}")
            return False

    # 3. Se não achou de nenhuma forma, avisa que não reconheceu
    print(f"❌ Tecla ou atalho '{tecla_falada}' não reconhecido.")
    return False
# --- FIM DA CORREÇÃO ---


def executar_acao_na_tela(app_falado):
    if not app_falado: print("⚠️ Alvo para abrir não especificado."); return False
    caminho_app = None
    if "explorer" in app_falado or "arquivos" in app_falado:
        os.system("start explorer"); caminho_app = "explorer"
    elif app_falado == "configurações":
        os.system("start ms-settings:"); caminho_app = "configurações"
    else:
        apps = listar_todos_apps_acessiveis()
        caminho_encontrado = encontrar_app_por_nome(app_falado, apps)
        if caminho_encontrado: os.startfile(caminho_encontrado); caminho_app = caminho_encontrado
    if caminho_app:
        print(f"🟢 '{app_falado}' executado. Aguardando a janela aparecer...")
        time.sleep(3)
        try:
            janela_app = pyautogui.getActiveWindow()
            if janela_app: janela_app.maximize(); print("✅ Janela maximizada.")
        except Exception as e: print(f"⚠️ Não foi possível maximizar a janela: {e}")
        return True
    else: print(f"❌ Nenhum aplicativo correspondente a '{app_falado}' encontrado."); return False


def tirar_print():
    try:
        pasta_prints = os.path.join(os.path.expanduser('~'), 'Pictures', 'LISA_Prints')
        os.makedirs(pasta_prints, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_arquivo = f"Print_{timestamp}.png"
        caminho_completo = os.path.join(pasta_prints, nome_arquivo)
        pyautogui.screenshot(caminho_completo)
        print(f"📸 Print salvo em: {caminho_completo}")
        return caminho_completo
    except Exception as e: print(f"🤯 Ocorreu um erro ao tentar tirar o print: {e}"); return None


def copiar_arquivo_selecionado():
    try:
        time.sleep(0.2); pyautogui.hotkey('ctrl', 'c')
        print("✅ Comando 'Copiar Arquivo' (Ctrl+C) executado.")
        return True
    except Exception as e: print(f"⚠️ Erro ao tentar copiar o arquivo: {e}"); return False


def copiar_caminho_selecionado():
    try:
        time.sleep(0.2); pyautogui.hotkey('ctrl', 'shift', 'c'); time.sleep(0.2)
        caminho_com_aspas = pyperclip.paste()
        caminho_sem_aspas = caminho_com_aspas.strip().strip('"')
        pyperclip.copy(caminho_sem_aspas)
        print("✅ Comando 'Copiar Caminho' executado e limpo.")
        return True
    except Exception as e: print(f"⚠️ Erro ao tentar copiar o caminho: {e}"); return False


def colar():
    try:
        pyautogui.hotkey('ctrl', 'v'); print("📝 Conteúdo colado.")
        return True
    except Exception as e: print(f"⚠️ Erro ao tentar colar: {e}"); return False


def digitar_texto(texto):
    time.sleep(1); pyautogui.write(texto, interval=0.05)
    print("⌨️ Texto digitado.")


def rolar_tela(sentido="baixo", quantidade=720):
    passos = 5; intervalo = 0.01
    rolagem_por_passo = quantidade // passos
    if sentido in ["baixo", "descer", "para baixo", "pra baixo"]:
        print("⬇️ Rolando para baixo...")
        for _ in range(passos): pyautogui.scroll(-rolagem_por_passo); time.sleep(intervalo)
    elif sentido in ["cima", "subir", "para cima", "pra cima"]:
        print("⬆️ Rolando para cima...")
        for _ in range(passos): pyautogui.scroll(rolagem_por_passo); time.sleep(intervalo)


def fechar_janela_por_nome(nome_janela_falado):
    print(f"🔎 Procurando por uma janela parecida com '{nome_janela_falado}' para fechar...")
    try:
        desktop = Desktop(backend="win32"); janelas = desktop.windows()
        if not janelas: print("❌ Nenhuma janela aberta encontrada."); return None, 0
        melhor_match = {'janela': None, 'score': 0.0, 'titulo': ''}
        for janela in janelas:
            titulo = janela.window_text()
            if titulo and "Program Manager" not in titulo:
                score = SequenceMatcher(None, nome_janela_falado.lower(), titulo.lower()).ratio()
                if score > melhor_match['score']:
                    melhor_match['score'] = score; melhor_match['janela'] = janela; melhor_match['titulo'] = titulo
        if melhor_match['janela']:
            janela_para_fechar = melhor_match['janela']; titulo_real = melhor_match['titulo']; score_final = melhor_match['score']
            print(f"✅ Melhor correspondência encontrada: '{titulo_real}' (Score: {score_final:.2f}). Fechando...")
            janela_para_fechar.close()
            return titulo_real, score_final
        else: print(f"❌ Nenhuma janela com título visível foi encontrada."); return None, 0
    except Exception as e: print(f"🤯 Ocorreu um erro ao tentar fechar a janela: {e}"); return None, 0