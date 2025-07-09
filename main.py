# main.py (Versão Final de Produção - Limpa e Estável)

import asyncio
import speech_recognition as sr

# Importando todas as nossas ferramentas
from voice_control import falar, parar_fala, recognizer, mic
from screen_control import (
    executar_acao_na_tela,
    digitar_texto,
    apertar_tecla,
    rolar_tela,
    copiar_arquivo_selecionado,
    copiar_caminho_selecionado,
    colar
)
from transcriber import transcrever_audio_copiado
from utils.vision import clicar_em_palavra
from gpt_bridge import perguntar_ao_gpt
from memory import registrar_evento
from code_writer import gerar_codigo
from whatsapp_bot import enviar_mensagem_por_voz

# --- Variáveis Globais ---
ativada = False
loop_principal = None


async def processar_comando(comando):
    """
    Processa o comando do usuário com uma lógica de if/elif simples, direta e robusta,
    incluindo todas as funcionalidades implementadas.
    """
    global ativada
    comando = comando.strip().lower()

    # --- Comandos de Prioridade Máxima (Silêncio e Desligar) ---
    palavras_de_silencio = ["cala a boca", "cala", "cale", "calada", "cale-se", "quieta", "quieto", "fique quieta",
                            "fique quieto", "silencio", "silêncio", "faça silêncio", "xiu", "shh", "parar", "pare",
                            "para", "chega", "basta", "já deu", "pode parar", "pause", "pausa"]
    if any(palavra in comando for palavra in palavras_de_silencio):
        registrar_evento(f"Comando de silêncio: {comando}")
        return

    palavras_de_desligar = ["desliga", "desligar", "dormir", "fim"]
    if comando in palavras_de_desligar:
        ativada = False
        await falar("Ok, estarei aqui se precisar.")
        registrar_evento("Comando de desligar.")
        return

    # --- Sequência Lógica de Comandos Estruturados ---

    # 1. Comando de CLIQUE
    gatilhos_clique = ["clicar em", "clica em", "clique em", "clicar no", "clica no", "clicar na", "clica na", "clicar",
                       "clica", "clique"]
    for gatilho in gatilhos_clique:
        if comando.startswith(gatilho):
            palavra_alvo = comando[len(gatilho):].strip()
            if not palavra_alvo:
                await falar("Comando de clique incompleto. Por favor, diga no que devo clicar.")
            else:
                sucesso, score, texto_clicado = clicar_em_palavra(palavra_alvo)
                if sucesso and score < 0.7:
                    await falar(f"Não tenho certeza, mas cliquei no item mais parecido: {texto_clicado}.")
                elif not sucesso:
                    await falar(f"Não encontrei '{palavra_alvo}' na tela para clicar.")
            registrar_evento(f"Comando de clique: {comando}")
            return

    # 2. Comando de ABRIR
    gatilhos_abrir = ["abrir", "abra", "abre"]
    for gatilho in gatilhos_abrir:
        if comando.startswith(gatilho):
            argumento = comando[len(gatilho):].strip()
            # Passa apenas o nome do app para a função
            executar_acao_na_tela(argumento)
            registrar_evento(f"Comando de abrir: {comando}")
            return

    # 3. Comandos de Cópia/Cola (sem argumento)
    if comando == "copiar arquivo":
        if copiar_arquivo_selecionado():
            await falar("Arquivo copiado.")
        else:
            await falar("Erro ao copiar o arquivo.")
        registrar_evento("Comando: copiar arquivo")
        return

    elif comando == "copiar caminho":
        if copiar_caminho_selecionado():
            await falar("Caminho copiado.")
        else:
            await falar("Erro ao copiar o caminho.")
        registrar_evento("Comando: copiar caminho")
        return

    elif comando == "colar" or comando == "cola":
        if colar():
            await falar("Colei.")
        else:
            await falar("Erro ao colar.")
        registrar_evento("Comando: colar")
        return

    # 4. Comando de Transcrição
    elif comando == "transcrever áudio copiado":
        await falar("Ok, iniciando a transcrição. Isso pode levar um momento...")
        resposta = transcrever_audio_copiado()
        await falar(resposta)
        registrar_evento("Comando: transcrever")
        return

    # 5. Comando de Digitar
    elif comando.startswith("digitar"):
        texto_para_digitar = comando.replace("digitar", "", 1).strip()
        if texto_para_digitar:
            digitar_texto(texto_para_digitar)
            registrar_evento(f"Comando de digitar: {comando}")
        else:
            await falar("Comando de digitar incompleto. Diga 'digitar' seguido do texto.")
        return

    # 6. Comando de Apertar Tecla
    elif comando.startswith(("apertar", "aperte", "pressione")):
        try:
            tecla_para_apertar = comando.split(" ", 1)[1]
            apertar_tecla(tecla_para_apertar)
            registrar_evento(f"Comando de apertar: {comando}")
        except IndexError:
            await falar("Comando de apertar incompleto.")
        return

    # 7. Comando de Rolar
    elif any(gatilho in comando for gatilho in ["rolar", "rola", "descer", "sobe", "subir"]):
        if "cima" in comando or "subir" in comando or "sobe" in comando:
            rolar_tela("cima")
        else:
            rolar_tela("baixo")
        registrar_evento(f"Comando de rolar: {comando}")
        return

    # Se nada acima funcionou, vai para o GPT
    await falar(f"Não reconheci o comando '{comando}'. Vou perguntar ao GPT...")
    resposta = perguntar_ao_gpt(comando)
    await falar(resposta)
    registrar_evento(f"Comando para GPT: {comando}")


def callback_escuta(recognizer, audio):
    global ativada, loop_principal
    try:
        frase = recognizer.recognize_google(audio, language='pt-BR').lower()
        print(f"🗣️ Você disse: {frase}")
        if not ativada and any(x in frase for x in ["lisa", "lissa", "lista", "ligar", "ativar"]):
            parar_fala()
            ativada = True
            registrar_evento("LISA ativada")
            asyncio.run_coroutine_threadsafe(falar("Pois não, mestre?"), loop_principal)
        elif ativada:
            parar_fala()
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
    if not mic:
        print("❌ Programa encerrado por falta de microfone.")
        return
    stop_listening = recognizer.listen_in_background(mic, callback_escuta, phrase_time_limit=5)
    print("👋 Olá, eu sou a LISA. Diga 'LISA' para me ativar.")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")