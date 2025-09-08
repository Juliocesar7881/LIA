import tkinter as tk
from PIL import Image, ImageTk
import os
import queue
import customtkinter
import webbrowser


class StatusIndicator:
    def __init__(self, command_queue: queue.Queue):
        self.command_queue = command_queue
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")

        self._drag_start_x = 0
        self._drag_start_y = 0

        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
            self.icon_image = Image.open(icon_path).resize((64, 64), Image.Resampling.LANCZOS)
            self.icon_photo = ImageTk.PhotoImage(self.icon_image)
        except Exception as e:
            print(f"Erro ao carregar o ícone principal: {e}")
            self.root.destroy()
            return

        self.root.geometry(f"{self.icon_photo.width()}x{self.icon_photo.height()}")
        screen_width = self.root.winfo_screenwidth()
        x_pos = screen_width - self.root.winfo_width() - 122
        y_pos = 62
        self.root.geometry(f"+{x_pos}+{y_pos}")

        self.label = tk.Label(self.root, image=self.icon_photo, bg='black', borderwidth=0)
        self.label.pack()

        self.label.bind("<ButtonPress-1>", self.on_press_drag)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonPress-3>", self.toggle_menu)

        self.set_inactive()
        self.menu_window = None

    def _update_menu_position(self):
        if not (self.menu_window and self.menu_window.winfo_exists()):
            return
        self.menu_window.update_idletasks()
        menu_width = self.menu_window.winfo_reqwidth()
        menu_height = self.menu_window.winfo_reqheight()
        icon_x = self.root.winfo_x()
        icon_y = self.root.winfo_y()
        icon_width = self.root.winfo_width()
        icon_height = self.root.winfo_height()
        new_menu_x = icon_x - menu_width - 4
        new_menu_y = icon_y + icon_height + 5
        self.menu_window.geometry(f"{menu_width}x{menu_height}+{new_menu_x}+{new_menu_y}")

    def on_press_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def on_drag(self, event):
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        new_icon_x = self.root.winfo_x() + dx
        new_icon_y = self.root.winfo_y() + dy
        self.root.geometry(f"+{new_icon_x}+{new_icon_y}")
        self._update_menu_position()

    def toggle_menu(self, event=None):
        if self.menu_window and self.menu_window.winfo_exists():
            self.close_menu()
        else:
            self.show_menu()

    def show_menu(self):
        cor_transparente = "#010101"
        self.menu_window = customtkinter.CTkToplevel(self.root, fg_color=cor_transparente)
        self.menu_window.overrideredirect(True)
        self.menu_window.wm_attributes("-topmost", True)
        self.menu_window.wm_attributes("-transparentcolor", cor_transparente)

        menu_frame = customtkinter.CTkFrame(
            self.menu_window,
            corner_radius=12,
            border_width=3,
            border_color="gray30",
            fg_color="gray10"
        )
        menu_frame.pack(padx=1, pady=1)

        try:
            icon_size = (20, 20)
            assets_dir = os.path.join(os.path.dirname(__file__), "assets")
            settings_icon = customtkinter.CTkImage(Image.open(os.path.join(assets_dir, "settings_icon.png")), size=icon_size)
            manual_icon = customtkinter.CTkImage(Image.open(os.path.join(assets_dir, "manual_icon.png")), size=icon_size)
            close_icon = customtkinter.CTkImage(Image.open(os.path.join(assets_dir, "close_icon.png")), size=icon_size)
        except Exception as e:
            print(f"Erro ao carregar ícones do menu: {e}. Usando menu sem ícones.")
            settings_icon, manual_icon, close_icon = None, None, None

        title_label = customtkinter.CTkLabel(
            menu_frame, text="Menu LIA", font=customtkinter.CTkFont(family="Segoe UI", size=14, weight="bold")
        )
        title_label.pack(pady=(10, 8), padx=20)

        settings_button = customtkinter.CTkButton(
            menu_frame, text="Configurações", command=self.open_settings,
            font=customtkinter.CTkFont(family="Segoe UI", size=13), height=30,
            image=settings_icon, compound="left", anchor="w", corner_radius=8
        )
        settings_button.pack(pady=4, padx=10, fill='x')

        manual_button = customtkinter.CTkButton(
            menu_frame, text="Manual de uso", command=self.open_manual,
            font=customtkinter.CTkFont(family="Segoe UI", size=13), height=30,
            fg_color="#333333", hover_color="#444444",
            image=manual_icon, compound="left", anchor="w", corner_radius=8
        )
        manual_button.pack(pady=4, padx=10, fill='x')

        close_button = customtkinter.CTkButton(
            menu_frame, text="Fechar LIA", command=self.close_app, fg_color="#D32F2F",
            hover_color="#B71C1C", font=customtkinter.CTkFont(family="Segoe UI", size=13), height=30,
            image=close_icon, compound="left", anchor="w", corner_radius=8
        )
        close_button.pack(pady=(4, 10), padx=10, fill='x')

        self._update_menu_position()
        self.menu_window.focus_set()

    def close_menu(self, event=None):
        if self.menu_window and self.menu_window.winfo_exists():
            self.menu_window.destroy()
        self.menu_window = None

    def open_settings(self):
        self.command_queue.put("open_settings")
        self.close_menu()

    def open_manual(self):
        webbrowser.open("https://www.google.com/search?q=Como+usar+a+LIA")
        self.close_menu()

    def close_app(self):
        self.command_queue.put("quit_app")
        self.close_menu()

    def set_active(self):
        self.root.wm_attributes("-alpha", 0.9)

    def set_inactive(self):
        self.root.wm_attributes("-alpha", 0.25)

    def update(self):
        try:
            if self.root.winfo_exists():
                self.root.update()
        except tk.TclError:
            pass

    # --- NOVA FUNÇÃO ADICIONADA AQUI ---
    def schedule_main_thread_task(self, task_func):
        """Agenda uma função para ser executada com segurança na thread principal da GUI."""
        if self.root.winfo_exists():
            self.root.after(0, task_func)

    def close(self):
        if self.root.winfo_exists():
            self.root.destroy()