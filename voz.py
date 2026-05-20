"""
Ditado por voz — versão avançada
- Reconhecimento: faster-whisper (local, offline, pt-BR) com fallback Google
- VAD: Silero VAD embutido no Whisper + webrtcvad para captura precisa
- Comandos: fuzzy matching com rapidfuzz (sem precisar de 30+ variações)
- Feedback sonoro: beep ao capturar frase e ao executar comando
- Undo: 'executar desfazer' apaga o último texto digitado
"""

import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"  # cache sem symlinks no Windows
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import speech_recognition as sr
import pyautogui
import pyperclip
import ctypes
import subprocess
import time
import threading
import queue
import winsound
import numpy as np

# ── Imports opcionais ────────────────────────────────────────────────────────

try:
    from faster_whisper import WhisperModel
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False
    print("Aviso: faster-whisper não encontrado — usando Google Speech API.")

try:
    from rapidfuzz import process as fuzz
    FUZZY_OK = True
except ImportError:
    FUZZY_OK = False
    print("Aviso: rapidfuzz não encontrado — usando matching exato.")

user32 = ctypes.windll.user32

# ── Comandos ─────────────────────────────────────────────────────────────────
# Com fuzzy matching não precisamos de dezenas de variações — apenas as mais
# diferentes são suficientes para guiar o matcher.

COMANDOS = {
    # Enviar (Enter)
    "executar enviar":  "enter",
    "executar send":    "enter",
    "executar mandar":  "enter",

    # Nova linha (Shift+Enter)
    "executar nova linha": "new_line",
    "executar new line":   "new_line",

    # Backspace
    "executar linha nova":  "backspace",
    "executar backspace":   "backspace",

    # Pause / Start
    "executar pause":   "pause",
    "executar pausar":  "pause",
    "executar pau":     "pause",
    "executar start":   "start",
    "executar iniciar": "start",
    "executar retomar": "start",
    "executar sta":     "start",

    # Limpar tudo
    "executar limpar":  "clear",
    "executar clear":   "clear",
    "executar apagar":  "clear",

    # Desfazer último texto digitado
    "executar desfazer": "undo",
    "executar undo":     "undo",
}

# ── Estado global ─────────────────────────────────────────────────────────────

pausado = False
ultimo_len = 0          # quantos caracteres foram colados por último (para undo)
audio_queue = queue.Queue()

# ── Ações ─────────────────────────────────────────────────────────────────────

def acao_undo():
    if ultimo_len > 0:
        for _ in range(ultimo_len):
            pyautogui.press("backspace")

ACOES = {
    "enter":     lambda: pyautogui.press("enter"),
    "new_line":  lambda: pyautogui.hotkey("shift", "enter"),
    "clear":     lambda: (pyautogui.hotkey("ctrl", "a"), pyautogui.press("delete")),
    "backspace": lambda: pyautogui.press("backspace"),
    "undo":      acao_undo,
}

# ── Sons ──────────────────────────────────────────────────────────────────────

def beep_captura():
    """Frase capturada pelo microfone."""
    threading.Thread(target=lambda: winsound.Beep(700, 60), daemon=True).start()

def beep_comando():
    """Comando reconhecido e executado."""
    threading.Thread(target=lambda: (winsound.Beep(1100, 60), time.sleep(0.05), winsound.Beep(1400, 60)), daemon=True).start()

def beep_erro():
    """Não entendeu."""
    threading.Thread(target=lambda: winsound.Beep(400, 120), daemon=True).start()

# ── Volume do microfone ───────────────────────────────────────────────────────

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
    print(f"Aviso: não foi possível ajustar o volume: {e}")

# ── Reconhecimento Whisper ────────────────────────────────────────────────────

whisper_model = None
if WHISPER_OK:
    print("Carregando modelo Whisper (small) — na 1ª execução faz download de ~465 MB...")
    whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    print("Modelo carregado.")

