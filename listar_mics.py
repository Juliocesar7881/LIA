# listar_mics.py
import speech_recognition as sr

print("Procurando por microfones conectados...")
nomes_dos_microfones = sr.Microphone.list_microphone_names()

if not nomes_dos_microfones:
    print("Nenhum microfone encontrado!")
else:
    print("Estes são os microfones que encontrei:")
    for i, nome_mic in enumerate(nomes_dos_microfones):
        print(f"Índice {i}: {nome_mic}")