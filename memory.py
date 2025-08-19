from datetime import datetime

def registrar_evento(texto):
    with open("lisa_logs.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {texto}\n")