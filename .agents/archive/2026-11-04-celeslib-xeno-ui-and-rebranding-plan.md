# Celeslib Xeno UI, Rebranding, Versioning & Dual-Language (ID/EN) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy CPDD outer Rust wrapper and branding with a native Windows x86-64 **Celeslib Xeno v1.3.0 UI** executable (`Celeslib-HoK-Ace-Patcher-v1.0.0.exe`, release tag `v1.0.0-celeslib`) featuring official **Celeslib** branding/logos from `/home/whise/project/project-pribadi/celeslib-webnovel/public/`, a Xeno (`https://www.xeno.now/`) ultra-dark carbon interface, real-time **UI Language switching (`ID` / `EN`)**, and selectable **Game Patch Language Mode (`Indonesian Hybrid Gameplay` / `Full English`)**.

**Architecture:**
1. **Branding & Icon Pipeline (`scripts/07_build_celeslib_assets.py`):** Extracts the official Celeslib pixel-star logo from `/home/whise/project/project-pribadi/celeslib-webnovel/public/Logo.webp` and `web-app-manifest-512x512.png` to generate multi-resolution Windows `.ico` (`assets/branding/celeslib.ico`: `16x16`..`256x256`) and PNG assets (`assets/branding/celeslib_logo_64.png`, `celeslib_logo_32.png`) for embedding into the PE `.rsrc` section.
2. **Bilingual Engine & Selectable Patch Mode (`src/acepatchindo/dual_state_patch.py`, `scripts/03_patch_worker_modules.py`, `scripts/05_repack_windows_exe.py`):** Enhances `wxq_patch/table_catalog.pyc` and `wxq_patch/adaptive.pyc` inside `ace-worker.exe` so the engine reads:
   - `CELESLIB_PATCH_LANG` (`"id"` default for Indonesian Hybrid Gameplay, or `"en"` for 100% Full English game text via embedded `zh_to_en_gameplay` and `id_to_en` maps in `catalog.json.gz`), and
   - `CELESLIB_UI_LANG` (`"id"` or `"en"`) to return status/error messages in `result.json` matching the user's active Patcher UI language.
3. **Native Xeno v1.3.0 Windows GUI Launcher (`src/gui/celeslib_xeno_gui.cpp`, `src/gui/celeslib_xeno.rc`):** Compiled via `x86_64-w64-mingw32-g++` and `x86_64-w64-mingw32-windres` (`-mwindows -lgdiplus -ldwmapi -luxtheme -lshlwapi -lole32 -luuid -static-libgcc -static-libstdc++`), replicating the **Xeno v1.3.0 (`https://www.xeno.now/`)** layout:
   - Collapsible Left Sidebar with **Celeslib Logo**, **`Celeslib`** brand header, **`v1.0.0`** badge, and 4 navigation views: **`Dashboard`**, **`Patcher`**, **`Android (USB)`**, and **`Settings`**.
   - Top Pill Action Toolbar (`[▷ Pasang Patch / Install Patch]`, `[↺ Pulihkan / Restore]`, `[🔍 Periksa / Verify]`, `[📁 Pilih Folder / Browse]`, `[⚡ Auto-Detect]`, `[🗑 Clear]`) and quick header toggles (`[🌐 UI: ID | EN]`, `[🎯 Patch: ID Hybrid | EN Full]`).
   - Line-numbered Xeno Editor-style Monospace Diagnostic Console (`Consolas`) with syntax-colored status badges and right-hand minimap strip.
   - Deterministic embedded worker container at the PE overlay (`CELESLIB_WORKER_V1` header + 64-byte uppercase SHA-256 + `\r\n` + `"ace-worker.exe"` + `53,927,862`-byte `ace-worker.exe` payload), plus `--smoke-ui <dir>` offscreen GDI+ PNG renderer and CLI pass-through flags (`--verify-bundle`, `--status`, `--install`, `--restore`, `--self-test`).

**Tech Stack:** Python 3.12 (`uv run --python 3.12`), Pillow (`PIL`), MinGW-w64 (`x86_64-w64-mingw32-g++`, `x86_64-w64-mingw32-windres`), Win32 + GDI+ + DWM API, Pytest, GitHub CLI (`gh`), Graft (`graft build`).

**Spec:** `/home/whise/project/project-klien/patcher/.agents/plan/2026-11-04-celeslib-xeno-ui-and-rebranding-plan.md`

## Global Constraints

- **Runtime Python Version:** Always use `/home/whise/.local/bin/uv run --python 3.12` when compiling `.pyc`, packing `PYZ.pyz`, or running `pytest`.
- **Protected Archive Rule:** NEVER touch or delete `/home/whise/project/project-pribadi/celeslib-webnovel/.agents/archive` or its contents. Only read `/home/whise/project/project-pribadi/celeslib-webnovel/public/Logo.webp` and `web-app-manifest-512x512.png`.
- **Sudo / Host Packages:** If `x86_64-w64-mingw32-g++` is not installed, install `g++-mingw-w64-x86-64` and `binutils-mingw-w64-x86-64` via `echo whisegroup089 | sudo -S apt-get update && echo whisegroup089 | sudo -S apt-get install -y g++-mingw-w64-x86-64 binutils-mingw-w64-x86-64`.
- **Zero CPDD Branding Leakage:** The final executable must contain **zero** occurrences of `"CPDD"`, `"CPDD Discord"`, or the old cyan/purple dragon PNG in its outer GUI binary or PE resources.
- **Release Versioning:**
  - Application Brand & Title: `Celeslib Honor of Kings: Ace Patcher`
  - Application Release Version: `v1.0.0` (Git tag `v1.0.0-celeslib`, PE `FileVersion` `1.0.0.0`, `ProductVersion` `1.0.0-celeslib`)
  - Target Game Build Badge: `Game Build 1.4.12`
  - Primary Output Executable: `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (with compatibility copy at `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` so both filenames remain valid if referenced by external scripts, or unified via `dist/SHA256SUMS.txt`).

---

## Forensic Note: Why Certificates (`certifi` & `x509`) Exist in This Project

1. **`Honor of Kings Ace English Patcher 1.4.12.exe_extracted/certifi/cacert.pem` (`235,863` bytes):**
   - This is the Mozilla Root CA Certificate Bundle from the Python `certifi` package.
   - It was bundled into `ace-worker.exe` by PyInstaller only because the upstream CPDD developer's build environment included `httpx` / `httpcore` / `ssl` (referenced by `wxq_patch/gemini.pyc`, an offline script used during development to call the Google Gemini API).
   - At runtime on a player's PC, `wxq_patch/adaptive.pyc` operates **100% offline** (`"Only restore receipts persist. No translation learning, network calls..."`), so `certifi/cacert.pem` is never used during PC patching.
2. **`cryptography.x509.CertificateBuilder` inside `wxq_patch/mobile.pyc` (`cryptography-50.0.2`):**
   - Used exclusively by the **Android Phone (USB)** patching mode. Modifying the Android game's `base.apk` invalidates Tencent's original APK signature, and Android rejects unsigned APKs. `mobile.pyc` generates a local per-Windows-user self-signed X.509 certificate on the user's PC to re-sign the patched APK locally.
3. **Windows PE Authenticode Certificate (`IMAGE_DIRECTORY_ENTRY_SECURITY`):**
   - The `.exe` PE header has `SecurityDir = 0x0 (size 0)` — neither the original `.exe` nor the repacked `.exe` uses a commercial Microsoft Authenticode code-signing certificate.

---

### Task 1: Build Official Celeslib Branding Assets & Multi-Size Windows Icon

**Files:**
- Create: `scripts/07_build_celeslib_assets.py`
- Create: `assets/branding/celeslib.ico`
- Create: `assets/branding/celeslib_logo_512.png`
- Create: `assets/branding/celeslib_logo_64.png`
- Create: `assets/branding/celeslib_logo_32.png`
- Test: `tests/test_celeslib_branding.py`

**Interfaces:**
- Consumes: `/home/whise/project/project-pribadi/celeslib-webnovel/public/Logo.webp`, `/home/whise/project/project-pribadi/celeslib-webnovel/public/web-app-manifest-512x512.png`
- Produces: `assets/branding/celeslib.ico`, `assets/branding/celeslib_logo_512.png`, `assets/branding/celeslib_logo_64.png`, `assets/branding/celeslib_logo_32.png`, `src/gui/celeslib_logo_rgba.h` (pre-decoded RGBA pixel array of the Celeslib Star logo for zero-failure rendering inside GDI+)

- [x] **Step 1: Add `pillow` to dev dependencies and write failing test `tests/test_celeslib_branding.py`**

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "assets" / "branding"
HEADER_PATH = ROOT / "src" / "gui" / "celeslib_logo_rgba.h"


def test_celeslib_branding_assets_generated() -> None:
    ico = BRAND_DIR / "celeslib.ico"
    png512 = BRAND_DIR / "celeslib_logo_512.png"
    png64 = BRAND_DIR / "celeslib_logo_64.png"
    png32 = BRAND_DIR / "celeslib_logo_32.png"

    assert ico.exists() and ico.stat().st_size > 1_000
    assert png512.exists() and png512.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert png64.exists() and png64.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert png32.exists() and png32.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert HEADER_PATH.exists()
    header_txt = HEADER_PATH.read_text(encoding="utf-8")
    assert "CELESLIB_LOGO_64_BGRA" in header_txt
    assert "CELESLIB_LOGO_32_BGRA" in header_txt
```

- [x] **Step 2: Run test to verify it fails**

Run: `/home/whise/.local/bin/uv run --python 3.12 pytest tests/test_celeslib_branding.py -v`
Expected: FAIL (`AssertionError: assert False` because `assets/branding/celeslib.ico` does not exist yet).

