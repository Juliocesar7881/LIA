# verify_install.py

try:
    import google.generativeai as genai
    print("--- Diagnóstico da Biblioteca Google Gemini ---")
    print(f"Versão instalada: {genai.__version__}")
    print(f"Localização do ficheiro: {genai.__file__}")
    print("---------------------------------------------")

    if genai.__version__ < '0.5.0':
        print("\nAVISO: A versão instalada é MUITO ANTIGA. Este é o problema.")
        print("A versão precisa de ser 0.5.4 ou superior.")
    else:
        print("\nINFO: A versão da biblioteca parece estar correta.")

except ImportError:
    print("ERRO: A biblioteca 'google-generativeai' não foi encontrada.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")