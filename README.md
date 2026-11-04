# Celeslib Honor of Kings: Ace Patcher (`v1.0.0` — Game Build `1.4.12`)

<p align="center">
  <img src="assets/branding/celeslib_logo_64.png" alt="Celeslib Logo" width="64" height="64" />
</p>

Aplikasi pemasang *patch* lokalisasi resmi **Celeslib** untuk gim PC **Honor of Kings: Ace (`WXQ.exe`)**, dibangun dengan antarmuka native Windows x86-64 **Single-Page Monochrome Obsidian UI** (`980 × 620`, `#090909` canvas, aksen kontras tinggi `#FFFFFF` / `#000000`, border presisi `1px #333333`), pergantian bahasa UI real-time (**`🌐 UI: Indonesia | English`**), dan mode patch game fleksibel (**`🎯 Mode: ID Hybrid | EN Full`**).

---

## Pratinjau Antarmuka Single-Page Celeslib

| Mode Bahasa Indonesia (`UI: Indonesia` • `Mode: ID Hybrid`) | Mode Bahasa Inggris (`UI: English` • `Mode: EN Full`) |
| :---: | :---: |
| ![Celeslib Patcher ID](assets/previews/celeslib_patcher_id.png) | ![Celeslib Patcher EN](assets/previews/celeslib_patcher_en.png) |

---

## Fitur Utama

1. **Antarmuka Native Windows Celeslib Single-Page Monochrome Obsidian (`Win32` + `GDI+` + `DWM Frameless Dark Mode`):**
   - Mengusung sistem desain visual *Monochrome Obsidian* murni (`#090909` main canvas, `#0D0D0D` cards & toolbars, `#050505` input boxes/tracks, `1px solid #333333` crisp borders, tombol utama & toggle aktif Putih Solid `#FFFFFF` dengan teks Hitam Tebal `#000000`).
   - Seluruh kontrol dan diagnostik berada di satu layar tunggal responsif (**Single-Page `980 × 620`**, tanpa tab tersembunyi).
   - Custom dark titlebar frameless dengan logo 4-pointed star resmi Celeslib, badge versi `v1.0.0`, target game badge `Game Build 1.4.12`, dan kontrol jendela (`—`, `□`, `×`).
   - **Connected 3-Column Configuration Strip:**
     - **Kolom 1:** Jalur Direktori Game (HOK: Ace) dengan input path box dan tombol mini `[Auto-Detect]` serta `[Pilih Folder / Browse]`.
     - **Kolom 2:** Mode Bahasa Patch dengan segmented pill control (`[ID Hybrid]` / `[EN Full]`).
     - **Kolom 3:** Bahasa UI Antarmuka dengan segmented pill control (`[Indonesia]` / `[English]`).
   - **Unified Action Toolbar:** Menggabungkan aksi PC (`▶ Pasang Patch`, `↺ Pulihkan`, `✓ Periksa`) dan aksi Android USB (`📱 Pindai USB`, `⚡ Patch APK`, `↺ Pulihkan APK`) dalam satu bilah aksi terpadu, lengkap dengan tombol `[🗑 Clear]`.
   - **Monaco/Executor-Style Diagnostic Console:** Konsol diagnostik monospace bernomor baris (*gutter line numbers*) dengan status pill, pewarnaan log sintetis, dan minimap rail visual di sisi kanan.

2. **Dua Mode Terjemahan Game (`🎯 Mode Patch`):**
   - **`ID Hybrid Gameplay` (Default):** Menerjemahkan seluruh deskripsi efek gameplay, kartu hero (*On Play*, *Sacrifice*, *Awaken*), skill aktif/pasif, talent cards, dan deskripsi kontestan ke Bahasa Indonesia, sementara nama hero/skill/talent dan sistem menu non-gameplay tetap dalam Bahasa Inggris standar.
   - **`EN Full English`:** Menerjemahkan 100% berkas ke Bahasa Inggris resmi (memulihkan gameplay ke English dan melengkapi string Mandarin yang belum diterjemahkan).
   - Penggantian mode otomatis melakukan *pre-install restore* dari cadangan `originals/` tanpa resiko tumpang tindih terjemahan.

3. **Pergantian Bahasa UI Real-Time (`🌐 Bahasa UI`):**
   - Segmented toggle **`[Indonesia | English]`** untuk berpindah antara Bahasa Indonesia dan English secara instan.
   - Laporan status worker `result.json` otomatis disajikan sesuai bahasa UI yang dipilih.

4. **Zero CPDD Branding Leakage:**
   - Seluruh biner luar, resources Windows PE, ikon multi-resolusi `.ico` (`16x16`..`256x256`), dan logo RGBA pre-decoded pre-rendered 100% menggunakan identitas resmi Celeslib tanpa kebocoran aset legacy (`0` kemunculan CPDD).

