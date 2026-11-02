# Honor of Kings: Ace — Patch Bahasa Indonesia (`v1.4.12-id.1`)

Aplikasi pemasang *patch* lokalisasi **Bahasa Indonesia** mandiri (*standalone*) untuk gim PC **Honor of Kings: Ace (`WXQ.exe`)**, dibangun secara deterministik di atas arsitektur QtsVFS `1.4.12` dengan dukungan **Dual-State Engine** (`Mandarin -> Indonesia` dan `Inggris -> Indonesia`).

---

## Fitur Utama

1. **Cakupan Terjemahan Penuh (100% Bebas Sisa Mandarin pada `originals/`):**
   - **41.483** entri kamus utama (`unique`), mencakup **41.375** entri basis `1.4.12` ditambah **108 string Mandarin (`409` record)** yang sebelumnya terlewat oleh *English Patcher 1.4.12*.
   - **29.750** entri pembaruan kontekstual (`english_updates`).
   - **22.520** pemetaan pembalik tervalidasi (`en_to_id`) untuk instalasi gim yang sudah terpasang *English Patch*.
2. **Hierarki Terminologi 3-Tier HoK Ace Indonesia:**
   - **Tier 1 (Utama):** Kamus komunitas Indonesia [hok-ace-translate-id.netlify.app](https://hok-ace-translate-id.netlify.app/) (`#data` & `#lords-data`, mencakup Lord/Penguasa, Talent, Equipment, Efek, dan Hero) dengan penyelarasan ulang (*re-injection*) kerangka tag Unity (`<color=...>`, `<a href=...>`, `<b>`), *placeholder* (`{0}`), token kontrol (`╫`), serta titik koma (`;`).
   - **Tier 2 (Referensi Kedua):** Ensiklopedia [hokace.wiki](https://hokace.wiki/search/) (`624` entri istilah resmi *Hero*, *Artifact*, *Spell*, *Scroll*, dan *Trait* yang diadaptasi ke Bahasa Indonesia).
   - **Tier 3 (Cakupan Menyeluruh):** Lokalisasi seluruh sisa dialog, antarmuka, pencapaian (*achievement*), dan deskripsi sistem dengan kepatuhan 100% terhadap 7 aturan `validate_translation`.
3. **Dual-State Engine & Pemulihan Otomatis Cadangan Mandarin (`originals/`):**
   - Jika gim Anda **masih berbahasa Mandarin asli**, *patcher* langsung mencadangkan berkas asli dan memasang Bahasa Indonesia.
   - Jika gim Anda **sudah terpasang English Patcher 1.4.12**, *patcher* secara otomatis memulihkan cadangan Mandarin terverifikasi di `%LOCALAPPDATA%\HoK Ace English Patch\adaptive` terlebih dahulu sebelum memasang Bahasa Indonesia (menjaga keutuhan cadangan asli gim Anda), serta menyediakan *fallback* langsung `EN -> ID` apabila cadangan lokal tidak ditemukan.
4. **Keamanan Kapasitas Chunk QtsVFS (`0` Overflow):**
   - Seluruh `508` tabel Protobuf `.bytes` pada 6 paket QtsVFS (`1`, `4`, `15`, `19`, `20`, `21`) telah diverifikasi lulus alokasi *chunk* LZ4 dan pemeriksaan baca-balik (*read-back verification*).

---

## Cara Penggunaan (Windows 10/11 64-bit)

1. **Tutup gim `Honor of Kings: Ace` (`WXQ.exe`)** dan *launcher* sepenuhnya sebelum menjalankan *patcher*.
2. Unduh berkas **`Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`** dan **`SHA256SUMS.txt`** dari halaman [**GitHub Releases (`v1.4.12-id.1`)**](https://github.com/voseu/acepatchindo/releases/tag/v1.4.12-id.1).
3. Jalankan `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` (klik **More info -> Run anyway** apabila muncul jendela Windows SmartScreen, lalu izinkan akses Administrator apabila gim terpasang di `C:\Program Files\WXQLauncher\WXQ`).
4. Pastikan lokasi folder gim mengarah ke direktori instalasi `WXQ` (misalnya `C:\Program Files\WXQLauncher\WXQ`).
5. Klik tombol **`Pasang Patch ID`** dan tunggu hingga proses penyiapan serta verifikasi paket selesai.
6. Untuk mengembalikan gim ke berkas Mandarin asli kapan saja, buka kembali aplikasi ini dan klik **`Pulihkan File`**.

---

## Struktur Repositori & Reproduksi Build (Linux / Python 3.12)

Repositori ini menyimpan kode sumber kakas rekayasa balik, penyelarasan tag Unity, glosarium 3-Tier, dan pengemas deterministik CArchive tanpa menyertakan berkas biner besar:

```text
├── data/references/                   # Ekstraksi referensi Tier 1 (ID), Tier 2 (EN), & 108 string Mandarin tambahan
├── scripts/
│   ├── 01_extract_baseline_and_refs.py  # Ekstraksi referensi web & deteksi 108 string Mandarin yang belum diterjemahkan
│   ├── 02_build_indonesian_catalog.py   # Pembangunan catalog.json.gz Bahasa Indonesia (0 kegagalan validasi)
│   ├── 03_patch_worker_modules.py       # Kompilasi modul Python 3.12 Dual-State (table_catalog.pyc & adaptive.pyc)
│   ├── 04_verify_real_windows_game.py   # Verifikasi penuh 6 paket QtsVFS terhadap berkas gim asli
│   ├── 05_repack_windows_exe.py         # Pengemasan deterministik PYZ.pyz, CArchive, & SHA-256 guard Rust GUI
│   └── 06_publish_github_release.py     # Publikasi rilis GitHub v1.4.12-id.1 beserta aset .exe & SHA256SUMS.txt
├── src/acepatchindo/
│   ├── validator.py                     # Implementasi ketat 7 aturan validate_translation
│   ├── tag_aligner.py                   # Penyelaras kerangka tag Unity (<a href>, <color>, placeholder, ╫, ;)
│   ├── glossary.py                      # Mesin glosarium & penerjemah 3-Tier Bahasa Indonesia
│   └── dual_state_patch.py              # Generator bytecode mandiri untuk PyInstaller PYZ.pyz
└── tests/                             # Rangkaian pengujian unit & integrasi QtsVFS / CArchive
```

Menjalankan seluruh pengujian dengan Python 3.12 (`uv`):

```bash
uv run --python 3.12 --with lz4 --with httpx --with pytest pytest -v
```

---

## Verifikasi Integritas (`SHA-256`)

| Berkas / Komponen | Ukuran (Byte) | SHA-256 |
| :--- | ---: | :--- |
| `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` | `59.877.888` | `f98af7f76b4b9ae8a250637895c8f57318daf0d95838833f2defb175db9bf293` |
| `ace-worker.exe` (*embedded* `0x4CAC4A..0x3838C00`) | `53.927.862` | `2c9952158ff04be043117c9b3cb71ff3db0ac3fef4537b91ee17fccf9946dd11` |


