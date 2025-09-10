# config_manager.py
import json
import os

CONFIG_FILE = "config.json"

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                config_data = json.load(f)
                # Lógica para garantir compatibilidade com versões antigas do config.json
                if "nome_usuario" in config_data:
                    config_data["user_name"] = config_data.pop("nome_usuario")
                if "humor_lia" in config_data:
                    config_data["lia_personality"] = config_data.pop("humor_lia")
                if "cidade" in config_data:
                    config_data["cidade_padrao"] = config_data.pop("cidade")
                # Adiciona o valor padrão para a nova configuração, se ela não existir
                if "iniciar_com_windows" not in config_data:
                    config_data["iniciar_com_windows"] = False
                return config_data
            except json.JSONDecodeError:
                os.remove(CONFIG_FILE)
                return None
    return None

def salvar_config(nome_usuario, humor_lia, cidade, iniciar_com_windows):
    # Adicionada a nova chave "iniciar_com_windows"
    config_data = {
        "user_name": nome_usuario,
        "lia_personality": humor_lia,
        "cidade_padrao": cidade,
        "iniciar_com_windows": iniciar_com_windows
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Configurações salvas para o usuário '{nome_usuario}'!")