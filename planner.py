import json
import asyncio
import re  # <-- IMPORTAÇÃO ADICIONADA
from gpt_bridge import perguntar_ao_gpt
from voice_control import falar

# Importa todas as funções de ação dos seus módulos existentes
import screen_control
import utils.tools
import whatsapp_bot
import youtube_downloader
import agenda_control
import smart_device_control
import file_converter
import transcriber
import code_writer

# --- O CATÁLOGO DE FERRAMENTAS DA LIA ---
AVAILABLE_TOOLS = {
    "abrir_programa": screen_control.executar_acao_na_tela,
    "fechar_programa": screen_control.fechar_janela_por_nome,
    "minimizar_programa": screen_control.minimizar_janela_por_nome,
    "digitar_texto": screen_control.digitar_texto,
    "apertar_tecla": screen_control.apertar_tecla,
    "clicar_em_texto": screen_control.clicar_em_elemento,
    "clicar_em_icone": screen_control.clicar_em_imagem,
    "rolar_tela": screen_control.rolar_tela,
    "tirar_print": screen_control.tirar_print,
    "copiar_texto_selecionado": lambda: screen_control.apertar_tecla('ctrl+c'),
    "colar_texto": screen_control.colar,
    "obter_previsao_tempo": utils.tools.obter_previsao_tempo,
    "obter_cotacao_ativo": utils.tools.obter_cotacao_acao,
    "obter_noticias": utils.tools.obter_noticias_do_dia,
    "enviar_whatsapp": whatsapp_bot.enviar_mensagem_whatsapp,
    "baixar_video_youtube": lambda url: youtube_downloader.baixar_media_youtube(url, baixar_audio=False),
    "baixar_musica_youtube": lambda url: youtube_downloader.baixar_media_youtube(url, baixar_audio=True),
    "criar_alarme": agenda_control.criar_alarme,
    "controlar_tomada": smart_device_control.encontrar_e_controlar,
    "converter_arquivo_para_mp3": lambda caminho: file_converter.converter_video_para_audio(caminho, "mp3"),
    "transcrever_audio_video": transcriber.transcrever_localmente,
    "gerar_codigo_python": code_writer.gerar_codigo_e_abrir_no_navegador,
    "esperar": asyncio.sleep,
}

def _limpar_json_da_resposta(texto_da_ia: str) -> str:
    """Extrai blocos de código JSON de uma string de texto."""
    match = re.search(r'```json\s*([\s\S]*?)\s*```', texto_da_ia)
    if match:
        return match.group(1).strip()
    try:
        start_index = texto_da_ia.find('[')
        end_index = texto_da_ia.rfind(']')
        if start_index != -1 and end_index != -1:
            return texto_da_ia[start_index:end_index+1]
    except:
        pass
    return texto_da_ia

