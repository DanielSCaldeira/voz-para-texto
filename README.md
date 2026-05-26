# Ditado por Voz

Ferramenta de ditado contínuo em **português do Brasil** que escuta pelo microfone
e digita o texto reconhecido na janela em foco. Funciona offline com Whisper
local, com fallback para Google Speech.

## Recursos

- Reconhecimento offline com `faster-whisper` (modelo `small` por padrão)
- Escuta contínua sem gaps via `listen_in_background` + fila assíncrona
- Comandos de voz com **fuzzy matching** (não precisa decorar a frase exata)
- Feedback sonoro: beep ao capturar frase, dois beeps ao executar comando, beep grave em erro
- `executar desfazer` apaga o último texto digitado
- Volume do microfone ajustado para 100% automaticamente (Core Audio API)

## Requisitos

- Windows 10/11
- Python 3.10+
- Microfone

## Instalação

### Com Make (recomendado)

```powershell
make setup
```

Cria o `.venv`, atualiza `pip` e instala todas as dependências.

> No Windows, `make` está disponível via Git Bash, MSYS2, Chocolatey
> (`choco install make`) ou Scoop (`scoop install make`).

### Sem Make

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Se o `PyAudio` falhar para instalar, baixe o wheel pré-compilado em
> <https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio> ou use
> `pipwin install pyaudio`.

## Execução

```powershell
make run
# ou
python main.py
```

Na primeira execução o modelo Whisper (~465 MB) é baixado automaticamente.

## Comandos de voz

| Frase                                    | Ação                       |
| ---------------------------------------- | -------------------------- |
| `executar enviar` / `send` / `mandar`    | Enter                      |
| `executar nova linha` / `new line`       | Shift+Enter                |
| `executar backspace` / `linha nova`      | Backspace                  |
| `executar limpar` / `clear` / `apagar`   | Ctrl+A → Delete            |
| `executar desfazer` / `undo`             | Apaga o último texto colado |
| `executar pause` / `pausar`              | Pausa o ditado              |
| `executar start` / `iniciar` / `retomar` | Retoma o ditado             |

Diga o comando no final da frase: *"olá tudo bem **executar enviar**"* cola
*"olá tudo bem "* e dispara Enter.

## Estrutura do projeto

```
voz-para-texto/
├── main.py             # entry point
├── Makefile            # setup, run, clean
├── requirements.txt
├── README.md
├── CLAUDE.md
└── voz/                # pacote principal, separado por responsabilidade
    ├── config.py       # comandos, prompts e thresholds
    ├── state.py        # estado mutável (pausado, ultimo_len)
    ├── sounds.py       # beeps
    ├── window.py       # foco de janela (Win32)
    ├── mic_volume.py   # ajuste de volume via PowerShell/Core Audio
    ├── recognition.py  # Whisper + fallback Google
    ├── actions.py      # ações de teclado
    ├── commands.py     # detecção fuzzy + processamento
    └── listener.py     # microfone, fila e worker
```

## Ajuste fino

Tudo o que se costuma calibrar está em `voz/config.py`:

- `WHISPER_MODEL_NAME` — `tiny`, `base`, `small`, `medium`, `large-v3`
- `PAUSE_THRESHOLD` — quanto silêncio fecha uma frase
- `ENERGY_THRESHOLD` — sensibilidade do microfone
- `INITIAL_PROMPT_PT` — pista de vocabulário para o Whisper
- `FUZZY_THRESHOLD` — quão tolerante o matcher de comandos é

## Encerrar

`Ctrl+C` no terminal onde o `main.py` está rodando.
