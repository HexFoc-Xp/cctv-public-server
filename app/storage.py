"""Penyimpanan katalog kamera berbasis file JSON (tanpa database).

Format file (data/cameras.json):
    {
      "version": 1,
      "updated_at": "2026-10-19T00:00:00+00:00",
      "cameras": [ { ...Camera... }, ... ]
    }
"""

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models import Camera, CameraCreate

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Ubah teks menjadi slug sederhana untuk ID kamera."""
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:60] or "camera"


class JsonStorage:
    """Katalog kamera yang disimpan sebagai satu file JSON.

    Aman dipakai dari beberapa request karena semua operasi kunci
    internal dilindungi RLock.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        self._cameras: dict[str, Camera] = {}

    # ------------------------------------------------------------------ I/O
    def load(self) -> None:
        """Muat katalog dari file JSON (jika ada). Entri rusak dilewati."""
        with self._lock:
            self._cameras = {}
            if not self.path.exists():
                return
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return
            items = raw.get("cameras", []) if isinstance(raw, dict) else raw
            for item in items:
                try:
                    cam = Camera(**item)
                except Exception:  # noqa: BLE001 — jangan biarkan 1 entri rusak mematikan server
                    continue
                self._cameras[cam.id] = cam

    def save(self) -> None:
        """Simpan seluruh katalog ke file JSON (tulis atomik via .tmp)."""
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "cameras": [cam.model_dump(mode="json") for cam in self._cameras.values()],
            }
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)

    # -------------------------------------------------------------- Operasi
    def all(self) -> list[Camera]:
        """Kembalikan salinan daftar seluruh kamera."""
        with self._lock:
            return list(self._cameras.values())

    def count(self) -> int:
        """Jumlah kamera dalam katalog."""
        with self._lock:
            return len(self._cameras)

    def get(self, camera_id: str) -> Optional[Camera]:
        """Ambil satu kamera berdasarkan ID."""
        with self._lock:
            return self._cameras.get(camera_id)

    def add(self, payload: CameraCreate) -> Camera:
        """Tambah kamera baru; ID dibuat otomatis dari judul bila kosong."""
        with self._lock:
            camera_id = payload.id or f"manual-{slugify(payload.title)}"
            if camera_id in self._cameras:
                camera_id = f"{camera_id}-{uuid.uuid4().hex[:6]}"
            camera = Camera(
                **payload.model_dump(exclude={"id"}),
                id=camera_id,
                status="active" if payload.source == "hls" else "unknown",
                last_updated=datetime.now(timezone.utc),
            )
            self._cameras[camera_id] = camera
            self.save()
            return camera

    def update(self, camera_id: str, payload: CameraCreate) -> Optional[Camera]:
        """Perbarui data kamera (ID & status tetap)."""
        with self._lock:
            existing = self._cameras.get(camera_id)
            if existing is None:
                return None
            updated = Camera(
                **payload.model_dump(exclude={"id"}),
                id=camera_id,
                status=existing.status,
                last_updated=datetime.now(timezone.utc),
            )
            self._cameras[camera_id] = updated
            self.save()
            return updated

    def delete(self, camera_id: str) -> bool:
        """Hapus kamera; kembalikan False bila ID tidak ada."""
        with self._lock:
            if camera_id not in self._cameras:
                return False
            del self._cameras[camera_id]
            self.save()
            return True

    def replace_source(self, source: str, cameras: list[Camera]) -> None:
        """Ganti semua kamera dari satu sumber (mis. 'windy') dengan daftar baru.

        Kamera dari sumber lain (manual/demo) tetap dipertahankan.
        """
        with self._lock:
            kept = {cid: cam for cid, cam in self._cameras.items() if cam.source != source}
            for cam in cameras:
                kept[cam.id] = cam
            self._cameras = kept
            self.save()


# Instance tunggal yang dipakai seluruh aplikasi (lokasi file diatur via .env).
storage = JsonStorage(settings.data_file)
