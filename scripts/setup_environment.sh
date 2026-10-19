#!/usr/bin/env bash
# Повторяемая подготовка среды. Запускать из корня проекта.
set -euo pipefail
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements-lock.txt
.venv/bin/python scripts/configure.py
docker compose up -d --wait
.venv/bin/python scripts/create_test_db.py
.venv/bin/python -m app.init_db --demo
