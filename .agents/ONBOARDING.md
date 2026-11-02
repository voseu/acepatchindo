# 🚀 Panduan Onboarding: Honor of Kings: Ace Indonesian Patcher (Untuk Prompter & AI Agent Eksekutor)

Selamat datang di proyek **Honor of Kings: Ace Indonesian Patcher (`acepatchindo`)**! Dokumen ini adalah kompas utama bagi AI Agent Eksekutor yang berjalan dari IDE.

---

## 🎯 1. Tujuan Akhir Proyek
Mengubah dan membangun ulang **Honor of Kings: Ace English Patcher 1.4.12** menjadi **Honor of Kings: Ace Indonesian Patcher 1.4.12** yang:
1. Menerjemahkan **100% teks di dalam game** (`catalog/catalog.json.gz` yang berisi 41.375 string unik + 29.750 contextual updates + **108 string Mandarin yang sebelumnya terlewat oleh patcher Inggris** di game asli user) ke **Bahasa Indonesia** secara akurat dan konsisten.
2. Mendukung instalasi baik pada **Game Fresh (Masih Bahasa Mandarin)** maupun **Game yang Sudah Ter-patch Bahasa Inggris** (seperti instalasi game di partisi Windows user saat ini).
3. Menghasilkan file executable Windows siap pakai (`Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`) serta mempublikasikannya ke **GitHub Releases** pada repositori `https://github.com/voseu/acepatchindo.git`.

---

## 📚 2. Wajib Baca Sebelum Menyentuh Kode (Urutan Mutlak)
1. **Master Implementation Plan:**
   - Baca [`/home/whise/project/project-klien/patcher/.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md`](file:///home/whise/project/project-klien/patcher/.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md) dari awal sampai akhir.
2. **4 Project Skills Wajib di `.agents/skills/`:**
   - [`wxq-binary-and-vfs-architecture`](file:///home/whise/project/project-klien/patcher/.agents/skills/wxq-binary-and-vfs-architecture/SKILL.md) — Arsitektur 2-lapis biner (Rust outer + PyInstaller `ace-worker.exe` inner), offset SHA-256 `0x4CABFA`, dan path game Windows asli.
   - [`hok-ace-translation-hierarchy`](file:///home/whise/project/project-klien/patcher/.agents/skills/hok-ace-translation-hierarchy/SKILL.md) — Aturan 3-Tier Referensi Terjemahan (`hok-ace-translate-id.netlify.app` -> `hokace.wiki` -> `ZH -> EN -> ID`).
   - [`wxq-tag-and-validation-guard`](file:///home/whise/project/project-klien/patcher/.agents/skills/wxq-tag-and-validation-guard/SKILL.md) — Aturan lolos `validate_translation` (`TAG_RE`, `PLACEHOLDER_RE`, `CONTROL_TOKEN_RE` `╫`, jumlah titik koma `;`, batas panjang) & QtsVFS chunk capacity.
   - [`patcher-repack-and-github-release`](file:///home/whise/project/project-klien/patcher/.agents/skills/patcher-repack-and-github-release/SKILL.md) — Algoritma repacking deterministik `.exe` di Linux dan pembuatan GitHub Release.

---

## 🛑 3. Hukum Tertinggi Proyek Ini (Dilarang Dilanggar)

1. **Hierarki 3-Tier Terjemahan:**
   - **Tier 1 (Utama):** https://hok-ace-translate-id.netlify.app/ (Gunakan nama & deskripsi Bahasa Indonesia dari web ini jika ada).
   - **Tier 2 (Fallback 1):** https://hokace.wiki/ (Jika tidak ada di Tier 1, ambil dari web Inggris ini lalu terjemahkan ke Bahasa Indonesia dengan gaya istilah Tier 1).
   - **Tier 3 (Fallback 2):** Jika tidak ada di kedua web referensi, terjemahkan dari Bahasa Mandarin ke Bahasa Inggris (`ZH -> EN`, gunakan/verifikasi `EN` bawaan `catalog.json.gz`), baru terjemahkan ke Bahasa Indonesia (`EN -> ID`).
2. **Gunakan Python 3.12 via `uv`:**
   - Seluruh bytecode PyInstaller di proyek ini menggunakan **Python 3.12**. Selalu jalankan skrip pemrosesan `.pyc` / `PYZ.pyz` dengan `/home/whise/.local/bin/uv run --python 3.12`.
3. **Partisi Game Windows Bersifat Read-Only:**
   - Instalasi game asli user ada di `/run/media/whise/Windows/Program Files/WXQLauncher/WXQ` dan backup original Mandarin-nya ada di `/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`.
   - **DILARANG** memodifikasi file di `/run/media/whise/Windows` secara langsung dari Linux. Gunakan hanya sebagai sumber pembacaan & verifikasi `adaptive.scan` / `capacity_report`.
4. **Nol Toleransi untuk `invalid_translation` & `capacity_skipped`:**
   - Setiap string terjemahan WAJIB lulus `validate_translation(source, translated) == (True, 'ok')` dan uji `adaptive.scan` terhadap `originals/` WAJIB menghasilkan `invalid_translation == 0`, `capacity_skipped == 0`, dan `unknown == 0`.
