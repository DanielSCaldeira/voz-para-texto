"""Ações de teclado executadas em resposta a comandos de voz."""

import pyautogui

from .state import state


def _acao_undo() -> None:
    if state.ultimo_len > 0:
        for _ in range(state.ultimo_len):
            pyautogui.press("backspace")


def _acao_clear() -> None:
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("delete")


ACOES = {
    "enter":     lambda: pyautogui.press("enter"),
    "new_line":  lambda: pyautogui.hotkey("shift", "enter"),
    "clear":     _acao_clear,
    "backspace": lambda: pyautogui.press("backspace"),
    "undo":      _acao_undo,
}
