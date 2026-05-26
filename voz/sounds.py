"""Feedback sonoro — beeps disparados em threads para não bloquear."""

import threading
import time
import winsound


def _beep_async(fn):
    threading.Thread(target=fn, daemon=True).start()


def beep_captura():
    """Frase capturada pelo microfone."""
    _beep_async(lambda: winsound.Beep(700, 60))


def beep_comando():
    """Comando reconhecido e executado."""
    def _seq():
        winsound.Beep(1100, 60)
        time.sleep(0.05)
        winsound.Beep(1400, 60)
    _beep_async(_seq)


def beep_erro():
    """Não entendeu."""
    _beep_async(lambda: winsound.Beep(400, 120))
