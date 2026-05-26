"""Detecção fuzzy de comandos e processamento do texto reconhecido."""

import time

import pyautogui
import pyperclip

from .actions import ACOES
from .config import COMANDOS, FUZZY_THRESHOLD
from .sounds import beep_comando
from .state import state
from .window import restaurar_foco

try:
    from rapidfuzz import process as fuzz
    FUZZY_OK = True
except ImportError:
    FUZZY_OK = False
    print("Aviso: rapidfuzz não encontrado — usando matching exato.")


def detectar_comando(texto_lower: str):
    """
    Retorna (acao, texto_antes_do_comando) ou (None, None).
    Tenta: match exato → suffix exato → fuzzy completo → fuzzy sufixo.
    """
    if texto_lower in COMANDOS:
        return COMANDOS[texto_lower], ""

    for cmd, acao in COMANDOS.items():
        if texto_lower.endswith(" " + cmd):
            return acao, texto_lower[:-(len(cmd) + 1)].strip()

    if not FUZZY_OK:
        return None, None

    match, score, _ = fuzz.extractOne(texto_lower, COMANDOS.keys())
    if score >= FUZZY_THRESHOLD and " " not in texto_lower.replace(match, "").strip():
        return COMANDOS[match], ""

    palavras = texto_lower.split()
    for n in range(1, min(5, len(palavras))):
        sufixo = " ".join(palavras[-n:])
        match, score, _ = fuzz.extractOne(sufixo, COMANDOS.keys())
        if score >= FUZZY_THRESHOLD:
            antes = " ".join(palavras[:-n]).strip()
            return COMANDOS[match], antes

    return None, None


def _colar(texto: str) -> int:
    """Cola via clipboard e retorna o número de caracteres colados."""
    pyperclip.copy(texto)
    pyautogui.hotkey("ctrl", "v")
    return len(texto)


def processar(texto: str, hwnd: int) -> None:
    texto_lower = texto.lower()
    print(f"[reconhecido]: '{texto_lower}'")

    acao, texto_antes = detectar_comando(texto_lower)

    # pause/start tratados antes de restaurar foco
    if acao == "pause":
        state.pausado = True
        beep_comando()
        print("[PAUSADO] Diga 'executar start' para retomar.")
        return
    if acao == "start":
        state.pausado = False
        beep_comando()
        print("[RETOMADO] Ouvindo novamente.")
        return

    if state.pausado:
        print("(pausado — ignorando)")
        return

    restaurar_foco(hwnd)

    if acao is not None:
        if texto_antes:
            state.ultimo_len = _colar(texto_antes + " ")
            time.sleep(0.1)
        print(f"[comando]: {acao}")
        beep_comando()
        ACOES[acao]()
        if acao != "undo":
            state.ultimo_len = 0
        return

    # Texto puro
    state.ultimo_len = _colar(texto + " ")
