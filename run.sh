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

# PORT=8000 (default) | PORT=random -> port acak otomatis dari sistem
PORT="${PORT:-8000}"
if [ "$PORT" = "random" ]; then
  PORT="$(python -c 'import socket; s=socket.socket(); s.bind(("0.0.0.0", 0)); print(s.getsockname()[1]); s.close()')"
  echo "[*] Port acak dipilih: $PORT"
fi

echo "[*] Server jalan di http://localhost:${PORT}  (docs: /docs)"
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "$PORT"