- [x] **Step 3: Implement `scripts/07_build_celeslib_assets.py` and run it**

```python
#!/usr/bin/env python3
"""Extract official Celeslib logo from celeslib-webnovel and build .ico, .png, and C++ BGRA headers."""

from __future__ import annotations

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WEBNOVEL_PUBLIC = Path("/home/whise/project/project-pribadi/celeslib-webnovel/public")
BRAND_DIR = ROOT / "assets" / "branding"
GUI_DIR = ROOT / "src" / "gui"


def _to_bgra_c_array(img: Image.Image, var_name: str) -> str:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    raw = rgba.tobytes()
    bgra = bytearray(len(raw))
    # Convert RGBA -> premultiplied-ready BGRA for GDI+ PixelFormat32bppARGB
    for i in range(0, len(raw), 4):
        r, g, b, a = raw[i], raw[i + 1], raw[i + 2], raw[i + 3]
        bgra[i] = b
        bgra[i + 1] = g
        bgra[i + 2] = r
        bgra[i + 3] = a
    hex_vals = ", ".join(f"0x{b:02X}" for b in bgra)
    return (
        f"static const unsigned int {var_name}_WIDTH = {w};\n"
        f"static const unsigned int {var_name}_HEIGHT = {h};\n"
        f"static const unsigned char {var_name}[{len(bgra)}] = {{ {hex_vals} }};\n"
    )


def main() -> None:
    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    GUI_DIR.mkdir(parents=True, exist_ok=True)

    src_512 = WEBNOVEL_PUBLIC / "web-app-manifest-512x512.png"
    src_webp = WEBNOVEL_PUBLIC / "Logo.webp"
    base_img = Image.open(src_512 if src_512.exists() else src_webp).convert("RGBA")

    img_512 = base_img.resize((512, 512), Image.Resampling.NEAREST)
    img_256 = base_img.resize((256, 256), Image.Resampling.NEAREST)
    img_128 = base_img.resize((128, 128), Image.Resampling.NEAREST)
    img_64 = base_img.resize((64, 64), Image.Resampling.NEAREST)
    img_48 = base_img.resize((48, 48), Image.Resampling.NEAREST)
    img_32 = base_img.resize((32, 32), Image.Resampling.NEAREST)
    img_16 = base_img.resize((16, 16), Image.Resampling.NEAREST)

    img_512.save(BRAND_DIR / "celeslib_logo_512.png", format="PNG")
    img_64.save(BRAND_DIR / "celeslib_logo_64.png", format="PNG")
    img_32.save(BRAND_DIR / "celeslib_logo_32.png", format="PNG")

    img_256.save(
        BRAND_DIR / "celeslib.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    header_content = (
        "#pragma once\n"
        "// Auto-generated from celeslib-webnovel/public/Logo.webp\n\n"
        + _to_bgra_c_array(img_64, "CELESLIB_LOGO_64_BGRA")
        + "\n"
        + _to_bgra_c_array(img_32, "CELESLIB_LOGO_32_BGRA")
    )
    (GUI_DIR / "celeslib_logo_rgba.h").write_text(header_content, encoding="utf-8")
    print("Generated Celeslib branding assets in", BRAND_DIR)


if __name__ == "__main__":
    main()
```

- [x] **Step 4: Run `scripts/07_build_celeslib_assets.py` and verify `tests/test_celeslib_branding.py` passes**

Run:
```bash
/home/whise/.local/bin/uv add --dev pillow
/home/whise/.local/bin/uv run --python 3.12 python scripts/07_build_celeslib_assets.py
/home/whise/.local/bin/uv run --python 3.12 pytest tests/test_celeslib_branding.py -v
```
Expected: PASS

- [x] **Step 5: Commit Task 1**

```bash
git add pyproject.toml uv.lock scripts/07_build_celeslib_assets.py assets/branding/ src/gui/celeslib_logo_rgba.h tests/test_celeslib_branding.py
git commit -m "feat(branding): add Celeslib logo assets, multi-size Windows icon, and BGRA C++ headers"
```

---

### Task 2: Dual-Language Worker Engine (`CELESLIB_PATCH_LANG=id|en` & `CELESLIB_UI_LANG=id|en`)

**Files:**
- Modify: `src/acepatchindo/dual_state_patch.py`
- Modify: `scripts/05_repack_windows_exe.py`
- Modify: `scripts/03_patch_worker_modules.py`
- Modify: `tests/test_dual_state_engine.py`

**Interfaces:**
- Consumes: `data/catalog_checkpoints/catalog.json.gz`, `data/catalog_checkpoints/en_to_id_map.json`, `Honor of Kings Ace English Patcher 1.4.12.exe_extracted/catalog/catalog.json.gz`
- Produces:
  - Updated `build_combined_catalog_gz()` in `scripts/05_repack_windows_exe.py` that embeds:
    - `en_to_id`: maps English gameplay descriptions -> Indonesian gameplay descriptions (`~4,183` entries)
    - `id_to_en`: maps Indonesian gameplay descriptions -> English gameplay descriptions (`~4,183` entries)
    - `zh_to_en_gameplay`: maps Chinese gameplay descriptions -> original English gameplay descriptions (`~4,183` entries)
  - Updated `Catalog` and `translate_table` in `src/acepatchindo/dual_state_patch.py` that checks `os.environ.get("CELESLIB_PATCH_LANG", "id").lower()`:
    - When `CELESLIB_PATCH_LANG == "id"` (default): translates Chinese or English game files into **Indonesian Hybrid Gameplay (`ID`)**.
    - When `CELESLIB_PATCH_LANG == "en"`: swaps the 4,183 gameplay targets to `zh_to_en_gameplay` and uses `id_to_en` so Chinese or Indonesian-patched game files are translated into **100% Full English (`EN`)**!
  - Updated `_localize_report_message` and `_catalog_fingerprint` in `src/acepatchindo/dual_state_patch.py`:
    - `_catalog_fingerprint` appends `:lang={patch_lang}` to the SHA-256 stamp so switching between `ID Hybrid` and `EN Full` automatically triggers pre-install restore of untouched Chinese `originals/` before applying the new language mode!
    - `_localize_report_message` checks `os.environ.get("CELESLIB_UI_LANG", "id").lower()`: if `"en"`, returns clean English report messages (updating `"English installed..."` to `"Indonesian Hybrid patch installed and verified..."` when `patch_lang == "id"` and `"Full English patch installed and verified..."` when `patch_lang == "en"`); if `"id"`, returns Bahasa Indonesia report messages!

- [x] **Step 1: Write failing tests in `tests/test_dual_state_engine.py` for `CELESLIB_PATCH_LANG=en` and `CELESLIB_UI_LANG=en|id`**

Add a test function `test_dual_state_patch_lang_switch_id_and_en(monkeypatch)` in `tests/test_dual_state_engine.py` that verifies:
1. With `CELESLIB_PATCH_LANG="id"`, a sample table containing Chinese and English gameplay descriptions translates to Bahasa Indonesia (`ID`), and switching to `CELESLIB_PATCH_LANG="en"` translates both Chinese and Indonesian-patched tables back to 100% English (`EN`).
2. `_localize_report_message` respects `CELESLIB_UI_LANG="id"` vs `CELESLIB_UI_LANG="en"`.

- [x] **Step 2: Run `pytest tests/test_dual_state_engine.py -v` to confirm failure**

Run: `/home/whise/.local/bin/uv run --python 3.12 pytest tests/test_dual_state_engine.py -v`
Expected: FAIL on the new language-switching assertions.

- [x] **Step 3: Update `src/acepatchindo/dual_state_patch.py` and `scripts/03_patch_worker_modules.py`**

Update `render_table_catalog_source` and `render_adaptive_source` in `src/acepatchindo/dual_state_patch.py`:

```python
def render_table_catalog_source(orig_marshal_bytes: bytes) -> str:
    return f'''"""Dual-state (ZH->ID, EN->ID, ZH->EN, ID->EN) table_catalog module for Celeslib HoK Ace Patcher."""
from __future__ import annotations

import copy
import gzip
import json
import marshal
import os
from collections import Counter
from pathlib import Path

_ORIG_MARSHAL = {orig_marshal_bytes!r}
exec(marshal.loads(_ORIG_MARSHAL), globals())

_OrigCatalog = Catalog


class Catalog(_OrigCatalog):
    def __init__(self, data: dict) -> None:
        patch_lang = os.environ.get("CELESLIB_PATCH_LANG", "id").strip().lower()
        self.patch_lang = "en" if patch_lang == "en" else "id"

        raw_en_to_id = data.get("en_to_id") if isinstance(data.get("en_to_id"), dict) else {{}}
        raw_id_to_en = data.get("id_to_en") if isinstance(data.get("id_to_en"), dict) else {{
            v: k for k, v in raw_en_to_id.items() if isinstance(k, str) and isinstance(v, str) and k != v
        }}
        raw_zh_to_en = data.get("zh_to_en_gameplay") if isinstance(data.get("zh_to_en_gameplay"), dict) else {{}}

        if self.patch_lang == "en" and (raw_zh_to_en or raw_id_to_en):
            data = copy.copy(data)
            if "unique" in data and isinstance(data["unique"], dict):
                u = dict(data["unique"])
                for zh_k, en_v in raw_zh_to_en.items():
                    if zh_k in u:
                        u[zh_k] = en_v
                data["unique"] = u
            if "assets" in data and isinstance(data["assets"], dict):
                new_assets = {{}}
                for a_k, a_map in data["assets"].items():
                    if isinstance(a_map, dict):
                        am = dict(a_map)
                        for rec_k, val in list(am.items()):
                            if isinstance(val, str) and val in raw_id_to_en:
                                am[rec_k] = raw_id_to_en[val]
                        new_assets[a_k] = am
                    else:
                        new_assets[a_k] = a_map
                data["assets"] = new_assets
            if "english_updates" in data and isinstance(data["english_updates"], list):
                new_eu = []
                for item in data["english_updates"]:
                    if isinstance(item, dict) and item.get("target") in raw_id_to_en:
                        it = dict(item)
                        it["target"] = raw_id_to_en[item["target"]]
                        new_eu.append(it)
                    else:
                        new_eu.append(item)
                data["english_updates"] = new_eu

        super().__init__(data)

        if self.patch_lang == "en":
            self.en_to_id: dict[str, str] = {{
                k: v
                for k, v in raw_id_to_en.items()
                if isinstance(k, str) and isinstance(v, str) and k != v and k not in self.targets
            }}
        else:
            self.en_to_id = {{
                k: v
                for k, v in raw_en_to_id.items()
                if isinstance(k, str) and isinstance(v, str) and k != v and k not in self.targets
            }}
```

