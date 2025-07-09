import os
import difflib

def listar_todos_apps_acessiveis():
    caminhos_busca = [
        os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
    ]

    atalhos = {}
    for caminho_base in caminhos_busca:
        for raiz, dirs, arquivos in os.walk(caminho_base):
            for nome in arquivos:
                if nome.lower().endswith((".lnk", ".exe")):
                    nome_base = nome.lower().replace(".lnk", "").replace(".exe", "").strip()
                    caminho_completo = os.path.join(raiz, nome)
                    atalhos[nome_base] = caminho_completo
    return atalhos

def encontrar_app_por_nome(nome_falado, atalhos):
    nome_falado = nome_falado.lower().strip()
    lista_nomes = list(atalhos.keys())
    mais_proximo = difflib.get_close_matches(nome_falado, lista_nomes, n=1, cutoff=0.5)
    if mais_proximo:
        return atalhos[mais_proximo[0]]
    return None
