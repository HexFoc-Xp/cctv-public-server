"""Titik masuk aplikasi: FastAPI + router API + web viewer statis.

Jalankan server:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import admin, cameras
from app.storage import storage

DESCRIPTION = """
API katalog untuk CCTV / webcam **publik dan legal**.

Sumber data yang didukung:
- **Windy Webcams API** — webcam publik resmi yang didaftarkan pemiliknya di Windy.
- **Stream HLS milik sendiri** — kamera yang Anda punya izin untuk menyiarkannya.
- **Player embed resmi** — iframe dari penyedia yang memang menyediakan widget embed.

⚠️ Etika & hukum: gunakan hanya untuk kamera publik resmi/berizin.
Jangan gunakan untuk kamera pribadi atau feed tanpa izin pemiliknya.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Muat katalog dari file JSON saat server mulai."""
    storage.load()
    yield


app = FastAPI(
    title=settings.app_name,
    description=DESCRIPTION,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health", tags=["Sistem"], summary="Cek kesehatan server")
async def health() -> dict:
    """Status server + jumlah kamera dalam katalog."""
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "cameras": storage.count(),
        "version": settings.version,
    }


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Halaman utama → arahkan ke web viewer."""
    return RedirectResponse(url="/static/index.html")


# Web viewer (peta + pemutar video) dilayani dari /static.
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
