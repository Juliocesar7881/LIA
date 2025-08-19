# main.py (Versão 100% completa com todas as funcionalidades)

import asyncio
import pyperclip
import random
import os
import re
from datetime import datetime, timedelta
import speech_recognition as sr
import time

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
    tirar_print,
    abrir_nova_aba,
    fechar_anuncio_na_tela,
    fechar_aba_por_nome,
    encontrar_abas_youtube,
    obter_url_da_aba,
    is_youtube_active
)
from utils.tools import encontrar_e_abrir_pasta, obter_cotacao_acao, obter_noticias_do_dia
from transcriber import transcrever_audio_copiado, extrair_caminho_do_clipboard
from utils.vision import clicar_em_palavra
from gpt_bridge import perguntar_ao_gpt, descrever_imagem
from memory import registrar_evento
from whatsapp_bot import enviar_mensagem_whatsapp
from file_converter import converter_video_para_audio
from youtube_downloader import baixar_media_youtube
from agenda_control import criar_alarme, listar_alarmes, remover_alarme

# --- Configurações e Funções Auxiliares ---
ativada = False
loop_principal = None
estado_conversa = {}
CONFIRMACOES_GERAIS = ["Ok.mp3", "Feito.mp3", "Sim.mp3", "Claro.mp3", "Beleza.mp3"]
CONFIRMACOES_ACAO = ["Ok.mp3", "Fechado.mp3"]
alarmes_atuais = []  # Armazena a última lista de alarmes para remoção por índice


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
    registrar_evento("Agendamento cancelado.")
    await falar("Cancelado.")


async def _iniciar_download(url, comando):
    baixar_so_audio = "música" in comando or "áudio" in comando
    if baixar_so_audio:
        await falar(f"Ok, a baixar a música, por favor aguarde.")
    else:
        await falar(f"Ok, a baixar o vídeo, por favor aguarde.")
    resultado = baixar_media_youtube(url, baixar_audio=baixar_so_audio)
    await falar(resultado)


