# startup_manager.py
import os
import sys

# Tenta importar as bibliotecas necessárias do pywin32
try:
    from win32com.client import Dispatch
except ImportError:
    print("AVISO: A biblioteca pywin32 não está instalada. A funcionalidade 'Iniciar com o Windows' não funcionará.")
    print("Para instalar, execute: pip install pywin32")
    Dispatch = None

APP_NAME = "LIA"
# Pega o caminho para o executável do Python que está rodando o script
PYTHON_EXE = sys.executable
# Pega o caminho absoluto do script principal que foi iniciado
SCRIPT_PATH = os.path.abspath(sys.argv[0])


def get_startup_folder():
    """Retorna o caminho da pasta de inicialização do usuário atual."""
    try:
        shell = Dispatch('WScript.Shell')
        # Usar "Startup" para o usuário atual
        return shell.SpecialFolders("Startup")
    except Exception:
        # Fallback para o método de variável de ambiente, caso o COM falhe
        return os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')


def get_shortcut_path():
    """Monta o caminho completo onde o atalho será criado."""
    startup_folder = get_startup_folder()
    return os.path.join(startup_folder, f"{APP_NAME}.lnk")


def add_to_startup():
    """Adiciona um atalho da aplicação na pasta de inicialização do Windows."""
    if not Dispatch: return False  # Retorna se a biblioteca não foi importada

    shortcut_path = get_shortcut_path()
    if os.path.exists(shortcut_path):
        print("Atalho de inicialização já existe.")
        return True

    try:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = PYTHON_EXE
        # Garante que o caminho do script seja passado como um argumento entre aspas
        shortcut.Arguments = f'"{SCRIPT_PATH}"'
        shortcut.WorkingDirectory = os.path.dirname(SCRIPT_PATH)
        shortcut.IconLocation = SCRIPT_PATH  # Opcional: define um ícone
        shortcut.save()
        print(f"LIA adicionada à inicialização do Windows.")
        return True
    except Exception as e:
        print(f"Erro ao adicionar LIA à inicialização: {e}")
        return False


def remove_from_startup():
    """Remove o atalho da aplicação da pasta de inicialização."""
    if not Dispatch: return False  # Retorna se a biblioteca não foi importada

    shortcut_path = get_shortcut_path()
    if not os.path.exists(shortcut_path):
        print("Atalho de inicialização não encontrado para remover.")
        return True

    try:
        os.remove(shortcut_path)
        print(f"LIA removida da inicialização do Windows.")
        return True
    except Exception as e:
        print(f"Erro ao remover LIA da inicialização: {e}")
        return False


def is_in_startup():
    """Verifica se o atalho já existe na pasta de inicialização."""
    if not Dispatch: return False
    return os.path.exists(get_shortcut_path())