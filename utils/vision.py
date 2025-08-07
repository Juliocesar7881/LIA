# utils/vision.py (Com busca de Tesseract e de elementos)

import pyautogui
import pytesseract
from difflib import SequenceMatcher
import os


# --- INÍCIO DA LÓGICA DE BUSCA E CACHE OTIMIZADA (SUA VERSÃO) ---

def encontrar_e_cachear_tesseract():
    """
    Procura a pasta de instalação do Tesseract no disco C: e, em seguida,
    procura o executável dentro dela. Salva o caminho em um cache.
    """
    cache_file = 'tesseract_path.txt'

    # 1. Tenta ler o caminho do cache primeiro
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            caminho_cache = f.read().strip()
            if os.path.exists(caminho_cache):
                print(f"✅ Tesseract-OCR encontrado via cache: {caminho_cache}")
                return caminho_cache
            else:
                print("⚠️ Caminho do cache inválido. Realizando nova busca...")

    # 2. Se não houver cache, faz a busca otimizada no Disco C:
    print("🤖 Realizando busca otimizada pelo Tesseract-OCR no Disco C:. Isso deve ser rápido...")

    for root, dirs, files in os.walk('C:\\'):
        # Procura por uma pasta com o nome padrão de instalação
        if 'Tesseract-OCR' in dirs:
            pasta_tesseract = os.path.join(root, 'Tesseract-OCR')
            caminho_executavel = os.path.join(pasta_tesseract, 'tesseract.exe')

            if os.path.exists(caminho_executavel):
                # Salva no cache para a próxima vez
                with open(cache_file, 'w') as f:
                    f.write(caminho_executavel)
                print(f"✅ Tesseract-OCR encontrado e salvo no cache: {caminho_executavel}")
                return caminho_executavel

    return None


# Configura o pytesseract com o caminho encontrado
caminho_tesseract = encontrar_e_cachear_tesseract()
if caminho_tesseract:
    pytesseract.pytesseract.tesseract_cmd = caminho_tesseract
else:
    print("❌ Tesseract-OCR não foi encontrado no Disco C:.")
    print("   A função de clicar em palavras não irá funcionar.")
    print(r"   Por favor, verifique se o Tesseract-OCR está instalado.")


# --- FIM DA LÓGICA DE BUSCA ---


# --- NOVAS FUNÇÕES ADICIONADAS ---

def encontrar_elemento_por_texto(texto_alvo):
    """
    Tira um print e retorna a posição e o tamanho do texto mais
    parecido com o texto_alvo na tela.
    Retorna um dicionário {'left': x, 'top': y, 'width': w, 'height': h} ou None.
    """
    try:
        screenshot = pyautogui.screenshot()
        dados_ocr = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT, lang='por')

        # Agrupa palavras na mesma linha para encontrar frases completas
        linhas = {}
        for i in range(len(dados_ocr['text'])):
            if int(dados_ocr['conf'][i]) > 60:
                id_linha = (dados_ocr['block_num'][i], dados_ocr['par_num'][i], dados_ocr['line_num'][i])
                palavra_info = {
                    'texto': dados_ocr['text'][i], 'left': dados_ocr['left'][i], 'top': dados_ocr['top'][i],
                    'width': dados_ocr['width'][i], 'height': dados_ocr['height'][i]
                }
                if id_linha not in linhas:
                    linhas[id_linha] = []
                linhas[id_linha].append(palavra_info)

        melhor_match = {'elemento': None, 'score': 0.0}
        for id_linha, palavras in linhas.items():
            texto_da_linha = ' '.join([p['texto'] for p in palavras]).strip().lower()
            score = SequenceMatcher(None, texto_alvo.lower(), texto_da_linha).ratio()

            if score > melhor_match['score']:
                elemento = {
                    'left': min([p['left'] for p in palavras]),
                    'top': min([p['top'] for p in palavras]),
                    'width': max([p['left'] + p['width'] for p in palavras]) - min([p['left'] for p in palavras]),
                    'height': max([p['top'] + p['height'] for p in palavras]) - min([p['top'] for p in palavras])
                }
                melhor_match['elemento'] = elemento
                melhor_match['score'] = score

        if melhor_match['score'] > 0.7:
            return melhor_match['elemento']
        return None

    except Exception as e:
        print(f"🤯 Erro ao encontrar elemento por texto: {e}")
        return None


def clicar_em_palavra(palavra_alvo):
    """
    Função original, agora usando a nova função de busca para encontrar e clicar.
    """
    print(f"🔍 Buscando pelo melhor alvo para '{palavra_alvo}'...")
    elemento = encontrar_elemento_por_texto(palavra_alvo)

    if elemento:
        x_centro = elemento['left'] + elemento['width'] // 2
        y_centro = elemento['top'] + elemento['height'] // 2
        print(f"✅ Alvo encontrado para '{palavra_alvo}'. Clicando em ({x_centro}, {y_centro})...")
        pyautogui.click(x_centro, y_centro)
        return True, 1.0, palavra_alvo
    else:
        print(f"❌ Nenhum alvo com boa correspondência encontrado para '{palavra_alvo}'.")
        return False, 0.0, ""