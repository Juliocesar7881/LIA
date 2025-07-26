# gerar_audios_cache.py (versão com áudio de transcrição)

import asyncio
import edge_tts
import os

# Dicionário com os nomes dos arquivos e os textos correspondentes
respostas_para_cache = {
    "Sim": "Sim.",
    "Claro": "Claro.",
    "Beleza": "Beleza.",
    "Feito": "Feito.",
    "Ok": "Ok!",
    "Fechado": "Fechado.",
    "OkTransscrito": "Ok, transcrito para sua area de transferencia."
}
pasta_cache = "audio_cache"

if not os.path.exists(pasta_cache):
    os.makedirs(pasta_cache)
    print(f"Pasta '{pasta_cache}' criada com sucesso.")


async def gerar_arquivo(texto, caminho):
    """Gera um único arquivo de áudio."""
    try:
        comunicador = edge_tts.Communicate(texto, "pt-BR-ThalitaMultilingualNeural")
        await comunicador.save(caminho)
        print(f"✅ Áudio para '{texto}' salvo como '{caminho}'")
    except Exception as e:
        print(f"❌ Erro ao gerar áudio para '{texto}': {e}")


async def main():
    """Função principal para gerar todos os áudios."""
    tarefas = []
    for nome_arquivo, texto in respostas_para_cache.items():
        caminho_arquivo = os.path.join(pasta_cache, nome_arquivo + ".mp3")
        tarefas.append(gerar_arquivo(texto, caminho_arquivo))

    await asyncio.gather(*tarefas)


if __name__ == "__main__":
    print("Iniciando a geração de cache de áudio...")
    asyncio.run(main())
    print("\nProcesso concluído!")
