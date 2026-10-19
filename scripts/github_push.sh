#!/usr/bin/env bash
# Push project ini ke GitHub memakai Personal Access Token (PAT).
#
# Pemakaian:
#   ./scripts/github_push.sh https://github.com/USERNAME/NAMA-REPO.git ghp_TOKENANDA
#
# Catatan:
# - Token HANYA dipakai sesaat untuk push, lalu dihapus dari konfigurasi git.
# - Buat PAT di: GitHub > Settings > Developer settings > Personal access
#   tokens (classic) dengan scope "repo".
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_URL="${1:-}"
TOKEN="${2:-}"

if [ -z "$REPO_URL" ] || [ -z "$TOKEN" ]; then
  echo "Pemakaian: $0 <url-repo> <token>"
  echo "Contoh   : $0 https://github.com/budi/cctv-public-server.git ghp_xxxx"
  exit 1
fi

git init -b main 2>/dev/null || true
git add -A
git commit -m "feat: CCTV Public Server v1.0.0" || echo "[i] Tidak ada perubahan untuk di-commit."

CLEAN_URL="${REPO_URL#https://}"
git remote remove origin 2>/dev/null || true
git remote add origin "https://${TOKEN}@${CLEAN_URL}"

echo "[*] Push ke ${REPO_URL} (branch main) ..."
git push -u origin main

# Hapus token dari konfigurasi lokal supaya tidak tertinggal di disk.
git remote set-url origin "https://${CLEAN_URL}"
echo "[OK] Selesai. Token sudah dibersihkan dari konfigurasi git lokal."
