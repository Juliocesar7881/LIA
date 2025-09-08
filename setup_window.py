import customtkinter
from tkinter import messagebox, Listbox, SINGLE, END
from config_manager import carregar_config, salvar_config
import webbrowser
import os
import json


class JanelaSetup(customtkinter.CTkToplevel):
    def __init__(self):
        super().__init__()

        self.cidades_lista = []
        self._carregar_cidades()

        customtkinter.set_appearance_mode("Dark")
        customtkinter.set_default_color_theme("blue")

        self.FONT_TITULO = customtkinter.CTkFont(family="Segoe UI", size=26, weight="bold")
        self.FONT_LABEL = customtkinter.CTkFont(family="Segoe UI", size=14)
        self.FONT_NORMAL = customtkinter.CTkFont(family="Segoe UI", size=13)
        self.FONT_PEQUENA = customtkinter.CTkFont(family="Segoe UI", size=12, slant="italic")
        self.COR_ACCENT = "#0078D7"

        self.title("Bem-vindo(a) à LIA!")

        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone. Erro: {e}")

        self.resizable(False, False)
        self.attributes('-topmost', True)
        self.lift()
        self.after(50, self.centralizar_janela)

        self.frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = customtkinter.CTkLabel(self.frame, text="Configuração Inicial", font=self.FONT_TITULO)
        titulo.pack(pady=(20, 25))

        pergunta1 = customtkinter.CTkLabel(self.frame, text="1. Como a LIA deve te chamar?", font=self.FONT_LABEL)
        pergunta1.pack(anchor="w", padx=20, pady=(10, 5))
        self.nome_entry = customtkinter.CTkEntry(self.frame, height=40, font=self.FONT_NORMAL,
                                                 placeholder_text="Digite seu nome aqui...",
                                                 border_color=self.COR_ACCENT)
        self.nome_entry.pack(fill="x", padx=20, ipady=4)
        self.nome_entry.focus()

        pergunta_cidade = customtkinter.CTkLabel(self.frame, text="2. Qual a sua cidade padrão (para o clima)?",
                                                 font=self.FONT_LABEL)
        pergunta_cidade.pack(anchor="w", padx=20, pady=(20, 5))
        self.cidade_var = customtkinter.StringVar()
        self.cidade_entry = customtkinter.CTkEntry(self.frame, height=40, font=self.FONT_NORMAL,
                                                   placeholder_text="Comece a digitar o nome da cidade...",
                                                   border_color=self.COR_ACCENT, textvariable=self.cidade_var)
        self.cidade_entry.pack(fill="x", padx=20, ipady=4)
        self.cidade_var.trace_add("write", self._atualizar_sugestoes)

        # MUDANÇA VISUAL 1: Removida a borda para um visual mais limpo e integrado.
        self.sugestoes_frame = customtkinter.CTkFrame(self.frame, width=0, height=0, corner_radius=8,
                                                      fg_color="#2B2B2B")

        self.lista_sugestoes = Listbox(self.sugestoes_frame, font=("Segoe UI", 13), background="#2B2B2B",
                                       foreground="white", selectbackground=self.COR_ACCENT, selectforeground="white",
                                       borderwidth=0, highlightthickness=0, relief="flat", exportselection=False)
        self.lista_sugestoes.pack(fill="both", expand=True, padx=2, pady=2)  # Adicionado padding interno
        self.lista_sugestoes.bind("<ButtonRelease-1>", self._selecionar_cidade)

        pergunta3 = customtkinter.CTkLabel(self.frame, text="3. Defina a personalidade da LIA:", font=self.FONT_LABEL)
        pergunta3.pack(anchor="w", padx=20, pady=(20, 5))
        self.humor_var = customtkinter.IntVar(value=50)
        self.slider = customtkinter.CTkSlider(self.frame, from_=0, to=100, variable=self.humor_var,
                                              command=self.atualizar_personalidade_label, button_color=self.COR_ACCENT,
                                              button_hover_color="#005a9e")
        self.slider.pack(fill="x", padx=20, pady=5)
        self.label_slider = customtkinter.CTkLabel(self.frame, text="Equilibrada (50%)", font=self.FONT_PEQUENA)
        self.label_slider.pack(pady=(0, 20))

        self.lembrar_var = customtkinter.BooleanVar(value=True)
        lembrar_check = customtkinter.CTkCheckBox(self.frame, text="Lembrar configuração", variable=self.lembrar_var,
                                                  font=self.FONT_NORMAL, fg_color=self.COR_ACCENT)
        lembrar_check.pack(pady=10)

        botoes_frame = customtkinter.CTkFrame(self.frame, fg_color="transparent")
        botoes_frame.pack(fill="x", pady=(20, 20), side="bottom")
        botoes_frame.grid_columnconfigure((0, 1), weight=1)

        manual_btn = customtkinter.CTkButton(botoes_frame, text="Manual", command=self.abrir_manual, height=40,
                                             font=customtkinter.CTkFont(size=14, weight="bold"), fg_color="gray50",
                                             hover_color="gray30")
        manual_btn.grid(row=0, column=0, sticky="ew", padx=(20, 5))
        concluir_btn = customtkinter.CTkButton(botoes_frame, text="Concluir e Iniciar", command=self.concluir,
                                               height=40, font=customtkinter.CTkFont(size=14, weight="bold"),
                                               fg_color=self.COR_ACCENT, hover_color="#005a9e")
        concluir_btn.grid(row=0, column=1, sticky="ew", padx=(5, 20))

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.bind("<FocusOut>", self._on_window_click)

    def _on_window_click(self, event):
        widget_foco = self.focus_get()
        if widget_foco != self.cidade_entry and widget_foco != self.lista_sugestoes:
            if self.sugestoes_frame.winfo_viewable():
                self.sugestoes_frame.place_forget()

    def _carregar_cidades(self):
        try:
            base_path = os.path.dirname(__file__)
            caminho_arquivo = os.path.join(base_path, "utils", "Cidades.json")
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                self.cidades_lista = json.load(f)
            self.cidades_lista.sort()
        except Exception as e:
            messagebox.showerror("Erro de Arquivo", f"Não foi possível carregar 'Cidades.json':\n{e}")
            self.cidades_lista = []

    def _atualizar_sugestoes(self, *args):
        texto_digitado = self.cidade_var.get().lower()
        if not texto_digitado:
            self.sugestoes_frame.place_forget()
            return

        sugestoes = [c for c in self.cidades_lista if c.lower().startswith(texto_digitado)]

        if sugestoes:
            self.lista_sugestoes.delete(0, END)
            for s in sugestoes[:10]:
                self.lista_sugestoes.insert(END, s)

            self.update_idletasks()
            entry_x = self.cidade_entry.winfo_x()
            entry_y = self.cidade_entry.winfo_y()
            entry_height = self.cidade_entry.winfo_height()
            entry_width = self.cidade_entry.winfo_width()

            # MUDANÇA VISUAL 2: Altura máxima menor (4 itens) e espaçamento entre eles.
            list_height = min(len(sugestoes), 4) * 28

            self.sugestoes_frame.configure(width=entry_width, height=list_height)

            # MUDANÇA VISUAL 3: Adicionado "+ 2" para um pequeno espaço entre a caixa de texto e as sugestões.
            self.sugestoes_frame.place(x=entry_x, y=entry_y + entry_height + 2)
            self.sugestoes_frame.lift()
        else:
            self.sugestoes_frame.place_forget()

    def _selecionar_cidade(self, event=None):
        if not self.lista_sugestoes.curselection():
            return
        selecionado = self.lista_sugestoes.get(self.lista_sugestoes.curselection())
        self.cidade_var.set(selecionado)
        self.sugestoes_frame.place_forget()
        self.frame.focus()

    def centralizar_janela(self, largura=500, altura=560):
        self.geometry(f"{largura}x{altura}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def atualizar_personalidade_label(self, valor):
        valor_int = int(float(valor))
        texto = f"Séria ({valor_int}%)" if valor_int <= 25 else f"Equilibrada ({valor_int}%)" if valor_int <= 75 else f"Engraçada ({valor_int}%)"
        self.label_slider.configure(text=texto)

    def abrir_manual(self):
        webbrowser.open("https://www.google.com/search?q=Como+usar+a+LIA")

    def concluir(self):
        self.sugestoes_frame.place_forget()
        self.update()
        self.attributes('-topmost', False)
        nome = self.nome_entry.get().strip()
        cidade = self.cidade_entry.get().strip()

        if not nome:
            messagebox.showwarning("Nome Inválido", "Por favor, digite um nome antes de continuar.")
            self.nome_entry.focus()
            self.attributes('-topmost', True)
            return

        if not cidade or cidade not in self.cidades_lista:
            messagebox.showwarning("Cidade Inválida", "Por favor, selecione uma cidade válida da lista de sugestões.")
            self.cidade_entry.focus()
            self.attributes('-topmost', True)
            return

        if self.lembrar_var.get():
            salvar_config(nome, self.humor_var.get(), cidade)
        self.destroy()

    def _on_closing(self):
        self.attributes('-topmost', False)
        if messagebox.askokcancel("Sair da Configuração",
                                  "Você tem certeza que deseja cancelar? A LIA não poderá iniciar sem que a configuração seja concluída."):
            self.destroy()
        else:
            self.attributes('-topmost', True)


def criar_janela_setup():
    app = JanelaSetup()
    app.grab_set()