And in `render_adaptive_source`:
- Update `_catalog_fingerprint(assets: Path) -> str` to include `patch_lang = os.environ.get("CELESLIB_PATCH_LANG", "id").strip().lower()`:
  `return f"{sha}:{patch_lang}"`
- Update `_localize_report_message(report: dict) -> dict` so that:
  - When `os.environ.get("CELESLIB_UI_LANG", "id").strip().lower() == "en"`:
    - If `patch_lang == "id"`, replaces `"English installed and verified."` with `"Indonesian Hybrid patch installed and verified."` and `"English files are installed"` with `"Indonesian Hybrid files are installed"`, keeping the rest of the message in clean English.
    - If `patch_lang == "en"`, keeps the clean English report message (`"English installed and verified..."`).
  - When `CELESLIB_UI_LANG` is `"id"` (default):
    - Applies `_ID_MESSAGE_REPLACEMENTS` (converting status messages to Bahasa Indonesia, adjusting `"Bahasa Indonesia berhasil dipasang..."` vs `"Bahasa Inggris (Full) berhasil dipasang..."` based on `patch_lang`).
- Also update `receipt_root` fallback in `render_adaptive_source` so it checks both `%LOCALAPPDATA%\Celeslib\HoK Ace Patcher\adaptive` and `%LOCALAPPDATA%\HoK Ace English Patch\adaptive` seamlessly.

- [x] **Step 4: Update `build_combined_catalog_gz()` in `scripts/05_repack_windows_exe.py` to include `id_to_en` and `zh_to_en_gameplay`**

In `scripts/05_repack_windows_exe.py`:
```python
ORIG_CATALOG_GZ = (
    ROOT
    / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
    / "catalog"
    / "catalog.json.gz"
)

def build_combined_catalog_gz() -> bytes:
    with gzip.open(ID_CATALOG_GZ, "rt", encoding="utf-8") as f:
        payload = json.load(f)
    en_to_id = json.loads(EN_TO_ID_JSON.read_text(encoding="utf-8"))
    payload["en_to_id"] = en_to_id
    payload["id_to_en"] = {v: k for k, v in en_to_id.items() if k != v}

    if ORIG_CATALOG_GZ.exists():
        with gzip.open(ORIG_CATALOG_GZ, "rt", encoding="utf-8") as f:
            orig_cat = json.load(f)
        orig_unique = orig_cat.get("unique", {})
        cur_unique = payload.get("unique", {})
        payload["zh_to_en_gameplay"] = {
            zh: en_val
            for zh, en_val in orig_unique.items()
            if zh in cur_unique and cur_unique[zh] != en_val
        }
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return gzip.compress(raw_json, compresslevel=9, mtime=0)
```

- [x] **Step 5: Recompile worker `.pyc` modules and run `pytest tests/test_dual_state_engine.py -v`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/03_patch_worker_modules.py
/home/whise/.local/bin/uv run --python 3.12 pytest tests/test_dual_state_engine.py -v
```
Expected: PASS

- [x] **Step 6: Commit Task 2**

```bash
git add src/acepatchindo/dual_state_patch.py scripts/03_patch_worker_modules.py scripts/05_repack_windows_exe.py extracted_source/wxq_patch/table_catalog.pyc extracted_source/wxq_patch/adaptive.pyc tests/test_dual_state_engine.py
git commit -m "feat(engine): support runtime ID/EN patch mode and bilingual UI report messages"
```

---

### Task 3: Native Windows x86-64 Celeslib Xeno v1.3.0 GUI (`src/gui/celeslib_xeno_gui.cpp` & `src/gui/celeslib_xeno.rc`)

**Files:**
- Create: `src/gui/celeslib_xeno.rc`
- Create: `src/gui/celeslib_xeno_i18n.h`
- Create: `src/gui/celeslib_xeno_gui.cpp`
- Create: `scripts/08_compile_xeno_gui.py`
- Test: `tests/test_xeno_gui_build.py`

**Interfaces:**
- Consumes: `src/gui/celeslib_logo_rgba.h`, `assets/branding/celeslib.ico`
- Produces: Compiled Windows 64-bit PE GUI binary `build/celeslib_xeno_stub.exe` (`IMAGE_SUBSYSTEM_WINDOWS_GUI = 2`) with:
  - Embedded Celeslib multi-resolution icon (`IDI_CELESLIB_ICON`) and `VS_VERSION_INFO` (`CompanyName = "Celeslib"`, `ProductName = "Celeslib Honor of Kings: Ace Patcher"`, `ProductVersion = "1.0.0-celeslib"`, `FileVersion = "1.0.0.0"`).
  - Xeno v1.3.0 UI (`https://www.xeno.now/`) rendered via double-buffered GDI+ (`#09090B` canvas, `#0D0D11` sidebar, `#14141A` pill buttons & cards, `#24242E` `1px` crisp borders, `#8B5CF6` Celeslib violet-blue accent, `#34D399` emerald status indicators):
    1. **Custom Frameless/Dark Titlebar:** Celeslib 32x32 pixel-star logo, `Celeslib` title, `v1.0.0` version badge, `HoK: Ace 1.4.12` target badge, quick language toggle pill `[🌐 UI: ID | EN]`, quick patch mode pill `[🎯 Mode: ID Hybrid | EN Full]`, and `[—] [□] [×]` window controls.
    2. **Left Sidebar (`Dashboard`, `Patcher`, `Android (USB)`, `Settings`)** with collapse toggle (`<`) and bottom Celeslib copyright badge.
    3. **Top Pill Action Toolbar (in `Patcher` view):**
       - `[▷ Pasang Patch]` / `[▷ Install Patch]`
       - `[↺ Pulihkan File]` / `[↺ Restore Files]`
       - `[🔍 Periksa File]` / `[🔍 Check Files]`
       - `[📁 Pilih Folder]` / `[📁 Browse Folder]`
       - `[⚡ Auto-Detect]`
       - `[🗑 Bersihkan]` / `[🗑 Clear Log]`
    4. **Editor-Style Diagnostic Console:** Line-numbered monospace console (`Consolas`) with syntax coloring, game path header bar, status badge, and right-side minimap strip matching `Xeno-V1.3.0aBETA.png`.
    5. **Settings View:** Interactive cards to switch **Application UI Language (`Bahasa Indonesia` / `English`)** and **Game Patch Language Mode (`Indonesian Hybrid Gameplay` / `Full English`)**, persisted in `%LOCALAPPDATA%\Celeslib\HoK Ace Patcher\config.json`.
    6. **Embedded Worker Extraction & Execution:** Reads the deterministic trailer (`CELESLIB_WORKER_V1` + 64-char SHA-256 + `\r\n` + `"ace-worker.exe"` + `ace-worker.exe` bytes, or fixed offset `0x4CABFA`/`0x4CAC4A`), verifies the SHA-256 digest before execution, caches `ace-worker.exe` in `%LOCALAPPDATA%\Celeslib\HoK Ace Patcher\engine\<sha256>\ace-worker.exe`, and invokes it asynchronously with `CELESLIB_UI_LANG` and `CELESLIB_PATCH_LANG`.
    7. **CLI & Headless Smoke Rendering Flags:** Supports `--smoke-ui <dir>` (renders `patcher_id.png`, `patcher_en.png`, `dashboard_id.png`, `settings_id.png` offscreen via `Gdiplus::Bitmap`), `--verify-bundle`, `--status`, `--install`, `--restore`, `--discover`, and `--self-test`.

- [x] **Step 1: Ensure `g++-mingw-w64-x86-64` and `binutils-mingw-w64-x86-64` are installed**

Run:
```bash
which x86_64-w64-mingw32-g++ x86_64-w64-mingw32-windres || (echo whisegroup089 | sudo -S apt-get update && echo whisegroup089 | sudo -S apt-get install -y g++-mingw-w64-x86-64 binutils-mingw-w64-x86-64)
x86_64-w64-mingw32-g++ --version
```
Expected: `x86_64-w64-mingw32-g++` version output with exit code `0`.

- [x] **Step 2: Write failing test `tests/test_xeno_gui_build.py`**

