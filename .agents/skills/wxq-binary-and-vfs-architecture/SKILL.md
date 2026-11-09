---
name: wxq-binary-and-vfs-architecture
description: Use when inspecting, unpacking, modifying, or repacking Honor of Kings Ace Patcher executables, PyInstaller CArchives, PYZ.pyz bytecode modules, catalog.json.gz, or QtsVFS .db game packages.
---

# WXQ Binary & QtsVFS Architecture

## Overview

`dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (`55,094,304` bytes) is a **two-layer Windows x86_64 executable**:
1. **Outer Native Win32 C++17 GUI Stub (`src/gui/celeslib_gui.cpp` + `src/gui/celeslib_i18n.h`):** Compiled via `x86_64-w64-mingw32-g++` (`scripts/08_compile_celeslib_gui.py`), featuring a custom Dark-Gold owner-drawn interface, instant `UI: Indonesia` / `UI: English` toggle, and `ID Hybrid` / `EN Full` patch mode selector.
2. **Embedded PyInstaller Worker (`ace-worker.exe`, `53,927,862` bytes):** Stored in the `.rdata` payload slot (`0x11CC62..0x348AC18`), verified via an embedded uppercase SHA-256 hex digest before extraction to `%LOCALAPPDATA%\Celeslib\HoKAcePatcher\worker\<sha256_prefix16>\ace-worker.exe`.

**CRITICAL RUNTIME REQUIREMENT:** Always use `/home/whise/.local/bin/uv run --python 3.12` or `.venv/bin/python` (Python 3.12) when unmarshalling, compiling, or executing `.pyc` and `PYZ.pyz` files.

## Two-Layer Binary Layout (`dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`)

| Component / Slice | Offset Range (Hex) | Size (Bytes) | Role |
|---|---|---:|---|
| Outer Win32 GUI Stub + Headers | `0x000000` – `0x11CC61` | `1,166,434` | Native Win32 C++17 Dark-Gold GUI code, embedded 64-char uppercase SHA-256 slot, icons & resources |
| Embedded `ace-worker.exe` Payload | `0x11CC62` – `0x348AC17` | `53,927,862` (`0x336DFB6`) | Complete Python 3.12 PyInstaller PE executable (`ace-worker.exe`) |
| Trailing PE Section Alignment | `0x348AC18` – `0x348AC3F` | `40` | Final section alignment up to `55,094,304` bytes |

*(Legacy baseline reference: `Honor of Kings Ace English Patcher 1.4.12.exe` (`59,877,888` bytes) had its `ace-worker.exe` at `0x4CAC4A..0x3838C00` and SHA-256 digest at `0x4CABFA`.)*

### Embedded Worker (`ace-worker.exe`) Internal Offsets (Relative to Worker Start)

- **PE Bootloader Stub:** Relative offset `0` to `348,672` (`348,672` bytes).
- **PyInstaller CArchive:** Relative offset `348,672` to `53,927,862` (`plen = 53,579,190` bytes).
- **PyInstaller `MEI` Cookie (88 bytes):** Relative offset `53,927,774` (`magic = b"MEI\x0c\x0b\x0a\x0b\x0e"`, `plen = 53579190`, `pyvers = 312`).
- **Fixed Size Constraint:** Keep `ace-worker.exe` at **exact `53,927,862` (`0x336DFB6`) bytes** by inserting zero-padding between the end of the CArchive TOC and the 88-byte `MEI` cookie.
- **Embedded Catalogs Inside CArchive:**
  - `catalog\catalog.json.gz` — Active `ID Hybrid` catalog (`41,483` `unique` entries + `29,750` `english_updates` entries).
  - `catalog\catalog_en_full.json.gz` — Full English catalog (`EN Full` mode).

## Real Game Installation on Windows Partition (Read-Only Reference)

The user's actual Honor of Kings: Ace installation is on `/dev/nvme0n1p3` (mounted read-only at `/run/media/whise/Windows`):

1. **Mount Command (Read-Only):**
   ```bash
   udisksctl mount -b /dev/nvme0n1p3 -o ro || sudo mount -o ro /dev/nvme0n1p3 /mnt/windows
   ```
2. **Untouched Original Chinese Game Backup (`originals/`):**
   `/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`
   - Contains the 6 untouched QtsVFS packages (`1`, `4`, `15`, `19`, `20`, `21` inside `WXQ_Data/Package/builtin/`), totaling **508 Protobuf localization tables** (`352,251` records, `39,470` unique Chinese strings used, plus **108 unique Chinese strings / 409 records** missed by English Patcher 1.4.12).
3. **Live Game Folder:**
   `/run/media/whise/Windows/Program Files/WXQLauncher/WXQ`

## Dual-State & Hotfix-Resilient Patching Architecture (`wxq_patch`)

In `wxq_patch/table_catalog.py` and `wxq_patch/adaptive.py`:
1. **Language Mode Selection (`--patch-lang id|en` or `WXQ_PATCH_LANG=id|en`):**
   - `id` (`ID Hybrid`, default): Loads `catalog\catalog.json.gz` (gameplay descriptions in Bahasa Indonesia, names/titles/UI chrome in canonical English).
   - `en` (`EN Full`): Loads `catalog\catalog_en_full.json.gz` (100% English).
2. **Unconditional Cross-Version Restore Before Install:**
   - When switching between `v1` Full-ID, English Patcher `1.4.12`, `ID Hybrid`, or `EN Full`, `adaptive.install` automatically restores untouched Chinese originals from the receipt backup when `catalog_sha` or `patch_lang` differs, ensuring zero stale string contamination.
3. **Runtime Numeric-Template Fallback (Live Balance Hotfix Resilience):**
   - If a server hotfix tweaks numbers inside a Chinese card description (e.g., `25%` -> `30%`), `Catalog.lookup` normalizes digits to `<N>` placeholders, matches the template, and reinjects the new live numbers at runtime if `validate_translation` passes.
