#!/usr/bin/env bash
# ============================================================
# CCTV Public Server — launcher Termux (Android) / proot Linux
#
# Pemakaian:
#   ./run-termux.sh                -> port ACAK (berubah tiap jalan)
#   PORT=8000 ./run-termux.sh      -> port tetap 8000
#   PORT=random ./run-termux.sh    -> port acak (sama seperti default)
#
# Catatan:
# - Memakai folder venv bernama "venv"; bila folder venv lama rusak
#   (mis. ImportError pydantic_core), script ini OTOMATIS memperbaiki
#   versi paket, dan bila tetap gagal akan membuat ulang venv.
# - Dependensi Termux semuanya PURE PYTHON (pydantic v1.10.26 yang
#   resmi mendukung Python 3.14 + uvicorn polos) -> tanpa kompilasi.
# ============================================================
set -e
cd "$(dirname "$0")"

VENV_DIR="venv"

echo "[1/4] Memastikan paket dasar ..."
if command -v pkg >/dev/null 2>&1; then
  pkg install -y python python-pip 2>/dev/null || true
elif command -v apt-get >/dev/null 2>&1; then
  (apt-get update -qq && apt-get install -y python3 python3-pip python3-venv) 2>/dev/null || true
fi

PYBIN="$(command -v python3 || command -v python)"

echo "[2/4] Menyiapkan lingkungan Python (${VENV_DIR}) ..."
make_venv() {
  rm -rf "$VENV_DIR"
  "$PYBIN" -m venv "$VENV_DIR" || python -m venv "$VENV_DIR"
}
if [ ! -x "$VENV_DIR/bin/python" ]; then
  make_venv || true
fi

# Venv gagal dibuat (mis. ensurepip tak ada)? -> pakai Python sistem.
if [ -x "$VENV_DIR/bin/python" ]; then
  PY="$VENV_DIR/bin/python"
  PIP="$VENV_DIR/bin/pip"
  [ -x "$PIP" ] || PIP="$PY -m pip"
else
  echo "[!] Virtualenv tidak tersedia -> memakai Python sistem + --break-system-packages bila perlu"
  PY="$PYBIN"
  PIP="$PY -m pip"
fi

install_deps() {
  $PIP install -r requirements-termux.txt || {
    echo "[!] pip gagal (mungkin PEP 668 / externally-managed) -> coba --break-system-packages ..."
    $PIP install --break-system-packages -r requirements-termux.txt
  }
}

echo "[3/4] Memasang dependensi (pure Python; venv lama yang rusak ikut diperbaiki) ..."
install_deps

# Validasi import — bila venv lama masih rusak, buat ulang dari nol.
if ! "$PY" -c "import fastapi, uvicorn, pydantic" >/dev/null 2>&1; then
  echo "[!] Lingkungan lama masih rusak -> membuat ulang ${VENV_DIR} dari nol ..."
  make_venv || true
  if [ -x "$VENV_DIR/bin/python" ]; then
    PY="$VENV_DIR/bin/python"
    PIP="$VENV_DIR/bin/pip"
    [ -x "$PIP" ] || PIP="$PY -m pip"
    install_deps
  fi
  "$PY" -c "import fastapi, uvicorn, pydantic" || {
    echo "[X] Gagal memasang dependensi. Salin pesan error di atas untuk laporan."
    exit 1
  }
fi
echo "      -> dependensi OK (pydantic $("$PY" -c 'import pydantic;print(pydantic.VERSION)'))"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "      -> file .env dibuat dari .env.example"
fi

echo "[4/4] Menentukan port server ..."
PORT="${PORT:-random}"
if [ "$PORT" = "random" ] || [ -z "$PORT" ]; then
  PORT="$("$PY" -c 'import socket; s=socket.socket(); s.bind(("0.0.0.0", 0)); print(s.getsockname()[1]); s.close()')"
  echo "      -> port ACAK dipilih: $PORT"
else
  echo "      -> port tetap: $PORT"
fi

echo ""
echo "  ============================================="
echo "   Server CCTV Public berjalan!"
echo "   Browser HP   : http://localhost:${PORT}"
echo "   Dokumentasi  : http://localhost:${PORT}/docs"
echo "   Dari perangkat lain: http://IP_HP:${PORT}"
echo "   (cek IP HP: ketik ifconfig, atau pkg install net-tools)"
echo "   Berhenti     : Ctrl+C  (Volume Down + C)"
echo "  ============================================="
echo ""
exec "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
