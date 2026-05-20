import speech_recognition as sr
import pyautogui
import pyperclip
import ctypes
import subprocess
import time
import threading
import queue

user32 = ctypes.windll.user32

# Mapeamento de variações → ação
COMANDOS = {
    # Enviar (Enter)
    "executar enviar":   "enter",
    "executar envia":    "enter",
    "executar invia":    "enter",
    "executar enviado":  "enter",
    "executar envio":    "enter",
    "executar mandar":   "enter",
    "executar manda":    "enter",
    "executar send":     "enter",

    # Nova linha (Shift+Enter)
    "executar nova linha":  "new_line",
    "executar nova lin":    "new_line",
    "executar novalinha":   "new_line",
    "executar nova lina":   "new_line",
    "executar nova line":   "new_line",
    "executar novo linha":  "new_line",

    # Backspace
    "executar linha nova":  "backspace",
    "executar lin nova":    "backspace",
    "executar lina nova":   "backspace",
    "executar linha novo":  "backspace",

    # Pause / Start
    "executar pause":    "pause",
    "executar pausar":   "pause",
    "executar pausa":    "pause",
    "executar pau":      "pause",
    "executar start":    "start",
    "executar iniciar":  "start",
    "executar inicia":   "start",
    "executar retomar":  "start",
    "executar sta":      "start",

    # Limpar tudo
    "executar limpa":    "clear",
    "executar limpar":   "clear",
    "executar limp":     "clear",
    "executar limpas":   "clear",
    "executar limpeza":  "clear",
    "executar limpo":    "clear",
    "executar apagar":   "clear",
    "executar apaga":    "clear",
    "executar clear":    "clear",
    "executar claro":    "clear",
    "executar tudo":     "clear",
}

ACOES = {
    "enter":     lambda: pyautogui.press("enter"),
    "new_line":  lambda: pyautogui.hotkey("shift", "enter"),
    "clear":     lambda: (pyautogui.hotkey("ctrl", "a"), pyautogui.press("delete")),
    "backspace": lambda: pyautogui.press("backspace"),
}

pausado = False
audio_queue = queue.Queue()

# Define volume do microfone para 100% via Windows Core Audio API
_ps_mic_volume = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
[Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    int NotImpl1();
    [PreserveSig] int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    [PreserveSig] int Activate(ref Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int NotImpl1(); int NotImpl2();
    [PreserveSig] int SetMasterVolumeLevelScalar(float fLevel, ref Guid pguidEventContext);
}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComObject {}
public class MicAudio {
    static readonly IMMDeviceEnumerator e = (IMMDeviceEnumerator)(new MMDeviceEnumeratorComObject());
    public static void SetVolume(float level) {
        IMMDevice dev; e.GetDefaultAudioEndpoint(1, 1, out dev);
        Guid iid = typeof(IAudioEndpointVolume).GUID; object o;
        dev.Activate(ref iid, 23, IntPtr.Zero, out o);
        IAudioEndpointVolume vol = (IAudioEndpointVolume)o;
        Guid empty = Guid.Empty;
        vol.SetMasterVolumeLevelScalar(level, ref empty);
    }
}
"@
[MicAudio]::SetVolume(1.0)
"""
try:
    subprocess.run(["powershell", "-Command", _ps_mic_volume], capture_output=True, timeout=10)
    print("Microfone definido para volume máximo.")
except Exception as e:
    print(f"Aviso: não foi possível ajustar o volume do microfone: {e}")


def restaurar_foco(hwnd):
    if hwnd:
        try:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.1)
        except Exception:
            pass


def processar(texto, hwnd):
    global pausado
    texto_lower = texto.lower()
    print(f"[reconhecido]: '{texto_lower}'")

    if texto_lower in COMANDOS and COMANDOS[texto_lower] == "pause":
        pausado = True
        print("[PAUSADO] Diga 'executar start' para retomar.")
        return
    if texto_lower in COMANDOS and COMANDOS[texto_lower] == "start":
        pausado = False
        print("[RETOMADO] Ouvindo novamente.")
        return

    if pausado:
        print("(pausado — ignorando)")
        return

    restaurar_foco(hwnd)

    if texto_lower in COMANDOS:
        acao = COMANDOS[texto_lower]
        print(f"[comando]: {acao}")
        ACOES[acao]()
        return

    executou_cmd = False
    for cmd, acao in COMANDOS.items():
        if texto_lower.endswith(" " + cmd):
            texto_sem_cmd = texto[:-(len(cmd) + 1)].strip()
            if texto_sem_cmd:
                pyperclip.copy(texto_sem_cmd + " ")
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.1)
            print(f"[comando]: {acao}")
            ACOES[acao]()
            executou_cmd = True
            break

    if not executou_cmd:
        pyperclip.copy(texto + " ")
        pyautogui.hotkey("ctrl", "v")


def worker_reconhecimento(r):
    """Thread separada: reconhece áudio da fila enquanto o mic continua gravando."""
    while True:
        item = audio_queue.get()
        if item is None:
            break
        audio, hwnd = item
        try:
            print("Processando...")
            texto = r.recognize_google(audio, language="pt-BR").strip()
            processar(texto, hwnd)
        except sr.UnknownValueError:
            print("(não entendi, fale novamente)")
        except sr.RequestError as e:
            print(f"Erro de conexão: {e}")
        finally:
            audio_queue.task_done()
            print("Ouvindo...")


def callback_audio(recognizer, audio):
    """Chamado pela thread de escuta ao detectar uma frase completa."""
    hwnd = user32.GetForegroundWindow()
    audio_queue.put((audio, hwnd))


r = sr.Recognizer()
r.pause_threshold = 2          # 2s de silêncio = fim da frase (era 3s)
r.phrase_threshold = 0.2       # mínimo 0.2s de fala para considerar uma frase
r.non_speaking_duration = 0.3  # buffer de silêncio ao redor da fala
r.energy_threshold = 200
r.dynamic_energy_threshold = True

mic = sr.Microphone()

# Inicia worker de reconhecimento em thread daemon
t = threading.Thread(target=worker_reconhecimento, args=(r,), daemon=True)
t.start()

# Calibra ruído ambiente
with mic as source:
    print("Calibrando microfone... aguarde.")
    r.adjust_for_ambient_noise(source, duration=2)
    print("Pronto! Pode falar.\n")

print("=== DITADO POR VOZ ===")
print("Comandos: 'executar enviar' | 'executar nova linha' | 'executar limpa' | 'executar pause' | 'executar start'")
print("Pressione Ctrl+C para parar.\n")
print("Ouvindo...")

# Escuta contínua em background — sem gaps entre frases
stop_listening = r.listen_in_background(mic, callback_audio, phrase_time_limit=20)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    stop_listening(wait_for_stop=False)
    audio_queue.put(None)  # sinaliza worker para encerrar
    print("\nDitado encerrado.")