```python
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB_EXE = ROOT / "build" / "celeslib_xeno_stub.exe"


def test_compiled_xeno_gui_stub_pe_headers_and_branding() -> None:
    assert STUB_EXE.exists(), f"Missing compiled GUI stub: {STUB_EXE}"
    raw = STUB_EXE.read_bytes()
    assert raw[:2] == b"MZ"
    pe_off = struct.unpack_from("<I", raw, 0x3C)[0]
    assert raw[pe_off : pe_off + 4] == b"PE\x00\x00"
    subsystem = struct.unpack_from("<H", raw, pe_off + 24 + 68)[0]
    assert subsystem == 2, f"Expected IMAGE_SUBSYSTEM_WINDOWS_GUI (2), got {subsystem}"

    # Must contain Celeslib branding, version v1.0.0, and bilingual ID/EN strings
    assert b"Celeslib" in raw
    assert b"v1.0.0" in raw
    assert b"1.4.12" in raw
    assert b"Pasang Patch" in raw
    assert b"Install Patch" in raw
    assert b"CELESLIB_UI_LANG" in raw
    assert b"CELESLIB_PATCH_LANG" in raw

    # Must NOT contain legacy CPDD branding
    assert b"CPDD" not in raw
    assert b"cpdd-logo" not in raw
```

- [x] **Step 3: Run `pytest tests/test_xeno_gui_build.py -v` to confirm it fails**

Run: `/home/whise/.local/bin/uv run --python 3.12 pytest tests/test_xeno_gui_build.py -v`
Expected: FAIL (`Missing compiled GUI stub`).

- [x] **Step 4: Create `src/gui/celeslib_xeno.rc`, `src/gui/celeslib_xeno_i18n.h`, `src/gui/celeslib_xeno_gui.cpp`, and `scripts/08_compile_xeno_gui.py`**

1. **`src/gui/celeslib_xeno.rc`**:
   - Embeds `IDI_CELESLIB_ICON ICON "../../assets/branding/celeslib.ico"`
   - Embeds `VS_VERSION_INFO` with:
     - `CompanyName`: `"Celeslib"`
     - `FileDescription`: `"Celeslib Honor of Kings: Ace Patcher"`
     - `FileVersion`: `"1.0.0.0"`
     - `InternalName`: `"CeleslibHoKAcePatcher"`
     - `LegalCopyright`: `"Copyright (C) 2026 Celeslib. All Rights Reserved."`
     - `OriginalFilename`: `"Celeslib-HoK-Ace-Patcher-v1.0.0.exe"`
     - `ProductName`: `"Celeslib Honor of Kings: Ace Patcher"`
     - `ProductVersion`: `"1.0.0-celeslib (Game Build 1.4.12)"`
2. **`src/gui/celeslib_xeno_i18n.h`**:
   - Defines `struct UiStrings` with full **Bahasa Indonesia (`STRINGS_ID`)** and **English (`STRINGS_EN`)** tables for every UI element:
     - Sidebar: `Dashboard` (`Beranda` / `Dashboard`), `Patcher` (`Eksekutor Patch` / `Patch Executor`), `Android` (`Android (USB)` / `Android (USB)`), `Settings` (`Pengaturan` / `Settings`).
     - Toolbar pills: `Pasang Patch` / `Install Patch`, `Pulihkan File` / `Restore Files`, `Periksa File` / `Check Files`, `Pilih Folder` / `Browse Folder`, `Deteksi Otomatis` / `Auto-Detect`, `Bersihkan Log` / `Clear Log`.
     - Header toggles: `Bahasa UI: ID` / `UI Lang: EN`, `Mode Patch: ID Hybrid` / `Patch Mode: EN Full`.
     - Confirmation dialogs, status badges (`SIAP / READY`, `TERPASANG / INSTALLED`, `MEMPROSES / WORKING`, `GALAT / ERROR`), Settings descriptions, and Android USB guide.
3. **`src/gui/celeslib_xeno_gui.cpp`**:
   - Implements the complete Win32 + GDI+ Xeno v1.3.0 interface (`980x620` window, custom frameless/dark hit-testing `WM_NCHITTEST` for dragging/resizing, hover state tracking, double-buffered `WM_PAINT` via `RenderXenoFrame(Gdiplus::Graphics&, ...)`).
   - Implements `LocateAndExtractWorker()` which reads the embedded `ace-worker.exe` from the executable's deterministic slot (`WORKER_MAGIC_HEADER` or offset `0x4CABFA`..`0x3838C00`), verifies the 64-character uppercase SHA-256 hex digest, extracts to `%LOCALAPPDATA%\Celeslib\HoK Ace Patcher\engine\<sha256>\ace-worker.exe`, and executes worker actions on a background thread with `CELESLIB_UI_LANG` and `CELESLIB_PATCH_LANG` set in the environment.
   - Implements `--smoke-ui <dir>` offscreen PNG generation using `Gdiplus::Bitmap` and `RenderXenoFrame` so UI screenshots can be exported and verified automatically.
4. **`scripts/08_compile_xeno_gui.py`**:
   - Runs `x86_64-w64-mingw32-windres` on `src/gui/celeslib_xeno.rc` -> `build/celeslib_xeno_res.o`
   - Runs `x86_64-w64-mingw32-g++ -O2 -std=c++17 -municode -mwindows` on `src/gui/celeslib_xeno_gui.cpp` + `build/celeslib_xeno_res.o` -> `build/celeslib_xeno_stub.exe` (`-lgdiplus -ldwmapi -luxtheme -lshlwapi -lcomdlg32 -lshell32 -lole32 -luuid -static-libgcc -static-libstdc++ -Wl,-Bstatic -lstdc++ -lpthread -Wl,-Bdynamic -s`).
   - Also includes a Python/Pillow pixel-accurate preview generator `render_xeno_ui_previews(out_dir)` in `scripts/08_compile_xeno_gui.py` that renders `assets/previews/xeno_patcher_id.png` and `assets/previews/xeno_patcher_en.png` on Linux for visual inspection and documentation.

- [x] **Step 5: Compile the Xeno GUI stub and run `pytest tests/test_xeno_gui_build.py -v`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/08_compile_xeno_gui.py
/home/whise/.local/bin/uv run --python 3.12 pytest tests/test_xeno_gui_build.py -v
```
Expected: PASS

- [x] **Step 6: Commit Task 3**

```bash
git add src/gui/ scripts/08_compile_xeno_gui.py assets/previews/ tests/test_xeno_gui_build.py
git commit -m "feat(gui): implement Celeslib Xeno v1.3.0 native Windows GUI with ID/EN toggle"
```

---

### Task 4: Assemble Final Celeslib Release Executable (`v1.0.0-celeslib`) & Update Integrity Suite

**Files:**
- Modify: `scripts/05_repack_windows_exe.py`
- Modify: `tests/test_repack_integrity.py`
- Modify: `scripts/06_publish_github_release.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `build/celeslib_xeno_stub.exe`, repacked `ace-worker.exe` (`53,927,862` bytes)
- Produces:
  - `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (and compatibility copy `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`)
  - `dist/SHA256SUMS.txt`
  - Binary Layout of `Celeslib-HoK-Ace-Patcher-v1.0.0.exe`:
    - `[0 .. stub_len)`: Compiled native `celeslib_xeno_stub.exe` (aligned to 16 bytes)
    - `[marker_offset .. marker_offset + 18)`: `b"CELESLIB_WORKER_V1"` (`18` bytes)
    - `[sha_offset .. sha_offset + 66)`: `worker_sha256.upper().encode('ascii') + b"\r\n"` (`66` bytes)
    - `[name_offset .. name_offset + 14)`: `b"ace-worker.exe"` (`14` bytes)
    - `[worker_start .. worker_end)`: Repacked `ace-worker.exe` (`53,927,862` bytes)
    - `[worker_end .. worker_end + 8)`: `struct.pack("<Q", sha_offset)` (`8`-byte footer storing the exact offset of the 66-byte SHA-256 slot so both `celeslib_xeno_gui.cpp` and `tests/test_repack_integrity.py` locate the embedded worker in $O(1)$ time!)

- [x] **Step 1: Update `tests/test_repack_integrity.py` to test the new Celeslib Xeno executable, SHA-256 worker guard, zero CPDD leakage, and bilingual catalog (`en_to_id`, `id_to_en`, `zh_to_en_gameplay`)**

Update `tests/test_repack_integrity.py` to verify:
1. `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` exists and has a valid PE32+ GUI header (`IMAGE_SUBSYSTEM_WINDOWS_GUI == 2`).
2. The embedded `ace-worker.exe` slice (`53,927,862` bytes) matches the 64-byte uppercase SHA-256 hex digest stored before `"ace-worker.exe"`.
3. The outer GUI stub contains Celeslib branding (`b"Celeslib"`, `b"v1.0.0"`, `b"Pasang Patch"`, `b"Install Patch"`, `b"CELESLIB_UI_LANG"`, `b"CELESLIB_PATCH_LANG"`) and zero `b"CPDD"` strings.
4. `pyinstxtractor.py` extracts the embedded `ace-worker.exe` with zero errors under Python 3.12, and `catalog/catalog.json.gz` contains `unique` (`41,483`), `english_updates` (`29,750`), `en_to_id` (`3,000..6,000`), `id_to_en` (`3,000..6,000`), and `zh_to_en_gameplay` (`3,000..6,000`).

- [x] **Step 2: Update `scripts/05_repack_windows_exe.py` to build `build/celeslib_xeno_stub.exe` and assemble `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` (plus compatibility copy `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`)**

- [x] **Step 3: Run `scripts/05_repack_windows_exe.py` and run the full test suite (`pytest -v`)**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py
/home/whise/.local/bin/uv run --python 3.12 pytest -v
```
Expected: All tests across all test files pass (`0` failures).

- [x] **Step 4: Update `README.md`, `scripts/06_publish_github_release.py`, and rebuild Graft index (`graft build`)**

1. Update `README.md` with Celeslib branding, Xeno v1.3.0 UI preview screenshots, release version `v1.0.0-celeslib` (Target Game Build `1.4.12`), dual-language instructions (`UI: ID / EN` and `Patch Mode: ID Hybrid / EN Full`), certificate explanation, and updated SHA-256 checksums.
2. Update `scripts/06_publish_github_release.py` to publish release tag `v1.0.0-celeslib` (`Celeslib Honor of Kings: Ace Patcher v1.0.0 (Game Build 1.4.12)`) with `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` and `dist/SHA256SUMS.txt`.
3. Run `graft build` to refresh the repository context graph.

