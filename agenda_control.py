# agenda_control.py (Versão Final com Agendador de Tarefas do Windows)

import os
import re
import sys
import base64
from datetime import datetime


def _limpar_titulo_para_nome_tarefa(titulo: str) -> str:
    """Cria um nome de tarefa válido para o Windows a partir de um título."""
    titulo_limpo = re.sub(r'[\\/*?:"<>|]', "", titulo)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"LISA_Alarme_{titulo_limpo[:30].strip()}_{timestamp}"


def criar_alarme(titulo: str, data_hora: datetime) -> str:
    """
    Cria um ficheiro .bat e uma tarefa no Agendador de Tarefas para executar o alarme.
    """
    try:
        nome_tarefa = _limpar_titulo_para_nome_tarefa(titulo)
        data_formatada = data_hora.strftime('%d/%m/%Y')
        hora_formatada = data_hora.strftime('%H:%M')

        python_exe = sys.executable
        script_alarme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarme_player.py")

        # --- LÓGICA DO FICHEIRO .BAT ---
        caminho_bat = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{nome_tarefa}.bat")
        comando_para_bat = f'@echo off\n"{python_exe}" "{script_alarme_path}" "{titulo}"'

        with open(caminho_bat, "w", encoding="utf-8") as f:
            f.write(comando_para_bat)
        # --- FIM DA LÓGICA DO FICHEIRO .BAT ---

        comando_schtasks = (
            f'schtasks /create /tn "{nome_tarefa}" /tr "{caminho_bat}" '
            f'/sc once /sd {data_formatada} /st {hora_formatada} /f'
        )

        print(f"Executando comando: {comando_schtasks}")
        resultado_os = os.system(comando_schtasks)
        if resultado_os != 0:
            os.remove(caminho_bat)  # Remove o .bat se a criação da tarefa falhar
            raise OSError(f"O comando schtasks falhou com o código de saída {resultado_os}")

        return f"Ok, alarme definido para '{titulo}'."

    except Exception as e:
        print(f"Ocorreu um erro ao criar alarme: {e}")
        return "Desculpe, não consegui definir o alarme."


def listar_alarmes() -> list:
    """
    Lista as tarefas de alarme agendadas pela LISA.
    Retorna uma lista de dicionários, cada um com o título e o nome completo da tarefa.
    """
    try:
        # Usa /fo csv /v /nh para obter uma saída detalhada, sem cabeçalho e em formato CSV
        comando = 'schtasks /query /fo csv /v /nh | findstr "LISA_Alarme_"'
        resultado = os.popen(comando).read()

        if not resultado:
            return []

        tarefas = []
        for linha in resultado.strip().split('\n'):
            try:
                partes = linha.split('","')
                nome_tarefa_completo = partes[1].strip('"').lstrip('\\')
                proxima_execucao_str = partes[2].strip('"')

                match = re.search(r'LISA_Alarme_(.*)_\d{14}', nome_tarefa_completo)
                titulo = match.group(1) if match else "Alarme sem título"

                data_valida = None
                formatos_possiveis = ['%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S']
                for fmt in formatos_possiveis:
                    try:
                        data_valida = datetime.strptime(proxima_execucao_str, fmt)
                        break
                    except ValueError:
                        continue

                if data_valida:
                    tarefas.append({
                        "titulo": titulo,
                        "data": data_valida,
                        "nome_completo": nome_tarefa_completo
                    })
            except Exception as e:
                print(f"Aviso: Não foi possível analisar a linha da tarefa: {linha}. Erro: {e}")
                continue

        return sorted(tarefas, key=lambda x: x["data"])

    except Exception as e:
        print(f"Ocorreu um erro ao listar alarmes: {e}")
        return []


def remover_alarme(nome_tarefa: str) -> bool:
    """
    Remove uma tarefa agendada e o seu ficheiro .bat associado.
    """
    try:
        # 1. Remove a tarefa agendada
        comando_delete = f'schtasks /delete /tn "{nome_tarefa}" /f'
        print(f"Executando comando: {comando_delete}")
        resultado_delete = os.popen(comando_delete).read()

        # 2. Remove o ficheiro .bat correspondente
        caminho_bat = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{nome_tarefa}.bat")
        if os.path.exists(caminho_bat):
            os.remove(caminho_bat)
            print(f"Ficheiro de atalho removido: {caminho_bat}")

        return "sucesso" in resultado_delete.lower() or "success" in resultado_delete.lower()
    except Exception as e:
        print(f"Ocorreu um erro ao remover alarme: {e}")
        return False