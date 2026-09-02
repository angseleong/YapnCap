# SecurityNewsScraper — Implementation TODO

**Status Update Convention:**
- `[ ]` — Belum dikerjakan
- `[/]` — Sedang dikerjakan (aktif)
- `[x]` — Selesai dan terverifikasi

Gunakan file ini sebagai panduan kerja utama. **Jangan mulai tahap selanjutnya sebelum tahap aktif selesai.**

---

## Phase 0 — Project Foundation

- [x] Inisialisasi virtual environment Python (`python -m venv venv`)
- [x] Buat `backend/requirements.txt` dengan semua dependensi awal
- [x] Buat `backend/config.py` — central config reader dari `.env`
- [x] Buat `backend/.env.example` — template env vars tanpa nilai sensitif
- [x] Update `.gitignore` — `.env`, `data/`, `venv/`, `*.db` tidak ter-commit
- [x] `README.md` sudah ada
- [x] Buat struktur folder sesuai `docs/ARCHITECTURE.md §3`

**Checkpoint Phase 0:** Struktur folder berdiri, `python -c "import flask, feedparser, bs4, apscheduler"` tidak error.

---

## Phase 1 — Scraper Engine

- [x] Buat `scraper/base.py` — abstract base class `BaseScraper` dengan method `fetch()` dan `fetch_full_text()`
- [x] Buat `scraper/rss_parser.py` — generic RSS parser menggunakan `feedparser`, bisa dipakai oleh semua sumber
- [x] Buat `scraper/sources/thehackernews.py` — parser untuk The Hacker News RSS
- [x] Buat `scraper/sources/bleepingcomputer.py` — parser untuk Bleeping Computer RSS
- [x] Buat `scraper/sources/krebsonsecurity.py` — parser untuk Krebs on Security RSS
- [x] Buat `scraper/sources/securityweek.py` — parser untuk SecurityWeek RSS
- [x] Buat `scraper/html_parser.py` — HTML fallback scraper (BeautifulSoup) untuk mengambil `full_text` artikel
- [x] Test manual: jalankan setiap scraper sumber dan pastikan data `title, url, published_at, summary` berhasil di-parse
- [x] Implementasi rate limiting (delay antar request) di base scraper

**Checkpoint Phase 1:** Menjalankan `python -c "from scraper.sources.bleepingcomputer import BleepingComputerScraper; print(BleepingComputerScraper().fetch()[:2])"` menghasilkan 2 artikel valid.

---

## Phase 2 — CVE Extraction Engine

- [x] Buat `extractor/cve_extractor.py` — fungsi `extract_cves(text: str) -> list[str]` dengan regex `CVE-\d{4}-\d{4,7}`
- [x] Buat `extractor/severity_classifier.py` — fungsi `classify_severity(text: str) -> str` dengan keyword-based scoring
  - [x] Definisikan keyword list untuk Critical, High, Medium
  - [x] Pastikan mengembalikan salah satu dari: `"critical"`, `"high"`, `"medium"`, `"info"`
- [x] Buat `extractor/keyword_extractor.py` — fungsi `extract_affected_software(text: str) -> list[str]` dari preset daftar software
- [x] Buat `extractor/__init__.py` — wrapper `process_article(raw_article) -> ProcessedArticle` yang memanggil ketiga extractor di atas
- [x] Test unit untuk masing-masing extractor dengan teks artikel contoh

**Checkpoint Phase 2:** Memberikan teks artikel yang menyebut `CVE-2024-12345` dan kata `critical RCE` → extractor menghasilkan CVE list yang benar dan severity `"critical"`.

---

## Phase 3 — Database Layer

- [x] Buat folder `data/` (kosong, di-gitignore)
- [x] Buat `database/models.py` — definisi tabel menggunakan SQLAlchemy ORM: `Article`, `CVE`, `ScrapeLog`
- [x] Buat `database/db.py` — koneksi database, session factory, fungsi `init_db()` untuk membuat tabel
- [x] Buat `database/migrations/init_schema.sql` — SQL schema mentah sebagai referensi / fallback
- [x] Implementasi `save_article(article)` — simpan artikel dengan pengecekan duplikat (handle `IntegrityError`)
- [x] Implementasi `save_cves(cves, article_id)` — simpan daftar CVE yang terkait ke artikel
- [x] Implementasi `log_scrape_run(source, stats)` — simpan hasil setiap scraping ke `scrape_logs`
- [x] Test: pastikan article dengan URL yang sama tidak bisa disimpan dua kali (constraint UNIQUE berfungsi)
- [x] Test: pastikan foreign key antara `cves.article_id` dan `articles.id` berfungsi benar