- [x] **Step 5: Commit, tag `v1.0.0-celeslib`, push to GitHub, and publish release**

```bash
graft build
git add .
git commit -m "feat(release): Celeslib Xeno v1.3.0 UI, v1.0.0-celeslib branding, and ID/EN language switcher"
git push origin main
/home/whise/.local/bin/uv run --python 3.12 python scripts/06_publish_github_release.py
```

---

## Phase 2: Remediation of Executor Omissions & Critical Bugs (Tasks 5–7)

> **Audit Findings (Mandatory Fixes):**
> Deep forensic inspection of the executor's implementation revealed **6 critical defects/omissions** that MUST be fixed before the release can be considered functional:
> 1. **Broken `ace-worker.exe` CLI Invocation (`src/gui/celeslib_xeno_gui.cpp`):** `ExecuteWorkerAction` invokes `ace-worker.exe --json <action> --game "<path>"`, which crashes immediately with `argparse` exit code `2` because `wxq_patch/adaptive.pyc:main` requires positional `action` (`status`, `install`, `restore`, `stage`, `discover`, `self-test`), optional `--game-dir <path>`, **required `--work <work_dir>`**, and **required `--result <result_json_path>`** (and has NO `--json` or `--game` flags!). Furthermore, `ExecuteWorkerAction` never reads `result.json` to display `result["message"]`, update `g_state.status_text` / `g_state.status_color` from `result["state"]`, or populate `g_state.game_dir` from `result["game_dir"]` after `discover` (`Auto-Detect`).
> 2. **Dead Android (USB) Tab Buttons (`src/gui/celeslib_xeno_gui.cpp`):** `NavView::Android` renders buttons (`Pindai Perangkat` / `Scan Device`, `Pasang ke Android` / `Patch Android`), but `WM_LBUTTONDOWN` has zero click handlers for `NavView::Android`, and `NavView::Android` does not invoke `ace-worker.exe mobile-worker --work "<work_dir>" --operation devices|patch|recover` or render the diagnostic console output.
> 3. **Missing Cryptographic SHA-256 Verification & 64-Bit File Seeking (`src/gui/celeslib_xeno_gui.cpp`):** `LocateAndExtractWorker` uses 32-bit `SetFilePointer` without a high-order `LONG` and never computes or verifies the actual SHA-256 digest of the extracted `53,927,862`-byte `ace-worker.exe` via Windows CryptoAPI (`CryptAcquireContextW` / `CryptCreateHash(CALG_SHA_256)`), nor checks that an already-cached `ace-worker.exe` on disk has exact size `53,927,862` bytes.
> 4. **Incomplete Window Controls, Sidebar Collapse, Hover Tracking & CLI Pass-Through (`src/gui/celeslib_xeno_gui.cpp`):**
>    - Maximize/Restore button `[□]` click handler is missing, and dragging the custom header bar (`y < 48`) does not move the window.
>    - Collapsible sidebar toggle (`<` / `>`) and `WM_MOUSEMOVE` hover tracking (`hovered_btn`) were skipped.
>    - CLI pass-through flags (`--status`, `--install`, `--restore`, `--discover`, `--self-test`) and 4-view `--smoke-ui` rendering (`xeno_patcher_id.png`, `xeno_patcher_en.png`, `xeno_dashboard_id.png`, `xeno_settings_id.png`) were skipped or stubbed.
> 5. **Visual Defects in Preview PNGs (`scripts/08_compile_xeno_gui.py` & `src/gui/celeslib_xeno_i18n.h`):**
>    - Header toggles `[🌐 UI: ID]` and `[🎯 Mode: ID Hybrid]` render with missing-glyph tofu boxes (`▯ UI: ID`, `▯ Mode: ID Hybrid`) in `assets/previews/xeno_patcher_id.png` and `xeno_patcher_en.png` because `DejaVuSans` lacks multicolor emoji glyphs. Replace emoji prefixes with crisp vector icons or BMP geometric symbols supported across all fonts.
>    - Status badge in `scripts/08_compile_xeno_gui.py` draws both a green ellipse AND `"● SIAP"`, producing duplicate bullets (`🟢 ● SIAP`).
> 6. **Dead Code & Uncommitted Working Tree Changes:** Remove unused `GUI_STRING_PATCHES` and `apply_gui_patches` from `scripts/05_repack_windows_exe.py` and ensure `git status` is 100% clean.

---

### Task 5: Fix `ace-worker.exe` CLI Protocol, `result.json` Parser, CryptoAPI SHA-256 Verification & Android USB Execution in `src/gui/celeslib_xeno_gui.cpp`

**Files:**
- Modify: `src/gui/celeslib_xeno_i18n.h`
- Modify: `src/gui/celeslib_xeno_gui.cpp`
- Modify: `scripts/08_compile_xeno_gui.py`
- Modify: `tests/test_xeno_gui_build.py`

- [x] **Step 1: Add regression assertions to `tests/test_xeno_gui_build.py` verifying the exact worker CLI flags (`--game-dir`, `--work`, `--result`, `mobile-worker`, `--operation`), CryptoAPI SHA-256 verification, and 4 preview PNGs without tofu glyphs**

In `tests/test_xeno_gui_build.py`, assert that:
1. `build/celeslib_xeno_stub.exe` contains the exact wide/ASCII argument strings required by `wxq_patch/adaptive.pyc` and `wxq_patch/mobile.pyc`:
   - `"--game-dir".encode("utf-16le")`
   - `"--work".encode("utf-16le")`
   - `"--result".encode("utf-16le")`
   - `"mobile-worker".encode("utf-16le")`
   - `"--operation".encode("utf-16le")`
   - And does **NOT** contain the broken `"\" --json ".encode("utf-16le")` or `" --game \"".encode("utf-16le")` string.
2. `assets/previews/xeno_patcher_id.png`, `assets/previews/xeno_patcher_en.png`, `assets/previews/xeno_dashboard_id.png`, and `assets/previews/xeno_settings_id.png` all exist and are valid PNGs.

- [x] **Step 2: Fix `src/gui/celeslib_xeno_i18n.h` & `src/gui/celeslib_xeno_gui.cpp`**

1. **In `src/gui/celeslib_xeno_i18n.h`**:
   - Replace `L"🌐 UI: ID"` / `L"🌐 UI: EN"` with `L"UI: ID"` / `L"UI: EN"` (and draw a clean vector globe/language badge icon in GDI+/Pillow instead of relying on font emoji support).
   - Replace `L"🎯 Mode: ID Hybrid"` / `L"🎯 Mode: EN Full"` with `L"Mode: ID Hybrid"` / `L"Mode: EN Full"` (and draw a clean vector accent dot/diamond icon in GDI+/Pillow).
   - Add `android_btn_recover` (`L"Pulihkan Android"` / `L"Recover Android"`).
2. **In `src/gui/celeslib_xeno_gui.cpp`**:
   - **64-bit File Seeking & CryptoAPI SHA-256 Verification in `LocateAndExtractWorker()`:**
     - Use `SetFilePointerEx(hFile, liOffset, NULL, FILE_BEGIN)` instead of 32-bit `SetFilePointer`.
     - Include `<wincrypt.h>` and write `ComputeBufferOrFileSha256Hex(HANDLE hFile, uint64_t offset, uint64_t length)` using `CryptAcquireContextW(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT)`, `CryptCreateHash(hProv, CALG_SHA_256, 0, 0, &hHash)`, `CryptHashData`, and `CryptGetHashParam(hHash, HP_HASHVAL, ...)`.
     - If `out_worker_path` already exists on disk, verify its file size is `WORKER_EXACT_SIZE` (`53,927,862` bytes); if not, re-extract.
     - During extraction, compute the SHA-256 of the `53,927,862` bytes read from the executable and verify it matches `sha256_hex` case-insensitively before closing. If mismatched, delete `out_worker_path` and return `false`.
   - **Correct `ace-worker.exe` CLI Protocol & `result.json` Parsing in `ExecuteWorkerAction()`:**
     - Create `work_dir = GetCeleslibAppDataDir() + L"\\work"` and `result_path = work_dir + L"\\result.json"`. Delete any stale `result_path` before launching.
     - Construct the command line matching `wxq_patch/adaptive.pyc:main`:
       ```cpp
       cmd << L"\"" << worker_path << L"\" " << action
           << L" --work \"" << work_dir << L"\""
           << L" --result \"" << result_path << L"\"";
       if (!game_path.empty() && action != L"discover") {
           cmd << L" --game-dir \"" << game_path << L"\"";
       }
       ```
     - After `WaitForSingleObject(pi.hProcess, INFINITE)`, read `result_path` (UTF-8 JSON written by `ace-worker.exe`) and parse:
       - `"state"` (`"installed"`, `"clean"`, `"error"`),
       - `"message"` (append `[OK] <message>` or `[ERROR] <message>` to the console log!),
       - `"game_dir"` (if non-empty, update `g_state.game_dir` so `Auto-Detect` / `discover` and `status` automatically populate the detected game path in the UI!),
       - `"restore_available"` (log whether backup restore is available).
     - Update `g_state.status_text` and `g_state.status_color` accurately based on `"state"` and `exit_code`:
       - If `exit_code == 0`:
         - If `action == L"restore"` or `state == "clean"`: set status to `s.status_ready` (`SIAP` / `READY`) or `s.status_originals` (`FILE ASLI` / `ORIGINALS`).
         - If `action == L"install"` or `state == "installed"`: set status to `s.status_installed` (`TERPASANG` / `INSTALLED`).
   - **Working Android (USB) Actions (`ExecuteMobileWorkerAction`):**
     - Implement `ExecuteMobileWorkerAction(const std::wstring& operation)` which invokes:
       - For `devices` or `patch`: `"<worker_path>" mobile-worker --work "<work_dir>" --operation <operation>`
       - For `recover`: `"<worker_path>" mobile-recover --work "<work_dir>"`
     - Render the diagnostic console panel below the Android USB card in `NavView::Android` (`con_y = 244`) so the user can see live ADB device scan and patching output directly in the `Android (USB)` tab!
     - Wire up click handlers in `WM_LBUTTONDOWN` when `g_state.current_view == NavView::Android` for:
       1. `Pindai Perangkat` / `Scan Device` -> `ExecuteMobileWorkerAction(L"devices")`
       2. `Pasang ke Android` / `Patch Android` -> `ExecuteMobileWorkerAction(L"patch")`
       3. `Pulihkan Android` / `Recover Android` -> `ExecuteMobileWorkerAction(L"recover")`
   - **Complete Window Controls, Sidebar Collapse (`<`/`>`), Hover State (`WM_MOUSEMOVE`), and CLI Flags:**
     - Handle maximize/restore button `[□]` (`x >= g_state.width - 65 && x <= g_state.width - 40`) in `WM_LBUTTONDOWN` and allow dragging the window when clicking empty header space (`y < 48`).
     - Implement `bool sidebar_collapsed = false;` in `AppState` with a collapse toggle button `[<]` / `[>]` at the bottom/top of the sidebar, and implement `WM_MOUSEMOVE` to update `g_state.hovered_btn` for visual hover feedback on buttons.
     - Implement CLI pass-through in `wWinMain` for `--status`, `--install`, `--restore`, `--discover`, and `--self-test` (synchronously invoking `ace-worker.exe` with the proper `--work` and `--result` flags and returning its exit code), and update `--smoke-ui <dir>` to render all 4 previews (`xeno_patcher_id.png`, `xeno_patcher_en.png`, `xeno_dashboard_id.png`, `xeno_settings_id.png`).

