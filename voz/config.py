"""Configurações: comandos, prompts e thresholds."""

# ── Comandos de voz ──────────────────────────────────────────────────────────
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

# ── Reconhecimento ───────────────────────────────────────────────────────────
WHISPER_MODEL_NAME = "small"      # i3-8100 sem GPU — "medium" fica lento demais
WHISPER_COMPUTE    = "int8"
WHISPER_CPU_THREADS = 4

# Prompt que orienta o Whisper sobre estilo/idioma — reduz alucinação e
# erros de vocabulário em conversação em pt-BR.
INITIAL_PROMPT_PT = (
    "Olá, tudo bem? Esta é uma transcrição em português do Brasil, "
    "com pontuação correta, acentuação e linguagem natural do dia a dia."
)

# ── Microfone / VAD do speech_recognition ────────────────────────────────────
SAMPLE_RATE          = 16000   # nativo do Whisper
PAUSE_THRESHOLD      = 0.8     # silêncio para encerrar frase
PHRASE_THRESHOLD     = 0.2
NON_SPEAKING_DURATION = 0.3
ENERGY_THRESHOLD     = 300     # fixo — dynamic costuma derivar
DYNAMIC_ENERGY       = False
PHRASE_TIME_LIMIT    = 30      # máximo de uma única frase

# ── Detecção de comando ──────────────────────────────────────────────────────
FUZZY_THRESHOLD = 88           # % de similaridade mínima