**Checkpoint Phase 3:** Jalankan full pipeline (scrape → extract → save) untuk satu sumber, query database menghasilkan data yang benar, running kedua kali tidak menghasilkan duplikat.

---

## Phase 4 — Scheduler & Pipeline Integration

- [x] Buat `scheduler/jobs.py` — definisi job `scrape_all_sources()` yang memanggil semua scraper, extractor, dan database save secara berurutan
- [x] Integrasi APScheduler ke `main.py` — `BackgroundScheduler` berjalan bersamaan dengan Flask
- [x] Konfigurasi interval scraping dari `.env` (`SCRAPE_INTERVAL_HOURS`)
- [x] Tambahkan logging ke setiap tahap pipeline — output ke console dan/atau file `logs/scraper.log`
- [x] Test: jalankan `python main.py`, tunggu interval pertama, verifikasi artikel baru tersimpan di DB
- [x] Implementasi `cli.py` dengan command `scrape` untuk trigger manual tanpa buka browser

**Checkpoint Phase 4:** Server berjalan, setelah 1 siklus scraping (atau dipicu manual via CLI), database terisi dengan artikel baru dari semua sumber.

---

## Phase 5 — Backend REST API (Flask)

- [x] Buat `backend/api/app.py` — Flask application factory dengan support CORS
- [x] Buat `backend/api/routes.py` — definisi semua JSON endpoint:
  - [x] `GET /api/articles` — Endpoint data artikel dengan support query params: `?source=`, `?severity=`, `?q=`, `?has_cve=`, `?page=`
  - [x] `GET /api/cves` — Endpoint data CVE dengan support query params: `?q=`, `?severity=`
  - [x] `GET /api/stats` — Endpoint untuk statistik agregat dashboard
  - [x] `POST /api/scrape` — Endpoint trigger manual scraping
- [x] Test: jalankan server Flask, request ke semua endpoint menggunakan cURL/Postman, pastikan JSON responsenya valid.

**Checkpoint Phase 5:** REST API dapat diakses di `http://localhost:5000/api/*` dan memberikan JSON response dengan struktur data yang benar.

---

## Phase 6 — Frontend Dashboard (Next.js)

- [x] Inisialisasi Next.js (`npx create-next-app@latest frontend`) dengan Tailwind CSS, TypeScript, dan App Router
- [x] Install dependencies tambahan: `lucide-react`, `date-fns`
- [x] Konfigurasi `frontend/.env.local` untuk menyimpan `NEXT_PUBLIC_API_URL`
- [x] Buat `frontend/components/ArticleCard.tsx` — komponen untuk me-render satu berita dengan badge severity
- [x] Buat `frontend/components/FilterBar.tsx` — komponen interaktif untuk filter kategori dan search bar
- [x] Buat `frontend/app/page.tsx` — Halaman dashboard utama (fetching `GET /api/articles`)
- [x] Implementasi integrasi tombol "Scrape Now" yang memanggil `POST /api/scrape`
- [x] Test: jalankan `npm run dev`, pastikan tampilan merender sempurna, state filter berfungsi, dan mengambil data asli dari Flask backend.

**Checkpoint Phase 6:** Dashboard Next.js dapat diakses di `http://localhost:3000`, interaktif, menampilkan artikel dari SQLite, dan pencarian instan bekerja.

---

## Phase 7 — Telegram Notifier

- [x] Setup Telegram Bot via @BotFather — dokumentasikan langkah-langkahnya di README
- [x] Buat `notifier/telegram.py` — fungsi `send_alert(article, cves)` yang memformat dan mengirim pesan ke Telegram
- [x] Implementasi filter sebelum kirim notifikasi:
  - [x] Cek `article.severity` apakah `>= ALERT_MIN_SEVERITY` dari `.env`
  - [x] Cek apakah judul/teks mengandung keyword dari `ALERT_KEYWORDS` di `.env`
- [x] Implementasi retry logic (3x dengan backoff) untuk request yang gagal ke Telegram API
- [x] Integrasi notifier ke pipeline di `scheduler/jobs.py` — panggil notifier setelah artikel baru disimpan
- [x] Test: publish artikel test dengan severity critical → pesan notifikasi masuk di Telegram

