# smart_device_control.py

import os
from dotenv import load_dotenv
from tuya_connector import TuyaOpenAPI

# Carrega as variáveis do arquivo .env
load_dotenv()

# Pega as credenciais do ambiente
ACCESS_ID = os.getenv("TUYA_API_KEY")
ACCESS_SECRET = os.getenv("TUYA_API_SECRET")
API_ENDPOINT = "https://openapi.tuyaus.com"

# Verifica se as credenciais foram carregadas
if not ACCESS_ID or not ACCESS_SECRET:
    raise ValueError("Credenciais TUYA_API_KEY e TUYA_API_SECRET não encontradas no arquivo .env")

# Inicializa a conexão com a API
openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
openapi.connect()


def encontrar_id_dispositivo(nome_dispositivo="tomada"):
    """
    Busca na nuvem da Tuya por um dispositivo que contenha o nome fornecido.
    Retorna o ID do primeiro dispositivo encontrado.
    """
    try:
        # Pega a lista de todos os dispositivos vinculados à sua conta
        response = openapi.get("/v1.0/devices")

        if not response.get('success'):
            print(f"❌ Erro ao listar dispositivos: {response.get('msg')}")
            return None

        dispositivos = response['result']

        # Procura pelo dispositivo que contenha o nome (ex: "tomada")
        for dispositivo in dispositivos:
            if nome_dispositivo.lower() in dispositivo.get('name', '').lower():
                device_id = dispositivo['id']
                print(f"✅ Dispositivo encontrado: '{dispositivo['name']}' (ID: {device_id})")
                return device_id

        print(f"❌ Nenhum dispositivo com o nome '{nome_dispositivo}' foi encontrado.")
        return None

    except Exception as e:
        print(f"🤯 Erro ao tentar encontrar o ID do dispositivo: {e}")
        return None


def controlar_tomada(device_id, ligar: bool):
    """
    Envia um comando para ligar ou desligar um dispositivo específico.

    Args:
        device_id (str): O ID do dispositivo a ser controlado.
        ligar (bool): True para ligar, False para desligar.
    """
    if not device_id:
        return False

    try:
        commands = {'commands': [{'code': 'switch_1', 'value': ligar}]}
        response = openapi.post(f'/v1.0/devices/{device_id}/commands', commands)

        if response.get('success', False):
            acao = "ligada" if ligar else "desligada"
            print(f"✅ Tomada {acao} com sucesso!")
            return True
        else:
            print(f"❌ Falha ao enviar comando para o dispositivo {device_id}. Resposta: {response}")
            return False

    except Exception as e:
        print(f"🤯 Erro ao controlar a tomada com ID {device_id}: {e}")
        return False