#!/usr/bin/env bash
# Jalankan CCTV Public Server di Linux/macOS:
#   ./run.sh                  (port default 8000)
#   PORT=random ./run.sh      (port acak otomatis)
# Venv gagal dibuat? Skrip otomatis fallback ke pip sistem.
set -euo pipefail
cd "$(dirname "$0")"

# --- Pilih interpreter python yang tersedia ---
PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python
command -v "$PY" >/dev/null 2>&1 || { echo "[!] Python tidak ditemukan. Install dulu: sudo apt install python3 python3-venv python3-pip"; exit 1; }

# --- Siapkan virtualenv (cek file activate, bukan hanya foldernya) ---
VENV_OK=0
if [ -f .venv/bin/activate ]; then
  VENV_OK=1
else
  # Hapus sisa venv rusak/parsial agar tidak mengganggu
  if [ -d .venv ]; then
    echo "[*] .venv lama tidak lengkap -> dihapus dulu ..."
    rm -rf .venv
  fi
  echo "[*] Membuat virtualenv .venv ..."
  VENV_OUT="$("$PY" -m venv .venv 2>&1)" || true
  if [ -f .venv/bin/activate ]; then
    VENV_OK=1
  else
    echo "[!] Virtualenv gagal dibuat."
    [ -n "${VENV_OUT}" ] && printf '%s\n' "$VENV_OUT" | sed 's/^/    /'
    if printf '%s' "$VENV_OUT" | grep -qi "ensurepip\|python3-venv"; then
      echo "    -> Solusi Debian/Ubuntu : sudo apt install python3-venv"
      echo "    -> Solusi Termux/Android: pkg install python-pip lalu jalankan ./run-termux.sh"
    fi
    echo "[*] Lanjut dengan pip sistem (tanpa venv) ..."
  fi
fi

# --- Pasang dependensi ---
if [ "$VENV_OK" = "1" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "[*] Memasang dependensi (venv) ..."
  pip install -q --upgrade pip || true
  pip install -q -r requirements.txt
  RUN_PY="python"
else
  echo "[*] Memasang dependensi dengan pip sistem ..."
  if ! "$PY" -m pip install -q -r requirements.txt; then
    echo "[!] pip sistem menolak (PEP 668 / externally-managed) -> pakai --break-system-packages ..."
    "$PY" -m pip install -q --break-system-packages -r requirements.txt
  fi
  RUN_PY="$PY"
fi

# PORT=8000 (default) | PORT=random -> port acak otomatis dari sistem
PORT="${PORT:-8000}"
if [ "$PORT" = "random" ]; then
  PORT="$("$RUN_PY" -c 'import socket; s=socket.socket(); s.bind(("0.0.0.0", 0)); print(s.getsockname()[1]); s.close()')"
  echo "[*] Port acak dipilih: $PORT"
fi

echo "[*] Server jalan di http://localhost:${PORT}  (docs: /docs)"
exec "$RUN_PY" -m uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "$PORT"
