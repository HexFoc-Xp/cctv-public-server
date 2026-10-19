#!/usr/bin/env bash
# Jalankan CCTV Public Server di Linux/macOS:
#   ./run.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "[*] Membuat virtualenv .venv ..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[*] Memasang dependensi ..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "[*] Server jalan di http://localhost:${PORT:-8000}  (docs: /docs)"
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
