# utils/tools.py

import os
import difflib
from difflib import SequenceMatcher  # Usaremos um comparador de similaridade


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


def encontrar_e_abrir_pasta(nome_pasta_falado):
    """
    Procura por uma pasta com o nome mais parecido nas pastas do usuário e a abre.
    """
    print(f"🔎 Procurando pela pasta '{nome_pasta_falado}'...")
    # Define os diretórios base onde a busca será feita
    diretorios_base = [
        os.path.expanduser('~'),  # Pasta do usuário (ex: C:\Users\Luchini)
        os.path.join(os.path.expanduser('~'), 'Desktop'),
        os.path.join(os.path.expanduser('~'), 'Documents'),
        os.path.join(os.path.expanduser('~'), 'Downloads'),
        os.path.join(os.path.expanduser('~'), 'Pictures'),
        os.path.join(os.path.expanduser('~'), 'Music'),
        os.path.join(os.path.expanduser('~'), 'Videos'),
    ]

    # Adiciona os drives principais (C:, D:, etc.) à busca
    drives = [f"{chr(drive)}:\\" for drive in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(drive)}:")]
    diretorios_base.extend(drives)

    melhor_match = {'caminho': None, 'score': 0.0}

    for base in set(diretorios_base):  # 'set' para evitar buscas duplicadas
        # Usamos os.walk para percorrer as pastas
        for raiz, pastas, arquivos in os.walk(base):
            # Não vamos muito fundo para não demorar demais (ex: 3 níveis de profundidade)
            if raiz.count(os.sep) - base.count(os.sep) > 3:
                continue

            for pasta in pastas:
                score = SequenceMatcher(None, nome_pasta_falado.lower(), pasta.lower()).ratio()
                if score > melhor_match['score']:
                    melhor_match['score'] = score
                    melhor_match['caminho'] = os.path.join(raiz, pasta)

    # Se encontrou uma correspondência com boa confiança, abre a pasta
    if melhor_match['score'] > 0.7:
        caminho_final = melhor_match['caminho']
        print(f"✅ Pasta encontrada com score {melhor_match['score']:.2f}: {caminho_final}")
        os.startfile(caminho_final)
        return caminho_final
    else:
        print(f"❌ Nenhuma pasta correspondente a '{nome_pasta_falado}' encontrada com score suficiente.")
        return None