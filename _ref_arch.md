# SecurityNewsScraper — System Architecture

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-08-24

---

## 1. System Overview

SecurityNewsScraper terdiri dari dua lapisan utama yang bekerja secara independen namun saling terhubung melalui database:

1. **Backend Engine (Python):** Scraper, CVE extractor, scheduler, dan Telegram notifier. Semua berjalan di server/laptop sebagai proses Python.
2. **Web Interface (Flask + HTML/CSS/JS):** Dashboard yang membaca data dari database dan menyajikannya ke pengguna di browser.

---

## 2. High-Level Data Flow

```
[ RSS Feed / HTML Website ]
          │
          ▼
┌─────────────────────────┐
│     Scraper Engine      │  ← requests, feedparser, BeautifulSoup4
│  (fetch_rss / fetch_html)│
└──────────┬──────────────┘
           │  raw article (title, url, date, content)
           ▼
┌─────────────────────────┐
│   CVE Extraction Engine │  ← regex + keyword classifier
│  (extract_cves,         │
│   classify_severity)    │
└──────────┬──────────────┘
           │  structured article + CVE list + severity
           ▼
┌─────────────────────────┐
│   Database Layer        │  ← sqlite3 / SQLAlchemy
│   (SQLite)              │
│   articles + cves tables│
└──────────┬──────────────┘
           │
┌─────────┐  ┌──────────────┐
│ Next.js │  │  Telegram    │
│ Frontend│  │  Notifier    │
│(React)  │  │  (Bot API)   │
└─────────┘  └──────────────┘
     ▲
     │ API Request
┌─────────────┐
│  Flask REST │
│    API      │
└─────────────┘
┌─────────────┐
│  APScheduler│  ← runs scraper every N hours automatically
└─────────────┘
```

---

## 3. Project Structure (Monorepo)

```
SecurityNewsScraper/
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DESIGN.md
│   └── TODO.md
├── backend/                   ← Python REST API & Engine
│   ├── scraper/
│   │   ├── sources/
│   │   ├── base.py
│   │   ├── rss_parser.py
│   │   └── html_parser.py
│   ├── extractor/
│   │   ├── cve_extractor.py
│   │   ├── severity_classifier.py
│   │   └── keyword_extractor.py
│   ├── database/
│   │   ├── models.py
│   │   ├── db.py
│   │   └── migrations/
│   ├── scheduler/
│   │   └── jobs.py
│   ├── notifier/
│   │   └── telegram.py
│   ├── api/                   ← Flask REST API Endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── data/                  ← SQLite database
│   ├── config.py
│   ├── main.py                ← Runs Flask API + Scheduler
│   ├── requirements.txt
│   └── .env.example
├── frontend/                  ← Next.js React UI
│   ├── src/
│   │   ├── app/               ← Next.js App Router (pages & layouts)
│   │   ├── components/        ← React Components (UI, Cards, Badges)
│   │   ├── hooks/             ← Custom React hooks for data fetching
│   │   └── lib/               ← Utility functions
│   ├── public/
│   ├── tailwind.config.ts
│   ├── package.json
│   └── .env.local.example
├── cli.py                     ← Command-line interface
├── AGENTS.md
└── README.md
```

---

## 4. Database Schema

Database menggunakan **SQLite** (file lokal: `data/security_news.db`).

### 4.1 Tabel `articles`

