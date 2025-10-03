import google.generativeai as genai

genai.configure(api_key="AIzaSyCjIKOg7fj6tLLKBXeTb2TpLYvdcCn5hw8")

for m in genai.list_models():
    print(m.name)
