# Honor of Kings: Ace — Patch Bahasa Indonesia (`v1.4.12-id.2` — Hybrid Gameplay Edition)

Aplikasi pemasang *patch* lokalisasi **Bahasa Indonesia (Hybrid Gameplay Edition)** mandiri (*standalone*) untuk gim PC **Honor of Kings: Ace (`WXQ.exe`)**, dibangun secara deterministik di atas arsitektur QtsVFS `1.4.12` dengan dukungan **Dual-State Engine** (`Mandarin -> Hybrid` dan `Inggris -> Hybrid`).

---

## Fitur Utama

1. **Bahasa Indonesia (`ID`) Khusus Deskripsi Gameplay Inti:**
   - **Kartu Hero:** Seluruh efek kartu hero (*On Play*, *Sacrifice*, *Prepare*, *Awaken*, dan mekanik kartu).
   - **Skill Hero:** Deskripsi skill penuh, ringkasan skill pendek (*collapsed skill*), peningkatan skill Lv.10/40/100, *Combine Skills*, dan *Summon Skills*.
   - **Talent:** *Standard Talents*, *Contestant Lv.6 Exclusive Talents*, mode/brawl talents, dan deskripsi *Talent Cards*.
   - **Kontestan / Lord:** Deskripsi skill aktif/pasif kontestan, aturan misi *Secret Art*, *Secret Art Cards*, dan kartu kemampuan kontestan.
2. **Bahasa Inggris Standar (`EN`) untuk Seluruh Nama & Sistem Non-Gameplay:**
   - **Nama & Judul Entitas:** Seluruh nama Hero, Skill, Talent, dan Kontestan tetap dalam bahasa Inggris resmi, baik sebagai judul kartu maupun saat dirujuk di dalam kalimat deskripsi (misalnya `<color=#FFE897>Symphony of Tides</color>`, `<color=#FFE897>Three Kingdoms Banner</color>`, `<color=#FFE897>Super Copier</color>`, `<color=#FFE897>Build Upgrade</color>`).
   - **Sistem Non-Gameplay:** Antarmuka (UI), Menu, Pengaturan, Lobi, Toko, Tutorial, Loading Tips, Acara, Misi, Pencapaian (*Achievements*), Obrolan Singkat, Gelar Rank, Kosmetik/Skin, serta nama & efek kartu perlengkapan mandiri tetap dalam bahasa Inggris standar.
3. **Pemisahan Presisi 108 String Mandarin Tambahan:**
   - **18 deskripsi gameplay inti** diterjemahkan ke Bahasa Indonesia berkualitas tinggi.
   - **90 string non-target** diterjemahkan ke Bahasa Inggris alami dan terverifikasi.
4. **Pembaruan Satu-Klik Tanpa Kerumitan (*One-Click Auto-Restore*):**
   - Mesin *patcher* secara otomatis mendeteksi dan memulihkan berkas asli Mandarin (`originals/`) terlebih dahulu sebelum memasang versi hybrid apabila mendeteksi rilis sebelumnya (`v1.4.12-id.1` atau *English Patch*), memastikan seluruh string UI kembali ke bahasa Inggris tanpa sisa terjemahan lama.
5. **Keamanan Kapasitas Chunk QtsVFS (`0` Overflow) & Integritas Runtime:**
   - Seluruh `508` tabel Protobuf `.bytes` pada 6 paket QtsVFS (`1`, `4`, `15`, `19`, `20`, `21`) telah diverifikasi lulus alokasi *chunk* LZ4 dan pemeriksaan baca-balik (*read-back verification*).
   - Penjaga integritas SHA-256 binary GUI Rust dan bootloader CArchive PyInstaller 100% valid.

---

## Cara Penggunaan (Windows 10/11 64-bit)

1. **Tutup gim `Honor of Kings: Ace` (`WXQ.exe`)** dan *launcher* sepenuhnya sebelum menjalankan *patcher*.
2. Unduh berkas **`Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`** dan **`SHA256SUMS.txt`** dari halaman [**GitHub Releases (`v1.4.12-id.2`)**](https://github.com/voseu/acepatchindo/releases/tag/v1.4.12-id.2).
3. Jalankan `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` (klik **More info -> Run anyway** apabila muncul jendela Windows SmartScreen, lalu izinkan akses Administrator apabila gim terpasang di `C:\Program Files\WXQLauncher\WXQ`).
4. Pastikan lokasi folder gim mengarah ke direktori instalasi `WXQ` (misalnya `C:\Program Files\WXQLauncher\WXQ`).
5. Klik tombol **`Pasang Patch ID`** dan tunggu hingga proses penyiapan serta verifikasi paket selesai.
6. Untuk mengembalikan gim ke berkas Mandarin asli kapan saja, buka kembali aplikasi ini dan klik **`Pulihkan File`**.

---

## Struktur Repositori & Reproduksi Build (Linux / Python 3.12)

Repositori ini menyimpan kode sumber kakas rekayasa balik, penyelarasan tag Unity, glosarium 3-Tier, dan pengemas deterministik CArchive tanpa menyertakan berkas biner besar:

```text
├── data/references/                   # Ekstraksi referensi Tier 1 (ID), Tier 2 (EN), hybrid_vfs_index.json
├── scripts/
│   ├── 01_extract_baseline_and_refs.py  # Ekstraksi referensi web & deteksi 108 string Mandarin yang belum diterjemahkan
│   ├── 02_build_indonesian_catalog.py   # Pembangunan catalog.json.gz Hybrid (0 kegagalan validasi)
│   ├── 03_patch_worker_modules.py       # Kompilasi modul Python 3.12 Dual-State (table_catalog.pyc & adaptive.pyc)
│   ├── 04_verify_real_windows_game.py   # Verifikasi penuh 6 paket QtsVFS terhadap berkas gim asli
│   ├── 05_repack_windows_exe.py         # Pengemasan deterministik PYZ.pyz, CArchive, & SHA-256 guard Rust GUI
│   └── 06_publish_github_release.py     # Publikasi rilis GitHub v1.4.12-id.2 beserta aset .exe & SHA256SUMS.txt
├── src/acepatchindo/
│   ├── hybrid_classifier.py             # Klasifikasi presisi 4 kategori gameplay vs antarmuka non-target
│   ├── windows_108_split.py             # Pemisahan 18 target deskripsi ID + 90 non-target EN
│   ├── validator.py                     # Implementasi ketat 7 aturan validate_translation
│   ├── tag_aligner.py                   # Penyelaras kerangka tag Unity & rumus dinamis Skill Hero
│   ├── lexicon_id.py                    # Mesin leksikon, morfologi, & tata bahasa Inggris -> Indonesia
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
| `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` | `59.877.888` | `1d31762743e3a82a6e990beb794ef3063781ffe2f4707e7c12b82c886402f083` |
| `ace-worker.exe` (*embedded* `0x4CAC4A..0x3838C00`) | `53.927.862` | `328fa90caa826855a8b4530e788a0955a6aedec17ccffb99cd41db8388c49f68` |


