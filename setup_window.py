import customtkinter
from tkinter import messagebox, END
from config_manager import carregar_config, salvar_config
import webbrowser
import os
import json


class JanelaSetup(customtkinter.CTkToplevel):
    def __init__(self, master=None, callback=None):
        super().__init__(master)
        self.callback = callback

        self.cidades_lista = []
        self._carregar_cidades()
        self.processando_selecao = False

        customtkinter.set_appearance_mode("Dark")
        customtkinter.set_default_color_theme("blue")

        self.FONT_TITULO = customtkinter.CTkFont(family="Segoe UI", size=26, weight="bold")
        self.FONT_LABEL = customtkinter.CTkFont(family="Segoe UI", size=14)
        self.FONT_NORMAL = customtkinter.CTkFont(family="Segoe UI", size=13)
        self.FONT_PEQUENA = customtkinter.CTkFont(family="Segoe UI", size=12, slant="italic")
        self.COR_ACCENT = "#0078D7"

        self.title("Bem-vindo(a) à LIA!")
        self.geometry("500x580")  # MODIFICADO: Altura ajustada para o novo item

        try:
            # TESTE COM CAMINHO ABSOLUTO E EXPLÍCITO
            path_absoluto = r"C:\Users\Luchini\PycharmProjects\Lisa\assets\icon_blue.ico"

            print("\n--- INICIANDO TESTE DE CAMINHO ABSOLUTO ---")
            print(f"Tentando carregar o ícone de: '{path_absoluto}'")

            # Verificação crucial: o arquivo existe neste caminho exato?
            if os.path.exists(path_absoluto):
                print("✅ Arquivo encontrado no caminho absoluto.")
                # Tentativa de carregar o ícone
                self.iconbitmap(path_absoluto)
                print("✅ Comando self.iconbitmap() executado. Verifique a janela.")
            else:
                print(
                    "❌ ERRO CRÍTICO: O arquivo NÃO foi encontrado no caminho absoluto. Verifique se o caminho está 100% correto.")
            print("--- FIM DO TESTE DE CAMINHO ABSOLUTO ---\n")

        except Exception as e:
            # Se o arquivo existe mas dá erro ao carregar, o problema é o formato do arquivo.
            print(f"❌ ERRO AO CARREGAR O ÍCONE: {e}")
            print("Isso geralmente significa que o arquivo .ico não é válido ou está corrompido.")

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

        self.sugestoes_container = customtkinter.CTkScrollableFrame(self.frame, corner_radius=8, fg_color="#2B2B2B",
                                                                    height=120)
        self.sugestoes_container.pack_forget()

        pergunta3 = customtkinter.CTkLabel(self.frame, text="3. Defina a personalidade da LIA:", font=self.FONT_LABEL)
        pergunta3.pack(anchor="w", padx=20, pady=(10, 5))
        self.humor_var = customtkinter.IntVar(value=50)
        self.slider = customtkinter.CTkSlider(self.frame, from_=0, to=100, variable=self.humor_var,
                                              command=self.atualizar_personalidade_label, button_color=self.COR_ACCENT,
                                              button_hover_color="#005a9e")
        self.slider.pack(fill="x", padx=20, pady=5)
        self.label_slider = customtkinter.CTkLabel(self.frame, text="Equilibrada (50%)", font=self.FONT_PEQUENA)
        self.label_slider.pack(pady=(0, 20))

        # Frame para organizar as caixas de seleção
        checkbox_frame = customtkinter.CTkFrame(self.frame, fg_color="transparent")
        checkbox_frame.pack(pady=10, fill="x", padx=35)

        self.lembrar_var = customtkinter.BooleanVar(value=True)
        lembrar_check = customtkinter.CTkCheckBox(checkbox_frame, text="Lembrar configuração",
                                                  variable=self.lembrar_var,
                                                  font=self.FONT_NORMAL, fg_color=self.COR_ACCENT)
        lembrar_check.pack(anchor="w", side="left")

        # NOVO: Caixa de seleção para inicializar com o sistema
        self.iniciar_sistema_var = customtkinter.BooleanVar(value=False)
        iniciar_sistema_check = customtkinter.CTkCheckBox(checkbox_frame, text="Inicializar com o sistema",
                                                          variable=self.iniciar_sistema_var,
                                                          font=self.FONT_NORMAL, fg_color=self.COR_ACCENT)
        iniciar_sistema_check.pack(anchor="w", side="right")

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
        self.bind("<FocusOut>", self._on_window_click, add="+")
        self.cidade_entry.bind("<FocusOut>", self._on_window_click, add="+")

    def _on_window_click(self, event):
        self.after(100, self._check_focus)

    def _check_focus(self):
        widget_foco = self.focus_get()
        if widget_foco != self.cidade_entry and not (
                hasattr(widget_foco, 'master') and widget_foco.master == self.sugestoes_container):
            if self.sugestoes_container.winfo_ismapped():
                self.sugestoes_container.pack_forget()

    def _carregar_cidades(self):
        try:
            base_path = os.path.dirname(__file__)
            caminho_arquivo = os.path.join(base_path, "utils", "cidades.json")
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            lista_formatada = []
            for estado in dados['estados']:
                sigla_estado = estado['sigla']
                for cidade in estado['cidades']:
                    lista_formatada.append(f"{cidade}, {sigla_estado}")

            lista_formatada.sort()
            self.cidades_lista = lista_formatada

        except Exception as e:
            messagebox.showerror("Erro de Arquivo", f"Não foi possível carregar ou processar 'cidades.json':\n{e}")
            self.cidades_lista = []

    def _atualizar_sugestoes(self, *args):
        if self.processando_selecao:
            return

        for widget in self.sugestoes_container.winfo_children():
            widget.destroy()

        texto_digitado = self.cidade_var.get().lower()
        if not texto_digitado:
            self.sugestoes_container.pack_forget()
            return

        sugestoes = [c for c in self.cidades_lista if c.lower().startswith(texto_digitado)]

        if sugestoes:
            container_width = self.cidade_entry.winfo_width()
            label_width = container_width - 80

            for i, nome_cidade in enumerate(sugestoes[:10]):
                label = customtkinter.CTkLabel(self.sugestoes_container, text=nome_cidade, width=label_width,
                                               font=self.FONT_NORMAL, anchor="w")
                label.pack(fill="x", padx=10, pady=4)
                label.bind("<Button-1>", lambda event, cidade=nome_cidade: self._selecionar_cidade(cidade))

                if i < len(sugestoes[:10]) - 1:
                    linha = customtkinter.CTkFrame(self.sugestoes_container, height=1, fg_color="gray30")
                    linha.pack(fill="x", padx=5)

            if not self.sugestoes_container.winfo_ismapped():
                self.sugestoes_container.pack(padx=20, pady=2, after=self.cidade_entry, anchor="w")
        else:
            self.sugestoes_container.pack_forget()

    def _selecionar_cidade(self, cidade_selecionada):
        self.processando_selecao = True
        self.cidade_var.set(cidade_selecionada)
        self.sugestoes_container.pack_forget()
        self.cidade_entry.focus()
        self.cidade_entry.icursor(END)
        self.after(100, lambda: setattr(self, 'processando_selecao', False))

    def centralizar_janela(self):
        self.update_idletasks()
        x_pos = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y_pos = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x_pos}+{y_pos}")

    def atualizar_personalidade_label(self, valor):
        valor_int = int(float(valor))
        texto = f"Séria ({valor_int}%)" if valor_int <= 25 else f"Equilibrada ({valor_int}%)" if valor_int <= 75 else f"Engraçada ({valor_int}%)"
        self.label_slider.configure(text=texto)

    def abrir_manual(self):
        webbrowser.open("https://www.google.com/search?q=Como+usar+a+LIA")

    def concluir(self):
        if self.sugestoes_container.winfo_ismapped():
            self.sugestoes_container.pack_forget()
        self.update()
        self.attributes('-topmost', False)
        nome = self.nome_entry.get().strip()
        cidade = self.cidade_entry.get().strip()

        # NOVO: Obtém o valor da nova caixa de seleção
        iniciar_com_sistema = self.iniciar_sistema_var.get()

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
            # MODIFICADO: Passa o novo valor para a função de salvar
            # Lembre-se de atualizar a função 'salvar_config' para aceitar este novo parâmetro
            salvar_config(nome, self.humor_var.get(), cidade, iniciar_com_sistema)

        # NOVO: Aqui você adicionaria a lógica para configurar a inicialização com o sistema
        if iniciar_com_sistema:
            # Exemplo: self.configurar_inicializacao_auto(ativar=True)
            print("Configurando para iniciar com o sistema...")
        else:
            # Exemplo: self.configurar_inicializacao_auto(ativar=False)
            print("Removendo da inicialização com o sistema...")

        if self.callback:
            self.callback()
        self.destroy()

    def _on_closing(self):
        self.attributes('-topmost', False)
        if messagebox.askokcancel("Sair da Configuração",
                                  "Você tem certeza que deseja cancelar? A LIA não poderá iniciar sem que a configuração seja concluída."):
            self.destroy()
        else:
            self.attributes('-topmost', True)


def criar_janela_setup(callback=None):
    app = JanelaSetup(callback=callback)
    app.grab_set()