- [x] **Step 3: Fix `scripts/08_compile_xeno_gui.py` Preview Generator (No Tofu Boxes, No Duplicate Status Dots, Render All 4 Views)**

1. Update `compile_xeno_gui()` in `scripts/08_compile_xeno_gui.py` to link `-lcrypt32`.
2. Update `render_xeno_preview()` in `scripts/08_compile_xeno_gui.py`:
   - Draw a crisp vector globe/pill icon and target dot using `ImageDraw` instead of `🌐` and `🎯` characters so there are **zero missing-glyph tofu boxes (`▯`)**.
   - Change `status_str` from `"● SIAP"` / `"● READY"` to `"SIAP"` / `"READY"` (since the green status dot is already drawn via `draw.ellipse(...)`).
   - Support `view="patcher" | "dashboard" | "settings"` and generate all 4 preview images in `assets/previews/`:
     - `assets/previews/xeno_patcher_id.png`
     - `assets/previews/xeno_patcher_en.png`
     - `assets/previews/xeno_dashboard_id.png`
     - `assets/previews/xeno_settings_id.png`

- [x] **Step 4: Compile and test `tests/test_xeno_gui_build.py`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/08_compile_xeno_gui.py
/home/whise/.local/bin/uv run --python 3.12 pytest tests/test_xeno_gui_build.py -v
```
Expected: PASS

---

### Task 6: Clean Up Dead Legacy Code in `scripts/05_repack_windows_exe.py`, Rebuild Release Executables & Verify Full Test Suite

**Files:**
- Modify: `scripts/05_repack_windows_exe.py`
- Modify: `tests/test_repack_integrity.py`

- [x] **Step 1: Remove unused `GUI_STRING_PATCHES` and `apply_gui_patches` from `scripts/05_repack_windows_exe.py` and rebuild `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py
```

- [x] **Step 2: Update `tests/test_repack_integrity.py` to also assert that the outer GUI stub inside `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe` embeds `--game-dir`, `--work`, `--result`, and `mobile-worker`, and run the entire test suite**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 pytest -v
```
Expected: 100% PASS across all test modules.

---

### Task 7: Update Checksums in `README.md` & `scripts/06_publish_github_release.py`, Refresh Graft, Commit Cleanly & Re-Upload GitHub Release `v1.0.0-celeslib`

**Files:**
- Modify: `README.md`
- Modify: `scripts/06_publish_github_release.py`
- Modify: `.agents/plan/2026-11-04-celeslib-xeno-ui-and-rebranding-plan.md`

- [x] **Step 1: Update SHA-256 hashes and file sizes in `README.md` and `scripts/06_publish_github_release.py` to match the freshly built `dist/SHA256SUMS.txt`**
- [x] **Step 2: Run `graft build` and verify `git status` has zero untracked/uncommitted files after commit**
- [x] **Step 3: Commit, push to `origin main`, and re-upload the fixed release assets to `v1.0.0-celeslib` via `scripts/06_publish_github_release.py`**

```bash
graft build
git add .
git commit -m "fix(gui): fix ace-worker CLI protocol, result.json parser, CryptoAPI SHA-256 check, Android USB actions, and preview glyphs"
git push origin main
git tag -f v1.0.0-celeslib
git push origin v1.0.0-celeslib --force
/home/whise/.local/bin/uv run --python 3.12 python scripts/06_publish_github_release.py
```

---

## Phase 3: Complete Removal of "Xeno" Reference Naming & Frameless Window Polish (Task 8)

> **User Feedback & Audit Findings:**
> `https://www.xeno.now/` was strictly a **visual layout reference**, NOT part of the product brand. The product brand is **100% Celeslib (`Celeslib Honor of Kings: Ace Patcher`)**. Currently, `"xeno"` / `"Xeno"` is leaked into:
> 1. **GitHub Release `v1.0.0-celeslib` Assets & Release Notes (`scripts/06_publish_github_release.py`):**
>    - Uploaded preview files are named `xeno_patcher_id.png`, `xeno_patcher_en.png`, `xeno_dashboard_id.png`, `xeno_settings_id.png`, and the release description references `"Xeno v1.3.0 (https://www.xeno.now/)"`.
> 2. **Repository Preview Assets, Scripts, C++ Sources, and Tests:**
>    - `assets/previews/xeno_*.png` -> must be renamed to `assets/previews/celeslib_patcher_id.png`, `celeslib_patcher_en.png`, `celeslib_dashboard_id.png`, `celeslib_settings_id.png` (and old `assets/previews/xeno_*.png` deleted via `git rm`).
>    - `src/gui/celeslib_xeno_gui.cpp`, `src/gui/celeslib_xeno.rc`, `src/gui/celeslib_xeno_i18n.h` -> must be renamed to `src/gui/celeslib_gui.cpp`, `src/gui/celeslib_gui.rc`, `src/gui/celeslib_i18n.h` (and old files removed).
>    - `scripts/08_compile_xeno_gui.py` -> must be renamed to `scripts/08_compile_celeslib_gui.py`, producing `build/celeslib_gui_stub.exe`.
>    - `tests/test_xeno_gui_build.py` -> must be renamed to `tests/test_celeslib_gui_build.py`.
>    - Inside `src/gui/celeslib_gui.cpp`, `wc.lpszClassName` must be `L"CeleslibPatcherUI"` (NOT `L"CeleslibXenoUI"`), `RenderXenoFrame` must be `RenderCeleslibFrame`, and `--smoke-ui` must output `celeslib_patcher_id.png`, `celeslib_patcher_en.png`, `celeslib_dashboard_id.png`, `celeslib_settings_id.png`.
>    - `README.md` must have zero mentions of `Xeno` or `xeno.now` (use **"Antarmuka Native Celeslib Ultra-Dark Carbon"**).
> 3. **True Frameless Custom Titlebar (`WM_NCCALCSIZE` in `src/gui/celeslib_gui.cpp`):**
>    - Because `RenderCeleslibFrame` draws a custom dark titlebar at `Y: 0..48` with `[—] [□] [×]` controls, handle `WM_NCCALCSIZE` (`if (wParam == TRUE) return 0;`) or use `WS_POPUP | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU` so Windows does not draw a duplicate second titlebar above the custom Celeslib header!

### Task 8: Purge All "Xeno" Naming Across Files, Binary, Docs & GitHub Release Assets

**Files:**
- Rename (`git mv`): `src/gui/celeslib_xeno_gui.cpp` -> `src/gui/celeslib_gui.cpp`
- Rename (`git mv`): `src/gui/celeslib_xeno.rc` -> `src/gui/celeslib_gui.rc`
- Rename (`git mv`): `src/gui/celeslib_xeno_i18n.h` -> `src/gui/celeslib_i18n.h`
- Rename (`git mv`): `scripts/08_compile_xeno_gui.py` -> `scripts/08_compile_celeslib_gui.py`
- Rename (`git mv`): `tests/test_xeno_gui_build.py` -> `tests/test_celeslib_gui_build.py`
- Delete (`git rm -f`): `assets/previews/xeno_patcher_id.png`, `assets/previews/xeno_patcher_en.png`, `assets/previews/xeno_dashboard_id.png`, `assets/previews/xeno_settings_id.png`
- Create: `assets/previews/celeslib_patcher_id.png`, `assets/previews/celeslib_patcher_en.png`, `assets/previews/celeslib_dashboard_id.png`, `assets/previews/celeslib_settings_id.png`
- Modify: `scripts/05_repack_windows_exe.py`, `scripts/06_publish_github_release.py`, `tests/test_repack_integrity.py`, `README.md`

