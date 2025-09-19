# utils/tools.py (Versão completa com a correção do .env)

import os
import difflib
from difflib import SequenceMatcher
import yfinance as yf
import feedparser
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv  # <-- ADICIONADO PARA LER O .env

# Carrega as variáveis de ambiente do arquivo .env no início do script
load_dotenv()

# --- DICIONÁRIO EXPANDIDO DE TICKERS (GLOBAL) ---
TICKERS = {
    # --- Ações Globais (EUA e Mundo) ---
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "meta": "META", "facebook": "META",
    "tesla": "TSLA",
    "berkshire hathaway": "BRK-B",
    "eli lilly": "LLY",
    "visa": "V",
    "broadcom": "AVGO",
    "jpmorgan": "JPM", "jp morgan": "JPM",
    "mastercard": "MA",
    "exxon mobil": "XOM",
    "unitedhealth": "UNH",
    "johnson & johnson": "JNJ",
    "procter & gamble": "PG", "p&g": "PG",
    "costco": "COST",
    "home depot": "HD",
    "bank of america": "BAC",
    "merck": "MRK",
    "chevron": "CVX",
    "coca-cola": "KO", "coca cola": "KO",
    "pepsi": "PEP",
    "walmart": "WMT",
    "mcdonald's": "MCD",
    "disney": "DIS",
    "netflix": "NFLX",
    "adobe": "ADBE",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "cisco": "CSCO",
    "nike": "NKE",
    "intel": "INTC",
    "amd": "AMD",
    "qualcomm": "QCOM",
    "ibm": "IBM",
    "pfizer": "PFE",
    "moderna": "MRNA",
    "boeing": "BA",
    "lockheed martin": "LMT",
    "ford": "F",
    "general motors": "GM",
    "starbucks": "SBUX",
    "uber": "UBER",
    "airbnb": "ABNB",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "wells fargo": "WFC",
    "paypal": "PYPL",
    "shopify": "SHOP",
    "zoom": "ZM",
    "toyota": "TM",
    "samsung": "SSNLF",

    # --- Ações Brasileiras (Ibovespa e outras) ---
    "petrobras": "PETR4.SA",
    "vale": "VALE3.SA",
    "itau": "ITUB4.SA", "itaú": "ITUB4.SA",
    "bradesco": "BBDC4.SA",
    "banco do brasil": "BBAS3.SA",
    "ambev": "ABEV3.SA",
    "b3": "B3SA3.SA",
    "magazine luiza": "MGLU3.SA", "magalu": "MGLU3.SA",
    "weg": "WEGE3.SA",
    "suzano": "SUZB3.SA",
    "gerdau": "GGBR4.SA",
    "nubank": "ROXO34.SA",
    "itau sa": "ITSA4.SA", "itaúsa": "ITSA4.SA",
    "renner": "LREN3.SA", "lojas renner": "LREN3.SA",
    "localiza": "RENT3.SA",
    "natura": "NTCO3.SA",
    "rede d'or": "RDOR3.SA", "rede dor": "RDOR3.SA",
    "raia drogasil": "RADL3.SA", "drogasil": "RADL3.SA",
    "jbs": "JBSS3.SA",
    "eletrobras": "ELET3.SA",
    "brf": "BRFS3.SA",
    "csn": "CSNA3.SA",
    "pão de açúcar": "PCAR3.SA", "gpa": "PCAR3.SA",
    "cemig": "CMIG4.SA",
    "copel": "CPLE6.SA",
    "sabesp": "SBSP3.SA",
    "embraer": "EMBR3.SA",
    "azul": "AZUL4.SA",
    "gol": "GOLL4.SA",
    "cvc": "CVCB3.SA",
    "petz": "PETZ3.SA",
    "casas bahia": "BHIA3.SA", "via": "BHIA3.SA",
    "americanas": "AMER3.SA",
    "cyrela": "CYRE3.SA",
    "mrve": "MRVE3.SA",
    "braskem": "BRKM5.SA",
    "tim": "TIMS3.SA",
    "vivo": "VIVT3.SA", "telefonica brasil": "VIVT3.SA",
    "santander": "SANB11.SA",
    "xp": "XPBR31.SA",
    "btg pactual": "BPAC11.SA",
    "hapvida": "HAPV3.SA",
    "inter": "INBR32.SA", "banco inter": "INBR32.SA",
    "kering": "KER.PA",

    # --- Criptomoedas Populares ---
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
    "tether": "USDT-USD",
    "bnb": "BNB-USD",
    "solana": "SOL-USD",
    "xrp": "XRP-USD",
    "usd coin": "USDC-USD",
    "cardano": "ADA-USD",
    "dogecoin": "DOGE-USD",
    "avalanche": "AVAX-USD",
    "shiba inu": "SHIB-USD",
    "tron": "TRX-USD",
    "polkadot": "DOT-USD",
    "chainlink": "LINK-USD",
    "toncoin": "TON-USD",
    "polygon": "MATIC-USD",
    "litecoin": "LTC-USD",
    "internet computer": "ICP-USD",
    "bitcoin cash": "BCH-USD",
    "uniswap": "UNI-USD",
    "stellar": "XLM-USD",
    "okb": "OKB-USD",
    "cosmos": "ATOM-USD",
    "ethereum classic": "ETC-USD",
    "filecoin": "FIL-USD",
    "near protocol": "NEAR-USD",
    "hedera": "HBAR-USD",
    "aptos": "APT-USD",
    "monero": "XMR-USD",
    "render": "RNDR-USD",
    "vechain": "VET-USD",
    "algorand": "ALGO-USD",
    "the graph": "GRT-USD",
    "fantom": "FTM-USD",
    "aave": "AAVE-USD",
    "the sandbox": "SAND-USD",
    "decentraland": "MANA-USD",
    "tezos": "XTZ-USD",
    "axie infinity": "AXS-USD",
    "eos": "EOS-USD",
    "maker": "MKR-USD",
    "quant": "QNT-USD",
    "neo": "NEO-USD",
    "zcash": "ZEC-USD",
    "dash": "DASH-USD",
    "chiliz": "CHZ-USD",
    "enjin coin": "ENJ-USD",
    "gala": "GALA-USD",
    "pepe": "PEPE-USD",
}


