#!/usr/bin/env bash
# PostgreSQL должна быть установлена и запущена, базы созданы по setup_database.sql.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements-lock.txt
.venv/bin/python scripts/configure.py
.venv/bin/python scripts/create_test_db.py
.venv/bin/python -m app.init_db --demo
