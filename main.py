# main.py (Com máxima flexibilidade de comandos)

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
    tirar_print
)
from utils.tools import encontrar_e_abrir_pasta
from transcriber import transcrever_audio_copiado
from utils.vision import clicar_em_palavra
from gpt_bridge import perguntar_ao_gpt
from memory import registrar_evento

# --- Configurações e Funções Auxiliares (sem alterações) ---
ativada = False
loop_principal = None
CONFIRMACOES_GERAIS = ["Ok.mp3", "Feito.mp3", "Sim.mp3", "Claro.mp3", "Beleza.mp3"]
CONFIRMACOES_ACAO = ["Ok.mp3", "Fechado.mp3"]


def extrair_tempo_duracao_em_segundos(comando):
    unidades = {'segundo': 1, 'minuto': 60, 'hora': 3600, 'dia': 86400}
    match = re.search(r'(\d+)\s+(segundo|segundos|minuto|minutos|hora|horas|dia|dias)', comando, re.IGNORECASE)
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


# --- Processador de Comandos (COM MÁXIMA FLEXIBILIDADE) ---
async def processar_comando(comando):
    global ativada;
    comando = comando.strip().lower()

    palavras_de_interrupcao = [
        "cala a boca", "cala", "cale", "calada", "cale-se", "quieta", "quieto",
        "fique quieta", "fique quieto", "silencio", "silêncio", "faça silêncio",
        "xiu", "shh", "parar", "pare", "chega", "basta", "já deu", "pode parar", "pause", "pausa"
    ]
    if any(palavra in comando for palavra in palavras_de_interrupcao):
        registrar_evento("Comando de silêncio.");
        return
    if comando in ["desliga", "dormir", "fim"]:
        ativada = False;
        await falar("Até mais.");
        registrar_evento("Assistente desativada.");
        return

    # --- Comandos com Variações Expandidas ---

    # Desligar PC
    gatilhos_desligar = ["desligar pc", "desligar o computador", "desligar máquina", "desligue o pc",
                         "desligue o computador", "encerrar o sistema", "encerrar", "shutdown"]
    if any(gatilho in comando for gatilho in gatilhos_desligar) and "programar" not in comando:
        await falar("Desligando.");
        os.system("shutdown -s -t 1");
        return

    # Reiniciar PC
    gatilhos_reiniciar = ["reiniciar pc", "reiniciar o computador", "reiniciar máquina", "reinicie o pc",
                          "reinicie o computador", "reboot", "recomeçar"]
    if any(gatilho in comando for gatilho in gatilhos_reiniciar) and "programar" not in comando:
        await falar("Reiniciando.");
        os.system("shutdown -r -t 1");
        return

    # Programar Desligamento/Reinício (já é flexível pela extração de tempo)
    tempo_especifico = extrair_tempo_especifico_em_segundos(comando)
    tempo_duracao = extrair_tempo_duracao_em_segundos(comando)
    if tempo_especifico or tempo_duracao:
        tempo_total = tempo_especifico or tempo_duracao
        if "reiniciar" in comando:
            os.system(f"shutdown -r -t {tempo_total}");
            await falar("Ok, reinicialização agendada.");
            return
        elif "desligar" in comando:
            os.system(f"shutdown -s -t {tempo_total}");
            await falar("Ok, desligamento agendado.");
            return

    # Cancelar Agendamento
    gatilhos_cancelar = ["cancelar desligamento", "cancelar o desligamento", "cancelar reinicialização",
                         "cancelar agendamento", "não desligar mais", "parar desligamento", "não quero mais desligar"]
    if any(gatilho in comando for gatilho in gatilhos_cancelar):
        await cancelar_desligamento();
        return

    # Tirar Print
    gatilhos_print = ["tirar print", "tira print", "printar a tela", "printa a tela", "print", "capturar tela",
                      "captura de tela", "faz um print", "bater um print", "fotografar a tela"]
    if any(gatilho in comando for gatilho in gatilhos_print):
        if tirar_print(): falar_rapido("Feito.mp3"); return

    # Transcrição (já era flexível)
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

    # Comandos que iniciam com gatilhos
    gatilhos_fechar = ["fechar", "fecha", "feche","mate","mata"]
    for gatilho in gatilhos_fechar:
        if comando.startswith(gatilho):
            alvo = comando.replace(gatilho, "", 1).strip();
            if alvo and fechar_janela_por_nome(alvo)[0]:
                falar_rapido(random.choice(CONFIRMACOES_ACAO))
            else:
                await falar("Não encontrei."); return

    gatilhos_abrir_pasta = ["abrir pasta", "abre a pasta", "abra a pasta", "procurar a pasta","busque a pasta","procure pasta","busque pasta","ir para pasta", "vai pra pasta", "procurar pasta","buscar pasta"]
    for gatilho in gatilhos_abrir_pasta:
        if comando.startswith(gatilho):
            alvo = comando.replace(gatilho, "", 1).strip();
            if alvo and encontrar_e_abrir_pasta(alvo):
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar("Não encontrei."); return

    # Comandos exatos ou contidos na frase
    if any(palavra in comando for palavra in ["desfazer", "desfaz", "desfaça", "ctrl z", "voltar", "voltar uma vez","volta uma vez","volta uma ação"]):
        apertar_tecla('ctrl+z');
        falar_rapido(random.choice(CONFIRMACOES_GERAIS));
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

    # Comandos mais complexos que precisam de um argumento
    gatilhos_clique = ["clicar em", "clica em", "clique em", "clicar no", "clica no", "clicar na", "clica na", "clicar",
                       "clica", "clique"]
    for gatilho in gatilhos_clique:
        if comando.startswith(gatilho):
            palavra_alvo = comando[len(gatilho):].strip();
            if palavra_alvo and clicar_em_palavra(palavra_alvo)[0]:
                pass
            else:
                await falar("Não vi."); return

    gatilhos_abrir = ["abrir", "abra", "abre", "executar","executa", "execute", "iniciar", "inicia", "rodar", "rode","roda"]
    for gatilho in gatilhos_abrir:
        if comando.startswith(gatilho):
            argumento = comando[len(gatilho):].strip();
            if argumento and executar_acao_na_tela(argumento):
                falar_rapido(random.choice(CONFIRMACOES_GERAIS))
            else:
                await falar("Não achei."); return

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

    # Rolar tela (MUITO AMPLIADO)
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
        if not ativada and any(x in frase for x in ["lisa", "lissa", "ativar"]):
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