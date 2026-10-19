"""Konfigurasi aplikasi via environment variables / file .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_list(key: str, default: str = "*") -> list[str]:
    """Ambil nilai list dipisah koma dari environment."""
    raw = os.getenv(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    """Kumpulan pengaturan yang dipakai di seluruh aplikasi."""

    def __init__(self) -> None:
        self.app_name: str = "CCTV Public Server"
        self.version: str = "1.0.0"

        # Server
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))

        # Penyimpanan katalog (file JSON)
        self.data_file: Path = Path(
            os.getenv("DATA_FILE", str(BASE_DIR / "data" / "cameras.json"))
        )

        # Direktori file statis (web viewer)
        self.static_dir: Path = BASE_DIR / "app" / "static"

        # Windy Webcams API (https://www.windy.com/api)
        self.windy_api_key: str = os.getenv("WINDY_API_KEY", "")
        self.windy_base_url: str = "https://api.windy.com/webcams/api/v3/webcams"
        self.windy_lang: str = os.getenv("WINDY_LANG", "en")

        # Token admin opsional untuk endpoint /api/admin (header X-Admin-Token)
        self.admin_token: str = os.getenv("ADMIN_TOKEN", "")

        # CORS: "*" atau daftar origin dipisah koma
        self.cors_origins: list[str] = _get_list("CORS_ORIGINS", "*")


settings = Settings()