# --- FUNÇÃO DE PREVISÃO DO TEMPO CORRIGIDA ---
def obter_previsao_tempo(cidade, periodo="hoje"):
    """
    Busca a previsão do tempo para uma cidade, carregando a API key do arquivo .env
    e usando a URL HTTPS correta.
    """
    cidade_api = cidade.split(',')[0].strip()
    print(f"🌦️  Buscando previsão do tempo para {periodo.upper()} em: {cidade_api}")

    # --- CORREÇÃO 1: Carrega a chave correta do ambiente ---
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("❌ ERRO: A chave da API OPENWEATHER_API_KEY não foi encontrada no arquivo .env.")
        return "Desculpe, a chave para o serviço de meteorologia não foi configurada."

    # --- CORREÇÃO 2: Usa HTTPS na URL, que é obrigatório ---
    base_url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        'q': cidade_api,
        'appid': api_key,
        'units': 'metric',
        'lang': 'pt_br'
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if str(data.get("cod")) != "200":
            return f"Desculpe, não consegui encontrar a cidade {cidade_api}. Erro: {data.get('message', 'desconhecido')}."

        if periodo == "hoje":
            previsao_hoje = data['list'][0]
            temp = previsao_hoje['main']['temp']
            descricao = previsao_hoje['weather'][0]['description']
            return f"A previsão para hoje em {cidade_api} é de {descricao}, com temperatura de {temp:.0f} graus."

        elif periodo == "amanha":
            amanha = (datetime.now() + timedelta(days=1)).date()
            for previsao in data['list']:
                data_previsao = datetime.fromtimestamp(previsao['dt']).date()
                if data_previsao == amanha:
                    temp_max = previsao['main']['temp_max']
                    descricao = previsao['weather'][0]['description']
                    return f"Amanhã em {cidade_api}, a previsão é de {descricao}, com máxima de {temp_max:.0f} graus."
            return f"Não encontrei uma previsão específica para amanhã em {cidade_api}."

        elif periodo == "semana":
            resumo_semana = {}
            for previsao in data['list']:
                data_previsao = datetime.fromtimestamp(previsao['dt']).strftime('%A')
                if data_previsao not in resumo_semana:
                    resumo_semana[data_previsao] = {
                        'temp_max': previsao['main']['temp_max'],
                        'descricao': previsao['weather'][0]['description']
                    }
            resposta = f"Resumo da previsão para a semana em {cidade_api}: "
            for dia, valores in resumo_semana.items():
                resposta += f"{dia}, {valores['descricao']} com máxima de {valores['temp_max']:.0f} graus. "
            return resposta

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            print("Erro 401: A chave da API é inválida ou não está ativa. Verifique o .env e a URL (HTTPS).")
            return "Desculpe, minha chave de acesso ao serviço de clima parece estar inválida."
        print(f"Erro HTTP: {http_err}")
        return "Desculpe, o serviço de meteorologia não está respondendo como esperado."
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a API de clima: {e}")
        return "Desculpe, estou com problemas para me conectar ao serviço de meteorologia."
    except Exception as e:
        print(f"Erro inesperado ao processar previsão do tempo: {e}")
        return "Ocorreu um erro inesperado ao buscar a previsão do tempo."


