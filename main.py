import asyncio
import pyperclip
import random
import os
import re
from datetime import datetime, timedelta
import speech_recognition as sr
import time
import pyautogui
import queue
import sys
import traceback

# --- IMPORTAÇÕES ---
from config_manager import carregar_config
from setup_window import criar_janela_setup
from memory_manager import init_database, adicionar_memoria, limpar_memorias_antigas, gerar_resumo_da_memoria
from status_indicator import StatusIndicator
from voice_control import falar, parar_fala, recognizer, mic, falar_rapido, tts_is_active
from screen_control import (
    executar_acao_na_tela,
    digitar_texto,
    apertar_tecla,
    rolar_tela,
    copiar_arquivo_selecionado,
    copiar_caminho_selecionado,
    colar,
    fechar_janela_por_nome,
    minimizar_janela_por_nome,
    tirar_print,
    abrir_nova_aba,
    fechar_anuncio_na_tela,
    fechar_aba_por_nome,
    encontrar_abas_youtube,
    obter_url_da_aba,
    is_youtube_active,
    clicar_em_elemento,
    clicar_em_imagem
)
from utils.tools import encontrar_e_abrir_pasta, obter_cotacao_acao, obter_noticias_do_dia, obter_previsao_tempo
from transcriber import transcrever_audio_copiado, extrair_caminho_do_clipboard
from utils.vision import encontrar_elementos_por_texto
from gpt_bridge import perguntar_ao_gpt, descrever_imagem
from whatsapp_bot import enviar_mensagem_whatsapp
from file_converter import converter_video_para_audio
from youtube_downloader import baixar_media_youtube
from agenda_control import criar_alarme, listar_alarmes, remover_alarme
from code_writer import gerar_codigo_e_abrir_no_navegador, alterar_codigo_e_abrir_no_navegador

# --- Configurações e Variáveis Globais ---
config = None
ativada = False
loop_principal = None
estado_conversa = {}
CONFIRMACOES_GERAIS = ["Ok.mp3", "Feito.mp3", "Sim.mp3", "Claro.mp3", "Beleza.mp3"]
CONFIRMACOES_ACAO = ["Ok.mp3", "Fechado.mp3"]
alarmes_atuais = []
ultimo_codigo_gerado = None
ultima_resposta_gpt = None
resumo_memoria_principal = ""
indicator_ui = None
command_queue = queue.Queue()
stop_listening = None


# --- Funções de Callback e Configuração ---

async def recarregar_configuracoes_e_atualizar():
    """Recarrega o arquivo de configuração e atualiza a variável global."""
    global config
    print("Configurações salvas! Recarregando...")
    config = carregar_config()
    # --- CORREÇÃO: Usando a chave padronizada "user_name" ---
    nome_usuario = config.get("user_name", "usuário")
    adicionar_memoria("sistema", "Configurações foram atualizadas em tempo de execução.")
    await falar(f"Prontinho, {nome_usuario}! Configurações atualizadas.")

def agendar_recarregamento():
    """Função síncrona que agenda a corrotina de recarregamento no loop de eventos."""
    if loop_principal and loop_principal.is_running():
        asyncio.run_coroutine_threadsafe(recarregar_configuracoes_e_atualizar(), loop_principal)

async def abrir_janela_configuracoes_lia():
    """Função centralizada para abrir a janela de configurações da LIA."""
    adicionar_memoria("sistema", "Usuário pediu para abrir as configurações da LIA.")
    await falar("Ok, abrindo as minhas configurações. Faça as suas alterações e clique em 'Concluir' para salvar.")
    if indicator_ui:
        indicator_ui.schedule_main_thread_task(lambda: criar_janela_setup(callback=agendar_recarregamento))


# --- Funções Auxiliares ---

def extrair_valor_numerico(texto):
    match = re.search(r'\d+', texto)
    if match:
        return int(match.group(0))
    return None


def extrair_tempo_duracao_em_segundos(comando):
    comando_normalizado = comando.replace(" uma ", " 1 ").replace(" um ", " 1 ")
    unidades = {'segundo': 1, 'minuto': 60, 'hora': 3600, 'dia': 86400}
    match = re.search(r'(\d+)\s+(segundo|segundos|minuto|minutos|hora|horas|dia|dias)', comando_normalizado,
                      re.IGNORECASE)
    if match:
        valor = int(match.group(1));
        unidade_encontrada = match.group(2).lower()
        for chave_singular in unidades:
            if chave_singular in unidade_encontrada: return valor * unidades[chave_singular]
    return None


