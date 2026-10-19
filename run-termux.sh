#!/usr/bin/env bash
# ============================================================
# CCTV Public Server — launcher khusus Termux (Android)
# Pemakaian:
#   chmod +x run-termux.sh && ./run-termux.sh
#
# Versi Termux memakai dependensi PURE PYTHON
# (requirements-termux.txt: pydantic v1 + uvicorn polos)
# sehingga TIDAK perlu kompilasi Rust/C di HP.
# ============================================================
set -e
cd "$(dirname "$0")"

echo "[1/4] Memastikan paket dasar Termux ..."
pkg install -y python python-pip 2>/dev/null || true

echo "[2/4] Menyiapkan lingkungan Python ..."
if python -m venv .venv >/dev/null 2>&1 && [ -x .venv/bin/python ] && [ -x .venv/bin/pip ]; then
  PY=".venv/bin/python"
  PIP=".venv/bin/pip"
  echo "      -> memakai virtualenv .venv"
else
  PY="python"
  PIP="pip"
  echo "      -> virtualenv tidak tersedia, memakai pip sistem Termux"
fi

echo "[3/4] Memasang dependensi (pure Python, tanpa kompilasi) ..."
"$PIP" install -r requirements-termux.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "      -> file .env dibuat dari .env.example"
fi

echo "[4/4] Menjalankan server ..."
echo ""
echo "  Buka di browser HP : http://localhost:8000"
echo "  Dokumentasi API    : http://localhost:8000/docs"
echo "  Berhenti           : Ctrl+C (Volume Down + C)"
echo ""
exec "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