- [x] **Step 1: Rename files with `git mv`, remove `assets/previews/xeno_*.png`, and update all internal symbols/strings so `xeno` / `Xeno` does not exist anywhere in `src/`, `scripts/`, `tests/`, `assets/`, or `README.md`**
  - In `src/gui/celeslib_gui.cpp`:
    - Change `#include "celeslib_xeno_i18n.h"` -> `#include "celeslib_i18n.h"`.
    - Change `RenderXenoFrame` -> `RenderCeleslibFrame`.
    - Change `wc.lpszClassName = L"CeleslibXenoUI"` -> `wc.lpszClassName = L"CeleslibPatcherUI"`.
    - Change `--smoke-ui` output filenames to `celeslib_patcher_id.png`, `celeslib_patcher_en.png`, `celeslib_dashboard_id.png`, `celeslib_settings_id.png`.
    - Add `case WM_NCCALCSIZE: if (wParam == TRUE) return 0; break;` in `WndProc` so the custom dark header (`Y: 0..48`) serves as the single frameless titlebar without a duplicate OS titlebar.
  - In `scripts/08_compile_celeslib_gui.py` & `scripts/05_repack_windows_exe.py`:
    - Build `build/celeslib_gui_stub.exe` (and remove old `build/celeslib_xeno_stub.exe`).
    - Generate `assets/previews/celeslib_patcher_id.png`, `celeslib_patcher_en.png`, `celeslib_dashboard_id.png`, `celeslib_settings_id.png`.
  - In `tests/test_celeslib_gui_build.py` & `tests/test_repack_integrity.py`:
    - Assert that `b"xeno"`, `b"Xeno"`, `"xeno".encode("utf-16le")`, and `"Xeno".encode("utf-16le")` are **NOT** present in `build/celeslib_gui_stub.exe` or in the outer GUI stub of `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`!

- [x] **Step 2: Rebuild GUI stub, repack release executables, and run `pytest -v`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/08_compile_celeslib_gui.py
/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py
/home/whise/.local/bin/uv run --python 3.12 pytest -v
```

- [x] **Step 3: Update `README.md` & `scripts/06_publish_github_release.py`, delete old `xeno_*.png` assets from GitHub Release `v1.0.0-celeslib`, and publish clean Celeslib release**
  - In `scripts/06_publish_github_release.py`:
    - Remove all mentions of `Xeno` / `xeno.now` from `RELEASE_NOTES` and docstrings.
    - Reference `celeslib_patcher_id.png`, `celeslib_patcher_en.png`, `celeslib_dashboard_id.png`, `celeslib_settings_id.png`.
    - Before uploading assets in `publish_via_gh_cli()` and `publish_via_rest_api()`, explicitly delete any legacy `xeno_patcher_id.png`, `xeno_patcher_en.png`, `xeno_dashboard_id.png`, `xeno_settings_id.png` assets from the GitHub Release (`gh release delete-asset v1.0.0-celeslib <name> -y --repo voseu/acepatchindo` / `DELETE /repos/.../releases/assets/<id>`) so zero `xeno_*.png` files remain on the GitHub Release page!
  - Run `graft build` and verify `graft grep "xeno"` and `graft grep "Xeno"` return **0 hits** across all indexed source/script/test files!
  - Commit, push, and run `scripts/06_publish_github_release.py`.

---

## Phase 4: Single-Page Monochrome Obsidian UI Redesign (Tasks 9–10)

> **User Feedback & Reference Binary Inspection (`/home/whise/Downloads/xeno/Xeno-v1.3.65.exe`):**
> Inspecting the unpacked reference binary (`main.8f5e9cb7.css` & `main.cd475328.js`) revealed why its UI looks far cleaner and sharper than the current 4-tab layout:
> 1. **Single-Page Architecture (Zero Sidebar):**
>    - A patcher utility does NOT need 4 separate sidebar tabs (`Dashboard`, `Patcher`, `Android (USB)`, `Settings`) that hide controls and leave 70% empty space on `Dashboard` and `Settings`.
>    - Consolidating everything into a **Single-Page Layout (`980 × 620`, zero left sidebar)** lets the user view and operate Game Directory (`Browse` / `Auto-Detect`), Patch Mode (`ID Hybrid` / `EN Full`), UI Language (`ID` / `EN`), PC Patch Actions (`Install`, `Restore`, `Check`), Android USB Actions (`Scan`, `Patch`, `Recover`), the Line-Numbered Diagnostic Console + Minimap, and the Bottom Status Bar on one unified screen.
> 2. **Authentic Monochrome Obsidian Palette (No Neon Purple Blocks):**
>    - **Main Canvas / Titlebar / Status Bar:** `#090909` (`rgb(9, 9, 9)`)
>    - **Connected Cards / Toolbar Surface:** `#0D0D0D` to `#111111` (`rgb(13, 13, 13)` / `rgb(17, 17, 17)`) with crisp `1px solid #333333` borders (`#FFFFFF` or `#555555` on hover).
>    - **Primary Action Button & Active Segmented Toggle (`.card-button` / `.filter-segment-button.active`):** High-contrast **Pure White Fill (`#FFFFFF`) with Bold Pure Black Text (`#000000`)**, `6px` border radius.
>    - **Secondary Action Buttons (`.toolbar-button`):** `#090909` background, `1px solid #333333` border, `#FFFFFF` text, hovering to `#181818` with `#555555` border (and Restore/Destructive buttons hovering with `#EF4444` border & text).
>    - **Connected 3-Column Strip (`.connected-section`):** A unified `#0D0D0D` rounded box (`border: 1px solid #333333; border-radius: 10px`) divided into 3 equal columns by subtle vertical gradient dividers.
>    - **Crisp Vector Stroke Icons:** Every card header and action button includes a clean `14×14` or `16×16` vector stroke icon (`2px` stroke width: Folder, Search, Layers, Globe, Play triangle, Rotate-CCW arrow, Checkmark, Smartphone, Trash can) drawn via GDI+ (`celeslib_gui.cpp`) and Pillow (`scripts/08_compile_celeslib_gui.py`).
> 3. **Zero "Xeno" Naming:**
>    - Keep **zero** `"xeno"` / `"Xeno"` strings anywhere in code, binaries, filenames, or GitHub Release. Because the UI is now Single-Page, delete the obsolete multi-page preview files `assets/previews/celeslib_dashboard_id.png` and `assets/previews/celeslib_settings_id.png`, leaving only `assets/previews/celeslib_patcher_id.png` and `assets/previews/celeslib_patcher_en.png`.

### Task 9: Redesign `src/gui/celeslib_gui.cpp`, `src/gui/celeslib_i18n.h`, and `scripts/08_compile_celeslib_gui.py` into a Single-Page Monochrome Obsidian UI

**Files:**
- Modify: `src/gui/celeslib_i18n.h`
- Modify: `src/gui/celeslib_gui.cpp`
- Modify: `scripts/08_compile_celeslib_gui.py`
- Modify: `tests/test_celeslib_gui_build.py`
- Delete (`git rm -f`): `assets/previews/celeslib_dashboard_id.png`, `assets/previews/celeslib_settings_id.png`
- Regenerate: `assets/previews/celeslib_patcher_id.png`, `assets/previews/celeslib_patcher_en.png`

