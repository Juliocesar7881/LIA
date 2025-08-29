# config_manager.py
import json
import os

CONFIG_FILE = "config.json"

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                os.remove(CONFIG_FILE)
                return None
    return None

def salvar_config(nome_usuario, humor_lisa):
    config_data = {
        "nome_usuario": nome_usuario,
        "humor_lisa": humor_lisa
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
    print(f"✅ Configurações salvas para o usuário '{nome_usuario}'!")