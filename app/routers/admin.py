"""Endpoint admin: kelola kamera manual & sinkronisasi Windy.

Proteksi sederhana: bila ADMIN_TOKEN diatur di .env, semua endpoint di sini
mewajibkan header ``X-Admin-Token`` dengan nilai yang sama. Bila kosong,
endpoint terbuka (cocok untuk penggunaan lokal/pribadi).
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Header, HTTPException, Query

from app.config import settings
from app.models import Camera, CameraCreate
from app.storage import storage
from app.services.windy import sync_windy_cameras

router = APIRouter(prefix="/admin", tags=["Admin"])


def _guard(x_admin_token: Optional[str]) -> None:
    """Validasi header X-Admin-Token bila ADMIN_TOKEN diatur."""
    if settings.admin_token and x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=401, detail="Header X-Admin-Token tidak valid atau kosong"
        )


@router.post(
    "/cameras",
    response_model=Camera,
    status_code=201,
    summary="Tambah kamera manual (stream HLS milik sendiri / berizin)",
)
async def add_camera(
    payload: CameraCreate,
    x_admin_token: Optional[str] = Header(default=None),
) -> Camera:
    """Tambahkan satu kamera ke katalog. Contoh payload ada di README."""
    _guard(x_admin_token)
    if payload.source == "hls" and not payload.stream_url:
        raise HTTPException(status_code=422, detail="source=hls membutuhkan stream_url (.m3u8)")
    if payload.source == "embed" and not payload.embed_url:
        raise HTTPException(status_code=422, detail="source=embed membutuhkan embed_url")
    return storage.add(payload)


@router.put(
    "/cameras/{camera_id}",
    response_model=Camera,
    summary="Perbarui data kamera",
)
async def update_camera(
    camera_id: str,
    payload: CameraCreate,
    x_admin_token: Optional[str] = Header(default=None),
) -> Camera:
    _guard(x_admin_token)
    updated = storage.update(camera_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan")
    return updated


@router.delete("/cameras/{camera_id}", status_code=204, summary="Hapus kamera")
async def delete_camera(
    camera_id: str,
    x_admin_token: Optional[str] = Header(default=None),
) -> None:
    _guard(x_admin_token)
    if not storage.delete(camera_id):
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan")


@router.post(
    "/sync/windy",
    summary="Sinkronisasi katalog dari Windy Webcams API",
)
async def sync_windy(
    countries: Optional[str] = Query(
        None, description="Kode negara dipisah koma, mis. ID,US (kosong = semua negara)"
    ),
    max_items: int = Query(50, ge=1, le=500, description="Jumlah maksimum webcam yang diambil"),
    x_admin_token: Optional[str] = Header(default=None),
) -> dict:
    """Ambil webcam publik dari Windy dan ganti entri 'windy' di katalog.

    Kamera manual (hls/embed) tidak akan terhapus. Wajib mengatur
    WINDY_API_KEY di .env terlebih dahulu.
    """
    _guard(x_admin_token)
    try:
        return await sync_windy_cameras(countries=countries, max_items=max_items)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Windy API error {exc.response.status_code} — periksa WINDY_API_KEY Anda",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Gagal menghubungi Windy API: {exc}"
        ) from exc
