.PHONY: install dev test contract smoke lint

PYTHON ?= python3.12
VENV ?= .venv
BIN := $(VENV)/bin
BASE_URL ?= http://127.0.0.1:8000

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e ".[dev]"

dev:
	$(BIN)/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(BIN)/pytest -q

contract:
	$(BIN)/python scripts/check_contract.py

smoke:
	BASE_URL=$(BASE_URL) $(BIN)/python scripts/live_smoke.py

lint:
	$(BIN)/ruff check app tests scripts
	$(BIN)/ruff format --check app tests scripts
