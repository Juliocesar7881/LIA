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


def _buscar_texto_na_imagem(imagem_processada, texto_alvo, config_tesseract):
    """Função auxiliar para encontrar texto numa imagem específica."""
    dados_ocr = pytesseract.image_to_data(imagem_processada, lang='por', config=config_tesseract,
                                          output_type=pytesseract.Output.DICT)

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
    resultados = []

    for i in range(len(palavras_na_tela) - num_palavras_alvo + 1):
        frase_candidata_lista = palavras_na_tela[i: i + num_palavras_alvo]
        frase_candidata_texto = ' '.join([p['text'] for p in frase_candidata_lista])
        score = SequenceMatcher(None, texto_alvo, frase_candidata_texto).ratio()

        if score > 0.51:
            print(f"  - Encontrado: '{frase_candidata_texto}' (Similaridade: {score:.2f})")
            left = min([p['left'] for p in frase_candidata_lista])
            top = min([p['top'] for p in frase_candidata_lista])
            right = max([p['left'] + p['width'] for p in frase_candidata_lista])
            bottom = max([p['top'] + p['height'] for p in frase_candidata_lista])

            resultados.append({
                'left': left, 'top': top, 'width': right - left, 'height': bottom - top,
                'texto': frase_candidata_texto, 'score': score
            })
    return resultados


def encontrar_elementos_por_texto(texto_alvo):
    """
    Tira um print e analisa a imagem normal e a invertida para encontrar o texto
    alvo, combinando os resultados para máxima precisão.
    """
    try:
        screenshot_pil = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2GRAY)

        config_tesseract = '--psm 6'
        print(f"\n--- DEBUG DE VISÃO: Procurando por '{texto_alvo}' ---")

        # --- PASSO 1: Analisa a imagem normal (para temas claros) ---
        print("  -> Analisando imagem normal...")
        _, processada_normal = cv2.threshold(screenshot_cv, 128, 255, cv2.THRESH_BINARY)
        resultados_normais = _buscar_texto_na_imagem(Image.fromarray(processada_normal), texto_alvo, config_tesseract)

        # --- PASSO 2: Analisa a imagem invertida (para temas escuros) ---
        print("  -> Analisando imagem invertida...")
        _, processada_invertida = cv2.threshold(screenshot_cv, 128, 255, cv2.THRESH_BINARY_INV)
        resultados_invertidos = _buscar_texto_na_imagem(Image.fromarray(processada_invertida), texto_alvo,
                                                        config_tesseract)

        # --- PASSO 3: Combina e filtra os resultados ---
        todos_os_resultados = resultados_normais + resultados_invertidos

        if not todos_os_resultados:
            print("  - Nenhum texto com similaridade > 60% foi encontrado em ambas as análises.")
            print("--- FIM DO DEBUG DE VISÃO ---\n")
            return []

        # Remove duplicados mantendo o de maior score
        resultados_unicos = {}
        for res in todos_os_resultados:
            # Usa a posição como chave para identificar elementos duplicados
            chave = (res['left'] // 10, res['top'] // 10)  # Agrupa elementos próximos
            if chave not in resultados_unicos or res['score'] > resultados_unicos[chave]['score']:
                resultados_unicos[chave] = res

        resultados_finais = list(resultados_unicos.values())
        print(f"  -> Total de {len(resultados_finais)} resultado(s) único(s) encontrado(s).")
        print("--- FIM DO DEBUG DE VISÃO ---\n")

        # Ordena os resultados pela posição na tela
        resultados_ordenados = sorted(resultados_finais, key=lambda p: (p['top'], p['left']))

        return resultados_ordenados

    except Exception as e:
        print(f"🤯 Erro ao encontrar elementos por texto: {e}")
        return []