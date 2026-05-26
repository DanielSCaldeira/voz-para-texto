"""Captura de áudio, fila assíncrona e worker de reconhecimento."""

import queue
import threading

import speech_recognition as sr

from .commands import processar
from .config import (
    DYNAMIC_ENERGY,
    ENERGY_THRESHOLD,
    NON_SPEAKING_DURATION,
    PAUSE_THRESHOLD,
    PHRASE_THRESHOLD,
    PHRASE_TIME_LIMIT,
    SAMPLE_RATE,
)
from .recognition import reconhecer
from .sounds import beep_captura, beep_erro
from .window import janela_em_foco


def construir_recognizer() -> sr.Recognizer:
    r = sr.Recognizer()
    r.pause_threshold = PAUSE_THRESHOLD
    r.phrase_threshold = PHRASE_THRESHOLD
    r.non_speaking_duration = NON_SPEAKING_DURATION
    r.energy_threshold = ENERGY_THRESHOLD
    r.dynamic_energy_threshold = DYNAMIC_ENERGY
    return r


def construir_microfone() -> sr.Microphone:
    return sr.Microphone(sample_rate=SAMPLE_RATE)


class Listener:
    """Escuta contínua em background; processamento assíncrono via fila."""

    def __init__(self, recognizer: sr.Recognizer, microfone: sr.Microphone):
        self.recognizer = recognizer
        self.microfone = microfone
        self.audio_queue: queue.Queue = queue.Queue()
        self._stop_listening = None
        self._worker: threading.Thread | None = None

    # ── ciclo de vida ────────────────────────────────────────────────────────
    def calibrar(self, duration: float = 2.0) -> None:
        with self.microfone as source:
            print("Calibrando microfone... aguarde.")
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            print("Pronto!\n")

    def iniciar(self) -> None:
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        self._stop_listening = self.recognizer.listen_in_background(
            self.microfone, self._callback_audio, phrase_time_limit=PHRASE_TIME_LIMIT
        )

    def parar(self) -> None:
        if self._stop_listening is not None:
            self._stop_listening(wait_for_stop=False)
        self.audio_queue.put(None)

    # ── internos ─────────────────────────────────────────────────────────────
    def _callback_audio(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        hwnd = janela_em_foco()
        beep_captura()
        self.audio_queue.put((audio, hwnd))

    def _worker_loop(self) -> None:
        while True:
            item = self.audio_queue.get()
            if item is None:
                break
            audio, hwnd = item
            try:
                print("Processando...")
                texto = reconhecer(audio, self.recognizer)
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
                self.audio_queue.task_done()
                print("Ouvindo...")