5. **Integritas Biner & Transparansi Sertifikat:**
   - Penjaga digest SHA-256 64-karakter untuk memvalidasi integritas `ace-worker.exe` sebelum dieksekusi via Windows CryptoAPI.
   - **Forensik Sertifikat:** Patcher beroperasi **100% offline** tanpa transmisi jaringan. Berkas `certifi/cacert.pem` yang ada di dalam PyInstaller hanya sertifikat Mozilla Root CA bawaan dependensi upstream Python, dan modul X.509 `cryptography` hanya digunakan secara lokal ketika menandatangani ulang APK Android pada mode USB.

---

## Cara Penggunaan (Windows 10 / 11 64-bit)

1. **Tutup gim `Honor of Kings: Ace` (`WXQ.exe`)** dan *launcher* sepenuhnya sebelum menjalankan *patcher*.
2. Unduh berkas rilis **`Celeslib-HoK-Ace-Patcher-v1.0.0.exe`** (atau salinan kompatibilitas `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`) dan **`SHA256SUMS.txt`** dari halaman [**GitHub Releases (`v1.0.0-celeslib`)**](https://github.com/voseu/acepatchindo/releases/tag/v1.0.0-celeslib).
3. Jalankan `Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (klik **More info -> Run anyway** apabila muncul peringatan Windows SmartScreen).
4. Pilih mode patch yang diinginkan melalui strip konfigurasi **`[MODE BAHASA PATCH]`** (`ID Hybrid` atau `EN Full`).
5. Klik **`▶ Pasang Patch`** dan pantau log diagnostik hingga verifikasi 508 tabel Protobuf selesai.
6. Untuk memulihkan file gim ke kondisi awal, klik **`↺ Pulihkan`**.

---

## Struktur Repositori & Kompilasi (Linux / MinGW-w64 / Python 3.12)

```text
├── assets/
│   ├── branding/                      # celeslib.ico (multi-size), celeslib_logo_512/64/32.png
│   └── previews/                      # celeslib_patcher_id.png, celeslib_patcher_en.png
├── data/references/                   # Ekstraksi referensi Tier 1 (ID), Tier 2 (EN), hybrid_vfs_index.json
├── scripts/
│   ├── 07_build_celeslib_assets.py    # Ekstraksi logo Celeslib & pembuatan header C++ BGRA
│   ├── 08_compile_celeslib_gui.py     # Kompilasi Win32 GUI stub MinGW-w64 & render preview
│   ├── 03_patch_worker_modules.py     # Kompilasi modul Python 3.12 Dual-State
│   ├── 04_verify_real_windows_game.py # Verifikasi 508 tabel Protobuf terhadap file asli gim
│   ├── 05_repack_windows_exe.py       # Pengemasan deterministik Celeslib Release Executable
│   └── 06_publish_github_release.py   # Publikasi rilis GitHub v1.0.0-celeslib
├── src/
│   ├── acepatchindo/                  # Engine klasifikasi hybrid, leksikon, & dual-state bytecode
│   └── gui/                           # celeslib_gui.cpp, celeslib_gui.rc, celeslib_i18n.h
└── tests/                             # Rangkaian pengujian integritas PE, branding, & dual-state engine
```

### Membangun dari Kode Sumber

```bash
# 1. Ekstrak aset branding Celeslib
uv run --python 3.12 python scripts/07_build_celeslib_assets.py

# 2. Kompilasi GUI native Celeslib Single-Page Monochrome Obsidian
uv run --python 3.12 python scripts/08_compile_celeslib_gui.py

# 3. Patch worker modules & rakit executable rilis
uv run --python 3.12 python scripts/03_patch_worker_modules.py
uv run --python 3.12 python scripts/05_repack_windows_exe.py

# 4. Jalankan seluruh pengujian unit & integrasi
uv run --python 3.12 pytest -v
```

---

## Verifikasi Integritas (`SHA-256`)

| Berkas / Komponen | Ukuran (Byte) | SHA-256 |
| :--- | ---: | :--- |
| `Celeslib-HoK-Ace-Patcher-v1.0.0.exe` | `55.094.304` | `bb52ffcde848e0988698512aa2e64f6617d6733fc4b2ce5f7ea9148d69cc0d9e` |
| `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` | `55.094.304` | `bb52ffcde848e0988698512aa2e64f6617d6733fc4b2ce5f7ea9148d69cc0d9e` |
| `ace-worker.exe` (*embedded payload*) | `53.927.862` | `abbfffec6bab992b31c25e32dc8a33571fd5f279033185f84361af87632253f2` |
