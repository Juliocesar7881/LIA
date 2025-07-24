# main.py (Versão Final Corrigida e Estável)

import asyncio
import speech_recognition as sr
import random

from voice_control import falar, parar_fala, recognizer, mic, falar_rapido
from screen_control import (
    executar_acao_na_tela,
    digitar_texto,
    apertar_tecla,
    rolar_tela,
    copiar_arquivo_selecionado,
    copiar_caminho_selecionado,
    colar,
    fechar_janela_por_nome,
    tirar_print
)
from utils.tools import encontrar_e_abrir_pasta
from transcriber import transcrever_audio_copiado
from utils.vision import clicar_em_palavra
from gpt_bridge import perguntar_ao_gpt
from memory import registrar_evento
from code_writer import gerar_codigo
from whatsapp_bot import enviar_mensagem_por_voz

ativada = False
loop_principal = None

CONFIRMACOES_ACAO = ["Ok.mp3", "Fechado.mp3"]
CONFIRMACOES_GERAIS = ["Sim.mp3", "Claro.mp3", "Beleza.mp3", "Feito.mp3"]


async def processar_comando(comando):
    global ativada
    comando = comando.strip().lower()

    # --- Comandos de Prioridade Máxima (Silêncio e Desligar) ---
    palavras_de_silencio = ["cala a boca", "cala", "cale", "calada", "cale-se", "quieta", "quieto", "fique quieta",
                            "fique quieto", "silencio", "silêncio", "faça silêncio", "xiu", "shh", "parar", "pare",
                            "chega", "basta", "já deu", "pode parar", "pause", "pausa"]
    if any(palavra in comando for palavra in palavras_de_silencio):
        registrar_evento(f"Comando de silêncio: {comando}");
        return

    palavras_de_desligar = ["desliga", "desligar", "dormir", "fim"]
    if comando in palavras_de_desligar:
        ativada = False;
        await falar("Ok, estarei aqui se precisar.");
        registrar_evento("Comando de desligar.");
        return

    # --- Sequência Lógica de Comandos Estruturados ---

    if comando.startswith("transcrever audio") or comando.startswith("transcrever áudio"):
        gatilho = "transcrever audio" if comando.startswith("transcrever audio") else "transcrever áudio"
        nome_arquivo = comando.replace(gatilho, "", 1).strip()

        if not nome_arquivo:
            await falar("Por favor, diga o nome do arquivo de áudio que devo transcrever.")
        else:
            await falar(f"Ok, tentando transcrever o áudio '{nome_arquivo}'.")
            sucesso_clique, _, _ = clicar_em_palavra(nome_arquivo)
            if sucesso_clique:
                if copiar_caminho_selecionado():
                    await falar("Arquivo selecionado. Iniciando a transcrição, isso pode levar um momento...")
                    resposta = transcrever_audio_copiado()
                    await falar(resposta)
                else:
                    await falar("Consegui selecionar o arquivo, mas falhei ao copiar o caminho.")
            else:
                await falar(f"Não encontrei o arquivo de áudio '{nome_arquivo}' na tela.")
        registrar_evento(f"Comando de transcrição direta: {comando}");
        return

    gatilhos_print = ["tirar print", "tira print", "printar a tela", "printa a tela", "print", "prin", "capturar tela",
                      "captura de tela", "capturar", "captura"]
    if any(gatilho in comando for gatilho in gatilhos_print):
        caminho_do_print = tirar_print()
        if caminho_do_print:
            falar_rapido("Feito.mp3")
        else:
            await falar("Ocorreu um erro ao tentar tirar o print.")
        registrar_evento("Comando de tirar print executado.");
        return

    if comando.startswith("fechar"):
        alvo = comando.replace("fechar", "", 1).strip()
        if not alvo:
            await falar("Por favor, diga o que devo fechar.")
        else:
            janela_fechada, score = fechar_janela_por_nome(alvo)
            if janela_fechada:
                falar_rapido(random.choice(CONFIRMACOES_ACAO))
            else:
                await falar(f"Não encontrei nenhuma janela aberta parecida com '{alvo}'.")
        registrar_evento(f"Comando de fechar: {comando}");
        return

    elif comando.startswith("abrir pasta"):
        alvo = comando.replace("abrir pasta", "", 1).strip()
        if not alvo:
            await falar("Por favor, diga o nome da pasta que devo abrir.")
        else:
            await falar(f"Buscando pela pasta '{alvo}', só um momento!")
            if encontrar_e_abrir_pasta(alvo):
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar(f"Não consegui encontrar uma pasta parecida com '{alvo}'.")
        registrar_evento(f"Comando de abrir pasta: {comando}");
        return

    gatilhos_clique = ["clicar em", "clica em", "clique em", "clicar no", "clica no", "clicar na", "clica na", "clicar",
                       "clica", "clique"]
    for gatilho in gatilhos_clique:
        if comando.startswith(gatilho):
            palavra_alvo = comando[len(gatilho):].strip()
            if not palavra_alvo:
                await falar("Comando de clique incompleto.")
            else:
                sucesso, score, texto_clicado = clicar_em_palavra(palavra_alvo)
                if not sucesso: await falar(f"Não encontrei '{palavra_alvo}' na tela para clicar.")
            registrar_evento(f"Comando de clique: {comando}");
            return

    gatilhos_abrir = ["abrir", "abra", "abre"]
    for gatilho in gatilhos_abrir:
        if comando.startswith(gatilho):
            argumento = comando[len(gatilho):].strip()
            if executar_acao_na_tela(argumento): falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            registrar_evento(f"Comando de abrir: {comando}");
            return

    if comando == "copiar arquivo":
        if copiar_arquivo_selecionado():
            await falar("Arquivo copiado.")
        else:
            await falar("Erro ao copiar o arquivo.")
        registrar_evento("Comando: copiar arquivo");
        return

    elif comando == "copiar caminho":
        if copiar_caminho_selecionado():
            await falar("Caminho copiado.")
        else:
            await falar("Erro ao copiar o caminho.")
        registrar_evento("Comando: copiar caminho");
        return

    elif comando == "colar" or comando == "cola":
        if colar():
            falar_rapido(random.choice(CONFIRMACOES_GERAIS))
        else:
            await falar("Erro ao colar.")
        registrar_evento("Comando: colar");
        return

    elif comando == "transcrever áudio copiado":
        await falar("Ok, iniciando a transcrição...")
        resposta = transcrever_audio_copiado()
        await falar(resposta)
        registrar_evento("Comando: transcrever");
        return

    elif comando.startswith("digitar"):
        texto_para_digitar = comando.replace("digitar", "", 1).strip()
        if texto_para_digitar:
            digitar_texto(texto_para_digitar); registrar_evento(f"Comando de digitar: {comando}")
        else:
            await falar("Comando de digitar incompleto.")
        return

    elif comando.startswith(("apertar", "aperte", "pressione")):
        try:
            tecla_para_apertar = comando.split(" ", 1)[1]
            if not apertar_tecla(tecla_para_apertar):
                await falar(f"Não reconheci a tecla '{tecla_para_apertar}'.")
            registrar_evento(f"Comando de apertar: {comando}")
        except IndexError:
            await falar("Comando de apertar incompleto.")
        return

    rolar_cima_triggers = ["rolar para cima", "cima", "acima", "rolar cima", "rolar acima", "navegar para cima",
                           "navegar cima", "para cima", "subir", "rola para cima", "rola cima", "navegar para acima",
                           "navega para cima", "navega cima", "navega acima", "navegar acima"]
    rolar_baixo_triggers = ["rolar para baixo", "baixo", "abaixo", "rolar baixo", "rolar abaixo", "navegar para baixo",
                            "navegar baixo", "para baixo", "rola para baixo", "rola baixo", "navega para baixo",
                            "navega baixo", "rola abaixo", "navegar abaixo", "navega abaixo"]
    rolar_cima_triggers = list(set(rolar_cima_triggers))
    rolar_baixo_triggers = list(set(rolar_baixo_triggers))
    if comando in rolar_cima_triggers:
        rolar_tela("cima");
        registrar_evento(f"Comando de rolar para cima: {comando}");
        return
    elif comando in rolar_baixo_triggers:
        rolar_tela("baixo");
        registrar_evento(f"Comando de rolar para baixo: {comando}");
        return

    # --- MUDANÇA AQUI: REMOVIDA A FALA INTERMEDIÁRIA ---
    resposta = perguntar_ao_gpt(comando);
    await falar(resposta)
    registrar_evento(f"Comando para GPT: {comando}")


def callback_escuta(recognizer, audio):
    global ativada, loop_principal
    try:
        frase = recognizer.recognize_google(audio, language='pt-BR').lower()
        print(f"🗣️ Você disse: {frase}")
        if not ativada and any(x in frase for x in ["lisa", "lissa", "lista", "ligar", "ativar"]):
            parar_fala();
            ativada = True;
            registrar_evento("LISA ativada")
            asyncio.run_coroutine_threadsafe(falar("Pois não, mestre?"), loop_principal)
        elif ativada:
            parar_fala();
            asyncio.run_coroutine_threadsafe(processar_comando(frase), loop_principal)
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"⚠️ Erro no serviço de reconhecimento de voz; {e}")
    except Exception as e:
        print(f"🤯 Erro inesperado no callback: {e}")


async def main():
    global loop_principal
    loop_principal = asyncio.get_event_loop()
    if not mic: print("❌ Programa encerrado por falta de microfone."); return
    stop_listening = recognizer.listen_in_background(mic, callback_escuta, phrase_time_limit=5)
    print("👋 Olá, eu sou a LISA. Diga 'LISA' para me ativar.")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
