# config_manager.py
import json
import os

CONFIG_FILE = "config.json"


def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                config_data = json.load(f)
                # --- Sua Lógica de Migração (Mantida) ---
                if "humor_lisa" in config_data and "humor_lia" not in config_data:
                    config_data["humor_lia"] = config_data.pop("humor_lisa")

                # --- Lógica de Migração para a Chave da Cidade ---
                # Garante que o programa funcione mesmo com a chave antiga
                if "cidade" in config_data and "cidade_padrao" not in config_data:
                    config_data["cidade_padrao"] = config_data.pop("cidade")

                return config_data
            except json.JSONDecodeError:
                os.remove(CONFIG_FILE)
                return None
    return None


def salvar_config(nome_usuario, humor_lia, cidade):
    config_data = {
        "nome_usuario": nome_usuario,
        "humor_lia": humor_lia,
        # --- CORREÇÃO APLICADA AQUI ---
        # A chave foi alterada para "cidade_padrao" para ser consistente com o main.py
        "cidade_padrao": cidade
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Configurações salvas para o usuário '{nome_usuario}'!")