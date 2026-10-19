# CCTV Public Server

Backend server **Python (FastAPI)** untuk katalog CCTV / webcam **publik dan legal**, lengkap dengan REST API + dokumentasi Swagger otomatis + web viewer (peta interaktif & pemutar video).

> ⚠️ **Disclaimer hukum & etika**
> Tools ini hanya dirancang untuk mengindeks dan menayangkan sumber yang **memang dipublikasikan resmi oleh pemiliknya**, yaitu:
> 1. **Windy Webcams API** — webcam publik yang didaftarkan oleh pemiliknya di Windy dengan perjanjian penggunaan resmi;
> 2. **Stream HLS milik sendiri / yang Anda punya izinnya** (misalnya kamera milik instansi tempat Anda bekerja dengan izin tertulis);
> 3. **Player embed resmi** dari penyedia yang memang menyediakan widget embed.
>
> Tools ini **tidak** menyediakan, memindai, atau membobol CCTV pribadi/ilegal. Jangan gunakan untuk menayangkan kamera tanpa izin pemiliknya. Patuhi hukum setempat (termasuk UU ITE dan UU PDP di Indonesia). Risiko penyalahgunaan sepenuhnya ada pada pengguna.

---

## Fitur

- **REST API katalog** — daftar kamera dengan pencarian (nama/kota/negara), filter status online/offline, filter negara & kategori, serta paginasi.
- **Sumber Windy Webcams API v3** — sinkronisasi ribuan webcam publik resmi dari seluruh dunia (butuh API key gratis).
- **Kamera manual** — tambahkan stream HLS (`.m3u8`) milik sendiri lewat API admin atau edit file JSON langsung.
- **Web viewer siap pakai** — peta Leaflet + daftar kamera + pemutar video (HLS.js untuk stream `.m3u8`, iframe untuk player embed resmi Windy).
- **Penyimpanan file JSON** — tanpa instalasi database; katalog tersimpan di `data/cameras.json`.
- **Swagger UI otomatis** — dokumentasi interaktif di `/docs`, ReDoc di `/redoc`.
- **Proteksi admin opsional** — set `ADMIN_TOKEN` di `.env` untuk mengunci endpoint admin.
- **CORS fleksibel** — siap dipakai oleh frontend/aplikasi pihak ketiga.

## Persyaratan

- Python **3.10+** (direkomendasikan 3.11/3.12)
- Tidak butuh database, tidak butuh Docker

## Instalasi Cepat

```bash
# 1. Clone repo (atau ekstrak ZIP project ini)
git clone https://github.com/USERNAME/cctv-public-server.git
cd cctv-public-server

# 2. Salin contoh konfigurasi
cp .env.example .env

# 3. Jalankan (otomatis buat venv + install dependensi)
chmod +x run.sh
./run.sh
```

Di Windows jalankan `run.bat` (double-click atau dari Command Prompt).

Server berjalan di:

| URL | Keterangan |
|---|---|
| `http://localhost:8000/` | Web viewer (peta + pemutar) |
| `http://localhost:8000/docs` | Swagger UI — coba semua endpoint dari browser |
| `http://localhost:8000/redoc` | ReDoc — dokumentasi API alternatif |
| `http://localhost:8000/api/health` | Health check |

## Konfigurasi (.env)

| Variabel | Default | Keterangan |
|---|---|---|
| `HOST` | `0.0.0.0` | Alamat bind server |
| `PORT` | `8000` | Port server |
| `DATA_FILE` | `data/cameras.json` | Lokasi file katalog |
| `WINDY_API_KEY` | *(kosong)* | API key Windy Webcams (gratis) |
| `WINDY_LANG` | `en` | Bahasa metadata Windy (`en` pasti ada; coba `id`) |
| `ADMIN_TOKEN` | *(kosong)* | Bila diisi, endpoint `/api/admin` wajib header `X-Admin-Token` |
| `CORS_ORIGINS` | `*` | Origin yang diizinkan, pisah koma |

## Mendapatkan Windy API Key (gratis)

