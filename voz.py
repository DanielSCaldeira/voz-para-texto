import speech_recognition as sr
import pyautogui
import pyperclip
import pygetwindow as gw
import time

COMANDOS = {
    "enter": lambda: pyautogui.press("enter"),
    "new line": lambda: pyautogui.press("enter"),
    "clear": lambda: (pyautogui.hotkey("ctrl", "a"), pyautogui.press("delete")),
}

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

janela_ativa = None

while True:
    try:
        # Salva a janela ativa antes de ouvir
        try:
            janela_ativa = gw.getActiveWindow()
        except Exception:
            janela_ativa = None

        with mic as source:
            print("Ouvindo...")
            audio = r.listen(source, timeout=None, phrase_time_limit=15)

        print("Processando...")
        texto = r.recognize_google(audio, language="pt-BR").strip()
        print(f"Você disse: {texto}")

        # Volta o foco para a janela anterior
        if janela_ativa:
            try:
                janela_ativa.activate()
                time.sleep(0.2)
            except Exception:
                pass

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
