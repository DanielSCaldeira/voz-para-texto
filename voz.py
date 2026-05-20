import speech_recognition as sr
import pyautogui
import pyperclip
import time

COMANDOS = {
    "enter": lambda: pyautogui.press("enter"),
    "enviar": lambda: pyautogui.press("enter"),
    "apagar": lambda: pyautogui.hotkey("ctrl", "z"),
    "limpar": lambda: (pyautogui.hotkey("ctrl", "a"), pyautogui.press("delete")),
    "nova linha": lambda: pyautogui.press("enter"),
}

print("=== DITADO POR VOZ ===")
print("Fale qualquer coisa - o texto será digitado automaticamente.")
print()
print("Comandos de voz disponíveis:")
for cmd in COMANDOS:
    print(f"  '{cmd}' → ação especial")
print()
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
        texto = r.recognize_google(audio, language="pt-BR").strip()
        print(f"Você disse: {texto}")

        texto_lower = texto.lower()

        if texto_lower in COMANDOS:
            print(f"[comando: {texto_lower}]")
            COMANDOS[texto_lower]()
        else:
            # Verifica se termina com um comando
            for cmd, acao in COMANDOS.items():
                if texto_lower.endswith(" " + cmd):
                    texto_sem_cmd = texto[:-(len(cmd) + 1)].strip()
                    if texto_sem_cmd:
                        pyperclip.copy(texto_sem_cmd + " ")
                        pyautogui.hotkey("ctrl", "v")
                        time.sleep(0.1)
                    print(f"[comando: {cmd}]")
                    acao()
                    break
            else:
                pyperclip.copy(texto + " ")
                pyautogui.hotkey("ctrl", "v")

    except sr.UnknownValueError:
        print("(não entendi, fale novamente)")
    except sr.RequestError as e:
        print(f"Erro de conexão: {e}")
    except KeyboardInterrupt:
        print("\nDitado encerrado.")
        break