| Kolom | Tipe | Constraint | Deskripsi |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `source` | TEXT | NOT NULL | Nama portal (misal: `"bleepingcomputer"`) |
| `title` | TEXT | NOT NULL | Judul artikel |
| `url` | TEXT | NOT NULL, UNIQUE | URL artikel — basis deduplication |
| `published_at` | DATETIME | | Tanggal publikasi dari feed/sumber |
| `summary` | TEXT | | Ringkasan/excerpt artikel |
| `full_text` | TEXT | | Teks lengkap artikel (jika berhasil diambil) |
| `severity` | TEXT | | `critical` / `high` / `medium` / `info` |
| `has_cve` | BOOLEAN | DEFAULT 0 | Shortcut flag: apakah ada CVE di artikel ini? |
| `scraped_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Waktu artikel disimpan ke DB |

### 4.2 Tabel `cves`

| Kolom | Tipe | Constraint | Deskripsi |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `cve_id` | TEXT | NOT NULL | Misal: `CVE-2024-12345` |
| `article_id` | INTEGER | FOREIGN KEY → articles.id | Artikel yang menyebutkan CVE ini |
| `severity_hint` | TEXT | | Keparahan yang diestimasikan dari konteks artikel |
| `affected_software` | TEXT | | Software/vendor terdampak (jika terdeteksi) |
| `cvss_score` | REAL | | Skor CVSS jika disebut eksplisit di artikel |

### 4.3 Tabel `scrape_logs`

| Kolom | Tipe | Constraint | Deskripsi |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `source` | TEXT | NOT NULL | Nama portal yang di-scrape |
| `started_at` | DATETIME | | Waktu mulai scraping |
| `finished_at` | DATETIME | | Waktu selesai scraping |
| `articles_found` | INTEGER | | Total artikel ditemukan di feed |
| `articles_new` | INTEGER | | Artikel baru yang berhasil disimpan |
| `articles_skipped` | INTEGER | | Artikel yang dilewati (duplikat) |
| `status` | TEXT | | `success` / `failed` |
| `error_message` | TEXT | | Pesan error jika gagal |

### 4.4 Relasi Antar Tabel

```
articles (1) ──────── (N) cves
    └── id ◄── article_id
```

---

## 5. Component Details

### 5.1 Scraper Engine

Setiap sumber berita diimplementasikan sebagai kelas yang mewarisi `BaseScraper`:

```python
# Kontrak yang harus dipenuhi setiap scraper sumber
class BaseScraper:
    source_name: str       # Identifier unik sumber
    feed_url: str          # URL RSS feed
    
    def fetch(self) -> list[RawArticle]:
        """Ambil artikel terbaru dari sumber ini."""
        ...
    
    def fetch_full_text(self, url: str) -> str:
        """Ambil teks lengkap dari URL artikel (opsional)."""
        ...
```

**RawArticle** adalah dataclass sederhana: `{ title, url, published_at, summary, source }`.

### 5.2 CVE Extraction Engine

Tiga fungsi utama yang bekerja secara berurutan pada setiap artikel:

1. **`extract_cves(text)`** — Jalankan regex `CVE-\d{4}-\d{4,7}` pada judul + ringkasan + teks penuh. Kembalikan list CVE ID unik yang ditemukan.
2. **`classify_severity(text)`** — Scan teks untuk kata kunci yang menentukan keparahan:
   - **Critical:** `zero-day`, `0-day`, `actively exploited`, `rce`, `remote code execution`, `cvss 9`, `cvss 10`, `critical`
   - **High:** `high severity`, `privilege escalation`, `authentication bypass`, `cvss 7`, `cvss 8`
   - **Medium:** `medium severity`, `denial of service`, `dos`, `information disclosure`
   - **Info:** default jika tidak ada kata kunci di atas
3. **`extract_affected_software(text)`** — Cari nama software/vendor dari daftar preset (Windows, Linux, macOS, Android, iOS, Apache, Nginx, Cisco, Fortinet, Chrome, Firefox, dll.).

### 5.3 Scheduler

APScheduler dikonfigurasi dalam mode `BackgroundScheduler` sehingga berjalan di thread terpisah tanpa memblokir Flask server:

```
Job: scrape_all_sources()
  ├── Interval: setiap 6 jam (dapat dikonfigurasi via SCRAPE_INTERVAL_HOURS di .env)
  ├── Misfire grace: 30 menit (jika server sempat mati, job dijalankan saat kembali online)
  └── Job store: memory (tidak persisten antar restart — restart akan reset jadwal)
```

### 5.4 Telegram Notifier

Menggunakan library `python-telegram-bot`. Mengirim pesan ke satu `CHAT_ID` yang dikonfigurasi.

**Trigger kondisi notifikasi:**
- Artikel baru dengan `severity == "critical"` atau `severity == "high"`.
- Artikel yang menyebut salah satu keyword dari `ALERT_KEYWORDS` di `.env` (misal: `"Windows Server, OpenSSL, VMware"`).

**Format pesan Telegram:**
```
🔴 [CRITICAL] Judul Artikel

📰 Sumber: Bleeping Computer
📅 Tanggal: 2024-01-15
🔗 Link: https://...

