.PHONY: install dev test contract smoke lint

PYTHON ?= python3.12
VENV ?= .venv
BIN := $(VENV)/bin
# 8010, not 8000: a machine developing PreMan itself already has the PreMan API
# on 8000, and the pre-push hook looks for a local copy of this app by port. On
# 8000 it finds PreMan's spec instead and skips the push check. Override with
# `make dev PORT=8000` where nothing else is listening.
PORT ?= 8010
BASE_URL ?= http://127.0.0.1:$(PORT)

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e ".[dev]"

dev:
	$(BIN)/uvicorn app.main:app --reload --host 127.0.0.1 --port $(PORT)

test:
	$(BIN)/pytest -q

contract:
	$(BIN)/python scripts/check_contract.py
	$(BIN)/python scripts/export_openapi.py --check
	$(BIN)/python scripts/export_mock_schemas.py --check

smoke:
	BASE_URL=$(BASE_URL) $(BIN)/python scripts/live_smoke.py

lint:
	$(BIN)/ruff check app tests scripts
	$(BIN)/ruff format --check app tests scripts
