# utils/tools.py (Versão completa com lista global e massiva de ativos)

import os
import difflib
from difflib import SequenceMatcher
import yfinance as yf
import feedparser
import requests
from datetime import datetime, timedelta  # <-- NOVA IMPORTAÇÃO

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
    "kering": "KER.PA",  # Exemplo de ação europeia (Gucci)

    # --- Criptomoedas Populares (Top 50+) ---
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


# --- FUNÇÃO DE PREVISÃO DO TEMPO ATUALIZADA ---
def obter_previsao_tempo(cidade: str, periodo: str = "hoje") -> str:
    """Busca a previsão do tempo para hoje, amanhã ou para a semana."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "A chave da API de previsão do tempo não foi configurada."

    try:
        if periodo == "hoje":
            print(f"🌦️  Buscando previsão do tempo para HOJE em: {cidade}")
            url = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&units=metric&lang=pt_br"
            response = requests.get(url)
            if response.status_code != 200:
                dados_erro = response.json()
                return f"Desculpe, não consegui encontrar a cidade {cidade}. Erro: {dados_erro.get('message', 'desconhecido')}."

            dados = response.json()
            nome_cidade = dados['name']
            descricao_clima = dados['weather'][0]['description']
            temp_atual = dados['main']['temp']
            sensacao_termica = dados['main']['feels_like']
            temp_min = dados['main']['temp_min']
            temp_max = dados['main']['temp_max']
            umidade = dados['main']['humidity']

            return (
                f"A previsão do tempo para {nome_cidade} agora é de {descricao_clima}, "
                f"com temperatura atual de {temp_atual:.0f} graus e sensação térmica de {sensacao_termica:.0f} graus. "
                f"A mínima para hoje é de {temp_min:.0f} e a máxima de {temp_max:.0f} graus. "
                f"A umidade do ar está em {umidade}%."
            )

        elif periodo in ["amanha", "semana"]:
            print(f"🌦️  Buscando previsão futura para '{periodo}' em: {cidade}")
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={cidade}&appid={api_key}&units=metric&lang=pt_br"
            response = requests.get(url)
            if response.status_code != 200:
                dados_erro = response.json()
                return f"Desculpe, não consegui encontrar a previsão futura para {cidade}. Erro: {dados_erro.get('message', 'desconhecido')}."

            dados = response.json()
            nome_cidade = dados['city']['name']
            lista_previsoes = dados['list']

            if periodo == "amanha":
                amanha = (datetime.now() + timedelta(days=1)).date()
                for previsao in lista_previsoes:
                    data_previsao = datetime.fromtimestamp(previsao['dt']).date()
                    if data_previsao == amanha:
                        # Pega a previsão por volta do meio-dia para ser mais representativa
                        if "12:00:00" in previsao['dt_txt']:
                            descricao = previsao['weather'][0]['description']
                            temp = previsao['main']['temp']
                            return f"Amanhã em {nome_cidade}, a previsão é de {descricao} com temperatura por volta de {temp:.0f} graus."
                return f"Não encontrei uma previsão específica para amanhã em {nome_cidade}."

            elif periodo == "semana":
                dias_semana = {}
                for previsao in lista_previsoes:
                    data = datetime.fromtimestamp(previsao['dt']).strftime('%Y-%m-%d')
                    if data not in dias_semana:
                        dias_semana[data] = {'min': [], 'max': [], 'desc': []}
                    dias_semana[data]['min'].append(previsao['main']['temp_min'])
                    dias_semana[data]['max'].append(previsao['main']['temp_max'])
                    dias_semana[data]['desc'].append(previsao['weather'][0]['description'])

                resposta = f"Aqui está a previsão para os próximos dias em {nome_cidade}... "
                for data_str, valores in list(dias_semana.items())[:5]:
                    data_obj = datetime.strptime(data_str, '%Y-%m-%d')
                    nome_dia = data_obj.strftime("%A").replace("-feira", "")
                    temp_min_dia = min(valores['min'])
                    temp_max_dia = max(valores['max'])
                    desc_comum = max(set(valores['desc']), key=valores['desc'].count)
                    resposta += f"Para {nome_dia}: a previsão é de {desc_comum}, com mínima de {temp_min_dia:.0f} e máxima de {temp_max_dia:.0f} graus... "
                return resposta

    except requests.exceptions.RequestException as e:
        return f"Desculpe, estou sem conexão para verificar a previsão do tempo. Erro: {e}"
    except Exception as e:
        return f"Ocorreu um erro inesperado ao buscar a previsão do tempo. Erro: {e}"

    return "Não consegui obter a previsão."


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
        os.path.expanduser(''), os.path.join(os.path.expanduser(''), 'Desktop'),
        os.path.join(os.path.expanduser(''), 'Documents'), os.path.join(os.path.expanduser(''), 'Downloads'),
        os.path.join(os.path.expanduser(''), 'Pictures'), os.path.join(os.path.expanduser(''), 'Music'),
        os.path.join(os.path.expanduser('~'), 'Videos'),
    ]
    drives = [f"{chr(drive)}:\\" for drive in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(drive)}:")]
    diretorios_base.extend(drives)
    melhor_match = {'caminho': None, 'score': 0.0}
    for base in set(diretorios_base):
        for raiz, pastas, arquivos in os.walk(base):
            if raiz.count(os.sep) - base.count(os.sep) > 3: continue
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

        if ".SA" in ticker:
            moeda = "reais"
        else:
            moeda = "dólares"

        resposta = f"O valor atual de {nome_completo} é de {preco_atual:.2f} {moeda}."
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

        manchetes = [entrada.title for entrada in feed.entries[:3]]
        resposta = "Claro, aqui estão as principais manchetes do G1: ... " + " ... ".join(manchetes)
        return resposta

    except Exception as e:
        print(f"❌ Erro ao buscar notícias: {e}")
        return "Desculpe, estou com problemas para acessar o serviço de notícias agora."