# CLAUDE.md

Notas para o Claude Code ao trabalhar neste repositório.

## O que é o projeto

Ditado por voz em pt-BR para Windows. Captura áudio do microfone, transcreve
com `faster-whisper` (offline) e cola o texto na janela em foco usando o
clipboard + `Ctrl+V`. Comandos de voz (`executar enviar`, `executar limpar`,
etc.) disparam atalhos de teclado em vez de digitar o texto.

## Como rodar

```powershell
python main.py
```

`main.py` é o entry point. O pacote `voz/` é importado a partir dele.

## Estrutura

```
main.py                 entry point — só orquestração
voz/
  config.py             constantes (comandos, thresholds, prompt, modelo)
  state.py              estado mutável (singleton DitadorState)
  sounds.py             beeps (winsound, em threads)
  window.py             ctypes/user32 — foco de janela
  mic_volume.py         PowerShell → Core Audio para 100% de volume
  recognition.py        carrega Whisper, função reconhecer()
  actions.py            mapa ACOES = {nome: callable} usando pyautogui
  commands.py           detectar_comando (fuzzy) + processar(texto, hwnd)
  listener.py           Listener: recognizer, microfone, queue, worker
```

## Convenções

- **Plataforma:** Windows only. `winsound`, `ctypes.windll.user32`, PowerShell
  e PyAudio do Windows são dependências reais — não generalizar para Linux/Mac
  sem motivo.
- **Idioma do código e da interface:** português. Mensagens de log, prompts,
  comentários e nomes de funções/comandos em pt-BR. Não traduza para inglês.
- **Estado global** vive em `voz/state.py` como dataclass — não criar novas
  variáveis de módulo para estado mutável.
- **Configuração** (constantes, listas de comandos, thresholds) sempre em
  `voz/config.py`. Nunca espalhar pelo código.
- **Imports opcionais** (faster-whisper, rapidfuzz) seguem o padrão:
  `try/except ImportError` com flag `*_OK` e fallback. Mantenha esse padrão.

## Hardware-alvo

A máquina do dono é um **i3-8100 (4 cores) sem GPU NVIDIA**. Por isso o modelo
Whisper padrão é `small` com `compute_type=int8`. Não troque para `medium`/
`large-v3` automaticamente — em CPU dessa categoria a latência fica
inaceitável (5-10s por frase). Se a máquina mudar, atualize
`WHISPER_MODEL_NAME` em `voz/config.py`.

## Pontos sensíveis (cuidado ao mexer)

- **VAD duplo.** O `speech_recognition` já filtra silêncio. Não reative
  `vad_filter=True` no `transcribe()` — gerou cortes de palavras e
  alucinação. Mantém `vad_filter=False`.
- **`dynamic_energy_threshold`.** Causa drift e perda de fala suave.
  Mantém `False`.
- **`condition_on_previous_text=False`** evita que um erro contamine a
  próxima frase. Manter desligado.
- **`pause_threshold`.** 0.8s é o sweet-spot para conversação. Subir muito
  faz o usuário esperar antes de ver o texto; baixar demais corta no meio
  da frase.
- **`listen_in_background`.** A escuta é contínua justamente para não perder
  fala enquanto o Whisper processa. Não substitua por `listen()` síncrono.

## Antes de propor mudanças

1. Mudou comportamento de áudio? Teste rodando `main.py` e ditando ~5 frases,
   incluindo uma com comando no final. Type-checking não pega regressão de UX.
2. Adicionou dependência? Atualize `requirements.txt`.
3. Adicionou um novo comando? Coloque em `COMANDOS` (config.py) e, se houver
   ação nova, em `ACOES` (actions.py). O matcher fuzzy já cobre variações
   leves — não duplique 30 sinônimos.
