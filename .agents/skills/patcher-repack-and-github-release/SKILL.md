---
name: patcher-repack-and-github-release
description: Use when repacking the Windows executable Celeslib-HoK-Ace-Patcher-v1.0.0.exe on Linux, building the Win32 GUI stub and embedded ace-worker.exe, or publishing releases to GitHub repository voseu/acepatchindo.
---

# Celeslib Patcher Binary Repacking & GitHub Release (`v1.0.0-celeslib`)

## Overview

The production Windows 64-bit deliverable is `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (`55,094,304` bytes), published to GitHub repository `https://github.com/voseu/acepatchindo.git` under release tag [`v1.0.0-celeslib`](https://github.com/voseu/acepatchindo/releases/tag/v1.0.0-celeslib).

## End-to-End Rebuild & Repack Pipeline

1. **Rebuild `ID Hybrid` Catalog (`data/catalog_checkpoints/catalog.json.gz`):**
   - Run `PYTHONPATH=src:work/pyz_extracted .venv/bin/python3 scripts/02_build_indonesian_catalog.py` (using `ThreeTierGlossary.from_reference_files(Path("data/references/tier1_wiki_id.json"), Path("data/references/tier2_wiki_en.json"))`) so all `5,621` active `unique` descriptions and `15,397` active `english_updates` entries are translated, aligned, polished, wrapped (`<= 34` visible chars), and validated.
2. **Patch Worker Modules & Repack `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`:**
   - Run `PYTHONPATH=src:work/pyz_extracted .venv/bin/python3 scripts/03_patch_worker_modules.py` and `PYTHONPATH=src:work/pyz_extracted .venv/bin/python3 scripts/05_repack_windows_exe.py` (plus `scripts/08_compile_celeslib_gui.py` if `src/gui/celeslib_gui.cpp` changed).
   - This compiles modified `wxq_patch` runtime modules (`table_catalog.py`, `adaptive.py`) into Python 3.12 `.pyc` bytecode, repacks `PYZ.pyz`, rebuilds `ace-worker.exe` (`53,927,862` bytes = `0x336DFB6`), patches the uppercase SHA-256 hex digest into the Win32 GUI stub (`src/gui/celeslib_gui.cpp`), writes `ace-worker.exe` into `0x11CC62..0x348AC18`, and updates `dist/SHA256SUMS.txt`.
3. **Run Full Verification Suite (`52` Tests):**
   ```bash
   PYTHONPATH=src:work/pyz_extracted .venv/bin/pytest tests/ -v
   ```

## Atomic 5-Point SHA-256 Synchronization

Whenever `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` is rebuilt, the exact SHA-256 digests of both `Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (`55,094,304` bytes) and `ace-worker.exe` (`53,927,862` bytes @ `0x11CC62..0x348AC18`) MUST match across all 5 locations:
1. `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` ( currently `24180a28a2a96b7a3423d62984261c7de6d3643ae4772d52bc729534b16c8319` / worker `91a46a837ec83845bfdfb0cf98ca5e90ec4af205c81840dd7d1e3ce7751f6b6c` )
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
