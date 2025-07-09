# utils/vision.py (versão que retorna o score do clique)

import pytesseract
import pyautogui
import cv2
import numpy as np
from difflib import SequenceMatcher

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def clicar_em_palavra(palavra_falada):
    if not palavra_falada or not palavra_falada.strip():
        return False, 0, ""  # Retorna falha, score 0, e texto vazio

    print(f"🔍 Buscando pelo melhor alvo para '{palavra_falada}'...")
    # ... (toda a lógica de captura e processamento de imagem continua igual)
    imagem_original = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    imagem_cinza = cv2.cvtColor(imagem_original, cv2.COLOR_BGR2GRAY)
    imagem_invertida = cv2.bitwise_not(imagem_cinza)
    (thresh, img_final) = cv2.threshold(imagem_invertida, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    config_tesseract = '--psm 11'
    dados = pytesseract.image_to_data(
        img_final, lang='por', output_type=pytesseract.Output.DICT
    )
    # ... (toda a lógica de agrupar em linhas continua igual)
    linhas = {}
    for i in range(len(dados['text'])):
        if int(dados['conf'][i]) > 40:
            id_linha = (dados['block_num'][i], dados['par_num'][i], dados['line_num'][i])
            palavra_info = {'texto': dados['text'][i], 'left': dados['left'][i], 'top': dados['top'][i],
                            'width': dados['width'][i], 'height': dados['height'][i]}
            if id_linha not in linhas: linhas[id_linha] = []
            linhas[id_linha].append(palavra_info)
    itens_clicaveis = []
    for id_linha, palavras in linhas.items():
        texto_da_linha = ' '.join([p['texto'] for p in palavras])
        if texto_da_linha.strip():
            item = {'texto': texto_da_linha, 'left': min([p['left'] for p in palavras]),
                    'top': min([p['top'] for p in palavras]),
                    'width': max([p['left'] + p['width'] for p in palavras]) - min([p['left'] for p in palavras]),
                    'height': max([p['top'] + p['height'] for p in palavras]) - min([p['top'] for p in palavras])}
            itens_clicaveis.append(item)
    print(f"👀 Frases/Linhas encontradas: {[item['texto'] for item in itens_clicaveis]}")

    # ... (a lógica de pontuação continua igual)
    palavras_chave = palavra_falada.lower().split()
    melhor_item = None
    maior_score = 0.0
    if not palavras_chave: return False, 0, ""

    for item in itens_clicaveis:
        texto_da_tela_lower = item['texto'].lower()
        similaridade_geral = SequenceMatcher(None, palavra_falada.lower(), texto_da_tela_lower).ratio()
        palavras_encontradas = sum(1 for chave in palavras_chave if chave in texto_da_tela_lower)
        score_completude = palavras_encontradas / len(palavras_chave)
        score_final = (similaridade_geral * 0.4) + (score_completude * 0.6)
        if score_final > maior_score:
            maior_score = score_final
            melhor_item = item

    # --- MUDANÇA AQUI: SEMPRE CLICA SE ENCONTRAR ALGO ---
    if melhor_item:
        texto_encontrado = melhor_item['texto']
        print(f"✅ Melhor correspondência: '{texto_encontrado}' (Score: {maior_score:.2f})")
        x = melhor_item['left'] + melhor_item['width'] // 2
        y = melhor_item['top'] + melhor_item['height'] // 2
        pyautogui.click(x, y)
        print(f"🖱️ Clicado em '{texto_encontrado}' em ({x}, {y})")
        # Retorna sucesso, o score e o texto clicado
        return True, maior_score, texto_encontrado
    else:
        print(f"❌ Nenhuma correspondência encontrada.")
        return False, 0, ""


def ler_texto_na_tela(x, y, largura, altura):
    screenshot = pyautogui.screenshot(region=(x, y, largura, altura))
    imagem = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return pytesseract.image_to_string(imagem, lang='por').strip()