"""Klien Windy Webcams API v3 + pemetaan hasil ke model katalog.

Dokumentasi API : https://api.windy.com/point-forecast/docs
Halaman API key : https://www.windy.com/api (pilih "Webcams API", gratis)

Catatan: struktur respons dapat berubah mengikuti versi API Windy.
Semua akses field di sini defensif (dict.get) agar server tetap hidup.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings
from app.models import Camera
from app.storage import storage


def _first(*values: Optional[str]) -> Optional[str]:
    """Kembalikan nilai pertama yang tidak kosong."""
    for value in values:
        if value:
            return value
    return None


def map_webcam(raw: dict) -> Camera:
    """Ubah satu objek webcam dari respons Windy menjadi model Camera."""
    location = raw.get("location") or {}
    player = raw.get("player") or {}
    images = raw.get("images") or {}
    current = images.get("current") or {}
    categories = [c.get("name") for c in (raw.get("categories") or []) if c.get("name")]

    country_code = _first(location.get("countryCode"), location.get("country_code"))
    country_name = location.get("country")
    if country_code and not country_name:
        country_name = country_code

    return Camera(
        id=f"windy-{raw.get('webcamId')}",
        title=raw.get("title") or "Webcam tanpa nama",
        source="windy",
        stream_url=None,
        embed_url=_first(player.get("live"), player.get("day")),
        page_url=raw.get("webcamUrl"),
        city=location.get("city"),
        region=location.get("region"),
        country=country_code,
        country_name=country_name,
        latitude=location.get("latitude"),
        longitude=location.get("longitude"),
        categories=categories or ["webcam"],
        thumbnail=current.get("preview"),
        status="active" if raw.get("status") == "active" else "offline",
        last_updated=datetime.now(timezone.utc),
    )


async def fetch_webcams(
    countries: Optional[str], max_items: int, lang: str
) -> tuple[list[Camera], int]:
    """Ambil webcam dari Windy per halaman (maks. 50/request) hingga max_items.

    Mengembalikan (daftar Camera, total webcam tersedia di Windy).
    Melempar RuntimeError bila API key belum diatur, dan
    httpx.HTTPStatusError bila respons API tidak sukses.
    """
    api_key = settings.windy_api_key
    if not api_key:
        raise RuntimeError("WINDY_API_KEY belum diatur di file .env")

    collected: list[dict] = []
    offset = 0
    total = 0
    headers = {"x-windy-api-key": api_key}

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(collected) < max_items:
            page_size = min(50, max_items - len(collected))
            params: dict = {
                "limit": page_size,
                "offset": offset,
                "lang": lang,
                "includeLocation": "true",
                "includeImages": "true",
                "includePlayer": "true",
            }
            if countries:
                params["countries"] = countries

            response = await client.get(
                settings.windy_base_url, params=params, headers=headers
            )
            response.raise_for_status()
            data = response.json()

            total = int(data.get("total") or 0)
            webcams = data.get("webcams") or []
            if not webcams:
                break
            collected.extend(webcams)
            offset += len(webcams)
            if total and offset >= total:
                break

    return [map_webcam(item) for item in collected], total


async def sync_windy_cameras(
    countries: Optional[str] = None,
    max_items: int = 50,
    lang: Optional[str] = None,
) -> dict:
    """Sinkronkan katalog: ganti seluruh kamera 'windy' dengan hasil terbaru.

    Kamera manual (source hls/embed) tidak terpengaruh.
    """
    cameras, total = await fetch_webcams(countries, max_items, lang or settings.windy_lang)
    storage.replace_source("windy", cameras)
    return {
        "fetched": len(cameras),
        "windy_total_available": total,
        "total_catalog": storage.count(),
    }