1. Buat akun di [windy.com](https://www.windy.com/).
2. Buka [windy.com/api](https://www.windy.com/api) → pilih **Webcams API** → **Get access key / Request API key**.
3. Isi deskripsi penggunaan (mis. *katalog webcam publik untuk riset*), tunggu persetujuan (biasanya cepat).
4. Salin key ke `.env`:
   ```
   WINDY_API_KEY=xxxxxxxxxxxxxxxx
   ```
5. Restart server, lalu sinkronkan katalog (lihat bagian berikutnya).

> Tanpa API key Windy, server tetap berfungsi penuh untuk kamera manual/HLS milik sendiri. Dua entri DEMO (`demo-hls-mux`, `demo-hls-apple`) sudah disertakan agar viewer bisa diuji segera — hapus/ganti setelah siap.

## Sinkronisasi Kamera dari Windy

**Cara A — lewat Swagger UI (paling mudah):** buka `/docs` → `POST /api/admin/sync/windy` → isi `countries=ID` (opsional) dan `max_items=100` → Execute.

**Cara B — lewat curl:**

```bash
# Semua webcam publik Windy (maks 500)
curl -X POST "http://localhost:8000/api/admin/sync/windy?max_items=200"

# Hanya webcam Indonesia
curl -X POST "http://localhost:8000/api/admin/sync/windy?countries=ID&max_items=100"

# Dengan ADMIN_TOKEN aktif
curl -X POST "http://localhost:8000/api/admin/sync/windy?countries=ID" \
     -H "X-Admin-Token: TOKENANDA"
```

**Cara C — lewat CLI script:**

```bash
python scripts/sync_windy.py --countries ID --max-items 100
```

Sinkronisasi hanya **mengganti entri ber-sumber `windy`**; kamera manual (hls/embed) Anda tetap aman.

## Menambah Kamera Manual

**Lewat API** (`POST /api/admin/cameras`):

```bash
curl -X POST http://localhost:8000/api/admin/cameras \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: TOKENANDA" \
  -d '{
    "title": "CCTV Gerbang Kantor Saya",
    "source": "hls",
    "stream_url": "https://server-anda/live/kamera1/index.m3u8",
    "city": "Surabaya",
    "region": "Jawa Timur",
    "country": "ID",
    "country_name": "Indonesia",
    "latitude": -7.2575,
    "longitude": 112.7521,
    "categories": ["office"]
  }'
```

**Lewat file:** edit `data/cameras.json` lalu restart server. Skema field lengkap ada di `app/models.py` atau di Swagger (`/docs` → schema `Camera`).

## Referensi API

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/api/health` | Status server + jumlah kamera |
| GET | `/api/cameras` | Daftar kamera — param: `q, country, category, status, source, page, limit` |
| GET | `/api/cameras/{id}` | Detail satu kamera |
| GET | `/api/cameras/random` | Satu kamera acak (utamakan yang online) |
| GET | `/api/cameras/stats` | Statistik katalog per status/sumber/negara |
| POST | `/api/admin/cameras` | Tambah kamera manual |
| PUT | `/api/admin/cameras/{id}` | Perbarui kamera |
| DELETE | `/api/admin/cameras/{id}` | Hapus kamera |
| POST | `/api/admin/sync/windy` | Sinkronisasi dari Windy — param: `countries, max_items` |

Contoh respons `GET /api/cameras?limit=1`:

```json
{
  "total": 2,
  "page": 1,
  "limit": 1,
  "pages": 2,
  "items": [
    {
      "id": "demo-hls-mux",
      "title": "DEMO 1 - Stream Uji HLS (ganti dengan kamera Anda)",
      "source": "hls",
      "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
      "city": "Jakarta",
      "country": "ID",
      "country_name": "Indonesia",
      "latitude": -6.2,
      "longitude": 106.816666,
      "categories": ["demo", "test"],
      "status": "active",
      "last_updated": "2026-10-19T00:00:00Z"
    }
  ]
}
```

## Struktur Proyek

```
cctv-public-server/
├── app/
│   ├── main.py              # Entry point FastAPI + mount static + health
│   ├── config.py            # Konfigurasi via .env
│   ├── models.py            # Model Pydantic (Camera, paginasi)
│   ├── storage.py           # Penyimpanan JSON (load/save/query)
│   ├── routers/
│   │   ├── cameras.py       # Endpoint publik katalog
│   │   └── admin.py         # Endpoint admin (CRUD + sync Windy)
│   ├── services/
│   │   └── windy.py         # Klien Windy Webcams API v3
│   └── static/
│       └── index.html       # Web viewer (Leaflet + HLS.js)
├── data/
│   └── cameras.json         # Katalog kamera (seed 2 entri demo)
├── scripts/
│   ├── sync_windy.py        # CLI sinkronisasi Windy
│   └── github_push.sh       # Helper push pertama ke GitHub (pakai PAT)
├── requirements.txt
├── .env.example
├── run.sh / run.bat
├── LICENSE (MIT)
└── README.md
```

## Menjalankan Sebagai Layanan (opsional, VPS Linux)

Contoh unit systemd sederhana:

```ini
# /etc/systemd/system/cctv-public.service
[Unit]
Description=CCTV Public Server
After=network.target

[Service]
WorkingDirectory=/opt/cctv-public-server
ExecStart=/opt/cctv-public-server/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now cctv-public
```

Untuk produksi, taruh reverse proxy (Nginx/Caddy) di depan dan aktifkan HTTPS.

## Publish ke GitHub

Script helper sudah disiapkan — token hanya dipakai sesaat lalu dibersihkan dari konfigurasi git:

```bash
# 1. Buat repo kosong di github.com (tanpa README Lisensi bawaan)
# 2. Buat Personal Access Token (classic, scope "repo"):
#    GitHub > Settings > Developer settings > Personal access tokens
# 3. Jalankan:
./scripts/github_push.sh https://github.com/USERNAME/cctv-public-server.git ghp_TOKENANDA
```

## Roadmap

- [ ] Health check otomatis per kamera (status online/offline real-time)
- [ ] Endpoint GeoJSON untuk integrasi peta pihak ketiga
- [ ] Proxy HLS dengan rewrite URL (menyembunyikan URL asli)
- [ ] Rate limiting + API key untuk konsumen API
- [ ] Dockerfile & docker-compose

## Lisensi

[MIT](LICENSE) — bebas dipakai, dimodifikasi, dan didistribusikan. Gunakan dengan tanggung jawab.
