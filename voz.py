import speech_recognition as sr
import pyautogui
import pyperclip
import time

print("=== DITADO POR VOZ ===")
print("Fale qualquer coisa - o texto será digitado automaticamente.")
print("Pressione Ctrl+C para parar.\n")

r = sr.Recognizer()
mic = sr.Microphone()

with mic as source:
    print("Calibrando microfone... aguarde.")
    r.adjust_for_ambient_noise(source, duration=2)
    print("Pronto! Pode falar.\n")

while True:
    try:
        with mic as source:
            print("Ouvindo...")
            audio = r.listen(source, timeout=None, phrase_time_limit=15)

        print("Processando...")
        texto = r.recognize_google(audio, language="pt-BR")
        print(f"Você disse: {texto}")

        pyperclip.copy(texto + " ")
        pyautogui.hotkey("ctrl", "v")

    except sr.UnknownValueError:
        print("(não entendi, fale novamente)")
    except sr.RequestError as e:
        print(f"Erro de conexão: {e}")
    except KeyboardInterrupt:
        print("\nDitado encerrado.")
        break
