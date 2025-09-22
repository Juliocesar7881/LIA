# smart_device_control.py (versão corrigida)
import tinytuya
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

API_REGION = "us"
API_KEY = os.getenv("TUYA_API_KEY")
API_SECRET = os.getenv("TUYA_API_SECRET")

print("--- Módulo de Controle de Dispositivos Tuya Carregado ---")

try:
    cloud = tinytuya.Cloud(
        apiRegion=API_REGION,
        apiKey=API_KEY,
        apiSecret=API_SECRET
    )
    print("✅ Conexão com a nuvem Tuya estabelecida com sucesso.")
except Exception as e:
    cloud = None
    print(f"❌ ERRO FATAL ao conectar na nuvem Tuya. Erro: {e}")


def encontrar_e_controlar(nome_dispositivo, comando):
    if not cloud:
        return "Desculpe, a conexão com o sistema de dispositivos falhou na inicialização."

    comando_limpo = comando.lower().strip()
    print(f"DEBUG: Comando recebido pela função: '{comando_limpo}'")

    if comando_limpo not in ["ligar", "desligar", "status"]:
        return f"Comando '{comando_limpo}' não reconhecido. Use 'ligar', 'desligar' ou 'status'."

    try:
        print("Buscando dispositivos na sua conta...")
        devices = cloud.getdevices()

        if not isinstance(devices, list) or not devices:
            return "Nenhum dispositivo foi encontrado na sua conta."

        target_device = None
        for device in devices:
            if nome_dispositivo.lower() in device.get('name', '').lower():
                target_device = device
                break

        if not target_device:
            return f"Desculpe, não encontrei o dispositivo '{nome_dispositivo}'."

        device_id = target_device['id']
        print(f"✅ Dispositivo encontrado: '{target_device['name']}' (ID: {device_id})")

        # --- Pegando o estado atual ---
        status_data = cloud.getstatus(device_id)
        estado_atual_ligada = None

        if status_data and isinstance(status_data.get('result'), list):
            for item in status_data['result']:
                if item.get('code') == 'switch_1':
                    estado_atual_ligada = item.get('value')
                    break

        if estado_atual_ligada is None:
            return f"Não consegui interpretar o status da {nome_dispositivo}."

        print(f"Status atual: {'Ligada' if estado_atual_ligada else 'Desligada'}")

        # --- Se for apenas status ---
        if comando_limpo == "status":
            return f"A {nome_dispositivo} está {'ligada' if estado_atual_ligada else 'desligada'}."

        # --- Lógica correta de ligar/desligar ---
        if comando_limpo == "ligar":
            if estado_atual_ligada:
                return f"A {nome_dispositivo} já está ligada."
            valor = True
            acao_realizada = "ligada"

        elif comando_limpo == "desligar":
            if not estado_atual_ligada:
                return f"A {nome_dispositivo} já está desligada."
            valor = False
            acao_realizada = "desligada"

        print(f"Enviando comando para {acao_realizada.upper()} o ID: {device_id}")
        commands = {'commands': [{'code': 'switch_1', 'value': valor}]}
        result = cloud.sendcommand(device_id, commands)

        print(f"Resposta do comando: {result}")
        if result and result.get('success'):
            return f"Ok, a {nome_dispositivo} foi {acao_realizada}."
        else:
            return f"Houve uma falha ao tentar controlar a {nome_dispositivo}."

    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        traceback.print_exc()
        return "Ocorreu um erro inesperado ao me comunicar com o dispositivo."