async def criar_plano_de_acao(intencao: str, config: dict):
    """
    Envia a intenção do usuário e a lista de ferramentas para a IA e pede um plano.
    """
    descricao_ferramentas = """
    - `abrir_programa(nome_do_programa: str)`: Abre um aplicativo ou foca se já estiver aberto.
    - `fechar_programa(nome_do_programa: str)`: Fecha um aplicativo.
    - `minimizar_programa(nome_do_programa: str)`: Minimiza um aplicativo.
    - `digitar_texto(texto: str)`: Digita o texto fornecido.
    - `apertar_tecla(tecla: str)`: Pressiona uma tecla ou atalho (ex: 'enter', 'ctrl+c').
    - `clicar_em_texto(texto_na_tela: str)`: Encontra um texto na tela e clica nele.
    - `clicar_em_icone(nome_do_icone: str)`: Encontra um ícone (salvo em 'image_targets') e clica nele.
    - `rolar_tela(direcao: str)`: Rola a tela para 'cima' ou 'baixo'.
    - `tirar_print()`: Tira uma captura de tela.
    - `copiar_texto_selecionado()`: Copia o texto atualmente selecionado (Ctrl+C).
    - `colar_texto()`: Cola o texto da área de transferência (Ctrl+V).
    - `obter_previsao_tempo(cidade: str)`: Retorna a previsão do tempo.
    - `obter_cotacao_ativo(nome_do_ativo: str)`: Retorna o valor de uma ação ou criptomoeda.
    - `obter_noticias()`: Retorna as principais manchetes de notícias.
    - `enviar_whatsapp(nome_contato: str, mensagem: str)`: Envia uma mensagem no WhatsApp.
    - `baixar_video_youtube(url: str)`: Baixa um vídeo do YouTube.
    - `baixar_musica_youtube(url: str)`: Baixa apenas o áudio de um vídeo do YouTube em MP3.
    - `criar_alarme(titulo: str, data_hora: datetime)`: Cria um alarme.
    - `controlar_tomada(nome_dispositivo: str, comando: str)`: 'ligar' ou 'desligar' um dispositivo inteligente.
    - `converter_arquivo_para_mp3(caminho_do_arquivo: str)`: Converte um vídeo para MP3.
    - `transcrever_audio_video(caminho_do_arquivo: str)`: Transcreve o conteúdo de um arquivo de áudio/vídeo.
    - `gerar_codigo_python(descricao_do_pedido: str)`: Gera um código Python a partir de uma descrição.
    - `esperar(segundos: int)`: Pausa a execução por um número de segundos.
    """
    prompt = f"""
    Você é o cérebro avançado de uma assistente de IA chamada LIA. Sua tarefa é decompor uma instrução complexa do usuário em um plano de ação passo a passo.
    A instrução do usuário é: '{intencao}'
    Aqui estão as ferramentas que você pode usar:
    {descricao_ferramentas}
    Analise o pedido e retorne um plano de ação em formato JSON. O JSON deve ser uma lista de dicionários, onde cada dicionário representa um passo e contém as chaves "tool" e "args".
    Se um passo não requer argumentos, use uma lista vazia: [].
    Use a ferramenta 'esperar' para aguardar o carregamento de páginas ou aplicativos.
    Responda APENAS com o bloco de código JSON.
    """
    try:
        # Usamos humor 0 para a chamada do planner para obter uma resposta mais direta (apenas JSON)
        resposta_bruta = await perguntar_ao_gpt(prompt, 0)
        json_limpo = _limpar_json_da_resposta(resposta_bruta)
        plano = json.loads(json_limpo)
        return plano
    except Exception as e:
        print(f"❌ Erro ao criar o plano de ação: {e}")
        return None

async def executar_plano(plano: list):
    """
    Executa cada passo de um plano de ação gerado pela IA.
    """
    await falar("Entendido. Iniciando a execução da tarefa.")
    for i, passo in enumerate(plano):
        nome_ferramenta = passo.get("tool")
        args = passo.get("args", [])
        print(f"▶️  Passo {i+1}/{len(plano)}: Executando '{nome_ferramenta}' com args: {args}")
        if nome_ferramenta in AVAILABLE_TOOLS:
            funcao_ferramenta = AVAILABLE_TOOLS[nome_ferramenta]
            try:
                if asyncio.iscoroutinefunction(funcao_ferramenta):
                    resultado = await funcao_ferramenta(*args)
                else:
                    resultado = funcao_ferramenta(*args)
                if isinstance(resultado, str):
                    await falar(resultado)
                await asyncio.sleep(0.7)
            except Exception as e:
                print(f"💥 Erro ao executar o passo {i+1} ('{nome_ferramenta}'): {e}")
                await falar(f"Ocorreu um erro no passo {i+1}. Abortando a tarefa.")
                return
        else:
            print(f"⚠️ Ferramenta '{nome_ferramenta}' não encontrada no catálogo.")
            await falar(f"Desculpe, eu planejei usar uma ferramenta chamada '{nome_ferramenta}', mas não a encontrei.")
            return
    await falar("Tarefa concluída com sucesso.")

async def processar_intencao_complexa(intencao: str, config: dict):
    """
    Orquestra o processo de criação e execução de um plano para uma intenção complexa.
    """
    plano = await criar_plano_de_acao(intencao, config)
    if plano:
        await executar_plano(plano)
    else:
        await falar("Desculpe, não consegui criar um plano de ação para isso.")