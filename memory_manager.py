# memory_manager.py

import sqlite3
import os
from datetime import datetime

# A importação do gpt_bridge foi movida para as funções para evitar importação circular

DB_FILE = "lisa_memory.db"


def init_database():
    """Cria ou atualiza o banco de dados com as tabelas necessárias."""
    print("🧠 Verificando a estrutura do banco de dados de memória...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Cria a tabela de memórias de curto prazo, se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        consolidada INTEGER DEFAULT 0
    )
    ''')

    # Cria a tabela de fatos de longo prazo, se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fatos_permanentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fato TEXT NOT NULL UNIQUE,
        timestamp_aprendido TEXT NOT NULL
    )
    ''')

    # Verifica e adiciona a coluna 'consolidada' se ela não existir (para atualizações)
    try:
        cursor.execute("SELECT consolidada FROM memories LIMIT 1")
    except sqlite3.OperationalError:
        print("   -> Atualizando tabela 'memories' para Fase 3...")
        cursor.execute("ALTER TABLE memories ADD COLUMN consolidada INTEGER DEFAULT 0")

    conn.commit()
    conn.close()
    print("✅ Banco de dados pronto para a Fase 3.")


def adicionar_memoria(tipo: str, conteudo: str):
    """Adiciona um novo registro de memória ao banco de dados."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO memories (timestamp, type, content) VALUES (?, ?, ?)",
                       (timestamp, tipo, conteudo))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao adicionar memória: {e}")


def buscar_memorias_recentes(limit: int = 50):
    """Busca as 'limit' memórias mais recentes."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT type, content FROM memories ORDER BY id DESC LIMIT ?", (limit,))

        memorias = cursor.fetchall()
        conn.close()

        return memorias
    except Exception as e:
        print(f"❌ Erro ao buscar memórias: {e}")
        return []


async def consolidar_memorias():
    """
    Busca memórias não consolidadas, extrai fatos permanentes com a IA,
    salva na memória de longo prazo e marca as memórias como consolidadas.
    """
    from gpt_bridge import extrair_fatos_da_memoria  # Importação local para evitar ciclo

    print("🧠 Verificando se há memórias para consolidar...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, type, content FROM memories WHERE consolidada = 0")
    memorias_nao_consolidadas = cursor.fetchall()

    if len(memorias_nao_consolidadas) < 20:  # Só roda se tiver um número mínimo de novas memórias
        print("   -> Poucas memórias novas para consolidar. Aguardando mais interações.")
        conn.close()
        return

    print(f"   -> Encontradas {len(memorias_nao_consolidadas)} memórias para processar. Enviando para a IA...")
    texto_para_analise = "\n".join(
        [f"- Tipo: {tipo}, Conteúdo: {conteudo}" for id, tipo, conteudo in memorias_nao_consolidadas])

    fatos_extraidos = await extrair_fatos_da_memoria(texto_para_analise)

    if fatos_extraidos:
        timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for fato in fatos_extraidos:
            # A cláusula 'OR IGNORE' impede a inserção de fatos duplicados
            cursor.execute("INSERT OR IGNORE INTO fatos_permanentes (fato, timestamp_aprendido) VALUES (?, ?)",
                           (fato, timestamp_atual))
        print(f"✅ Fatos de longo prazo aprendidos e salvos: {fatos_extraidos}")

    # Marca as memórias processadas como consolidadas
    ids_processados = [memoria[0] for memoria in memorias_nao_consolidadas]
    cursor.executemany("UPDATE memories SET consolidada = 1 WHERE id = ?", [(id,) for id in ids_processados])

    conn.commit()
    conn.close()


async def gerar_resumo_da_memoria():
    """Busca memórias recentes E fatos de longo prazo para criar o contexto."""
    from gpt_bridge import summarize_memories_with_gpt  # Importação local

    print("🧠 Resumindo memórias recentes e fatos para construir contexto...")
    memorias_recentes = buscar_memorias_recentes(limit=50)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT fato FROM fatos_permanentes ORDER BY id DESC")
    fatos = cursor.fetchall()
    conn.close()

    contexto = ""
    if fatos:
        texto_fatos = " ".join([f[0] for f in fatos])
        contexto += f"Fatos de longo prazo sobre o usuário: {texto_fatos}. "

    if memorias_recentes:
        texto_formatado = "\n".join(
            [f"- Tipo: {tipo}, Conteúdo: {conteudo}" for tipo, conteudo in reversed(memorias_recentes)])
        resumo_recente = await summarize_memories_with_gpt(texto_formatado)
        if resumo_recente:
            contexto += f"Resumo das interações recentes: {resumo_recente}"

    if contexto:
        print(f"✅ Contexto da memória gerado: {contexto[:150]}...")
    else:
        print("   -> Nenhuma memória encontrada para resumir.")

    return contexto.strip()


def limpar_memorias_antigas(limite_maximo=30000, manter_recente=10000):
    """Verifica o total de memórias e apaga as mais antigas se o limite for atingido."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) FROM memories")
        total_registros = cursor.fetchone()[0]

        if total_registros > limite_maximo:
            print(f"🧠 Memória de curto prazo atingiu {total_registros} registros. Iniciando limpeza...")
            cursor.execute("SELECT id FROM memories ORDER BY id DESC LIMIT 1 OFFSET ?", (manter_recente - 1,))
            resultado = cursor.fetchone()
            if resultado:
                id_limite = resultado[0]
                cursor.execute("DELETE FROM memories WHERE id < ?", (id_limite,))
                conn.commit()
                registros_apagados = total_registros - manter_recente
                print(f"✅ Limpeza concluída. {registros_apagados} memórias antigas foram apagadas.")
        conn.close()
    except Exception as e:
        print(f"❌ Erro durante a limpeza da memória: {e}")