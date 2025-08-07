# screen_control.py (Com a nova função para abrir abas)

import pyautogui
import time
import os
import pyperclip
import pytesseract
from pywinauto import Desktop
from difflib import SequenceMatcher
from datetime import datetime
from utils.tools import listar_todos_apps_acessiveis, encontrar_app_por_nome
from utils.vision import encontrar_elemento_por_texto
import cv2
import numpy as np

# --- DICIONÁRIO DE TECLAS (sem alterações) ---
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


# --- NOVA FUNÇÃO ADICIONADA ---
def abrir_nova_aba():
    """Abre uma nova aba no navegador usando o atalho universal Ctrl+T."""
    try:
        print("📑 Abrindo nova aba (Ctrl+T)...")
        pyautogui.hotkey('ctrl', 't')
        return True
    except Exception as e:
        print(f"🤯 Erro ao tentar abrir nova aba: {e}")
        return False

# --- FUNÇÕES DE NAVEGAÇÃO (ATUALIZADAS) ---

def fechar_anuncio_na_tela():
    """
    Procura por um 'X' ou o texto "fechar" para fechar anúncios.
    Se uma nova aba for aberta, ela a fecha automaticamente.
    """
    print("🔎 Procurando por anúncio para fechar...")
    try:
        janela_original = pyautogui.getActiveWindow()
        if not janela_original: return False
        titulo_original = janela_original.title

        ponto_clique = None

        print("   -> Tentando encontrar o texto 'fechar'...")
        posicao_texto_fechar = encontrar_elemento_por_texto("fechar")
        if posicao_texto_fechar:
            x = posicao_texto_fechar['left'] + posicao_texto_fechar['width'] // 2
            y = posicao_texto_fechar['top'] + posicao_texto_fechar['height'] // 2
            ponto_clique = (x, y)
            print(f"✅ Texto 'fechar' encontrado. Preparando para clicar em {ponto_clique}...")

        if not ponto_clique:
            print("   -> Texto não encontrado. Tentando encontrar ícone 'X'...")
            screenshot_pil = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
            gray_screenshot = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            template = np.zeros((20, 20), dtype=np.uint8)
            cv2.line(template, (2, 2), (18, 18), 255, 3)
            cv2.line(template, (2, 18), (18, 2), 255, 3)
            res = cv2.matchTemplate(gray_screenshot, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.7
            loc = np.where(res >= threshold)

            largura_tela, altura_tela = pyautogui.size()
            y_limite_superior = altura_tela * 0.08

            pontos_validos = [pt for pt in zip(*loc[::-1]) if pt[1] > y_limite_superior]

            if pontos_validos:
                ponto_final = max(pontos_validos, key=lambda p: (-p[1], p[0]))
                ponto_clique = (ponto_final[0] + 10, ponto_final[1] + 10)
                print(f"✅ Ícone 'X' de anúncio encontrado. Preparando para clicar em {ponto_clique}...")

        if not ponto_clique:
            print("❌ Nenhum método para fechar anúncio funcionou.")
            return False

        pyautogui.click(ponto_clique)
        time.sleep(1.5)

        janela_depois_clique = pyautogui.getActiveWindow()
        if janela_depois_clique and janela_depois_clique.title != titulo_original:
            print("   -> Nova aba/janela detectada. Fechando-a...")
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(0.5)
            print("   -> Retornando à aba original.")

        return True
    except Exception as e:
        print(f"🤯 Erro ao tentar fechar anúncio: {e}")
        return False


def fechar_aba_por_nome(nome_aba):
    """
    CORRIGIDO: Encontra uma janela que contenha o nome da aba e a fecha com Ctrl+W.
    """
    print(f"🔎 Procurando pela janela/aba '{nome_aba}' para fechar...")
    try:
        desktop = Desktop(backend="win32")
        janelas = desktop.windows(visible_only=True, enabled_only=True)

        melhor_match = None
        maior_score = 0.0

        for janela in janelas:
            titulo = janela.window_text()
            if titulo and nome_aba.lower() in titulo.lower():
                # Encontrou uma janela que contém o nome da aba
                score = SequenceMatcher(None, nome_aba.lower(), titulo.lower()).ratio()
                if score > maior_score:
                    maior_score = score
                    melhor_match = janela

        if melhor_match:
            print(f"✅ Janela '{melhor_match.window_text()}' encontrada. Trazendo para frente e fechando a aba...")
            if melhor_match.is_minimized():
                melhor_match.restore()
            melhor_match.set_focus()
            time.sleep(0.2)  # Pausa para garantir o foco
            pyautogui.hotkey('ctrl', 'w')
            return True
        else:
            print(f"❌ Nenhuma janela correspondente à aba '{nome_aba}' foi encontrada.")
            return False

    except Exception as e:
        print(f"🤯 Erro ao tentar fechar aba por nome: {e}")
        return False


# --- SUAS FUNÇÕES ORIGINAIS (MANTIDAS) ---

def executar_acao_na_tela(app_falado):
    if not app_falado:
        print("⚠️ Alvo para abrir não especificado.")
        return False

    print(f"🔎 Procurando por janelas abertas de '{app_falado}'...")
    try:
        desktop = Desktop(backend="win32")
        janelas = desktop.windows(visible_only=True, enabled_only=True)
        janela_encontrada = None
        for janela in janelas:
            titulo = janela.window_text()
            if titulo and app_falado.lower() in titulo.lower():
                janela_encontrada = janela
                break
        if janela_encontrada:
            print(f"✅ Janela '{janela_encontrada.window_text()}' já está aberta. Trazendo para frente...")
            if janela_encontrada.is_minimized():
                janela_encontrada.restore()
            janela_encontrada.set_focus()
            return True
    except Exception as e:
        print(f"🤯 Erro ao verificar janelas abertas: {e}")

    print(f"ℹ️ Nenhuma janela encontrada. Tentando abrir o aplicativo '{app_falado}'...")
    if "explorer" in app_falado or "arquivos" in app_falado:
        os.system("start explorer")
        return True
    elif app_falado == "configurações":
        os.system("start ms-settings:")
        return True

    apps = listar_todos_apps_acessiveis()
    caminho_encontrado = encontrar_app_por_nome(app_falado, apps)
    if caminho_encontrado:
        os.startfile(caminho_encontrado)
        print(f"🟢 '{app_falado}' executado. Aguardando a janela aparecer...")
        time.sleep(3)
        try:
            janela_app = pyautogui.getActiveWindow()
            if janela_app:
                janela_app.maximize()
                print("✅ Janela maximizada.")
        except Exception as e:
            print(f"⚠️ Não foi possível maximizar a nova janela: {e}")
        return True
    else:
        print(f"❌ Nenhum aplicativo correspondente a '{app_falado}' encontrado.")
        return False


def apertar_tecla(tecla_falada):
    tecla_falada = tecla_falada.lower().strip()
    if '+' in tecla_falada:
        teclas_do_atalho = [key.strip() for key in tecla_falada.split('+')]
        try:
            pyautogui.hotkey(*teclas_do_atalho)
            print(f"⌨️  Atalho '{tecla_falada}' pressionado.")
            return True
        except Exception as e:
            print(f"❌ Erro ao pressionar atalho '{tecla_falada}': {e}")
            return False
    tecla_real = KEY_MAP.get(tecla_falada)
    if tecla_real:
        try:
            pyautogui.press(tecla_real)
            print(f"⌨️  Tecla '{tecla_real}' pressionada.")
            return True
        except Exception as e:
            print(f"❌ Erro ao pressionar tecla '{tecla_falada}': {e}")
            return False
    print(f"❌ Tecla ou atalho '{tecla_falada}' não reconhecido.")
    return False


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
    except Exception as e:
        print(f"🤯 Ocorreu um erro ao tentar tirar o print: {e}")
        return None


def copiar_arquivo_selecionado():
    try:
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        print("✅ Comando 'Copiar Arquivo' (Ctrl+C) executado.")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao tentar copiar o arquivo: {e}")
        return False


def copiar_caminho_selecionado():
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


def rolar_tela(sentido="baixo", quantidade=720):
    passos = 5
    intervalo = 0.01
    rolagem_por_passo = quantidade // passos
    if sentido in ["baixo", "descer", "para baixo", "pra baixo"]:
        print("⬇️ Rolando para baixo...")
        for _ in range(passos):
            pyautogui.scroll(-rolagem_por_passo)
            time.sleep(intervalo)
    elif sentido in ["cima", "subir", "para cima", "pra cima"]:
        print("⬆️ Rolando para cima...")
        for _ in range(passos):
            pyautogui.scroll(rolagem_por_passo)
            time.sleep(intervalo)


def fechar_janela_por_nome(nome_janela_falado):
    print(f"🔎 Procurando por uma janela parecida com '{nome_janela_falado}' para fechar...")
    try:
        desktop = Desktop(backend="win32")
        janelas = desktop.windows()
        if not janelas:
            print("❌ Nenhuma janela aberta encontrada.")
            return None, 0
        melhor_match = {'janela': None, 'score': 0.0, 'titulo': ''}
        for janela in janelas:
            titulo = janela.window_text()
            if titulo and "Program Manager" not in titulo:
                score = SequenceMatcher(None, nome_janela_falado.lower(), titulo.lower()).ratio()
                if score > melhor_match['score']:
                    melhor_match['score'] = score
                    melhor_match['janela'] = janela
                    melhor_match['titulo'] = titulo
        if melhor_match['janela']:
            janela_para_fechar = melhor_match['janela']
            titulo_real = melhor_match['titulo']
            score_final = melhor_match['score']
            print(f"✅ Melhor correspondência encontrada: '{titulo_real}' (Score: {score_final:.2f}). Fechando...")
            janela_para_fechar.close()
            return titulo_real, score_final
        else:
            print(f"❌ Nenhuma janela com título visível foi encontrada.")
            return None, 0
    except Exception as e:
        print(f"🤯 Ocorreu um erro ao tentar fechar a janela: {e}")
        return None, 0