# --- SUAS FUNÇÕES ORIGINAIS (MANTIDAS) ---

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
    print(f"🔎 Procurando pela pasta '{nome_pasta_falado}'...")
    diretorios_base = [
        os.path.expanduser('~'), os.path.join(os.path.expanduser('~'), 'Desktop'),
        os.path.join(os.path.expanduser('~'), 'Documents'), os.path.join(os.path.expanduser('~'), 'Downloads'),
        os.path.join(os.path.expanduser('~'), 'Pictures'), os.path.join(os.path.expanduser('~'), 'Music'),
        os.path.join(os.path.expanduser('~'), 'Videos'),
    ]
    drives = [f"{chr(drive)}:\\" for drive in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(drive)}:")]
    diretorios_base.extend(drives)
    melhor_match = {'caminho': None, 'score': 0.0}
    for base in set(diretorios_base):
        for raiz, pastas, arquivos in os.walk(base):
            # Limita a profundidade da busca para evitar lentidão
            if raiz.count(os.sep) - base.count(os.sep) > 4:
                continue
            for pasta in pastas:
                score = SequenceMatcher(None, nome_pasta_falado.lower(), pasta.lower()).ratio()
                if score > melhor_match['score']:
                    melhor_match['score'] = score
                    melhor_match['caminho'] = os.path.join(raiz, pasta)
    if melhor_match['score'] > 0.7:
        caminho_final = melhor_match['caminho']
        print(f"✅ Pasta encontrada com score {melhor_match['score']:.2f}: {caminho_final}")
        os.startfile(caminho_final)
        return caminho_final
    else:
        print(f"❌ Nenhuma pasta correspondente a '{nome_pasta_falado}' encontrada.")
        return None


def obter_cotacao_acao(nome_ativo):
    nome_ativo = nome_ativo.lower().strip()
    ticker = TICKERS.get(nome_ativo)

    if not ticker:
        nomes_conhecidos = list(TICKERS.keys())
        melhor_match = difflib.get_close_matches(nome_ativo, nomes_conhecidos, n=1, cutoff=0.7)
        if melhor_match:
            ticker = TICKERS[melhor_match[0]]
        else:
            return f"Desculpe, não tenho o código para {nome_ativo} na minha lista."

    try:
        print(f"📈 Buscando dados para o ticker: {ticker}")
        ativo = yf.Ticker(ticker)
        dados = ativo.history(period="1d")

        if dados.empty:
            return f"Desculpe, não encontrei dados para {nome_ativo}."

        preco_atual = dados['Close'].iloc[-1]
        nome_completo = ativo.info.get('longName', nome_ativo.capitalize())

        # Correção para buscar a moeda correta
        moeda = ativo.info.get('currency', 'USD').upper()
        if moeda == 'BRL':
            moeda_falada = "reais"
        elif moeda == 'USD':
            moeda_falada = "dólares"
        else:
            moeda_falada = moeda

        resposta = f"O valor atual de {nome_completo} é de {preco_atual:.2f} {moeda_falada}."
        return resposta

    except Exception as e:
        print(f"❌ Erro ao buscar dados da ação: {e}")
        return f"Desculpe, tive um problema ao buscar a cotação de {nome_ativo}."


def obter_noticias_do_dia():
    print("📰 Buscando as principais notícias do dia...")
    try:
        feed = feedparser.parse("https://g1.globo.com/rss/g1/")
        if not feed.entries:
            return "Desculpe, não consegui carregar as notícias no momento."

        # Limpa o título para remover o nome do jornal
        manchetes = [entrada.title.split(',')[0].strip() for entrada in feed.entries[:3]]
        resposta = "Claro, aqui estão as principais manchetes do G1: ... " + " ... ".join(manchetes)
        return resposta

    except Exception as e:
        print(f"❌ Erro ao buscar notícias: {e}")
        return "Desculpe, estou com problemas para acessar o serviço de notícias agora."