def extrair_tempo_especifico_em_segundos(comando):
    match = re.search(r'(?:às|as|para as|para)\s+(\d{1,2})(?::(\d{2}))?', comando, re.IGNORECASE)
    if not match: return None
    hora_alvo = int(match.group(1));
    minuto_alvo = int(match.group(2)) if match.group(2) else 0
    if hora_alvo < 12 and any(termo in comando for termo in ["da noite", "da tarde"]): hora_alvo += 12
    agora = datetime.now();
    horario_agendado = agora.replace(hour=hora_alvo, minute=minuto_alvo, second=0, microsecond=0)
    if horario_agendado < agora: horario_agendado += timedelta(days=1)
    return int((horario_agendado - agora).total_seconds())


async def cancelar_desligamento():
    os.system("shutdown -a");
    adicionar_memoria("acao", "Agendamento de desligamento cancelado.")
    await falar("Cancelado.")


async def _iniciar_download(url, comando):
    adicionar_memoria("acao", f"Iniciando download do YouTube: {url}")
    baixar_so_audio = "música" in comando or "áudio" in comando
    if baixar_so_audio:
        await falar(f"Ok, a baixar a música, por favor aguarde.")
    else:
        await falar(f"Ok, a baixar o vídeo, por favor aguarde.")
    resultado = baixar_media_youtube(url, baixar_audio=baixar_so_audio)
    await falar(resultado)


