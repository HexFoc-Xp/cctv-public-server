"""Model data Pydantic untuk katalog kamera.

Kompatibel dengan pydantic v1 DAN v2:
- v2 dipakai di Linux/Windows (requirements.txt)
- v1 dipakai di Termux/Android (requirements-termux.txt) karena v2
  membutuhkan pydantic-core (Rust) yang menyulitkan instalasi di HP.
"""

import json
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

CameraSource = Literal["hls", "embed", "windy"]
CameraStatus = Literal["active", "offline", "unknown"]


class CameraBase(BaseModel):
    """Field dasar yang berlaku untuk semua kamera."""

    title: str = Field(..., min_length=1, max_length=200, description="Nama kamera yang tampil di katalog")
    source: CameraSource = Field(
        ...,
        description=(
            "Jenis sumber: 'hls' (stream .m3u8 milik sendiri/berizin), "
            "'embed' (player iframe pihak resmi), 'windy' (webcam terdaftar Windy)"
        ),
    )
    stream_url: Optional[str] = Field(None, description="URL stream HLS (.m3u8), wajib jika source=hls")
    embed_url: Optional[str] = Field(None, description="URL player embed (iframe), untuk source=embed/windy")
    page_url: Optional[str] = Field(None, description="URL halaman asli kamera (opsional)")
    city: Optional[str] = Field(None, description="Kota lokasi kamera")
    region: Optional[str] = Field(None, description="Provinsi/wilayah kamera")
    country: Optional[str] = Field(None, description="Kode negara ISO 3166-1 alpha-2, mis. ID")
    country_name: Optional[str] = Field(None, description="Nama negara, mis. Indonesia")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Lintang untuk tampil di peta")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Bujur untuk tampil di peta")
    categories: list[str] = Field(default_factory=list, description="Daftar kategori, mis. ['traffic']")
    thumbnail: Optional[str] = Field(None, description="URL gambar thumbnail kamera")


class Camera(CameraBase):
    """Kamera lengkap dengan identitas dan status."""

    id: str = Field(..., min_length=1, max_length=100, description="ID unik kamera, mis. windy-123abc / manual-slug")
    status: CameraStatus = Field("unknown", description="Status kamera: active | offline | unknown")
    last_updated: Optional[datetime] = Field(None, description="Waktu entri terakhir diperbarui (UTC)")


class CameraCreate(CameraBase):
    """Payload penambahan/perubahan kamera (id kosong = dibuat otomatis)."""

    id: Optional[str] = Field(None, min_length=1, max_length=100, description="ID kustom (opsional)")


class PaginatedCameras(BaseModel):
    """Hasil daftar kamera dengan paginasi."""

    total: int = Field(..., description="Total seluruh hasil setelah filter")
    page: int = Field(..., description="Halaman saat ini")
    limit: int = Field(..., description="Jumlah item per halaman")
    pages: int = Field(..., description="Total halaman")
    items: list[Camera] = Field(..., description="Daftar kamera pada halaman ini")


def dump_model(model: BaseModel, exclude: Optional[set] = None) -> dict:
    """Serialisasi model pydantic ke dict yang JSON-safe (v1 & v2).

    - pydantic v2 : model_dump(mode="json") — datetime dsb. otomatis diubah.
    - pydantic v1 : .json(exclude=...) — sudah JSON-safe, parse balik ke dict.
    """
    if hasattr(model, "model_dump"):  # pydantic v2
        return model.model_dump(mode="json", exclude=exclude)
    return json.loads(model.json(exclude=exclude))  # pydantic v1