# --- Processador de Comandos ---
async def processar_comando(comando):
    global ativada, estado_conversa, alarmes_atuais
    comando = comando.strip().lower()

    # --- LÓGICA DE CONVERSA ---
    if estado_conversa.get('acao') == 'aguardando_confirmacao_desligar':
        if "computador" in comando or "pc" in comando:
            await falar("Ok, desligando o computador.")
            os.system("shutdown -s -t 1")
        elif "lisa" in comando or "assistente" in comando or "você" in comando:
            ativada = False
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
    # --- FIM DA LÓGICA DE CONVERSA ---

    palavras_de_interrupcao = [
        "cala a boca", "cala", "cale", "calada", "cale-se", "quieta", "quieto",
        "fique quieta", "fique quieto", "silencio", "silêncio", "faça silêncio",
        "xiu", "shh", "parar", "pare", "chega", "basta", "já deu", "pode parar", "pause", "pausa"
    ]
    if any(palavra in comando for palavra in palavras_de_interrupcao):
        registrar_evento("Comando de silêncio.");
        return

    # --- LÓGICA DE DESLIGAMENTO (ATUALIZADA) ---
    if comando in ["dormir", "fim", "desativar", "desativa", "desative"]:
        ativada = False;
        await falar("Até mais.");
        registrar_evento("Assistente desativada.");
        return

    if comando in ["desligar", "desliga"]:
        estado_conversa = {'acao': 'aguardando_confirmacao_desligar'}
        await falar("Você quer desligar a assistente ou o computador?")
        return

    gatilhos_desligar_pc = ["desligar pc", "desligar o computador", "desligar máquina", "desligue o pc",
                            "desligue o computador", "encerrar o sistema", "encerrar", "shutdown"]
    if any(gatilho in comando for gatilho in gatilhos_desligar_pc) and "programar" not in comando:
        await falar("Desligando.");
        os.system("shutdown -s -t 1");
        return
    # --- FIM DA LÓGICA DE DESLIGAMENTO ---

    # --- COMANDOS DE CONTROLE DE MÍDIA (LÓGICA REFINADA) ---
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
    # --- FIM DO BLOCO DE MÍDIA ---

    # --- BLOCO DE DESPERTADOR (LÓGICA FINAL) ---
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

            # Tenta remover por índice primeiro
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
            titulo_completo = comando.replace(gatilho, "", 1).strip()
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
    # --- FIM DO BLOCO DE DESPERTADOR ---

    # Comandos de Navegação
    gatilhos_nova_aba = ["abrir nova aba", "abre uma nova aba", "nova aba", "nova guia", "abre nova guia"]
    if any(gatilho in comando for gatilho in gatilhos_nova_aba):
        if abrir_nova_aba():
            falar_rapido(random.choice(CONFIRMACOES_GERAIS))
        else:
            await falar("Não consegui abrir uma nova aba.")
        return

    # Comandos de Informação em Tempo Real
    gatilhos_noticias = ["quais as notícias", "me dê as notícias", "notícias de hoje", "manchetes do dia",
                         "me atualize", "últimas notícias", "notícias do dia"]
    if any(gatilho in comando for gatilho in gatilhos_noticias):
        await falar("Buscando as últimas notícias...")
        noticias = obter_noticias_do_dia()
        await falar(noticias)
        return

    gatilhos_cotacao = [
        "qual a cotação de", "quanto tá a ação da", "preço da ação da", "cotação da", "quanto custa a ação da",
        "qual o valor de", "qual o valor do", "qual o valor da", "valor atual de", "valor atual do", "valor atual da",
        "cotação do", "preço do", "preço da", "valor atual do"
    ]
    for gatilho in gatilhos_cotacao:
        if comando.startswith(gatilho):
            nome_ativo = comando.replace(gatilho, "", 1).strip()
            if nome_ativo:
                await falar(f"Buscando a cotação de {nome_ativo}, um momento...")
                resultado = obter_cotacao_acao(nome_ativo)
                await falar(resultado)
            else:
                await falar("Por favor, diga o nome do ativo que você quer saber.")
            return

    # Comandos de Sistema e Automação
    gatilhos_reiniciar = ["reiniciar pc", "reiniciar o computador", "reiniciar máquina", "reinicie o pc",
                          "reinicie o computador", "reboot", "recomeçar"]
    if any(gatilho in comando for gatilho in gatilhos_reiniciar) and "programar" not in comando:
        await falar("Reiniciando.");
        os.system("shutdown -r -t 1");
        return

    tempo_especifico = extrair_tempo_especifico_em_segundos(comando)
    tempo_duracao = extrair_tempo_duracao_em_segundos(comando)
    if tempo_especifico or tempo_duracao:
        if 'desligar' in comando or 'reiniciar' in comando:
            tempo_total = tempo_especifico or tempo_duracao
            acao = "r" if "reiniciar" in comando else "s"
            os.system(f"shutdown -{acao} -t {tempo_total}")
            await falar(f"Ok, agendamento de {'reinicialização' if acao == 'r' else 'desligamento'} concluído.")
            return

    gatilhos_cancelar = ["cancelar desligamento", "cancelar o desligamento", "cancelar reinicialização",
                         "cancelar agendamento", "não desligar mais", "parar desligamento", "não quero mais desligar"]
    if any(gatilho in comando for gatilho in gatilhos_cancelar):
        await cancelar_desligamento();
        return

    gatilhos_print = ["tirar print", "tira print", "printar a tela", "printa a tela", "print", "capturar tela",
                      "captura de tela", "faz um print", "bater um print", "fotografar a tela"]
    if any(gatilho in comando for gatilho in gatilhos_print):
        if tirar_print(): falar_rapido("Feito.mp3"); return

    # Comandos de Visão
    gatilhos_descrever_tela = [
        "descreva a tela", "o que você vê", "descreve o que você tá vendo", "analisar a tela", "o que tem na tela",
        "o que está na tela", "leia a tela", "lê a tela pra mim", "o que é isso", "descreve isso pra mim",
        "o que tá rolando aí", "me diz o que tem aí"
    ]
    if any(gatilho in comando for gatilho in gatilhos_descrever_tela):
        await falar("Ok, um momento...")
        caminho_do_print = tirar_print()
        if caminho_do_print:
            prompt = "Descreva de forma concisa o que está visível nesta imagem da tela de um computador."
            descricao = descrever_imagem(caminho_do_print, prompt)
            await falar(descricao)
        else:
            await falar("Desculpe, falhei ao tirar o print para analisar.")
        return

    gatilhos_descrever_imagem = [
        "descreva essa imagem", "descreva a imagem", "o que é essa imagem", "analisar imagem",
        "descreva a imagem copiada", "analise o que eu copiei", "o que é isso que eu copiei", "descreve a foto",
        "me diga o que é essa foto", "e essa imagem", "identifique a imagem"
    ]
    if any(gatilho in comando for gatilho in gatilhos_descrever_imagem):
        await falar("Certo, vou analisar a imagem copiada.")
        caminho_da_imagem = extrair_caminho_do_clipboard()
        if caminho_da_imagem:
            prompt = "O que é esta imagem? Descreva-a para mim de forma concisa."
            descricao = descrever_imagem(caminho_da_imagem, prompt)
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

    gatilhos_fechar_aba = ["fechar aba", "fecha a aba", "feche a aba"]
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

    # --- LÓGICA DO WHATSAPP (CORRIGIDA) ---
    gatilhos_whatsapp = [
        "mande um zap para", "manda um zap para", "enviar um zap para",
        "mande uma mensagem para", "manda uma mensagem para", "enviar uma mensagem para"
    ]
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
    # --- FIM DA LÓGICA DO WHATSAPP ---

    if comando.startswith("transcrever"):
        falar_rapido(random.choice(CONFIRMACOES_GERAIS));
        texto_transcrito = None
        if "copiado" in comando:
            texto_transcrito = transcrever_audio_copiado()
        elif "selecionado" in comando:
            if copiar_caminho_selecionado(): texto_transcrito = transcrever_audio_copiado()
        else:
            nome_arquivo = comando.replace("transcrever áudio", "").replace("transcrever", "").strip()
            if not nome_arquivo: await falar("Especifique o arquivo."); return
            if clicar_em_palavra(nome_arquivo)[0]:
                if copiar_caminho_selecionado(): texto_transcrito = transcrever_audio_copiado()
        if texto_transcrito and "Não encontrei" not in texto_transcrito and "erro" not in texto_transcrito and "não parece" not in texto_transcrito:
            pyperclip.copy(texto_transcrito);
            falar_rapido("OkTransscrito.mp3")
        else:
            await falar(texto_transcrito or "Falha na transcrição.")
        return

    gatilhos_converter = ["converta o arquivo", "converter arquivo", "mudar o formato"]
    if any(gatilho in comando for gatilho in gatilhos_converter):
        partes_comando = comando.split(" para ")
        if len(partes_comando) < 2:
            await falar("Por favor, especifique o formato de destino. Por exemplo: 'converta para mp3'.")
            return

        formato_saida = partes_comando[-1].strip().lower()
        caminho_arquivo_copiado = extrair_caminho_do_clipboard()

        if not caminho_arquivo_copiado:
            await falar(
                f"Certo. Para converter para {formato_saida}, por favor, copie o arquivo. Você tem 10 segundos.")
            await asyncio.sleep(10)
            caminho_arquivo_copiado = extrair_caminho_do_clipboard()

            if not caminho_arquivo_copiado:
                await falar(
                    "Ainda não encontrei um arquivo válido na sua área de transferência. Tente o comando novamente.")
                return

        await falar("Ok, encontrei o arquivo. Iniciando a conversão, isso pode demorar um pouco.")

        if formato_saida in ["mp3", "wav", "m4a"]:
            resultado = converter_video_para_audio(caminho_arquivo_copiado, formato_saida)
        else:
            resultado = f"Desculpe, a conversão para o formato {formato_saida} ainda não foi implementada."

        await falar(resultado)
        return

    gatilhos_youtube = ["baixar do youtube", "baixar vídeo", "baixar música"]
    if any(gatilho in comando for gatilho in gatilhos_youtube):
        abas_yt = encontrar_abas_youtube()

        if len(abas_yt) == 1:
            await falar("Encontrei uma aba do YouTube aberta. Iniciando o download.")
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

            estado_conversa['acao'] = 'aguardando_selecao_youtube'
            estado_conversa['abas'] = abas_yt
            estado_conversa['comando_original'] = comando

        else:
            await falar(
                "Não encontrei nenhuma aba do YouTube aberta. Por favor, copie o link. Você tem 10 segundos.")
            await asyncio.sleep(10)
            url = pyperclip.paste()
            if "youtube.com" in url or "youtu.be" in url:
                await _iniciar_download(url, comando)
            else:
                await falar("Não encontrei um link válido. Tente o comando novamente.")
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

    # Comandos de Ação Direta
    gatilhos_enviar = ["enviar", "envie", "mandar", "manda", "confirmar", "confirme", "envia", "mande", "confirma"]
    if comando in gatilhos_enviar:
        apertar_tecla('enter')
        falar_rapido(random.choice(CONFIRMACOES_GERAIS))
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
                sucesso_clique, _, _ = clicar_em_palavra(nome_arquivo)
                if not sucesso_clique:
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

    # Comandos com Argumento
    gatilhos_clique = ["clicar em", "clica em", "clique em", "clicar no", "clica no", "clicar na", "clica na", "clicar",
                       "clica", "clique"]
    for gatilho in gatilhos_clique:
        if comando.startswith(gatilho):
            palavra_alvo = comando[len(gatilho):].strip();
            if palavra_alvo and clicar_em_palavra(palavra_alvo)[0]:
                pass
            else:
                await falar("Não vi.");
                return

    gatilhos_abrir = ["abrir", "abra", "abre", "executar", "executa", "execute", "iniciar", "inicia", "rodar", "rode",
                      "roda"]
    for gatilho in gatilhos_abrir:
        if comando.startswith(gatilho):
            argumento = comando[len(gatilho):].strip();
            if argumento and executar_acao_na_tela(argumento):
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
                return
            else:
                await falar("Não achei.");
                return

    gatilhos_digitar = ["digitar", "digita", "digite", "escrever", "escreve", "escreva"]
    for gatilho in gatilhos_digitar:
        if comando.startswith(gatilho):
            texto_para_digitar = comando.replace(gatilho, "", 1).strip();
            if texto_para_digitar: digitar_texto(texto_para_digitar); return

    gatilhos_apertar = ["apertar", "aperte", "pressionar", "pressione", "tecla"]
    for gatilho in gatilhos_apertar:
        if comando.startswith(gatilho):
            tecla = comando.replace(gatilho, "", 1).strip();
            if tecla: apertar_tecla(tecla); return

    gatilhos_rolar_cima = ["rolar para cima", "sobe", "subir", "rola pra cima", "navegar para cima", "vai pra cima",
                           "sobe a página", "página pra cima", "scroll pra cima", "pra cima", "cima"]
    gatilhos_rolar_baixo = ["rolar para baixo", "desce", "descer", "rola pra baixo", "navegar para baixo",
                            "vai pra baixo", "desce a página", "página pra baixo", "scroll pra baixo", "pra baixo",
                            "baixo"]
    if any(gatilho in comando for gatilho in gatilhos_rolar_cima):
        rolar_tela("cima");
        return
    if any(gatilho in comando for gatilho in gatilhos_rolar_baixo):
        rolar_tela("baixo");
        return

    # Se nada correspondeu, pergunta ao GPT
    resposta = perguntar_ao_gpt(comando)
    await falar(resposta)


# --- Callback de Escuta e Função Main (sem alterações) ---
def callback_escuta(recognizer, audio):
    global ativada, loop_principal
    try:
        frase = recognizer.recognize_google(audio, language='pt-BR').lower()
        print(f"🗣️  Você disse: {frase}")
        if tts_is_active.is_set():
            print("🎤 Interrompendo a fala atual para processar novo comando.")
            parar_fala()
            time.sleep(0.1)
        if not ativada and any(x in frase for x in ["lisa", "lissa", "ativar", "ativa"]):
            ativada = True
            asyncio.run_coroutine_threadsafe(falar("Pois não?"), loop_principal)
        elif ativada:
            asyncio.run_coroutine_threadsafe(processar_comando(frase), loop_principal)
    except sr.UnknownValueError:
        pass
    except Exception as e:
        print(f"🤯 Erro inesperado no callback: {e}")


async def main():
    global loop_principal
    loop_principal = asyncio.get_event_loop()
    if not mic: print("❌ Microfone não encontrado."); return
    recognizer.listen_in_background(mic, callback_escuta, phrase_time_limit=5)
    print("👋 Olá, eu sou a LISA. Diga 'LISA' para me ativar.")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma encerrado.")