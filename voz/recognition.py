"""Reconhecimento de fala — Whisper local com fallback para Google."""

import numpy as np
import speech_recognition as sr

from .config import (
    INITIAL_PROMPT_PT,
    WHISPER_COMPUTE,
    WHISPER_CPU_THREADS,
    WHISPER_MODEL_NAME,
)

try:
    from faster_whisper import WhisperModel
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False
    print("Aviso: faster-whisper não encontrado — usando Google Speech API.")


_whisper_model = None


def carregar_modelo() -> None:
    """Carrega o modelo Whisper. Idempotente."""
    global _whisper_model
    if not WHISPER_OK or _whisper_model is not None:
        return
    print(f"Carregando modelo Whisper ({WHISPER_MODEL_NAME}) — 1ª execução baixa ~465 MB...")
    _whisper_model = WhisperModel(
        WHISPER_MODEL_NAME,
        device="cpu",
        compute_type=WHISPER_COMPUTE,
        cpu_threads=WHISPER_CPU_THREADS,
        num_workers=1,
    )
    print("Modelo carregado.")


def reconhecer(audio: sr.AudioData, recognizer: sr.Recognizer) -> str:
    """Retorna texto reconhecido. Prioriza Whisper; fallback: Google."""
    if _whisper_model is not None:
        pcm = np.frombuffer(audio.frame_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = _whisper_model.transcribe(
            pcm,
            language="pt",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            initial_prompt=INITIAL_PROMPT_PT,
            vad_filter=False,                    # speech_recognition já filtrou
        )
        return " ".join(s.text for s in segments).strip()
    return recognizer.recognize_google(audio, language="pt-BR").strip()