async def processar_comando(comando):
    global ativada, estado_conversa, alarmes_atuais, ultimo_codigo_gerado, ultima_resposta_gpt, config, resumo_memoria_principal
    comando = comando.strip().lower()
    adicionar_memoria("conversa", f"Usuário disse: {comando}")

    if estado_conversa.get('acao') == 'aguardando_confirmacao_configuracoes':
        if any(termo in comando for termo in ["windows", "do windows", "sistema"]):
            await falar("Ok, abrindo as configurações do Windows.")
            os.system("start ms-settings:")
        elif any(termo in comando for termo in ["assistente", "lia", "sua", "suas"]):
            await abrir_janela_configuracoes_lia()
        else:
            await falar("Não entendi sua escolha. Operação cancelada.")
        estado_conversa = {}
        return

    if estado_conversa.get('acao') == 'aguardando_confirmacao_desligar':
        if "computador" in comando or "pc" in comando:
            await falar("Ok, desligando o computador.")
            os.system("shutdown -s -t 1")
        elif "lia" in comando or "assistente" in comando or "você" in comando:
            ativada = False
            loop_principal.call_soon_threadsafe(indicator_ui.set_inactive)
            await falar("Até mais.")
        else:
            await falar("Não entendi sua escolha. Operação cancelada.")
        estado_conversa = {}
        return

    if estado_conversa.get('acao') == 'aguardando_selecao_youtube':
        aba_selecionada = None
        if any(x in comando for x in ["a primeira", "primeira", "número um", "opção 1"]):
            aba_selecionada = estado_conversa['abas'][0]
        elif any(x in comando for x in ["a segunda", "segunda", "número dois", "opção 2"]):
            if len(estado_conversa['abas']) > 1:
                aba_selecionada = estado_conversa['abas'][1]
        if aba_selecionada:
            url = obter_url_da_aba(aba_selecionada)
            if url:
                await _iniciar_download(url, estado_conversa['comando_original'])
            else:
                await falar("Desculpe, não consegui obter o link dessa aba.")
        else:
            await falar("Não entendi a sua escolha. Operação cancelada.")
        estado_conversa = {}
        return

    if estado_conversa.get('acao') == 'aguardando_selecao_clique':
        opcao_selecionada = None
        if any(x in comando for x in ["o primeiro", "primeiro", "a primeira", "primeira", "número um", "opção 1"]):
            if len(estado_conversa['elementos']) > 0:
                opcao_selecionada = estado_conversa['elementos'][0]
        elif any(x in comando for x in ["o segundo", "segundo", "a segunda", "segunda", "número dois", "opção 2"]):
            if len(estado_conversa['elementos']) > 1:
                opcao_selecionada = estado_conversa['elementos'][1]
        elif any(x in comando for x in ["o terceiro", "terceiro", "a terceira", "terceira", "número três", "opção 3"]):
            if len(estado_conversa['elementos']) > 2:
                opcao_selecionada = estado_conversa['elementos'][2]

        if opcao_selecionada:
            clicar_em_elemento(opcao_selecionada)
            falar_rapido(random.choice(CONFIRMACOES_GERAIS))
        else:
            await falar("Não entendi a sua escolha. Operação cancelada.")

        estado_conversa = {}
        return

    palavras_de_interrupcao = [
        "cala a boca", "cala", "cale", "calada", "cale-se", "quieta", "quieto",
        "fique quieta", "fique quieto", "silencio", "silêncio", "faça silêncio",
        "xiu", "shh", "parar", "pare", "chega", "basta", "já deu", "pode parar", "pause", "pausa"
    ]
    if any(palavra in comando for palavra in palavras_de_interrupcao):
        adicionar_memoria("interrupcao", "Comando de silêncio recebido.")
        return

    gatilhos_config = ["configurar lia", "configurações", "abrir configurações", "mudar configuração", "configurar"]
    if any(gatilho in comando for gatilho in gatilhos_config):
        estado_conversa = {'acao': 'aguardando_confirmacao_configuracoes'}
        await falar("Você quer abrir as configurações do Windows ou da assistente?")
        return

        # No arquivo: main.py

        # No arquivo: main.py

    gatilhos_clima = ["previsão do tempo", "como está o tempo", "qual o clima", "temperatura em"]
    for gatilho in gatilhos_clima:
        if gatilho in comando:
            periodo = "hoje"

            # --- CORREÇÃO APLICADA AQUI ---
            # Lógica aprimorada para detectar o período

            # Palavras-chave completas para "semana"
            periodos_semana = ["essa semana", "nesta semana", "dessa semana", "desta semana"]
            # Finais de frase incompletos que também indicam "semana"
            terminos_semana = [" para essa", " dessa", " para esta", " desta"]

            if "amanhã" in comando:
                periodo = "amanha"
            # Verifica tanto as palavras-chave completas quanto os finais de frase
            elif any(termo in comando for termo in periodos_semana) or any(
                    comando.endswith(termo) for termo in terminos_semana):
                periodo = "semana"
            # --- FIM DA CORREÇÃO ---

            # Lógica robusta para extrair o nome da cidade (mantida da correção anterior)
            period_keywords = [
                'para hoje', 'hoje', 'para amanhã', 'amanhã',
                'para essa semana', 'essa semana', 'para nesta semana', 'nesta semana',
                'para dessa semana', 'dessa semana', 'para desta semana', 'desta semana'
            ]
            temp_comando = comando.replace(gatilho, '', 1)
            for keyword in period_keywords:
                temp_comando = re.sub(r'\b' + re.escape(keyword) + r'\b', '', temp_comando, flags=re.IGNORECASE)

            # Adicionalmente, remove os finais de frase para limpar o nome da cidade
            for termino in terminos_semana:
                if temp_comando.endswith(termino):
                    temp_comando = temp_comando[:-len(termino)]

            cidade_extraida = temp_comando.replace("em", "").strip()

            cidade_padrao = config.get('cidade_padrao', 'São Paulo')
            if not cidade_extraida:
                cidade = cidade_padrao
                if periodo != "hoje":
                    await falar(f"Mostrando a previsão para {periodo} em {cidade}, sua cidade padrão.")
                else:
                    await falar(f"Mostrando a previsão para {cidade}, sua cidade padrão.")
            else:
                cidade = cidade_extraida

            adicionar_memoria("acao",
                              f"Usuário pediu previsão do tempo para '{cidade}' para o período '{periodo}'.")
            previsao = obter_previsao_tempo(cidade, periodo)
            ultima_resposta_gpt = previsao
            await falar(previsao)
            return

    gatilhos_alterar_codigo = ["altere o código", "alterar o código", "modifique o código", "modifica o código",
                               "adicione ao código"]
    for gatilho in gatilhos_alterar_codigo:
        if gatilho in comando:
            if not ultimo_codigo_gerado:
                await falar("Não há nenhum código na memória para alterar. Por favor, crie um código primeiro.")
                return

            pedido_de_alteracao = comando.split(gatilho, 1)[-1].strip()
            if not pedido_de_alteracao:
                await falar("Ok, o que você gostaria de alterar ou adicionar?")
                return

            await falar(
                f"Entendido. Ainda estou a aprender a programar, por isso considere esta uma função beta. Modificando o código para {pedido_de_alteracao}. Um momento...")
            resultado, novo_codigo = await alterar_codigo_e_abrir_no_navegador(ultimo_codigo_gerado,
                                                                               pedido_de_alteracao)
            if novo_codigo:
                ultimo_codigo_gerado = novo_codigo
            await falar(resultado)
            return

    gatilhos_criar_codigo = ["crie um código", "escreva um código", "faça um código", "crie um script",
                             "escreva um script", "programe", "gera um código"]
    for gatilho in gatilhos_criar_codigo:
        if gatilho in comando:
            descricao_do_codigo = comando.split(gatilho, 1)[-1].strip()
            if "para" in descricao_do_codigo.lower().split()[0]:
                descricao_do_codigo = descricao_do_codigo.split("para", 1)[-1].strip()

            if not descricao_do_codigo:
                await falar("Claro, o que você quer que eu programe?")
                return

            await falar(
                f"Ok. Ainda estou a aprender a programar, por isso considere esta uma função beta. Preparando um ambiente para {descricao_do_codigo}. Um momento...")
            resultado, codigo_gerado = await gerar_codigo_e_abrir_no_navegador(descricao_do_codigo)
            if codigo_gerado:
                ultimo_codigo_gerado = codigo_gerado
            await falar(resultado)
            return

    if comando in ["dormir", "fim", "desativar", "desativa", "desative"]:
        ativada = False;
        loop_principal.call_soon_threadsafe(indicator_ui.set_inactive)
        await falar("Até mais.");
        adicionar_memoria("estado", "Assistente foi desativada pelo usuário.")
        return

    if comando in ["desligar", "desliga"]:
        estado_conversa = {'acao': 'aguardando_confirmacao_desligar'}
        await falar("Você quer desligar a assistente ou o computador?")
        return

    gatilhos_desligar_pc = ["desligar pc", "desligar o computador", "desligar máquina", "desligue o pc",
                            "desligue o computador", "encerrar o sistema", "encerrar", "shutdown"]
    if any(gatilho in comando for gatilho in gatilhos_desligar_pc) and "programar" not in comando:
        adicionar_memoria("acao_critica", "Comando para desligar o computador recebido.")
        await falar("Desligando.");
        os.system("shutdown -s -t 1");
        return

    if any(palavra in comando for palavra in ["play", "pausar", "tocar", "continuar", "pausa"]):
        apertar_tecla('play/pause')
        return

    if any(palavra in comando for palavra in ["próxima música", "próxima faixa", "próximo"]):
        if is_youtube_active():
            apertar_tecla('shift+n')
        else:
            apertar_tecla('próxima')
        return

    if any(palavra in comando for palavra in ["música anterior", "faixa anterior", "anterior"]):
        apertar_tecla('anterior')
        return

    if any(palavra in comando for palavra in ["aumentar o volume", "aumenta o som"]):
        valor = extrair_valor_numerico(comando)
        repeticoes = 3
        if valor:
            repeticoes = valor // 2
        for _ in range(repeticoes):
            apertar_tecla('aumentar volume')
            time.sleep(0.05)
        return

    if any(palavra in comando for palavra in ["diminuir o volume", "abaixar o som", "abaixa o som"]):
        valor = extrair_valor_numerico(comando)
        repeticoes = 3
        if valor:
            repeticoes = valor // 2
        for _ in range(repeticoes):
            apertar_tecla('diminuir volume')
            time.sleep(0.05)
        return

    if comando in ["mudo", "silenciar"]:
        apertar_tecla('mudo')
        return

    gatilhos_listar = ["quais são meus alarmes", "meus lembretes", "o que tenho agendado"]
    if any(gatilho in comando for gatilho in gatilhos_listar):
        alarmes_atuais = listar_alarmes()
        if not alarmes_atuais:
            await falar("Você não tem nenhum alarme definido.")
        else:
            resposta_falada = "Aqui estão os seus alarmes em ordem: "
            partes_resposta = []
            for i, alarme in enumerate(alarmes_atuais):
                partes_resposta.append(f"{i + 1}. {alarme['titulo']}.")
            resposta_falada += " ".join(partes_resposta)
            await falar(resposta_falada)
        return

    gatilhos_remover = ["remova o alarme", "remover alarme", "apagar alarme", "remova o lembrete"]
    for gatilho in gatilhos_remover:
        if gatilho in comando:
            termo_para_remover = comando.split(gatilho, 1)[-1].strip()
            indice = extrair_valor_numerico(termo_para_remover)
            if indice and 0 < indice <= len(alarmes_atuais):
                alarme_a_remover = alarmes_atuais.pop(indice - 1)
                if remover_alarme(alarme_a_remover['nome_completo']):
                    await falar(f"Ok, removi o alarme {indice}.")
                else:
                    await falar("Ocorreu um erro ao tentar remover esse alarme.")
                return
            await falar(f"Não encontrei o alarme número {indice}. Tente listar os alarmes primeiro.")
            return

    gatilhos_alarme = ["defina um alarme", "crie um alarme", "me lembre de"]
    for gatilho in gatilhos_alarme:
        if comando.startswith(gatilho):
            titulo_completo = comando.split(gatilho, 1)[-1].strip()
            if not titulo_completo:
                await falar("Por favor, diga o motivo do alarme.")
                return
            segundos = extrair_tempo_duracao_em_segundos(comando)
            if not segundos:
                await falar(
                    "Não consegui entender para quando devo definir. Por favor, inclua um tempo como 'em 5 minutos'.")
                return
            data_hora = datetime.now() + timedelta(seconds=segundos)
            padrao_limpeza = r'\s+(em|daqui a)\s+.*'
            titulo_final = re.sub(padrao_limpeza, '', titulo_completo, flags=re.IGNORECASE)
            if titulo_final.startswith("para "):
                titulo_final = titulo_final[5:]
            resultado = criar_alarme(titulo_final.strip(), data_hora)
            await falar(resultado)
            return

    gatilhos_nova_aba = ["abrir nova aba", "abre uma nova aba", "nova aba", "nova guia", "abre nova guia"]
    if any(gatilho in comando for gatilho in gatilhos_nova_aba):
        if abrir_nova_aba():
            falar_rapido(random.choice(CONFIRMACOES_GERAIS))
        else:
            await falar("Não consegui abrir uma nova aba.")
        return

    gatilhos_noticias = ["quais as notícias", "me dê as notícias", "notícias de hoje", "manchetes do dia",
                         "me atualize", "últimas notícias", "notícias do dia"]
    if any(gatilho in comando for gatilho in gatilhos_noticias):
        await falar("Buscando as últimas notícias...")
        noticias = obter_noticias_do_dia()
        ultima_resposta_gpt = noticias
        await falar(noticias)
        return

    if any(gatilho in comando for gatilho in ["cancelar desligamento", "cancelar reinicialização"]):
        await cancelar_desligamento();
        return

    gatilhos_print = ["tirar print", "tira print", "printar a tela", "printa a tela", "print", "capturar tela",
                      "captura de tela", "faz um print", "bater um print", "fotografar a tela"]
    if any(gatilho in comando for gatilho in gatilhos_print):
        if tirar_print(): falar_rapido("Feito.mp3"); return

    gatilhos_descrever_tela = ["descreva a tela", "o que você vê", "descreve o que você tá vendo", "analisar a tela",
                               "o que tem na tela",
                               "o que está na tela", "leia a tela", "lê a tela pra mim", "o que é isso",
                               "descreve isso pra mim",
                               "o que tá rolando aí", "me diz o que tem aí"]
    if any(gatilho in comando for gatilho in gatilhos_descrever_tela):
        await falar("Ok, um momento...")
        caminho_do_print = tirar_print()
        if caminho_do_print:
            prompt = "Descreva de forma concisa o que está visível nesta imagem da tela de um computador."
            descricao = await descrever_imagem(caminho_do_print, prompt)
            ultima_resposta_gpt = descricao
            await falar(descricao)
        else:
            await falar("Desculpe, falhei ao tirar o print para analisar.")
        return

    gatilhos_descrever_imagem = ["descreva essa imagem", "descreva a imagem", "o que é essa imagem", "analisar imagem",
                                 "descreva a imagem copiada", "analise o que eu copiei", "o que é isso que eu copiei",
                                 "descreve a foto",
                                 "me diga o que é essa foto", "e essa imagem", "identifique a imagem"]
    if any(gatilho in comando for gatilho in gatilhos_descrever_imagem):
        await falar("Certo, vou analisar a imagem copiada.")
        caminho_da_imagem = extrair_caminho_do_clipboard()
        if caminho_da_imagem:
            prompt = "O que é esta imagem? Descreva-a para mim de forma concisa."
            descricao = await descrever_imagem(caminho_da_imagem, prompt)
            ultima_resposta_gpt = descricao
            await falar(descricao)
        else:
            await falar("Não encontrei um caminho de imagem válido. Copie o arquivo da imagem e tente de novo.")
        return

    gatilhos_fechar_anuncio = ["fechar anúncio", "fecha o anúncio", "fecha esse anúncio", "clica no x",
                               "tira esse anúncio", "fechar propaganda"]
    if any(gatilho in comando for gatilho in gatilhos_fechar_anuncio):
        if fechar_anuncio_na_tela():
            falar_rapido(random.choice(CONFIRMACOES_ACAO))
        else:
            await falar("Não encontrei um anúncio para fechar.")
        return

    gatilhos_cotacao = ["qual a cotação de", "valor da ação da", "preço do"]
    for gatilho in gatilhos_cotacao:
        if comando.startswith(gatilho):
            nome_ativo = comando.replace(gatilho, "", 1).strip()
            if nome_ativo:
                await falar(f"Buscando a cotação de {nome_ativo}, um momento...")
                resultado = obter_cotacao_acao(nome_ativo)
                ultima_resposta_gpt = resultado
                await falar(resultado)
            else:
                await falar("Por favor, diga o nome do ativo que você quer saber.")
            return

    gatilhos_fechar_aba = ["fechar aba", "fecha a aba"]
    for gatilho in gatilhos_fechar_aba:
        if comando.startswith(gatilho):
            nome_da_aba = comando.replace(gatilho, "", 1).strip()
            if nome_da_aba:
                if fechar_aba_por_nome(nome_da_aba):
                    falar_rapido(random.choice(CONFIRMACOES_ACAO))
                else:
                    await falar(f"Não encontrei a aba {nome_da_aba}.")
            else:
                await falar("Por favor, diga o nome da aba que devo fechar.")
            return

    gatilhos_whatsapp = ["mande um zap para", "enviar uma mensagem para"]
    for gatilho in gatilhos_whatsapp:
        if comando.startswith(gatilho):
            resto_comando = comando.replace(gatilho, "", 1).strip()
            partes = resto_comando.split(" ", 1)
            if len(partes) < 2:
                await falar("Por favor, diga o nome do contato e a mensagem que quer enviar.")
                return
            nome_contato, mensagem = partes[0], partes[1]
            await falar(f"Ok, a enviar a seguinte mensagem para {nome_contato}: {mensagem}")
            resultado = await enviar_mensagem_whatsapp(nome_contato, mensagem)
            await falar(resultado)
            return

    if comando.startswith("transcrever"):
        texto_transcrito = transcrever_audio_copiado()
        if texto_transcrito and not any(err in texto_transcrito for err in ["Não encontrei", "erro", "não parece"]):
            pyperclip.copy(texto_transcrito)
            falar_rapido("OkTransscrito.mp3")
        else:
            await falar(texto_transcrito or "Falha na transcrição.")
        return

    if any(gatilho in comando for gatilho in ["converta o arquivo", "converter arquivo"]):
        partes_comando = comando.split(" para ")
        if len(partes_comando) < 2:
            await falar("Por favor, especifique o formato de destino.")
            return
        formato_saida = partes_comando[-1].strip().lower()
        caminho_arquivo_copiado = extrair_caminho_do_clipboard()
        if not caminho_arquivo_copiado:
            await falar(
                f"Certo. Para converter para {formato_saida}, por favor, copie o arquivo. Você tem 10 segundos.")
            await asyncio.sleep(10)
            caminho_arquivo_copiado = extrair_caminho_do_clipboard()
            if not caminho_arquivo_copiado:
                await falar("Ainda não encontrei um arquivo válido. Tente o comando novamente.")
                return
        await falar("Ok, iniciando a conversão, isso pode demorar um pouco.")
        resultado = converter_video_para_audio(caminho_arquivo_copiado, formato_saida)
        await falar(resultado)
        return

    if any(gatilho in comando for gatilho in ["baixar do youtube", "baixar vídeo", "baixar música"]):
        abas_yt = encontrar_abas_youtube()
        if len(abas_yt) == 1:
            url = obter_url_da_aba(abas_yt[0])
            if url:
                await _iniciar_download(url, comando)
            else:
                await falar("Desculpe, não consegui obter o link da aba.")
        elif len(abas_yt) > 1:
            await falar(f"Encontrei {len(abas_yt)} abas do YouTube. Qual delas você quer baixar?")
            for i, aba in enumerate(abas_yt[:3]):
                titulo_limpo = aba['titulo'].replace("- YouTube", "").strip()
                await falar(f"A {'primeira' if i == 0 else 'segunda' if i == 1 else 'terceira'} é: {titulo_limpo}")
            estado_conversa.update({'acao': 'aguardando_selecao_youtube', 'abas': abas_yt, 'comando_original': comando})
        else:
            await falar("Não encontrei abas do YouTube. Copie o link. Você tem 10 segundos.")
            await asyncio.sleep(10)
            url = pyperclip.paste()
            if "youtube.com" in url or "youtu.be" in url:
                await _iniciar_download(url, comando)
            else:
                await falar("Não encontrei um link válido.")
        return

    gatilhos_minimizar = ["minimizar", "minimize a janela", "minimize"]
    for gatilho in gatilhos_minimizar:
        if comando.startswith(gatilho):
            alvo = comando.replace(gatilho, "", 1).strip()
            if not alvo:
                alvo = "janela atual"
                pyautogui.hotkey('win', 'down')
                await falar("Ok.")
                return

            titulo_real, score = minimizar_janela_por_nome(alvo)
            if titulo_real:
                falar_rapido(random.choice(CONFIRMACOES_ACAO))
            else:
                await falar("Não encontrei essa janela para minimizar.");
            return

    gatilhos_fechar = ["fechar", "fecha", "feche", "mate", "mata"]
    for gatilho in gatilhos_fechar:
        if comando.startswith(gatilho):
            alvo = comando.replace(gatilho, "", 1).strip();
            if alvo and fechar_janela_por_nome(alvo)[0]:
                falar_rapido(random.choice(CONFIRMACOES_ACAO))
            else:
                await falar("Não encontrei.");
                return

    gatilhos_abrir_pasta = ["abrir pasta", "abre a pasta", "abra a pasta", "procurar a pasta", "busque a pasta",
                            "procure pasta", "busque pasta", "ir para pasta", "vai pra pasta", "procurar pasta",
                            "buscar pasta"]
    for gatilho in gatilhos_abrir_pasta:
        if comando.startswith(gatilho):
            alvo = comando.replace(gatilho, "", 1).strip();
            if alvo and encontrar_e_abrir_pasta(alvo):
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar("Não encontrei.");
                return

    gatilhos_enviar = ["enviar", "envie", "mandar", "manda", "confirmar", "confirme", "envia", "mande", "confirma"]
    if comando in gatilhos_enviar:
        apertar_tecla('enter')
        falar_rapido(random.choice(CONFIRMACOES_GERAIS))
        return

    gatilhos_apagar = ["apagar", "backspace", "excluir"]
    if comando in gatilhos_apagar:
        apertar_tecla('backspace')
        return

    gatilhos_selecionar_tudo = ["selecionar tudo", "seleciona tudo", "selecione tudo", "selecionar todos",
                                "seleciona todos", "ctrl a"]
    if any(gatilho in comando for gatilho in gatilhos_selecionar_tudo):
        apertar_tecla('ctrl+a')
        falar_rapido(random.choice(CONFIRMACOES_GERAIS))
        return

    if any(palavra in comando for palavra in
           ["desfazer", "desfaz", "desfaça", "ctrl z", "voltar", "voltar uma vez", "volta uma vez", "volta uma ação"]):
        apertar_tecla('ctrl+z');
        falar_rapido(random.choice(CONFIRMACOES_GERAIS));
        return

    gatilhos_copiar_arquivo = ["copiar arquivo", "copiar o arquivo", "copia o arquivo", "copia arquivo"]
    for gatilho in gatilhos_copiar_arquivo:
        if comando.startswith(gatilho):
            nome_arquivo = comando.replace(gatilho, "", 1).strip()
            if nome_arquivo:
                await falar(f"Ok, tentando selecionar e copiar {nome_arquivo}...")
                elementos = encontrar_elementos_por_texto(nome_arquivo)
                if elementos:
                    clicar_em_elemento(elementos[0])
                else:
                    await falar("Não consegui encontrar esse arquivo na tela.")
                    return
            if copiar_arquivo_selecionado():
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar("Falha ao copiar.")
            return

    if any(gatilho in comando for gatilho in ["copiar caminho", "copiar o caminho", "copiar local", "copia o local"]):
        if copiar_caminho_selecionado(): await falar("Copiado."); return
    if comando in ["copiar", "copia", "copie", "ctrl c"]:
        apertar_tecla('ctrl+c');
        falar_rapido(random.choice(CONFIRMACOES_GERAIS));
        return
    if comando in ["colar", "cola", "cole", "ctrl v"]:
        colar();
        falar_rapido(random.choice(CONFIRMACOES_GERAIS));
        return

    gatilhos_clique_icone = ["clique no ícone", "clica no ícone", "clicar no ícone"]
    for gatilho in gatilhos_clique_icone:
        if comando.startswith(gatilho):
            nome_do_icone = comando.split(gatilho, 1)[-1].strip()
            if not nome_do_icone:
                await falar("Qual ícone devo clicar?")
                return
            if clicar_em_imagem(nome_do_icone):
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar(f"Não encontrei o ícone {nome_do_icone} na tela.")
            return

    gatilhos_clique = ["clicar em", "clica em", "clique em"]
    for gatilho in gatilhos_clique:
        if comando.startswith(gatilho):
            palavra_alvo = comando.split(gatilho, 1)[-1].strip()
            if not palavra_alvo:
                await falar("O que devo clicar?")
                return
            elementos = encontrar_elementos_por_texto(palavra_alvo)
            if not elementos:
                await falar("Não vi.")
                return
            if len(elementos) == 1:
                clicar_em_elemento(elementos[0])
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar(
                    f"Encontrei {len(elementos)} opções para '{palavra_alvo}'. Qual devo clicar? A primeira ou a segunda?")
                estado_conversa['acao'] = 'aguardando_selecao_clique'
                estado_conversa['elementos'] = elementos
            return

    gatilhos_abrir = ["abrir", "abra", "abre", "executar"]
    for gatilho in gatilhos_abrir:
        if comando.startswith(gatilho):
            argumento = comando[len(gatilho):].strip()
            if argumento and executar_acao_na_tela(argumento):
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar("Não achei.");
            return

    gatilhos_digitar = ["digitar", "digita", "escrever"]
    for gatilho in gatilhos_digitar:
        if comando.startswith(gatilho):
            texto_para_digitar = comando.replace(gatilho, "", 1).strip()
            if texto_para_digitar: digitar_texto(texto_para_digitar); return

    gatilhos_apertar = ["apertar", "aperte", "pressionar", "tecla"]
    for gatilho in gatilhos_apertar:
        if comando.startswith(gatilho):
            tecla = comando.replace(gatilho, "", 1).strip()
            if tecla: apertar_tecla(tecla); return

    if any(gatilho in comando for gatilho in ["rolar para cima", "sobe"]):
        rolar_tela("cima");
        return
    if any(gatilho in comando for gatilho in ["rolar para baixo", "desce"]):
        rolar_tela("baixo");
        return

    if comando in ["copiar resposta", "copiar a resposta"]:
        if ultima_resposta_gpt:
            pyperclip.copy(ultima_resposta_gpt)
            await falar("Copiado.")
        else:
            await falar("Não há nenhuma resposta recente para copiar.")
        return

    if comando in ["anotar resposta", "anotar a resposta"]:
        if ultima_resposta_gpt:
            await falar("Ok, anotei a resposta para você.")
            pyperclip.copy(ultima_resposta_gpt)
            os.system("start notepad.exe")
            await asyncio.sleep(1)
            pyautogui.hotkey('ctrl', 'v')
        else:
            await falar("Não há nenhuma resposta recente para anotar.")
        return

    resposta = await perguntar_ao_gpt(comando, config.get('lia_personality', 50), contexto_memoria=resumo_memoria_principal)
    ultima_resposta_gpt = resposta
    adicionar_memoria("conversa", f"LIA respondeu: {resposta}")
    await falar(resposta)


