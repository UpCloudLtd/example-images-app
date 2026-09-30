#!/usr/bin/env bash
# Runs the image generator natively (e.g. to use Apple MPS) and the other services with Docker Compose.
set -xeuo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [[ -z "${PYTHON:-}" ]]; then
  for candidate in python3.14 python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null; then
      PYTHON="$candidate"
      break
    fi
  done
fi
if [[ -z "${PYTHON:-}" ]]; then
  echo "Python 3.10 or newer is required; set PYTHON to its path." >&2
  exit 1
fi

venv="$root/generator/.venv"
if [[ ! -x "$venv/bin/python" ]]; then
  "$PYTHON" -m venv "$venv"
fi
"$venv/bin/python" -m pip install --upgrade pip
"$venv/bin/python" -m pip install -r generator/requirements.txt

export GENERATOR_TOKEN="${GENERATOR_TOKEN:-local-generator-token}"
docker compose stop generator
docker compose up --build -d db storage backend frontend

cd generator
BACKEND_URL=http://localhost:5000 exec "$venv/bin/python" generator.py
