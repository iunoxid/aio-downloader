LINK BOT https://t.me/aio_downloaders_bot

AIO Downloader Telegram Bot

- Bot menerima link dari
  - TikTok,
  - Facebook,
  - Instagram,
  - Threads,
  - Douyin, dan
  - YouTube;


- Memanggil API downloader lalu mengirim media ke pengguna.Audio (MP3) tidak dikirim otomatis; tersedia tombol inline "Download MP3" per item.

Fitur
- Deteksi platform dari hostname/path (TikTok, Douyin, Instagram, Threads, Facebook, YouTube).
- Validasi URL dan pesan contoh URL yang didukung.
- Endpoint AIO diatur melalui file `config.yml` (lihat `config.yml.example`).
  - Sumber API: layanan downloader dari pitucode.com (contoh default: https://api.pitucode.com/downloader/aio).
- Parsing `result.medias[]` (type, url, extension, quality, data_size, duration) sesuai contoh di "contoh.txt"/`yt.txt`.
- Video: kirim 1 video kualitas terbaik sebagai hasil utama (prioritas kualitas dan prefer muxed/beraudio). Jika terlalu besar/gagal, kirim ringkasan + tombol.
- Gambar: TikTok photo mode dikirim sebagai album; platform lain dikirim satu per satu; ringkasan muncul setelah gambar.
- Audio: tidak dikirim otomatis. Tombol "Download MP3" memicu unduh dan kirim sebagai audio.
- Batas ukuran `MAX_UPLOAD_TO_TELEGRAM_BYTES`; jika terlampaui, kirim link langsung.
- Concurrency per user (default 3) dan dedup callback MP3.
- Pesan "Sedang memproses..." otomatis dihapus setelah hasil terkirim; bot juga menambahkan reaction emoji (best-effort) di pesan user.
- Logging jelas (endpoint, param, fallback, error).

Environment variables
- `TELEGRAM_BOT_TOKEN` — token bot Telegram.
- `DOWNLOADER_API_KEY` — opsional jika API memerlukan.
- Batas dan performa:
  - `MAX_UPLOAD_TO_TELEGRAM_BYTES` — default 52428800 (50 MB)
  - `MAX_CONCURRENT_PER_USER` — default 3
  - `HTTP_CONNECT_TIMEOUT`, `HTTP_READ_TIMEOUT`, `HTTP_TOTAL_TIMEOUT` — default 10/60/120 detik

Konfigurasi endpoint (config.yml)
- Salin `config.yml.example` ke `config.yml` lalu sesuaikan:

```
endpoints:
  default: https://api.pitucode.com/downloader/aio
  per_platform:
    # douyin: https://api.pitucode.com/douyin-downloader
    # youtube: https://api.pitucode.com/downloader/aio
```

Struktur direktori
- `bot/` — core modules (config, context, state, downloader_client, media_utils, media_normalizer, platforms, ui, app, main)
- `handlers/` — Telegram handlers (/start, callback MP3, text router, flow utils)
- `processors/` — per‑platform processors (tiktok, instagram, facebook, threads, douyin, youtube, generic)
- `main.py` — entrypoint

Menjalankan
- Python 3.10+
- `pip install -r requirements.txt`
- Salin `.env.example` ke `.env` lalu isi variabel.
- Salin `config.yml.example` ke `config.yml` bila ingin mengganti endpoint default/per-platform.
- `python main.py`
- Opsional: aktifkan rate limiter PTB — `pip install "python-telegram-bot[rate-limiter]==21.6"`

Cara pakai
- Kirim URL ke bot. Contoh:
  - https://www.tiktok.com/@user/video/123
  - https://www.facebook.com/watch/?v=123
  - https://www.instagram.com/p/POST_ID/
  - https://www.threads.net/@user/post/123
  - https://www.douyin.com/video/123
  - https://www.youtube.com/watch?v=VIDEO_ID
- Bot membalas "Sedang memproses..." (dan menambahkan reaction), lalu menghapusnya setelah hasil terkirim.
- Bot mengirim:
  - Video: 1 video terbaik + tombol
  - Gambar: album (TikTok) atau per‑foto (lainnya)
  - Audio: tombol "Download MP3" (tanpa auto‑upload)

Catatan & batasan
- Hormati hak cipta dan ToS platform. Gunakan untuk konten yang Anda miliki haknya.
- Batas upload Telegram dapat berbeda per lingkungan; `MAX_UPLOAD_TO_TELEGRAM_BYTES` adalah fallback internal.
- Jika API rate-limited/timeout: bot membalas "Maaf, server downloader sedang sibuk. Coba lagi nanti."

