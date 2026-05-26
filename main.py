"""
Ditado por voz — entry point.

Reconhecimento: faster-whisper (local, offline, pt-BR) com fallback Google.
VAD: webrtcvad embutido no speech_recognition.
Comandos: fuzzy matching com rapidfuzz.
Feedback: beeps ao capturar frase e ao executar comando.
Undo: 'executar desfazer' apaga o último texto digitado.
"""

import os

# Suprime warnings do HuggingFace Hub no Windows (cache sem symlinks).
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import time

from voz.listener import Listener, construir_microfone, construir_recognizer
from voz.mic_volume import set_max_volume
from voz.recognition import carregar_modelo


def main() -> None:
    set_max_volume()
    carregar_modelo()

    recognizer = construir_recognizer()
    microfone = construir_microfone()

    listener = Listener(recognizer, microfone)
    listener.calibrar()

    print("=== DITADO POR VOZ ===")
    print("Comandos: 'executar enviar' | 'executar nova linha' | 'executar limpar'")
    print("         'executar pause/start' | 'executar desfazer'")
    print("Pressione Ctrl+C para parar.\n")
    print("Ouvindo...")

    listener.iniciar()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        listener.parar()
        print("\nDitado encerrado.")


if __name__ == "__main__":
    main()
