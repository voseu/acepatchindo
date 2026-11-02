---
name: patcher-repack-and-github-release
description: Use when repacking the Windows executable Honor of Kings Ace Indonesian Patcher.exe on Linux, patching outer Rust GUI strings and SHA-256 worker digest, or publishing releases to GitHub repository voseu/acepatchindo.
---

# Patcher Binary Repacking & GitHub Release

## Overview

Because the development host is Linux and the target deliverable is a standalone Windows 64-bit `.exe` (`Honor of Kings Ace Indonesian Patcher 1.4.12.exe`), we repack the embedded PyInstaller `ace-worker.exe` in-place while preserving exact PE section and slice lengths, update the outer Rust binary's SHA-256 verification digest, and publish the release to `https://github.com/voseu/acepatchindo.git`.

## Deterministic In-Place Repacking Algorithm

1. **Compile Modified `wxq_patch` Modules (Python 3.12):**
   - Use `/home/whise/.local/bin/uv run --python 3.12` to compile modified `.py` files (such as `table_catalog.py` with dual Chinese + English-to-Indonesian support) into `.pyc` files.
   - Repack `PYZ.pyz` using `zlib.compress(code_marshal_bytes, 9)` (keep `length == 0` for namespace packages like `archspec.vendor`).
2. **Minify & Compress `catalog\catalog.json.gz`:**
   - Serialize JSON with `json.dumps(cat, ensure_ascii=False, separators=(',', ':')).encode('utf-8')`.
   - Compress with `gzip.compress(raw_json, compresslevel=9)`.
3. **Rebuild the PyInstaller CArchive of `ace-worker.exe`:**
   - Extract the original `ace-worker.exe` slice from `Honor of Kings Ace English Patcher 1.4.12.exe` (`data[0x4CAC4A : 0x3838C00]`, exact length `53,927,862` bytes).
   - Keep the first `348,672` bytes (PE bootloader stub, offset `0` to `348,672` of `ace-worker.exe`) intact.
   - Rebuild the CArchive entries starting at offset `348,672`:
     - Replace `catalog\catalog.json.gz` (`cflag=1`, `zlib.compress(gz_bytes, 9)`, `ulen=len(gz_bytes)`).
     - Replace `PYZ.pyz` (`cflag=0`, `typcd=ord('z')`).
     - If total CArchive size (entries + TOC + 88-byte cookie) is less than `53,579,190` bytes, insert zero-padding (`\x00`) between the end of the TOC and the 88-byte `MEI` cookie so `plen` remains **exact `53,579,190` bytes** and `len(new_ace_worker)` remains **exact `53,927,862` (`0x336DFB6`) bytes**.
     - *(If additional byte slack is ever needed, unused offline generator dicts in `PYZ.pyz` such as `wxq_patch.direct_remaining_group_overrides_01..07` can be replaced with empty stub dicts in `PYZ.pyz`, freeing > 600 KB without affecting runtime `adaptive.pyc` or `mobile.pyc`.)*
4. **Update Outer Rust Binary SHA-256 Digest:**
   - Compute `worker_sha256 = hashlib.sha256(new_ace_worker).hexdigest().upper().encode('ascii')` (64 bytes).
   - Write `worker_sha256` at file offset `0x4CABFA` (preserving the trailing `\r\n` at `0x4CAC3A`).
   - Write `new_ace_worker` at file offset `0x4CAC4A` to `0x3838C00`.
5. **Localize Fixed-Length Outer Rust GUI Strings (Safe In-Place Byte Replacement):**
   - Only replace strings in `.rdata` after `0x3838C00` when the replacement UTF-8 byte length is **strictly equal** to the original UTF-8 byte length (because Rust `&str` fat pointers hardcode `(ptr, len)` in `.text`).
   - Verify with a round-trip extraction test (`pyinstxtractor.py` + `SHA-256` check at `0x4CABFA`).

## GitHub Repository & Release (`https://github.com/voseu/acepatchindo.git`)

1. **Repository Hygiene (`.gitignore`):**
   - Never commit 60 MB `.exe` binaries, `.dll`/`.pyd` files, or `Honor of Kings Ace English Patcher 1.4.12.exe_extracted/` into Git tree history (GitHub rejects files > 100 MB and bloats clones).
   - Commit all source code (`src/`, `scripts/`, `tests/`, `.agents/`, `README.md`, `.github/workflows/`).
2. **Publishing the Windows `.exe` Release:**
   - Upload the built `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` and `SHA256SUMS.txt` directly to **GitHub Releases** on `voseu/acepatchindo` (using authenticated GitHub API / `gh release create` or GitHub Actions release workflow) so the user can download and install it directly on Windows.