🛡️ CVE Terdeteksi: CVE-2024-1234, CVE-2024-5678
💻 Software Terdampak: Windows Server, IIS
```

### 5.5 Frontend Dashboard (Next.js)

Next.js dan React digunakan sebagai frontend SPA (Single Page Application) yang sangat interaktif dan terstruktur dalam beberapa halaman (Routing):
- **`/` (Landing Page):** Halaman pembuka dengan desain minimalis untuk menyambut pengguna.
- **`/radar` (Live Threat Feed):** Halaman utama; mengonsumsi data via HTTP GET ke Flask REST API (`/api/articles`). Filter state dikelola di client (React state).
- **`/cves` (CVE Explorer):** Mesin pencari khusus kerentanan.
- **`/analytics` (Threat Trends):** Menampilkan visualisasi data (grafik/chart) dari statistik ancaman.
- **`/watchlist` (Scope & Settings):** Tempat konfigurasi target aset.

**Detail Teknis Frontend:**
- Mengonsumsi data via HTTP GET ke Flask REST API (`/api/articles`, `/api/cves`, `/api/stats`).
- Menangani request POST ke `/api/scrape` melalui tombol "Scrape Now" yang akan mengubah UI ke state "Loading" secara dinamis.
- Menggunakan Tailwind CSS (Neon Design System) untuk styling cepat dan modern, serta Lucide React untuk ikon.

---

## 6. Configuration

Semua konfigurasi sensitif disimpan di file `.env` (tidak di-commit ke Git):

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Scraping Settings
SCRAPE_INTERVAL_HOURS=6
REQUEST_TIMEOUT_SECONDS=15
REQUEST_DELAY_SECONDS=2        # Delay antara request ke satu sumber (rate limiting)

# Alert Rules
ALERT_KEYWORDS=Windows Server,OpenSSL,Linux Kernel,Cisco IOS
ALERT_MIN_SEVERITY=high        # Minimum severity untuk notifikasi: critical / high / medium

# Database
DATABASE_PATH=data/security_news.db

# Flask
FLASK_SECRET_KEY=your_random_secret_key
FLASK_DEBUG=false
PORT=5000
```

---

## 7. Deployment Architecture

### Development (Lokal)
```
Laptop 
 ├─ Terminal 1: python backend/main.py → Flask REST API di localhost:5000 + APScheduler
 └─ Terminal 2: npm run dev di frontend/ → Next.js Dev Server di localhost:3000
```

### Production
```
Server 1 (Backend API + Scraper)
  └→ python main.py
       ├→ Flask REST API
       ├→ APScheduler
       └→ SQLite file (persisten)
            └→ Telegram Bot API

Server 2 / CDN (Frontend Vercel/Render)
  └→ Next.js Production Build (mengonsumsi URL dari Server 1)
```

**Catatan deployment:** SQLite tidak cocok untuk deployment yang menggunakan filesystem ephemeral (seperti Heroku free tier). Gunakan Render (persistent disk) atau PythonAnywhere (filesystem persisten) agar database tidak terhapus saat server restart.

---

## 8. Error Handling Strategy

| Skenario | Penanganan |
|---|---|
| Request ke sumber berita timeout/gagal | `try/except`, catat ke `scrape_logs` dengan status `failed`, lanjut ke sumber berikutnya |
| Artikel sudah ada di database (duplikat) | SQLite `UNIQUE` constraint menolak insert — tangkap `IntegrityError`, catat sebagai `skipped` |
| Telegram gagal kirim | Retry 3x dengan backoff 5s, jika masih gagal log error dan lanjut |
| RSS feed tidak valid / malformed XML | `feedparser` menangani sebagian besar kasus ini dengan graceful parsing |
| CVE regex tidak menemukan apa pun | Artikel tetap disimpan dengan `has_cve = False` dan `severity = "info"` |

---

## 9. Tech Stack Summary

| Komponen | Teknologi | Versi Target |
|---|---|---|
| Language | Python | 3.11+ |
| HTTP Client | `requests` | latest |
| RSS Parser | `feedparser` | latest |
| HTML Parser | `beautifulsoup4` + `lxml` | latest |
| Database | SQLite (built-in) + `SQLAlchemy` | SQLAlchemy 2.x |
| Web API | `Flask` | 3.x |
| Scheduler | `APScheduler` | 3.x |
| Telegram | `python-telegram-bot` | 20.x (async) |
| Config | `python-dotenv` | latest |
| Frontend Core | `Next.js` + `React` | 14/15 |
| Frontend Style | `Tailwind CSS` | v3/v4 |
