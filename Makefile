# Makefile do projeto Ditado por Voz.
# Uso típico no Windows:
#   make setup    -> cria .venv e instala dependências
#   make run      -> executa main.py
#   make clean    -> remove .venv e caches
#
# Requer Python 3.10+ instalado e no PATH.

PYTHON ?= python
VENV   ?= .venv

ifeq ($(OS),Windows_NT)
    VENV_PYTHON := $(VENV)\Scripts\python.exe
    VENV_PIP    := $(VENV)\Scripts\pip.exe
    ACTIVATE    := .\$(VENV)\Scripts\Activate.ps1
    RM_VENV     := if exist $(VENV) rmdir /s /q $(VENV)
    RM_CACHE    := for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
    NULL        := NUL
else
    VENV_PYTHON := $(VENV)/bin/python
    VENV_PIP    := $(VENV)/bin/pip
    ACTIVATE    := source $(VENV)/bin/activate
    RM_VENV     := rm -rf $(VENV)
    RM_CACHE    := find . -type d -name __pycache__ -exec rm -rf {} +
    NULL        := /dev/null
endif

.PHONY: help check venv install setup run upgrade clean reinstall

help:
	@echo Ditado por Voz - alvos disponiveis:
	@echo   make check       - verifica versao do Python
	@echo   make venv        - cria virtualenv em $(VENV)
	@echo   make install     - instala dependencias no venv
	@echo   make setup       - venv + install [recomendado]
	@echo   make run         - executa main.py
	@echo   make upgrade     - atualiza dependencias para versoes mais recentes
	@echo   make reinstall   - clean + setup do zero
	@echo   make clean       - remove venv, caches e arquivos temporarios

check:
	@$(PYTHON) --version

venv:
	@$(PYTHON) -m venv $(VENV)
	@echo Virtualenv criado em $(VENV)

install:
	@$(VENV_PIP) install --upgrade pip setuptools wheel
	@$(VENV_PIP) install -r requirements.txt
	@echo.
	@echo Dependencias instaladas. Para ativar o venv:
	@echo   $(ACTIVATE)

setup: venv install
	@echo.
	@echo Setup concluido. Execute com: make run

run:
	@$(VENV_PYTHON) main.py

upgrade:
	@$(VENV_PIP) install --upgrade -r requirements.txt

reinstall: clean setup

clean:
	@$(RM_VENV)
	@$(RM_CACHE) 2>$(NULL) || exit 0
	@echo Limpeza concluida.