def callback_escuta(recognizer, audio):
    global ativada, loop_principal, config
    try:
        frase = recognizer.recognize_google(audio, language='pt-BR').lower()
        print(f"🗣️  Você disse: {frase}")
        if tts_is_active.is_set():
            print("🎤 Interrompendo a fala atual para processar novo comando.")
            parar_fala()
            time.sleep(0.1)
        if not ativada and any(x in frase for x in ["lia", "ativar", "ativa"]):
            ativada = True
            loop_principal.call_soon_threadsafe(indicator_ui.set_active)
            adicionar_memoria("estado", "Assistente ativada.")
            nome_usuario = config.get("user_name", "usuário")
            asyncio.run_coroutine_threadsafe(falar(f"Ativada para {nome_usuario}"), loop_principal)
        elif ativada:
            asyncio.run_coroutine_threadsafe(processar_comando(frase), loop_principal)
    except sr.UnknownValueError:
        pass
    except Exception as e:
        print(f"🤯 Erro inesperado no callback: {e}")


async def main():
    global loop_principal, resumo_memoria_principal, indicator_ui, stop_listening
    loop_principal = asyncio.get_event_loop()

    print("🧠 Agendando resumo de memória para ser executado em segundo plano...")
    asyncio.create_task(atualizar_resumo_memoria_em_background())

    if not mic:
        print("❌ Microfone não encontrado. Encerrando.")
        return

    stop_listening = recognizer.listen_in_background(mic, callback_escuta, phrase_time_limit=5)

    nome_usuario = config.get("user_name", "usuário")
    print(f"\n👋 Olá, {nome_usuario}! Eu sou a LIA. Diga 'LIA' para me ativar.")
    print(f"   (Humor definido em {config.get('lia_personality', 50)}%)")
    adicionar_memoria("sistema", "LIA iniciada com sucesso e ouvindo.")

    try:
        print("🚀 Iniciando a interface gráfica do StatusIndicator...")
        indicator_ui = StatusIndicator(command_queue)
        print("✅ StatusIndicator inicializado com sucesso.")

        print("🏁 Loop principal iniciado. A LIA está totalmente operacional.")
        while True:
            indicator_ui.update()
            try:
                command = command_queue.get_nowait()
                if command == "open_settings":
                    await abrir_janela_configuracoes_lia()
                elif command == "quit_app":
                    print("👋 Encerrando LIA a partir do ícone.")
                    break
            except queue.Empty:
                pass
            await asyncio.sleep(0.01)

    except Exception as e:
        print("\n" + "=" * 50)
        print("🚨 ERRO CRÍTICO NO LOOP PRINCIPAL 🚨")
        print(f"Ocorreu um erro inesperado que fez a LIA parar: {e}")
        traceback.print_exc()
        print("=" * 50 + "\n")


async def atualizar_resumo_memoria_em_background():
    global resumo_memoria_principal
    resumo_memoria_principal = await gerar_resumo_da_memoria()
    print("✅ Resumo da memória carregado em segundo plano e pronto para uso.")


if __name__ == "__main__":
    init_database()
    limpar_memorias_antigas()

    config = carregar_config()

    if config is None:
        print("👋 Bem-vindo(a) à LIA! Parece que esta é a sua primeira vez.")
        print("   Por favor, preencha as configurações na janela que abriu.")
        criar_janela_setup(callback=agendar_recarregamento)
        config = carregar_config()
        if config is None:
            print("❌ A configuração não foi salva. Encerrando o programa.")
            adicionar_memoria("erro", "Programa encerrado por falta de configuração.")
            exit()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        adicionar_memoria("sistema", "Programa encerrado pelo usuário (KeyboardInterrupt).")
        print("\nPrograma encerrado.")
    finally:
        print("🔚 Finalizando processos. O programa será encerrado agora.")
        if stop_listening:
            print("   -> Parando a escuta do microfone em segundo plano...")
            stop_listening(wait_for_stop=False)
        if 'indicator_ui' in globals() and indicator_ui:
            indicator_ui.close()
        sys.exit(0)