**Checkpoint Phase 7:** Setelah scraping menemukan artikel baru berkategori Critical, pesan Telegram terkirim dalam waktu <30 detik setelah artikel disimpan ke DB.

---

## Phase 8 — Deployment

- [x] Pastikan semua secret ada di `.env` dan tidak di-commit ke Git
- [x] Buat `Procfile` atau `render.yaml` untuk konfigurasi deployment di Render
- [x] Buat `runtime.txt` dengan versi Python yang digunakan
- [x] Test deployment di Render free tier:
  - [x] Backend API dapat diakses via public URL
  - [x] Next.js Frontend terdeploy (misal di Vercel atau Render) dan berhasil call Backend API
  - [x] Scheduler berjalan di background
  - [x] SQLite database persisten (tidak terhapus saat restart)
  - [x] Telegram notifikasi terkirim dari server backend
- [x] Update `README.md` dengan instruksi deployment lengkap

**Checkpoint Phase 8:** [SELESAI] Dashboard dapat diakses dari internet via URL publik. Tanpa membuka laptop, setelah interval waktu tertentu, artikel baru muncul di dashboard dan notifikasi Telegram terkirim.

---

## BACKLOG — "Bloomberg for Bug Hunters" (Upcoming Phases)

### Phase 9 — AI Threat Intel & Pre-computed Summary
- [x] Setup `GEMINI_API_KEY` di `config.py` dan `.env`.
- [x] Update Skema DB: Tambah kolom `ai_summary`, `ai_mitigation`, `ai_attack_vector`, `ai_shodan_dork` di tabel `articles`.
- [x] Buat `extractor/ai_analyzer.py`: Integrasi `google-genai` dengan instruksi terstruktur untuk mengekstrak data spesifik dari teks kerentanan.
- [x] Integrasi Pipeline: Panggil AI Analyzer di `scheduler/jobs.py` saat artikel baru ditemukan.
- [x] Update UI: Tambahkan *Expandable Drawer/Modal* di kartu artikel untuk menampilkan hasil ekstraksi AI secara instan.

### Phase 10 — Powerful Search & Filter
- [x] **Search by CVE / Vendor:** Modifikasi query database di `routes.py` agar pencarian bisa melacak CVE ID atau keyword vendor secara spesifik.
- [x] **Toggle Filter:** Tambahkan tombol cepat "Only with CVEs" dan "Critical Only" di UI Next.js.
- [x] **Date Filter:** Tambahkan dropdown filter waktu (Today, This Week, All Time).
- [x] **Scope Matcher (Watchlist):** Fitur untuk mendaftarkan aset target. Notifikasi diprioritaskan jika ada kerentanan di aset tersebut.

### Phase 11 — Analytics, Visualisasi Data & Terminal UI
- [x] **Bloomberg Terminal UI:** Rombak desain Next.js menjadi *dense data grid* dengan tema gelap, *glassmorphism*, dan indikator warna yang lebih mencolok.
- [x] **Top Affected Software:** Buat *Tag Cloud* atau *list* vendor yang paling banyak diserang minggu ini.
- [x] **Incident Trends Chart:** Pasang Chart.js/Recharts untuk grafik batang/garis tren kerentanan baru.
- [x] **CVE Explorer View:** Halaman khusus (`/cves`) untuk melihat daftar semua CVE beserta status eksploitasinya.
- [x] **Incident Grouping:** Gabungkan berita kerentanan yang sama dari berbagai sumber menjadi 1 insiden di UI.

### Phase 12 — Integration, Deep Intel & Export
- [x] **PoC & Exploit Radar:** Cek API GitHub atau Nuclei secara otomatis untuk melihat apakah PoC publik sudah dirilis untuk CVE terkait.
- [x] **CISA KEV & EPSS Score:** Panggil NVD API otomatis untuk menarik status eksploitasi resmi.
- [x] **Custom RSS / Webhook Out:** Buat endpoint `/api/feed.xml` agar Threat Intel ini bisa di-ingest oleh SIEM atau bot pihak ketiga.
- [x] **Weekly Report:** Auto-generate PDF/CSV laporan ancaman keamanan mingguan.
- [x] **Multi-Channel Alerts:** Tambahkan support notifikasi Discord Webhook dan Email.
