def gerar_codigo(descricao):
    print(f"💻 Criando código para: {descricao}")
    with open("codigo_gerado.py", "w", encoding="utf-8") as f:
        if "calculadora" in descricao:
            f.write("def soma(a, b):\n    return a + b\n\nprint(soma(2, 3))")
        elif "bot telegram" in descricao:
            f.write("# Bot Telegram com Python\nimport telegram\n# implemente aqui")
        else:
            f.write("# Código base gerado automaticamente\nprint('Olá, mundo!')")

    print("✅ Código salvo como codigo_gerado.py")
