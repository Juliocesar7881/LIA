import pyautogui
import time
import webbrowser

def enviar_mensagem_por_voz(comando):
    try:
        # comando esperado: "enviar mensagem para João bom dia"
        sem_prefixo = comando.replace("enviar mensagem para", "").strip()
        partes = sem_prefixo.split(" ", 1)

        if len(partes) < 2:
            print("❌ Nome ou mensagem incompletos.")
            return

        nome, mensagem = partes[0], partes[1]

        print(f"📨 Enviando mensagem para {nome}: {mensagem}")
        webbrowser.open("https://web.whatsapp.com")
        time.sleep(10)

        pyautogui.hotkey('ctrl', 'f')
        pyautogui.write(nome)
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(1)

        pyautogui.write(mensagem)
        pyautogui.press("enter")

        print("✅ Mensagem enviada com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro ao enviar mensagem: {e}")
