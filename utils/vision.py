# utils/vision.py (Com busca de Tesseract, pré-processamento de imagem e nova lógica de busca)

import pyautogui
import pytesseract
from difflib import SequenceMatcher
import os
import cv2
import numpy as np
from PIL import Image


# --- INÍCIO DA LÓGICA DE BUSCA E CACHE OTIMIZADA ---

def encontrar_e_cachear_tesseract():
    """
    Procura a pasta de instalação do Tesseract no disco C: e, em seguida,
    procura o executável dentro dela. Salva o caminho em um cache.
    """
    cache_file = 'tesseract_path.txt'

    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            caminho_cache = f.read().strip()
            if os.path.exists(caminho_cache):
                print(f"✅ Tesseract-OCR encontrado via cache: {caminho_cache}")
                return caminho_cache
            else:
                print("⚠️ Caminho do cache inválido. Realizando nova busca...")

    print("🤖 Realizando busca otimizada pelo Tesseract-OCR no Disco C:. Isso deve ser rápido...")
    for root, dirs, files in os.walk('C:\\'):
        if 'Tesseract-OCR' in dirs:
            pasta_tesseract = os.path.join(root, 'Tesseract-OCR')
            caminho_executavel = os.path.join(pasta_tesseract, 'tesseract.exe')
            if os.path.exists(caminho_executavel):
                with open(cache_file, 'w') as f:
                    f.write(caminho_executavel)
                print(f"✅ Tesseract-OCR encontrado e salvo no cache: {caminho_executavel}")
                return caminho_executavel
    return None


caminho_tesseract = encontrar_e_cachear_tesseract()
if caminho_tesseract:
    pytesseract.pytesseract.tesseract_cmd = caminho_tesseract
else:
    print("❌ Tesseract-OCR não foi encontrado no Disco C:.")
    print("   A função de clicar em palavras não irá funcionar.")
    print(r"   Por favor, verifique se o Tesseract-OCR está instalado.")


# --- FIM DA LÓGICA DE BUSCA ---


def _preprocessar_imagem_para_ocr(imagem_pil):
    """
    Aplica filtros na imagem para melhorar drasticamente a precisão do OCR,
    especialmente em temas escuros com texto claro.
    """
    imagem_cv = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2GRAY)
    # Inverte a imagem (texto branco sobre fundo preto torna-se texto preto sobre fundo branco)
    # e aplica um threshold binário. Esta é a melhor abordagem para UIs.
    _, processada = cv2.threshold(imagem_cv, 128, 255, cv2.THRESH_BINARY_INV)
    return Image.fromarray(processada)


def encontrar_elementos_por_texto(texto_alvo):
    """
    Tira um print, pré-processa a imagem, encontra todos os textos parecidos
    e os retorna ordenados, com debug no console.
    """
    try:
        screenshot_original = pyautogui.screenshot()
        screenshot_processada = _preprocessar_imagem_para_ocr(screenshot_original)

        # --- NOVA CONFIGURAÇÃO PARA O TESSERACT ---
        # --psm 6: Assume um único bloco de texto uniforme. É o melhor para ler UIs.
        config_tesseract = '--psm 6'
        dados_ocr = pytesseract.image_to_data(screenshot_processada, lang='por', config=config_tesseract,
                                              output_type=pytesseract.Output.DICT)

        print(f"\n--- DEBUG DE VISÃO: Procurando por '{texto_alvo}' ---")

        palavras_na_tela = []
        for i in range(len(dados_ocr['text'])):
            if int(dados_ocr['conf'][i]) > 30 and dados_ocr['text'][i].strip() != '':
                palavras_na_tela.append({
                    'text': dados_ocr['text'][i].lower(),
                    'left': dados_ocr['left'][i],
                    'top': dados_ocr['top'][i],
                    'width': dados_ocr['width'][i],
                    'height': dados_ocr['height'][i]
                })

        palavras_alvo = texto_alvo.lower().split()
        num_palavras_alvo = len(palavras_alvo)
        resultados_encontrados = []

        for i in range(len(palavras_na_tela) - num_palavras_alvo + 1):
            frase_candidata_lista = palavras_na_tela[i: i + num_palavras_alvo]
            frase_candidata_texto = ' '.join([p['text'] for p in frase_candidata_lista])

            score = SequenceMatcher(None, texto_alvo, frase_candidata_texto).ratio()

            # --- ALTERAÇÃO SOLICITADA: Similaridade mínima de 60% ---
            if score > 0.6:
                print(f"  - Encontrado: '{frase_candidata_texto}' (Similaridade: {score:.2f})")

                left = min([p['left'] for p in frase_candidata_lista])
                top = min([p['top'] for p in frase_candidata_lista])
                right = max([p['left'] + p['width'] for p in frase_candidata_lista])
                bottom = max([p['top'] + p['height'] for p in frase_candidata_lista])

                resultados_encontrados.append({
                    'left': left,
                    'top': top,
                    'width': right - left,
                    'height': bottom - top,
                    'texto': frase_candidata_texto,
                    'score': score
                })

        if not resultados_encontrados:
            print("  - Nenhum texto com similaridade > 60% foi encontrado.")

        print("--- FIM DO DEBUG DE VISÃO ---\n")

        resultados_ordenados = sorted(resultados_encontrados, key=lambda p: (p['top'], p['left']))

        return resultados_ordenados

    except Exception as e:
        print(f"🤯 Erro ao encontrar elementos por texto: {e}")
        return []