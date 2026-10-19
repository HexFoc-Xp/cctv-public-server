"""Endpoint publik untuk membaca katalog kamera (tanpa autentikasi)."""

import random
from collections import Counter
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import Camera, PaginatedCameras
from app.storage import storage

router = APIRouter(prefix="/cameras", tags=["Katalog"])


def _matches(
    cam: Camera, q: str, country: str, category: str, status: str, source: str
) -> bool:
    """Cek apakah satu kamera lolos semua filter aktif."""
    if status and cam.status != status:
        return False
    if source and cam.source != source:
        return False
    if country and (cam.country or "").upper() != country.upper():
        return False
    if category and category.lower() not in [c.lower() for c in cam.categories]:
        return False
    if q:
        haystack = " ".join(
            filter(None, [cam.title, cam.city, cam.region, cam.country_name, cam.country])
        ).lower()
        if q.lower() not in haystack:
            return False
    return True


@router.get(
    "",
    response_model=PaginatedCameras,
    summary="Daftar kamera (cari, filter, paginasi)",
)
async def list_cameras(
    q: Optional[str] = Query(None, description="Kata kunci: nama kamera, kota, wilayah, negara"),
    country: Optional[str] = Query(None, description="Kode negara, mis. ID"),
    category: Optional[str] = Query(None, description="Nama kategori, mis. traffic / beach / city"),
    status: Optional[str] = Query(None, description="Filter status: active | offline | unknown"),
    source: Optional[str] = Query(None, description="Filter sumber: hls | embed | windy"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(24, ge=1, le=200, description="Jumlah item per halaman (maks. 200)"),
) -> PaginatedCameras:
    """Katalog utama. Contoh: ``/api/cameras?q=jakarta&status=active&page=1&limit=12``."""
    items = [
        cam
        for cam in storage.all()
        if _matches(cam, q or "", country or "", category or "", status or "", source or "")
    ]
    items.sort(key=lambda c: c.title.lower())

    total = len(items)
    pages = max(1, -(-total // limit))
    current_page = min(page, pages)
    start = (current_page - 1) * limit

    return PaginatedCameras(
        total=total,
        page=current_page,
        limit=limit,
        pages=pages,
        items=items[start : start + limit],
    )


@router.get("/random", response_model=Camera, summary="Ambil satu kamera acak")
async def random_camera() -> Camera:
    """Berguna untuk fitur 'kejutan' di frontend; mengutamakan kamera aktif."""
    cameras = [c for c in storage.all() if c.status == "active"] or storage.all()
    if not cameras:
        raise HTTPException(status_code=404, detail="Katalog masih kosong")
    return random.choice(cameras)


@router.get("/stats", summary="Statistik ringkas katalog")
async def stats() -> dict:
    """Rekap jumlah kamera per status, sumber, dan negara."""
    cameras = storage.all()
    return {
        "total": len(cameras),
        "by_status": dict(Counter(c.status for c in cameras)),
        "by_source": dict(Counter(c.source for c in cameras)),
        "by_country": Counter(
            (c.country_name or c.country or "Lainnya") for c in cameras
        ).most_common(15),
    }


@router.get("/{camera_id}", response_model=Camera, summary="Detail satu kamera")
async def get_camera(camera_id: str) -> Camera:
    """Ambil metadata lengkap satu kamera berdasarkan ID."""
    cam = storage.get(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan")
    return cam
