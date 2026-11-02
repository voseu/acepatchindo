---
name: wxq-binary-and-vfs-architecture
description: Use when inspecting, unpacking, modifying, or repacking Honor of Kings Ace Patcher executables, PyInstaller CArchives, PYZ.pyz bytecode modules, catalog.json.gz, or QtsVFS .db game packages.
---

# WXQ Binary & QtsVFS Architecture

## Overview

`Honor of Kings Ace English Patcher 1.4.12.exe` (`59,877,888` bytes) is a **two-layer Windows executable**: an outer Rust (`egui`/`eframe`) GUI binary that embeds a complete Python 3.12 PyInstaller executable (`ace-worker.exe`) inside its `.rdata` section.

**CRITICAL RUNTIME REQUIREMENT:** Always use `/home/whise/.local/bin/uv run --python 3.12` when unmarshalling, compiling, or executing `.pyc` and `PYZ.pyz` files. Host Python 3.14 has an incompatible bytecode/opcode format.

## Two-Layer Binary Layout (`Honor of Kings Ace English Patcher 1.4.12.exe`)

| Offset Range (Hex / Dec) | Size (Bytes) | Role |
|---|---|---|
| `0x000000` – `0x4CABF9` (`0` – `5,024,761`) | `5,024,762` | Outer Rust `egui` code (`.text`) and initial `.rdata` |
| `0x4CABFA` – `0x4CAC3B` (`5,024,762` – `5,024,827`) | `66` (`0x42`) | Expected uppercase SHA-256 hex digest (`64` chars + `\r\n`) of `ace-worker.exe` |
| `0x4CAC3C` – `0x4CAC49` (`5,024,828` – `5,024,841`) | `14` (`0x0E`) | Embedded worker filename: `"ace-worker.exe"` |
| `0x4CAC4A` – `0x3838BFF` (`5,024,842` – `58,952,703`) | `53,927,862` (`0x336DFB6`) | Embedded PyInstaller PE executable (`ace-worker.exe`) |
| `0x3838C00` – `0x391A7FF` (`58,952,704` – `59,877,887`) | `925,184` | Outer Rust GUI strings, `.data`, `.pdata`, `.rsrc`, `.reloc` |

### Embedded Worker (`ace-worker.exe`) Internal Offsets

- **PE Bootloader Stub:** File offset `5,024,842` to `5,373,514` (`348,672` bytes).
- **PyInstaller CArchive:** File offset `5,373,514` to `58,952,704` (`plen = 53,579,190` bytes).
- **PyInstaller `MEI` Cookie (88 bytes):** File offset `58,952,616` (`magic = b"MEI\x0c\x0b\x0a\x0b\x0e"`, `plen = 53579190`, `toc_pos = 53531742`, `toc_len = 47360`, `pyvers = 312`).
- **Outer Rust Hardcoded Size References:** VMA `0x1400FEBF1`, `0x14010F49C`, `0x1401178D0`, `0x140117C16` all pass `$0x336DFB6` (`53,927,862`). Keep `ace-worker.exe` at **exact `53,927,862` bytes** by padding zeros before the 88-byte `MEI` cookie.

## Real Game Installation on Windows Partition (Read-Only Reference)

The user's actual Honor of Kings: Ace installation is on `/dev/nvme0n1p3` (mounted read-only at `/run/media/whise/Windows`):

1. **Mount Command (Read-Only):**
   ```bash
   udisksctl mount -b /dev/nvme0n1p3 -o ro || sudo mount -o ro /dev/nvme0n1p3 /mnt/windows
   ```
2. **Untouched Original Chinese Game Backup (`originals/`):**
   `/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`
   - Contains the 6 untouched QtsVFS packages (`1`, `4`, `15`, `19`, `20`, `21` inside `WXQ_Data/Package/builtin/`), totaling **508 Protobuf localization tables** (`352,251` records, `39,470` unique Chinese strings used, plus **108 unique Chinese strings / 409 records** missed by English Patcher 1.4.12).
3. **Live Game Folder (Currently English-Patched):**
   `/run/media/whise/Windows/Program Files/WXQLauncher/WXQ`

## Dual-State Patching Requirement (Chinese AND Already-English Games)

In `wxq_patch/table_catalog.py`, `translate_table` originally only calls `catalog.lookup(asset, key, source)` when `CJK_RE.search(source)` is `True`.
Because the user's live Windows game is **already patched to English** (`267,876` records are English, `CJK_RE.search(source)` is `False`), the Indonesian patcher MUST support both states:
1. **Unpatched Chinese Game (`CJK_RE.search(source)` is `True`):** Translates `Chinese -> Indonesian` via `catalog.lookup(asset, key, source)`.
2. **Already-English-Patched Game (`CJK_RE.search(source)` is `False`):**
   - In `Catalog.__init__`, build `self.en_to_id: dict[str, str]` (mapping English strings to Indonesian strings) and update `self.english_updates` targets to Indonesian.
   - In `translate_table`, if `source` is in `self.en_to_id`, translate `English -> Indonesian` and validate against the original Chinese source (or English source).
   - Also in `adaptive.py`, recognize receipts in `%LOCALAPPDATA%\HoK Ace English Patch\adaptive` so `Restore` or re-patching over the English patch works cleanly without losing the original Chinese backups!
