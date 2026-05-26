"""Manipulação da janela em foco (Win32)."""

import ctypes
import time

user32 = ctypes.windll.user32


def janela_em_foco() -> int:
    return user32.GetForegroundWindow()


def restaurar_foco(hwnd: int) -> None:
    if not hwnd:
        return
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.1)
    except Exception:
        pass
