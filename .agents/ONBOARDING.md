# 🚀 Panduan Onboarding: Celeslib Honor of Kings: Ace Indonesian Patcher (`v1.0.0-celeslib`)

Selamat datang di proyek **Celeslib Honor of Kings: Ace Patcher (`acepatchindo`)** — aplikasi *patcher* lokalisasi resmi **Celeslib** untuk gim **Honor of Kings: Ace (`WXQ.exe` Build `1.4.12`)** di PC (Windows) dan Android (USB/ADB). Dokumen ini adalah kompas utama bagi Prompter, Reviewer, maupun AI Agent Eksekutor.

---

## 🎯 1. Status Proyek & Arsitektur Saat Ini (`v1.0.0-celeslib`)

Seluruh **3 Fase Pembangunan Utama** telah **100% tuntas**, terverifikasi secara forensik (`55/55` *automated tests passed*), dan dipublikasikan ke GitHub Release [`v1.0.0-celeslib`](https://github.com/voseu/acepatchindo/releases/tag/v1.0.0-celeslib):

1. **Dual-State Localization Engine (`ID Hybrid` & `EN Full`):**
   - **`ID Hybrid` (`--patch-lang id`, Default):** Menerjemahkan seluruh **`5.621`** deskripsi efek gameplay aktif di `catalog["unique"]` (termasuk `58` deskripsi dari `108` string Mandarin yang sebelumnya terlewat di Windows) dan **`15.397`** entri `catalog["english_updates"]` aktif (mencakup *Hero Active/Passive Skills, Awakenings, Effect Cards, Equipment, Talents/Sub-Cards,* dan *Contestant/Lord Skills*) ke **Bahasa Indonesia** taktis yang natural, sembari menjaga:
     - **Nama Kartu, Nama Equipment, Nama Hero, & Menu UI Utama** tetap dalam Bahasa Inggris kanonik.
     - **Nama Faksi Kanonik:** `[Central Plains]`, `[Sunset Sea]`, `[Zhulu Plateau]`, `[Three Kingdoms]`, `[Riverlands]`, `[High Heaven]`, `[First Lands]`, `[Factionless]`, `[Great Wall]`, `[Jixia]`.
     - **Kata Kunci Mekanik Kanonik:** `Initiate`, `Deploy`, `Prepare`, `Revive`, `Perfect Revive`, `Arcomia Core`, `Fleeting`, `Retire`, `Combine`, `Steal`, `Soul Snatch`, `[Divinity]`, `Seer Totem`, `Bond Totem`, `Afterlife Totem`, `Fate Totem`.
     - **Nama Contestant Kanonik:** `Xiang`, `Ying Lü`, `Bai Ge`, `Little Daji`, `Little Sun Bin`, `Little Zhuang Fish`, `Little Chang'e`.
     - **Header & Footer Kanonik:** Header `... Series` (`Summon Series`, `General Series`, `Combine Series`, dll.) dan footer `#60D2` (`Cannot be copied`, `Unstackable`, `Disappears after triggering`, dll.) tetap dalam Bahasa Inggris.
   - **`EN Full` (`--patch-lang en`):** Menerjemahkan 100% teks gim ke Bahasa Inggris penuh menggunakan `catalog_en_full.json.gz`.
   - **Kompatibilitas Multi-State, Partial Game Update, & *Balance Hotfix*:** Mendukung instalasi langsung di atas gim *Fresh Mandarin*, gim yang sudah ter-patch (`v1` Full-ID atau English Patcher `1.4.12`), maupun gim yang mengalami *partial launcher update* (pembaruan sebagian paket `.db` seperti `builtin/0` & `builtin/1`), dilengkapi pembersihan *hardlink* staging otomatis sebelum `install`/`stage`, *per-file backup preservation & restore*, penghentian *orphan worker* otomatis saat jendela ditutup, serta *runtime numeric-template fallback* (`wxq_patch/adaptive.py`) yang tahan terhadap *balance hotfix* angka dari server.

2. **CJK-Safe Card Layout & Word-Wrap (`<= 34` Karakter Terlihat):**
   - Pembungkus baris otomatis (`src/acepatchindo/card_wrapper.py`) menjaga panjang baris terlihat `<= 34` karakter (untuk kalimat tanpa tabel `;`) tanpa memotong kata di tengah, tanpa memisahkan token `[...]`/`{...}`/`<...>` lintas baris, tanpa operator `+`/`-` menggantung di ujung baris, dan menjaga *box-drawing glyph* (`╪ ╨ ╫ ╬ ═ ╆ ╇ ╈ ╉ ╊ ╧`) menempel rapat (*snug*) pada kata kunci mekaniknya.

3. **Native Win32 C++17 Dark-Gold GUI + Embedded PyInstaller Worker:**
   - **Deliverable Utama:** `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (`55.095.328` byte, SHA-256: `fdcca7cf757a98fc1f5ad6c01641a6ebdf63cec3c2477efa2bc41ccf428a483a`).
   - **Outer Stub (`src/gui/celeslib_gui.cpp` + `src/gui/celeslib_i18n.h`):** Dikompilasi dengan `x86_64-w64-mingw32-g++` (`scripts/08_compile_celeslib_gui.py`), memiliki antarmuka bilingual instan (`UI: Indonesia` / `UI: English`), pilihan mode patch (`ID Hybrid` / `EN Full`), manajemen PC (`Auto-Detect`, `Pilih Folder`, `Pasang Patch`, `Pulihkan`, `Periksa`), dan Android USB/ADB (`Pindai USB`, `Patch APK`, `Pulihkan APK`).
   - **Embedded Payload (`ace-worker.exe`):** Berukuran tetap `53.927.862` byte (`0x336DFB6`) (SHA-256: `a648e25463685c392618ae46631f11fb79254f997d3e570bab4dd5dbf877476c`), diverifikasi dengan SHA-256 sebelum diekstrak ke `%LOCALAPPDATA%\Celeslib\HoK Ace Patcher\ace-worker.exe`.

---

## 📚 2. Peta Dokumentasi & Arsip Rencana Kerja

1. **Graft Context Graph (`AGENTS.md` / `GEMINI.md`):**
   - Repositori ini diindeks dengan **Graft** (`graft/`). Sebelum melakukan *grep* kasar atau membaca seluruh isi berkas kode, jalankan `graft map`, `graft ask "<pertanyaan>" --source`, `graft skeleton <file>`, atau `graft callers <symbol>`. Setelah perubahan kode besar, perbarui indeks dengan `graft build`.
2. **4 Project Skills Wajib di `.agents/skills/`:**
   - [`wxq-binary-and-vfs-architecture`](file:///home/whise/project/project-klien/patcher/.agents/skills/wxq-binary-and-vfs-architecture/SKILL.md) — Arsitektur biner 2-lapis (`Celeslib-HoK-Ace-Patcher-v1.0.0.exe` + `ace-worker.exe`), struktur PyInstaller CArchive/`PYZ.pyz`, serta lokasi partisi game Windows asli (*read-only*).
   - [`hok-ace-translation-hierarchy`](file:///home/whise/project/project-klien/patcher/.agents/skills/hok-ace-translation-hierarchy/SKILL.md) — Hierarki 3-Tier Referensi Terjemahan (`tier1_wiki_id.json` -> `tier2_wiki_en.json` -> `ZH -> EN -> ID`), klasifikasi `ID Hybrid`, serta daftar istilah & nama sub-kartu kanonik yang wajib terkunci.
   - [`wxq-tag-and-validation-guard`](file:///home/whise/project/project-klien/patcher/.agents/skills/wxq-tag-and-validation-guard/SKILL.md) — 7 aturan wajib `validate_translation` (`TAG_RE`, `PLACEHOLDER_RE`, `RUNTIME_BRACKET_TOKEN_RE`, `CONTROL_TOKEN_RE`, titik koma `;`, batas ekspansi, bebas CJK), penyelarasan tag/placeholder atomik, serta verifikasi kapasitas QtsVFS.
   - [`patcher-repack-and-github-release`](file:///home/whise/project/project-klien/patcher/.agents/skills/patcher-repack-and-github-release/SKILL.md) — Prosedur *build* katalog, *repack* deterministik `Celeslib-HoK-Ace-Patcher-v1.0.0.exe`, sinkronisasi SHA-256 5-titik, dan publikasi ke GitHub Release `v1.0.0-celeslib`.
3. **Arsip Rencana Implementasi (`.agents/archive/` — Jangan Dihapus):**
   - [Fase 1 — Engine & Katalog Awal (`2026-11-03`)](file:///home/whise/project/project-klien/patcher/.agents/archive/2026-11-03-hok-ace-indonesian-patcher-plan.md)
   - [Fase 2 — Rebranding Celeslib, Native Win32 GUI & Dual-State (`2026-11-04`)](file:///home/whise/project/project-klien/patcher/.agents/archive/2026-11-04-celeslib-xeno-ui-and-rebranding-plan.md)
   - [Fase 3 — Overhaul Terjemahan Kartu & Layout CJK-Safe (`2026-11-08`)](file:///home/whise/project/project-klien/patcher/.agents/archive/2026-11-08-comprehensive-card-translation-and-layout-overhaul.md)

---

## 🗂️ 3. Peta Modul Kode Utama (`src/acepatchindo/` & `gui/`)

| Berkas / Direktori | Tanggung Jawab Utama |
| :--- | :--- |
| [`src/acepatchindo/glossary.py`](file:///home/whise/project/project-klien/patcher/src/acepatchindo/glossary.py) | `ThreeTierGlossary`: pencocokan Tier 1 (`tier1_wiki_id.json` + pasangan kurasi `curated_t1_pairs`), Tier 2 (`tier2_wiki_en.json`), deterministik parser (Voucher, Peti Equipment, Faction Buff), *skeleton/formula reinjection*, dan pembersihan tanda baca CJK *fullwidth*. |
| [`src/acepatchindo/card_rewriter.py`](file:///home/whise/project/project-klien/patcher/src/acepatchindo/card_rewriter.py) | `rewrite_en_card_to_id` & `polish_indonesian_card_text`: aturan pratinjau/poles tata bahasa Indonesia taktis, sinkronisasi judul sub-kartu terkait, normalisasi `[Faction]` & kata kunci mekanik kanonik. |
| [`src/acepatchindo/tag_aligner.py`](file:///home/whise/project/project-klien/patcher/src/acepatchindo/tag_aligner.py) | Penyelarasan kerangka tag Unity (`<color=...>`, `<a href=...>`, `<b>`), pengikatan atomik `{N|val}{Icon}`, isolasi *placeholder* pelacak (`tracker_phs`), pelekatan rapat *box-drawing glyph* (`[\u2540-\u257f]`), dan spasi batas tag. |
| [`src/acepatchindo/card_wrapper.py`](file:///home/whise/project/project-klien/patcher/src/acepatchindo/card_wrapper.py) | `wrap_card_description`: *smart word-wrapper* CJK-safe (`max_visible_chars=34`) yang melindungi tag, token `[...]`, `{...}`, dan mencegah operator `+`/`-` menggantung di akhir baris. |
| [`src/acepatchindo/hybrid_classifier.py`](file:///home/whise/project/project-klien/patcher/src/acepatchindo/hybrid_classifier.py) | `HybridClassifier`: menentukan secara deterministik apakah entri `unique` (`5.621` target) atau `english_updates` (`15.397` target) merupakan deskripsi gameplay yang wajib diterjemahkan ke Bahasa Indonesia pada mode `ID Hybrid`. |
| [`src/acepatchindo/validator.py`](file:///home/whise/project/project-klien/patcher/src/acepatchindo/validator.py) | `validate_translation`: 7 aturan validasi ketat (`empty`, `still_chinese`, `tags_changed`, `placeholders_changed`, `bracket_tokens_changed`, `control_tokens_changed`, `semicolons_changed`, `extreme_expansion`). |
| [`src/acepatchindo/dual_state_patch.py`](file:///home/whise/project/project-klien/patcher/src/acepatchindo/dual_state_patch.py) | Injeksi kode runtime `wxq_patch` (`table_catalog.py` & `adaptive.py`) untuk mode `ID Hybrid` / `EN Full`, *unconditional cross-version restore*, dan *runtime numeric-template fallback*. |
| [`scripts/02_build_indonesian_catalog.py`](file:///home/whise/project/project-klien/patcher/scripts/02_build_indonesian_catalog.py) | Pembangun katalog `ID Hybrid` (`data/catalog_checkpoints/catalog.json.gz`) dan peta `en_to_id_map.json`. |
| [`scripts/05_repack_windows_exe.py`](file:///home/whise/project/project-klien/patcher/scripts/05_repack_windows_exe.py) | Kompilasi modul `wxq_patch` (`.pyc` Python 3.12), pemaketan ulang `PYZ.pyz` & `ace-worker.exe` (`53.927.862` byte), serta penyematan ke stub Win32 `Celeslib-HoK-Ace-Patcher-v1.0.0.exe`. |
| [`src/gui/celeslib_gui.cpp`](file:///home/whise/project/project-klien/patcher/src/gui/celeslib_gui.cpp) | Aplikasi GUI Win32 C++17 bertema Celeslib Dark-Gold ([`scripts/08_compile_celeslib_gui.py`](file:///home/whise/project/project-klien/patcher/scripts/08_compile_celeslib_gui.py) & [`scripts/07_build_celeslib_assets.py`](file:///home/whise/project/project-klien/patcher/scripts/07_build_celeslib_assets.py) untuk kompilasi silang MinGW-w64 & render *preview* PNG). |
| [`tests/test_catalog_zero_defects_audit.py`](file:///home/whise/project/project-klien/patcher/tests/test_catalog_zero_defects_audit.py) | Suite audit forensik komprehensif (`test_01` s/d `test_12`) yang mengunci seluruh invarian kualitas terjemahan, struktur tag/rumus, dan pembungkusan baris. |

---

## 🛑 4. Hukum Tertinggi Proyek Ini (Dilarang Dilanggar)

1. **Gunakan Python 3.12 (`.venv/bin/python` / `uv run --python 3.12`):**
   - Seluruh *bytecode* PyInstaller di `ace-worker.exe` menggunakan **Python 3.12**. Jalankan pengujian dan skrip dengan:
     ```bash
     PYTHONPATH=src:work/pyz_extracted .venv/bin/pytest tests/ -v
     ```
2. **Partisi Game Windows Bersifat Read-Only:**
   - Instalasi game asli user berada di `/run/media/whise/Windows/Program Files/WXQLauncher/WXQ` dan *backup* original Mandarin berada di `/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`.
   - **DILARANG** memodifikasi berkas di `/run/media/whise/Windows` secara langsung dari Linux.
3. **Nol Toleransi terhadap Regresi Validasi, Rumus, atau Evasion:**
   - Seluruh `71.291` pemeriksaan (`41.483` `unique` + `29.750` `english_updates` + `58` `WINDOWS_108_TARGET_DESC_ID`) **WAJIB** lulus `validate_translation` (`0` error), `0` kebocoran CJK atau tanda baca CJK *fullwidth* (`。，：；（）`) di luar `{...}`, `0` ketidakcocokan token rumus `[...]`, dan `0` baris `> 34` karakter terlihat (*non-table*).
   - Dilarang memanipulasi pengujian (seperti menambahkan *post-processing* di dalam file tes atau melonggarkan *assertion*) untuk menyembunyikan cacat katalog.
4. **Sinkronisasi SHA-256 5-Titik Setiap Kali Repack:**
   - Setiap perubahan pada katalog atau kode `wxq_patch`/`gui` wajib diikuti dengan pembangunan ulang biner dan penyelarasan SHA-256 di 5 titik:
     1. `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`
     2. `dist/SHA256SUMS.txt`
     3. Tabel `Verifikasi Integritas (SHA-256)` di `README.md`
     4. Tag Git `v1.0.0-celeslib` & branch `origin/main`
     5. Catatan rilis (*body*) dan aset terunggah di GitHub Release `v1.0.0-celeslib`
