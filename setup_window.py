# setup_window.py (versão com ícone personalizado)

import customtkinter
from tkinter import messagebox
from config_manager import salvar_config
import webbrowser
import os  # Necessário para construir o caminho do ícone


class JanelaSetup(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- APARÊNCIA PROFISSIONAL ---
        customtkinter.set_appearance_mode("Dark")
        customtkinter.set_default_color_theme("blue")

        self.FONT_TITULO = customtkinter.CTkFont(family="Segoe UI", size=26, weight="bold")
        self.FONT_LABEL = customtkinter.CTkFont(family="Segoe UI", size=14)
        self.FONT_NORMAL = customtkinter.CTkFont(family="Segoe UI", size=13)
        self.FONT_PEQUENA = customtkinter.CTkFont(family="Segoe UI", size=12, slant="italic")

        self.COR_ACCENT = "#0078D7"

        # --- CONFIGURAÇÃO DA JANELA ---
        self.title("Bem-vindo(a) à LISA!")

        # --- NOVO: LÓGICA PARA ADICIONAR O ÍCONE ---
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone em '{icon_path}'. Usando ícone padrão. Erro: {e}")

        self.resizable(False, False)
        self.attributes('-topmost', True)
        self.lift()
        self.after(50, self.centralizar_janela)

        # Frame principal com cantos arredondados
        frame = customtkinter.CTkFrame(self, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        titulo = customtkinter.CTkLabel(frame, text="Configuração Inicial", font=self.FONT_TITULO)
        titulo.pack(pady=(20, 25))

        # Pergunta 1: Nome
        pergunta1 = customtkinter.CTkLabel(frame, text="1. Como a LISA deve te chamar?", font=self.FONT_LABEL)
        pergunta1.pack(anchor="w", padx=20, pady=(10, 5))

        self.nome_entry = customtkinter.CTkEntry(
            frame,
            height=40,
            font=self.FONT_NORMAL,
            placeholder_text="Digite seu nome aqui...",
            border_color=self.COR_ACCENT
        )
        self.nome_entry.pack(fill="x", padx=20, ipady=4)
        self.nome_entry.focus()

        # Pergunta 2: Personalidade
        pergunta2 = customtkinter.CTkLabel(frame, text="2. Defina a personalidade da LISA:", font=self.FONT_LABEL)
        pergunta2.pack(anchor="w", padx=20, pady=(20, 5))

        self.humor_var = customtkinter.IntVar(value=50)
        self.slider = customtkinter.CTkSlider(
            frame,
            from_=0, to=100,
            variable=self.humor_var,
            command=self.atualizar_personalidade_label,
            button_color=self.COR_ACCENT,
            button_hover_color="#005a9e"
        )
        self.slider.pack(fill="x", padx=20, pady=5)

        self.label_slider = customtkinter.CTkLabel(frame, text="Equilibrada (50%)", font=self.FONT_PEQUENA)
        self.label_slider.pack(pady=(0, 20))

        # Checkbox
        self.lembrar_var = customtkinter.BooleanVar(value=True)
        lembrar_check = customtkinter.CTkCheckBox(
            frame,
            text="Lembrar configuração",
            variable=self.lembrar_var,
            font=self.FONT_NORMAL,
            fg_color=self.COR_ACCENT
        )
        lembrar_check.pack(pady=10)

        # Botões
        botoes_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
        botoes_frame.pack(fill="x", pady=(20, 20), side="bottom")
        botoes_frame.grid_columnconfigure((0, 1), weight=1)

        manual_btn = customtkinter.CTkButton(
            botoes_frame,
            text="Manual",
            command=self.abrir_manual,
            height=40,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color="gray50",
            hover_color="gray30"
        )
        manual_btn.grid(row=0, column=0, sticky="ew", padx=(20, 5))

        concluir_btn = customtkinter.CTkButton(
            botoes_frame,
            text="Concluir e Iniciar",
            command=self.concluir,
            height=40,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color=self.COR_ACCENT,
            hover_color="#005a9e"
        )
        concluir_btn.grid(row=0, column=1, sticky="ew", padx=(5, 20))

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def centralizar_janela(self, largura=500, altura=460):
        """Sua função de centralização, que funciona de forma precisa."""
        self.geometry(f"{largura}x{altura}")
        self.update_idletasks()

        largura_total = self.winfo_width()
        altura_total = self.winfo_height()

        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()

        x = (largura_tela - largura_total) // 2
        y = (altura_tela - altura_total) // 2

        self.geometry(f"+{x}+{y}")

    def atualizar_personalidade_label(self, valor):
        valor_int = int(float(valor))
        if valor_int <= 25:
            texto = f"Séria ({valor_int}%)"
        elif valor_int <= 75:
            texto = f"Equilibrada ({valor_int}%)"
        else:
            texto = f"Engraçada ({valor_int}%)"
        self.label_slider.configure(text=texto)

    def abrir_manual(self):
        webbrowser.open("https://www.google.com/search?q=Como+usar+a+LISA")

    def concluir(self):
        self.attributes('-topmost', False)
        nome = self.nome_entry.get().strip()
        if not nome:
            messagebox.showwarning("Nome Inválido", "Por favor, digite um nome antes de continuar.")
            self.nome_entry.focus()
            self.attributes('-topmost', True)
            return

        if self.lembrar_var.get():
            salvar_config(nome, self.humor_var.get())

        self.destroy()

    def _on_closing(self):
        self.attributes('-topmost', False)
        if messagebox.askokcancel("Sair da Configuração",
                                  "Você tem certeza que deseja cancelar? A LISA não poderá iniciar sem que a configuração seja concluída."):
            self.destroy()
        else:
            self.attributes('-topmost', True)


def criar_janela_setup():
    """Função que o main.py vai chamar."""
    app = JanelaSetup()
    app.mainloop()