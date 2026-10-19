#!/usr/bin/env python3
"""Sinkronisasi katalog kamera dari Windy Webcams API v3 (CLI).

Pemakaian:
    python scripts/sync_windy.py --countries ID --max-items 100

API key dibaca dari WINDY_API_KEY di file .env / environment.
Hasil ditulis ke file katalog (DATA_FILE, default data/cameras.json).
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Agar script bisa dijalankan dari mana saja
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.services.windy import fetch_webcams  # noqa: E402
from app.storage import JsonStorage  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description="Sinkron katalog kamera dari Windy Webcams API")
    parser.add_argument(
        "--countries",
        default="",
        help="Kode negara dipisah koma, mis. ID atau ID,SG,MY (kosong = semua)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=50,
        help="Jumlah maksimum webcam yang diambil (default 50)",
    )
    parser.add_argument(
        "--lang",
        default=settings.windy_lang,
        help="Bahasa metadata Windy (default dari WINDY_LANG, yaitu %(default)s)",
    )
    args = parser.parse_args()

    if not settings.windy_api_key:
        print(
            "ERROR: WINDY_API_KEY belum diatur.\n"
            "Daftar gratis di https://www.windy.com/api lalu isi .env "
            "(salin dari .env.example).",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[*] Mengambil maksimum {args.max_items} webcam "
          f"(negara: {args.countries or 'semua'}) ...")
    cameras, total = await fetch_webcams(args.countries or None, args.max_items, args.lang)

    storage = JsonStorage(settings.data_file)
    storage.load()
    storage.replace_source("windy", cameras)

    print(f"[OK] {len(cameras)} webcam tersimpan (tersedia di Windy: {total}).")
    print(f"[OK] Total katalog: {storage.count()} kamera -> {settings.data_file}")

    sample = [c.model_dump(mode="json") for c in cameras[:3]]
    print("[i] Contoh 3 entri pertama:")
    print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
