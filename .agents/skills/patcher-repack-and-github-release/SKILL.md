---
name: patcher-repack-and-github-release
description: Use when repacking the Windows executable Celeslib-HoK-Ace-Patcher-v1.0.0.exe on Linux, building the Win32 GUI stub and embedded ace-worker.exe, or publishing releases to GitHub repository voseu/acepatchindo.
---

# Celeslib Patcher Binary Repacking & GitHub Release (`v1.0.0-celeslib`)

## Overview

The production Windows 64-bit deliverable is `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (`55,095,328` bytes), published to GitHub repository `https://github.com/voseu/acepatchindo.git` under release tag [`v1.0.0-celeslib`](https://github.com/voseu/acepatchindo/releases/tag/v1.0.0-celeslib).

## End-to-End Rebuild & Repack Pipeline

1. **Rebuild `ID Hybrid` Catalog (`data/catalog_checkpoints/catalog.json.gz`):**
   - Run `PYTHONPATH=src:work/pyz_extracted .venv/bin/python3 scripts/02_build_indonesian_catalog.py` (using `ThreeTierGlossary.from_reference_files(Path("data/references/tier1_wiki_id.json"), Path("data/references/tier2_wiki_en.json"))`) so all `5,621` active `unique` descriptions and `15,397` active `english_updates` entries are translated, aligned, polished, wrapped (`<= 34` visible chars), and validated.
2. **Patch Worker Modules & Repack `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`:**
   - Run `PYTHONPATH=src:work/pyz_extracted .venv/bin/python3 scripts/03_patch_worker_modules.py` and `PYTHONPATH=src:work/pyz_extracted .venv/bin/python3 scripts/05_repack_windows_exe.py` (plus `scripts/08_compile_celeslib_gui.py` if `src/gui/celeslib_gui.cpp` changed).
   - This compiles modified `wxq_patch` runtime modules (`table_catalog.py`, `adaptive.py`) into Python 3.12 `.pyc` bytecode, repacks `PYZ.pyz`, rebuilds `ace-worker.exe` (`53,927,862` bytes = `0x336DFB6`), patches the uppercase SHA-256 hex digest into the Win32 GUI stub (`src/gui/celeslib_gui.cpp`), appends `ace-worker.exe` with the 8-byte footer pointer, and updates `dist/SHA256SUMS.txt`.
3. **Run Full Verification Suite (`55` Tests):**
   ```bash
   PYTHONPATH=src:work/pyz_extracted .venv/bin/pytest tests/ -v
   ```

## Atomic 5-Point SHA-256 Synchronization

Whenever `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` is rebuilt, the exact SHA-256 digests of both `Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (`55,095,328` bytes) and `ace-worker.exe` (`53,927,862` bytes) MUST match across all 5 locations:
1. `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` ( currently `c5d1633a069d8891af1f1c5e91c940174bfb2373e2e683bfbb0b8df5caf9f2f6` / worker `30b922b1bb6b7a12c6ad97e44244289b139c363b3217a3d3fe0ef8e289c9731c` )
2. `dist/SHA256SUMS.txt`
3. `README.md` (`## Verifikasi Integritas (SHA-256)`)
4. Git `origin/main` and tag `v1.0.0-celeslib` (`git tag -f v1.0.0-celeslib && git push origin main && git push origin v1.0.0-celeslib --force`)
5. Live GitHub Release `v1.0.0-celeslib` assets and release body:
   ```bash
   gh release upload v1.0.0-celeslib \
     dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe \
     dist/SHA256SUMS.txt \
     assets/previews/celeslib_patcher_id.png \
     assets/previews/celeslib_patcher_en.png \
     --clobber
   ```