def reconhecer(audio: sr.AudioData) -> str:
    """Retorna texto reconhecido. Prioriza Whisper; fallback: Google."""
    if whisper_model is not None:
        # Whisper espera float32 a 16 kHz
        pcm = np.frombuffer(audio.frame_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = whisper_model.transcribe(
            pcm,
            language="pt",
            beam_size=5,
            vad_filter=True,                          # Silero VAD remove silêncio/ruído
            vad_parameters={"min_silence_duration_ms": 400},
        )
        return " ".join(s.text for s in segments).strip()
    else:
        return r_sr.recognize_google(audio, language="pt-BR").strip()

# ── Detecção de comando com fuzzy ─────────────────────────────────────────────

FUZZY_THRESHOLD = 88  # % de similaridade mínima

def detectar_comando(texto_lower: str):
    """
    Retorna (acao, texto_antes_do_comando) ou (None, None).
    Tenta: match exato → suffix exato → fuzzy completo → fuzzy sufixo.
    """
    # 1. Comando completo exato
    if texto_lower in COMANDOS:
        return COMANDOS[texto_lower], ""

    # 2. Sufixo exato
    for cmd, acao in COMANDOS.items():
        if texto_lower.endswith(" " + cmd):
            return acao, texto_lower[:-(len(cmd) + 1)].strip()

    if not FUZZY_OK:
        return None, None

    # 3. Fuzzy no texto completo (sem texto antes)
    match, score, _ = fuzz.extractOne(texto_lower, COMANDOS.keys())
    if score >= FUZZY_THRESHOLD and " " not in texto_lower.replace(match, "").strip():
        return COMANDOS[match], ""

    # 4. Fuzzy no sufixo (últimas 1-4 palavras)
    palavras = texto_lower.split()
    for n in range(1, min(5, len(palavras))):
        sufixo = " ".join(palavras[-n:])
        match, score, _ = fuzz.extractOne(sufixo, COMANDOS.keys())
        if score >= FUZZY_THRESHOLD:
            antes = " ".join(palavras[:-n]).strip()
            return COMANDOS[match], antes

    return None, None

# ── Janela em foco ────────────────────────────────────────────────────────────

def restaurar_foco(hwnd):
    if hwnd:
        try:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.1)
        except Exception:
            pass

# ── Processamento do texto reconhecido ───────────────────────────────────────

def processar(texto: str, hwnd):
    global pausado, ultimo_len

    texto_lower = texto.lower()
    print(f"[reconhecido]: '{texto_lower}'")

    acao, texto_antes = detectar_comando(texto_lower)

    # pause/start tratados antes de restaurar foco
    if acao == "pause":
        pausado = True
        beep_comando()
        print("[PAUSADO] Diga 'executar start' para retomar.")
        return
    if acao == "start":
        pausado = False
        beep_comando()
        print("[RETOMADO] Ouvindo novamente.")
        return

    if pausado:
        print("(pausado — ignorando)")
        return

    restaurar_foco(hwnd)

    if acao is not None:
        # Digita o texto antes do comando (se houver)
        if texto_antes:
            pyperclip.copy(texto_antes + " ")
            pyautogui.hotkey("ctrl", "v")
            ultimo_len = len(texto_antes) + 1
            time.sleep(0.1)
        print(f"[comando]: {acao}")
        beep_comando()
        ACOES[acao]()
        if acao != "undo":
            ultimo_len = 0
        return

    # Texto puro — cola via clipboard
    conteudo = texto + " "
    pyperclip.copy(conteudo)
    pyautogui.hotkey("ctrl", "v")
    ultimo_len = len(conteudo)

# ── Worker de reconhecimento (thread separada) ────────────────────────────────

def worker_reconhecimento():
    while True:
        item = audio_queue.get()
        if item is None:
            break
        audio, hwnd = item
        try:
            print("Processando...")
            texto = reconhecer(audio)
            if texto:
                processar(texto, hwnd)
            else:
                print("(silêncio filtrado)")
        except sr.UnknownValueError:
            beep_erro()
            print("(não entendi, fale novamente)")
        except sr.RequestError as e:
            beep_erro()
            print(f"Erro de conexão: {e}")
        except Exception as e:
            beep_erro()
            print(f"Erro inesperado: {e}")
        finally:
            audio_queue.task_done()
            print("Ouvindo...")

# ── Callback do microfone ─────────────────────────────────────────────────────

def callback_audio(recognizer, audio):
    hwnd = user32.GetForegroundWindow()
    beep_captura()
    audio_queue.put((audio, hwnd))

# ── Inicialização ─────────────────────────────────────────────────────────────

# Microfone a 16 kHz — compatível com Whisper sem resampling
r_sr = sr.Recognizer()
r_sr.pause_threshold = 1.5         # 1.5s de silêncio = fim da frase
r_sr.phrase_threshold = 0.2        # mínimo de fala para considerar uma frase
r_sr.non_speaking_duration = 0.3   # buffer de silêncio ao redor da fala
r_sr.energy_threshold = 200
r_sr.dynamic_energy_threshold = True

mic = sr.Microphone(sample_rate=16000)  # 16 kHz nativo para Whisper

# Inicia worker
t = threading.Thread(target=worker_reconhecimento, daemon=True)
t.start()

# Calibra ruído ambiente
with mic as source:
    print("Calibrando microfone... aguarde.")
    r_sr.adjust_for_ambient_noise(source, duration=2)
    print("Pronto!\n")

print("=== DITADO POR VOZ ===")
print("Comandos: 'executar enviar' | 'executar nova linha' | 'executar limpar'")
print("         'executar pause/start' | 'executar desfazer'")
print("Pressione Ctrl+C para parar.\n")
print("Ouvindo...")

# Escuta contínua — sem gaps
stop_listening = r_sr.listen_in_background(mic, callback_audio, phrase_time_limit=20)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    stop_listening(wait_for_stop=False)
    audio_queue.put(None)
    print("\nDitado encerrado.")
