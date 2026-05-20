import speech_recognition as sr
import pyautogui
import pyperclip
import ctypes
import time

user32 = ctypes.windll.user32

COMANDOS = {
    "enter": lambda: pyautogui.press("enter"),
    "new line": lambda: pyautogui.press("enter"),
    "clear": lambda: (pyautogui.hotkey("ctrl", "a"), pyautogui.press("delete")),
}

def restaurar_foco(hwnd):
    if hwnd:
        try:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.15)
        except Exception:
            pass

print("=== DITADO POR VOZ ===")
print("Comandos de voz disponíveis:")
print("  'enter'    → pressiona Enter")
print("  'new line' → nova linha")
print("  'clear'    → limpa tudo")
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

        # Salva a janela ativa logo após capturar o áudio
        hwnd = user32.GetForegroundWindow()

        print("Processando...")
        texto = r.recognize_google(audio, language="pt-BR").strip()
        print(f"Você disse: {texto}")

        # Restaura o foco para a janela onde o usuário estava
        restaurar_foco(hwnd)

        texto_lower = texto.lower()

        if texto_lower in COMANDOS:
            print(f"[comando: {texto_lower}]")
            COMANDOS[texto_lower]()
        else:
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