- [x] **Step 1: Update `src/gui/celeslib_gui.cpp` and `src/gui/celeslib_i18n.h` to implement the 5-Zone Single-Page Monochrome Obsidian Layout (`980 × 620`)**
  - Remove `NavView` tab switching and the left sidebar completely. Every control lives on the single canvas (`980 × 620`):
    1. **Zone 1 — Custom Frameless Titlebar (`Y: 0..38`, `X: 0..980`, `#090909`, `1px` bottom border `#333333`):**
       - Left (`X: 18`): Celeslib `18×18` geometric 4-point star emblem (`#FFFFFF` stroke) + `"Celeslib"` bold title (`#FFFFFF`, `11pt`) + `"v1.0.0"` pill badge (`#141414` fill, `#333333` border, `#CCCCCC` text) + `"Honor of Kings: Ace Patcher • Game Build 1.4.12"` subtitle (`#888888`, `9pt`).
       - Right (`X: 842..980`): Window control buttons `[—]` (`X: 842..888`), `[□]` (`X: 888..934`), `[×]` (`X: 934..980`, `#4A0000` fill on hover).
    2. **Zone 2 — Connected 3-Column Configuration Strip (`Y: 50..146`, `X: 20..960`, `#0D0D0D` fill, `1px` `#333333` border, `10px` radius):**
       - Vertical dividers at `X = 420` and `X = 710` (`Y: 62..134`, `#262626` with `#3A3A3A` center).
       - **Column 1 — Game Directory (`X: 20..420`):**
         - Header (`Y: 60`): Vector `Folder` icon + `L.lbl_game_dir` (`"DIREKTORI GAME (HOK: ACE)"` / `"GAME DIRECTORY (HOK: ACE)"`, `#888888`, `8.5pt` bold) + right-aligned `[Auto-Detect]` mini button (`X: 318..406, Y: 56..78`, `#090909` fill, `#333333` border).
         - Path Input Box + Browse Button (`Y: 86..120`): Path box (`X: 34..312, Y: 86..120`, `#050505` fill, `#262626` border, `Consolas 9pt` `#E5E5E5` text) + `[Pilih Folder / Browse]` button (`X: 318..406, Y: 86..120`, `#141414` fill, `#333333` border, `#FFFFFF` text).
       - **Column 2 — Game Patch Mode (`X: 420..710`):**
         - Header (`Y: 60`): Vector `Layers` icon + `L.lbl_patch_mode` (`"MODE BAHASA PATCH"` / `"GAME PATCH MODE"`, `#888888`, `8.5pt` bold).
         - Segmented Control Pill (`X: 434..696, Y: 86..120`, `#050505` outer track with `#333333` border, `6px` radius):
           - `[ID Hybrid]` (`X: 437..564, Y: 89..117`): When active (`patch_mode == MODE_ID_HYBRID`), fill `#FFFFFF` with bold `#000000` text; when inactive, transparent fill with `#888888` text.
           - `[EN Full]` (`X: 566..693, Y: 89..117`): When active (`patch_mode == MODE_EN_FULL`), fill `#FFFFFF` with bold `#000000` text; when inactive, transparent fill with `#888888` text.
         - Subtitle (`Y: 124`): `"UI Indonesia + Istilah MOBA English"` (or `"100% Full English Localization"`, `#777777`, `8pt`).
       - **Column 3 — Interface Language (`X: 710..960`):**
         - Header (`Y: 60`): Vector `Globe` icon + `L.lbl_ui_lang` (`"BAHASA UI"` / `"UI LANGUAGE"`, `#888888`, `8.5pt` bold).
         - Segmented Control Pill (`X: 724..946, Y: 86..120`, `#050505` outer track with `#333333` border, `6px` radius):
           - `[Indonesia]` (`X: 727..834, Y: 89..117`): Active = `#FFFFFF` fill + `#000000` bold text; Inactive = `#888888` text.
           - `[English]` (`X: 836..943, Y: 89..117`): Active = `#FFFFFF` fill + `#000000` bold text; Inactive = `#888888` text.
         - Subtitle (`Y: 124`): `"Engine: 508 Tabel • 72.186 Entri"` / `"Engine: 508 Tables • 72,186 Entries"` (`#777777`, `8pt`).
    3. **Zone 3 — Unified Action Toolbar (`Y: 158..208`, `X: 20..960`, `#0D0D0D` fill, `1px` `#333333` border, `8px` radius):**
       - **PC Actions (Left):**
         - **Primary CTA `[▶ Pasang Patch / Install Patch]` (`X: 30..186, Y: 166..200`):** `#FFFFFF` pure white fill (`#E5E5E5` on hover), `#000000` bold text + vector Play triangle icon.
         - **`[↺ Pulihkan / Restore]` (`X: 194..326, Y: 166..200`):** `#090909` fill, `1px` `#333333` border (`#EF4444` red border & text on hover) + vector Rotate-CCW icon.
         - **`[✓ Periksa / Check]` (`X: 334..462, Y: 166..200`):** `#090909` fill, `1px` `#333333` border (`#555555` on hover) + vector Checkmark icon.
       - **Vertical Divider at `X = 476` (`Y: 168..198`, `#262626`)**
       - **Android USB Actions (Center-Right, on the same page):**
         - **`[📱 Pindai USB / Scan USB]` (`X: 490..616, Y: 166..200`):** `#090909` fill, `#333333` border + vector Smartphone icon -> invokes `RunAndroidOperation(L"devices")`.
         - **`[⚡ Patch APK]` (`X: 624..740, Y: 166..200`):** `#090909` fill, `#333333` border + vector Bolt/Play icon -> invokes `RunAndroidOperation(L"patch")`.
         - **`[↺ Pulihkan APK / Recover]` (`X: 748..868, Y: 166..200`):** `#090909` fill, `#333333` border (`#EF4444` hover) -> invokes `RunAndroidOperation(L"recover")`.
       - **Console Clear Button (Right):**
         - **`[🗑 Clear]` (`X: 878..950, Y: 166..200`):** `#090909` fill, `#333333` border + vector Trash icon -> clears console log lines.
    4. **Zone 4 — Monaco/Executor-Style Diagnostic Console (`Y: 220..576`, `X: 20..960`, `#050505` fill, `1px` `#333333` border, `8px` radius):**
       - **Console Top Header Bar (`Y: 220..252`, `#0D0D0D` fill, `1px` bottom border `#262626`):**
         - Left (`X: 34`): Vector Terminal `>_` icon + `"output.log — Celeslib Dual-State VFS Engine"` (`Consolas 9pt`, `#CCCCCC`).
         - Right (`X: 780..948`): Status Pill (`#111111` fill, `#333333` border, `8×8` glowing status dot `#22C55E` / `#EF4444` / `#EAB308` + status label `SIAP / READY`, `TERPASANG / INSTALLED`, etc.).
       - **Line-Number Gutter (`X: 21..64, Y: 253..575`, `#090909` fill, `1px` right border `#1E1E1E`):** Right-aligned line numbers `1..14` in `Consolas 9pt` (`#555555`).
       - **Log Viewport (`X: 74..904, Y: 258..570`):** `Consolas 9.5pt` log lines:
         - `[OK]` / `[READY]` lines in `#22C55E` (emerald green)
         - `[ERROR]` lines in `#EF4444` (crimson red)
         - `[PATCH]` / `[CHECK]` / `[ANDROID]` lines in `#FFFFFF` (bright white)
         - `[INFO]` / `[ENGINE]` lines in `#B0B0B0` (clean light gray)
       - **Right Minimap Rail (`X: 908..959, Y: 253..575`, `#090909` fill, `1px` left border `#1E1E1E`):** Minimap viewport slider block (`#1A1A1A` fill, `#333333` border) + color-coded micro-bars matching the log lines.
    5. **Zone 5 — Bottom Status Bar (`Y: 588..620`, `X: 0..980`, `#090909` fill, `1px` top border `#333333`):**
       - Left (`X: 20`): `8×8` glowing green dot (`#22C55E`) + `"Offline Dual-State VFS Engine • 508 Protobuf Tables • SHA-256 Verified"` (`#CCCCCC`, `8.5pt`).
       - Right (`X: 680..960`, right-aligned): `"© 2026 Celeslib • HoK: Ace 1.4.12 • v1.0.0"` (`#888888`, `8.5pt`).

- [x] **Step 2: Update `scripts/08_compile_celeslib_gui.py` and `tests/test_celeslib_gui_build.py` to match the Single-Page Monochrome Obsidian UI and remove obsolete multi-tab previews**
  - Delete `assets/previews/celeslib_dashboard_id.png` and `assets/previews/celeslib_settings_id.png` via `git rm -f`.
  - Update `render_celeslib_preview(lang, out_path)` in `scripts/08_compile_celeslib_gui.py` so it renders the exact same 5-Zone Single-Page Monochrome Obsidian layout (`980 × 620`) with crisp Pillow vector icons (Folder, Layers, Globe, Play, Rotate-CCW, Check, Smartphone, Bolt, Trash), producing `assets/previews/celeslib_patcher_id.png` and `assets/previews/celeslib_patcher_en.png`.
  - Update `--smoke-ui` in `src/gui/celeslib_gui.cpp` so it only generates `celeslib_patcher_id.png` and `celeslib_patcher_en.png`.
  - Update `tests/test_celeslib_gui_build.py` to verify the single-page preview images (`980 × 620`, `#090909` obsidian background, `#FFFFFF` primary CTA button pixels, `#22C55E` emerald status dot) and assert that `celeslib_dashboard_id.png` and `celeslib_settings_id.png` no longer exist.

### Task 10: Repack Executables, Update `README.md` & `scripts/06_publish_github_release.py`, Clean Old Multi-Tab Previews from GitHub Release `v1.0.0-celeslib`, and Publish

**Files:**
- Modify: `scripts/05_repack_windows_exe.py`
- Modify: `scripts/06_publish_github_release.py`
- Modify: `tests/test_repack_integrity.py`
- Modify: `README.md`
- Modify: `.agents/plan/2026-11-04-celeslib-xeno-ui-and-rebranding-plan.md`

- [x] **Step 1: Compile `build/celeslib_gui_stub.exe`, repack `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`, and run `pytest -v`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/08_compile_celeslib_gui.py
/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py
/home/whise/.local/bin/uv run --python 3.12 pytest -v
```

- [x] **Step 2: Update `README.md` and `scripts/06_publish_github_release.py` for the Single-Page UI (5 Release Assets total)**
  - In `README.md`:
    - Show the Single-Page preview images (`assets/previews/celeslib_patcher_id.png` and `assets/previews/celeslib_patcher_en.png`) and remove links to `celeslib_dashboard_id.png` / `celeslib_settings_id.png`.
    - Update the SHA-256 hashes and byte sizes to match the newly repacked `dist/SHA256SUMS.txt`.
  - In `scripts/06_publish_github_release.py`:
    - Update `RELEASE_ASSETS` so it uploads the **5 official files**:
      1. `dist/Celeslib-HoK-Ace-Patcher-v1.0.0.exe`
      2. `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`
      3. `dist/SHA256SUMS.txt`
      4. `assets/previews/celeslib_patcher_id.png`
      5. `assets/previews/celeslib_patcher_en.png`
    - Add `"celeslib_dashboard_id.png"` and `"celeslib_settings_id.png"` to `LEGACY_ASSET_NAMES` so `scripts/06_publish_github_release.py` automatically deletes those 2 old multi-page preview files from GitHub Release `v1.0.0-celeslib`!
    - Update `RELEASE_NOTES` to showcase only `celeslib_patcher_id.png` and `celeslib_patcher_en.png` and the updated SHA-256 checksums.

- [x] **Step 3: Refresh Graft, commit, push, and publish to GitHub Release `v1.0.0-celeslib`**

Run:
```bash
graft build
git add -A
git commit -m "feat(gui): redesign into single-page monochrome obsidian UI with unified PC & Android controls"
git push origin main
git tag -f v1.0.0-celeslib
git push origin v1.0.0-celeslib --force
/home/whise/.local/bin/uv run --python 3.12 python scripts/06_publish_github_release.py
```



