# SORA89 Game Demo Bot (CLI, tanpa browser)

Bot CLI untuk mengelola sesi permainan demo gratis melalui mekanisme integrasi non-browser.

## Status integrasi target

`sora89juli.com` **tidak dapat diakses secara non-browser** dari lingkungan ini:

- DNS diarahkan ke `aduankonten.id` (infrastruktur blokir Trust+ / "Internet Sehat"), bukan origin pemilik situs.
- Sertifikat TLS = block-page (`CN=internetsehatku.com`), hostname mismatch.
- `https://sora89juli.com/` → `301` → `https://internet-positif.info/` (interstitial Cloudflare managed challenge).
- Tidak ada dokumentasi API, OpenAPI/Swagger, atau endpoint publik yang terjangkau.

Kesimpulan: **tidak ada mekanisme integrasi non-browser yang sah** tersedia untuk target ini. Tidak ada upaya melewati kontrol akses atau Cloudflare challenge dilakukan.

## Solusi: simulasi lokal (fallback)

Karena integrasi langsung tidak tersedia, bot menyediakan **simulator lokal** yang merepresentasikan alur sesi demo gratis:

- State machine sesi: `DISCONNECTED` → `CONNECTED` → `DEMO_ACTIVE` → `DISCONNECTED`.
- Mock response konsisten untuk autentikasi, sesi aktif, interaksi demo, dan akhir sesi.
- Digunakan untuk menguji retry, timeout, dan penanganan error.
- Hasil simulasi **tidak** dilaporkan sebagai bukti akun target online atau permainan sungguhan berjalan.

## Struktur

```
config/        validasi konfigurasi
core/
  auth.py         autentikasi (resmi / simulasi)
  api_client.py   klien HTTP + simulator lokal
  session_manager.py  siklus hidup sesi (state machine)
  demo_runner.py  eksekusi interaksi demo dengan batas
  state_monitor.py  pemeriksaan status & hasil operasi
  logger.py       log disanitasi
cli.py            entri CLI
tests/            pengujian otomatis (unittest)
```

## Perintah CLI

```
python3 cli.py check-env         # verifikasi lingkungan & kemampuan
python3 cli.py run-demo --demo   # jalankan simulasi sesi demo (5 interaksi maksimum)
python3 -m pytest tests/         # jalankan pengujian otomatis
python3 cli.py stop              # pemberhentian & pembersihan sumber daya
```

## Batas eksekusi (aman, terkonfigurasi)

- Durasi maksimum satu sesi: 10 menit.
- Interaksi demo maksimum: 5 per sesi.
- Retry operasi aman & dapat diulang: maksimum 2 kali.
- Timeout setiap request: dikonfigurasi secara eksplisit.
- Tidak ada loop tak terbatas secara default.
- Tidak ada taruhan uang asli, deposit, withdraw, pembelian, atau klaim bonus.
- Tidak ada pemalsuan status online / heartbeat.
- Tidak ada browser atau browser automation.

## Keamanan

- Kredensial **tidak** ditanamkan dalam source code (gunakan `SORA89_USERNAME` / `SORA89_PASSWORD` dari environment).
- Password, token, cookie, secret **tidak** ditampilkan ke terminal.
- Tidak ada penyimpanan kredensial dalam Git / artefak pengujian.
- Tidak ada validasi sertifikat TLS dinonaktifkan.
- Tidak ada upaya melewati autentikasi, CAPTCHA, MFA, rate limit, atau kontrol anti-otomasi.