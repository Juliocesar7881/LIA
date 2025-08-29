# debug_geometria.py

import tkinter as tk
from tkinter import font

# Tenta importar as bibliotecas de diagnóstico
try:
    import win32api
    import win32con

    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

try:
    from screeninfo import get_monitors

    SCREENINFO_AVAILABLE = True
except ImportError:
    SCREENINFO_AVAILABLE = False

try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class AppDiagnostico(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ferramenta de Diagnóstico de Geometria")
        self.geometry("700x500")

        # Define uma fonte monoespaçada para melhor alinhamento
        self.mono_font = font.Font(family="Consolas", size=10)

        # Frame para o texto
        text_frame = tk.Frame(self, padx=10, pady=10)
        text_frame.pack(fill="both", expand=True)

        self.info_label = tk.Label(
            text_frame,
            text="Coletando dados...",
            font=self.mono_font,
            justify="left",
            anchor="nw"
        )
        self.info_label.pack(fill="both", expand=True)

        # Botão para atualizar
        update_button = tk.Button(self, text="Atualizar Dados", command=self.coletar_e_exibir_dados)
        update_button.pack(pady=10)

        self.coletar_e_exibir_dados()
        self.centralizar_janela()

    def coletar_e_exibir_dados(self):
        """Coleta dados de todas as fontes e atualiza o label."""
        info_text = "--- DADOS DE DIAGNÓSTICO DE TELA ---\n\n"

        # --- 1. DADOS DO TKINTER ---
        info_text += "[ DADOS DO TKINTER (Biblioteca Gráfica Padrão) ]\n"
        try:
            self.update_idletasks()
            info_text += f"  - Resolução da Tela (winfo_screen): {self.winfo_screenwidth()}x{self.winfo_screenheight()}\n"
            info_text += f"  - Tamanho da Janela (winfo):         {self.winfo_width()}x{self.winfo_height()}\n"
            info_text += f"  - Posição da Janela (winfo):          ({self.winfo_x()}, {self.winfo_y()})\n"
        except Exception as e:
            info_text += f"  - Erro ao obter dados do Tkinter: {e}\n"
        info_text += "\n"

        # --- 2. DADOS DO PYWIN32 (API do Windows) ---
        info_text += "[ DADOS DO PYWIN32 (API Direta do Windows) ]\n"
        if PYWIN32_AVAILABLE:
            try:
                monitor_info = win32api.GetMonitorInfo(
                    win32api.MonitorFromPoint((0, 0), win32con.MONITOR_DEFAULTTOPRIMARY))
                work_area = monitor_info['Work']
                full_area = monitor_info['Monitor']
                info_text += f"  - Área de Trabalho do Monitor Primário (Work): {work_area}\n"
                info_text += f"  - Área Total do Monitor Primário (Monitor):   {full_area}\n"
            except Exception as e:
                info_text += f"  - Erro ao obter dados do PyWin32: {e}\n"
        else:
            info_text += "  - Biblioteca 'pywin32' não instalada.\n"
        info_text += "\n"

        # --- 3. DADOS DO SCREENINFO ---
        info_text += "[ DADOS DO SCREENINFO (Biblioteca de Monitores) ]\n"
        if SCREENINFO_AVAILABLE:
            try:
                monitors = get_monitors()
                if not monitors:
                    info_text += "  - Nenhum monitor detectado.\n"
                for i, m in enumerate(monitors):
                    info_text += f"  - Monitor {i}: {m.width}x{m.height} na posição ({m.x}, {m.y}) {'(Primário)' if m.is_primary else ''}\n"
            except Exception as e:
                info_text += f"  - Erro ao obter dados do Screeninfo: {e}\n"
        else:
            info_text += "  - Biblioteca 'screeninfo' não instalada.\n"
        info_text += "\n"

        # --- 4. DADOS DO PYAUTOGUI (Cursor do Mouse) ---
        info_text += "[ DADOS DO PYAUTOGUI (Cursor) ]\n"
        if PYAUTOGUI_AVAILABLE:
            try:
                posicao_mouse = pyautogui.position()
                info_text += f"  - Posição atual do mouse: {posicao_mouse}\n"
            except Exception as e:
                info_text += f"  - Erro ao obter dados do PyAutoGUI: {e}\n"
        else:
            info_text += "  - Biblioteca 'pyautogui' não instalada.\n"

        self.info_label.config(text=info_text)

    def centralizar_janela(self):
        """Tenta centralizar a janela usando o método padrão para referência."""
        try:
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass  # A centralização é secundária aqui.


if __name__ == "__main__":
    app = AppDiagnostico()
    app.mainloop()