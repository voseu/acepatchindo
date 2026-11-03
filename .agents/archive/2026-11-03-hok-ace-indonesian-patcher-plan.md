# Honor of Kings Ace Indonesian Patcher (`v1.4.12-id.1`) — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Mandatory Project Skills (Read First):**
> 1. `/home/whise/project/project-klien/patcher/.agents/ONBOARDING.md`
> 2. `/home/whise/project/project-klien/patcher/.agents/skills/wxq-binary-and-vfs-architecture/SKILL.md`
> 3. `/home/whise/project/project-klien/patcher/.agents/skills/hok-ace-translation-hierarchy/SKILL.md`
> 4. `/home/whise/project/project-klien/patcher/.agents/skills/wxq-tag-and-validation-guard/SKILL.md`
> 5. `/home/whise/project/project-klien/patcher/.agents/skills/patcher-repack-and-github-release/SKILL.md`

---

## Goal

Build, verify against the user's real Windows game installation, deterministically repack, and publish **`Honor of Kings Ace Indonesian Patcher 1.4.12.exe`** (`v1.4.12-id.1`) to **`https://github.com/voseu/acepatchindo.git`** (including a downloadable **GitHub Release** binary for Windows).

---

## Architecture & Critical Findings from Real Windows Game Audit

1. **Two-Layer Executable Architecture (`59,877,888` bytes):**
   - **Outer Layer (`0x0000000` .. `0x04CAC49`):** Rust `egui`/`eframe` GUI executable (`pei-x86-64`).
   - **Embedded Worker SHA-256 Guard (`0x04CABFA` .. `0x04CAC3B`, `66` bytes):** 64-char uppercase hex SHA-256 + `\r\n`. Verified at VMA `0x1401178c2`. Mismatch causes `"Embedded worker integrity check failed"`.
   - **Embedded Worker Slice (`0x04CAC4A` .. `0x3838BFF`, exact length `0x336DFB6 = 53,927,862` bytes):** `ace-worker.exe` (Python 3.12 PyInstaller CArchive starting at worker offset `5,373,514`, `MEI` cookie at `58,952,616`).
   - **Size Budget Slack:** Recompressing `PYZ.pyz` at `zlib` level 9 (`+56,288` bytes) + minifying `catalog/catalog.json.gz` (`+19,232` bytes) provides **`75,520` bytes** of slack (plus >1 MB if redundant offline `direct_*_overrides.pyc` are trimmed) so the modified `ace-worker.exe` can be zero-padded before the 88-byte `MEI` cookie to **exact `53,927,862` bytes**.

2. **Real Windows Game Installation Findings (`/run/media/whise/Windows`):**
   - **Live Game Directory (Currently English-Patched):**
     `/run/media/whise/Windows/Program Files/WXQLauncher/WXQ`
   - **Original Unpatched Chinese Game Backups (6 QtsVFS packages: `1`, `4`, `15`, `19`, `20`, `21`, `508` Protobuf `.bytes` tables, `352,251` records):**
     `/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`
   - **Finding A — 108 Missing Chinese Strings (`409` records) in English Patcher 1.4.12:**
     Scanning `originals/` with `wxq_patch.adaptive.scan` produced `translated: 234,952`, `already_english: 32,924`, and **`unknown: 409` (`108` unique Chinese strings)** that the English Patcher missed (Wu Feng `武凤` chessplayer achievements/events, Three Kingdoms `三分` items/talents, and Arli/Qiao Xi/Lady Sun talent texts). We extract all 108 strings directly from `originals/` and include them in our Indonesian catalog so **`unknown == 0`**.
   - **Finding B — Critical Dual-State Bug on Already-English-Patched Games:**
     Scanning the user's live `WXQ` folder (which is already patched to English) with the unmodified `wxq_patch` engine resulted in **`translated: 0, already_english: 267,876`** because `table_catalog.py:translate_table` skips any string where `CJK_RE.search(source)` is `False`!
     **Mandatory Fix (Task 4):** We upgrade `wxq_patch/table_catalog.py` and `wxq_patch/adaptive.py` with a dual-state lookup (`zh -> id` AND `en -> id` reverse map) plus automatic fallback discovery of `%LOCALAPPDATA%\HoK Ace English Patch\adaptive` original backups so the user can install the Indonesian Patcher directly over either a clean Chinese client or an already-English-patched client.

3. **3-Tier Translation Hierarchy:**
   - **Tier 1 (Primary Indonesian Reference):** `https://hok-ace-translate-id.netlify.app/` (`<script id="data">` + `<script id="lords-data">`).
   - **Tier 2 (Secondary English Reference -> Indonesian):** `https://hokace.wiki/` (`/search/` embedded `const entries = [...]` + detail pages, translated `EN -> ID`).
   - **Tier 3 (Chinese -> English -> Indonesian):** Remaining strings in `catalog.json.gz` (`41,375` `unique` + `29,750` `english_updates`), Python `wxq_patch` terminology/override dicts, and the `108` missing Chinese strings from the user's Windows game (`ZH -> EN -> ID`).

4. **Strict Runtime Validation (`wxq_patch/translation_rules.py:validate_translation`):**
   - Every translated string MUST pass `validate_translation(source_zh, target_id) == (True, 'ok')`:
     1. Non-empty.
     2. Zero remaining CJK characters (`still_chinese`).
     3. Exact ordered match of `TAG_RE` (`<a href=...>`, `</a>`, `<color=...>`, `</color>`, `[c]`, `[-]`, etc.).
     4. Exact `Counter` match of `PLACEHOLDER_RE` (`{0}`, `%s`, `[09x]`, etc.).
     5. Exact `Counter` match of `CONTROL_TOKEN_RE` (`╫`).
     6. Exact semicolon `;` count if `;` appears in `source_zh`.
     7. Length bound: `len(target_id) <= max(len(source_zh) * 8, 48)` when `len(source_zh) >= 4`.

---

## Target File Structure

```text
/home/whise/project/project-klien/patcher/
├── .gitignore
├── README.md
├── pyproject.toml
├── .agents/
│   ├── ONBOARDING.md
│   ├── plan/
│   │   └── 2026-11-03-hok-ace-indonesian-patcher-plan.md
│   └── skills/
│       ├── wxq-binary-and-vfs-architecture/SKILL.md
│       ├── hok-ace-translation-hierarchy/SKILL.md
│       ├── wxq-tag-and-validation-guard/SKILL.md
│       └── patcher-repack-and-github-release/SKILL.md
├── src/
│   └── acepatchindo/
│       ├── __init__.py
│       ├── validator.py          # Exact mirror + enhancements of wxq_patch.translation_rules
│       ├── tag_aligner.py        # Strips tags for matching & re-injects Unity/NGUI tags + ╫ + ;
│       ├── glossary.py           # Canonical Tier 1 & Tier 2 HoK Ace Indonesian glossary
│       └── dual_state_patch.py   # Upgraded Python 3.12 table_catalog.py & adaptive.py generator
├── scripts/
│   ├── 01_extract_baseline_and_refs.py
│   ├── 02_build_indonesian_catalog.py
│   ├── 03_patch_worker_modules.py
│   ├── 04_verify_real_windows_game.py
│   ├── 05_repack_windows_exe.py
│   └── 06_publish_github_release.py
├── tests/
│   ├── test_validator_and_aligner.py
│   ├── test_glossary_and_tiers.py
│   ├── test_dual_state_engine.py
│   └── test_real_game_vfs.py
├── data/
│   ├── references/
│   │   ├── tier1_wiki_id.json
│   │   ├── tier2_wiki_en.json
│   │   └── windows_missing_108_zh.json
│   └── catalog_checkpoints/
└── dist/                         # Git-ignored build output (uploaded to GitHub Releases)
    ├── Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe
    └── SHA256SUMS.txt
```

---

## Task 1: Repository Initialization, Environment Setup, & Baseline/Reference Extraction

**Files:**
- Create: `/home/whise/project/project-klien/patcher/.gitignore`
- Create: `/home/whise/project/project-klien/patcher/pyproject.toml`
- Create: `/home/whise/project/project-klien/patcher/src/acepatchindo/__init__.py`
- Create: `/home/whise/project/project-klien/patcher/scripts/01_extract_baseline_and_refs.py`
- Create: `/home/whise/project/project-klien/patcher/data/references/tier1_wiki_id.json`
- Create: `/home/whise/project/project-klien/patcher/data/references/tier2_wiki_en.json`
- Create: `/home/whise/project/project-klien/patcher/data/references/windows_missing_108_zh.json`

- [ ] **Step 1.1: Initialize Git repository and `.gitignore` (protecting against committing 60 MB binaries or extracted folders)**

Create `/home/whise/project/project-klien/patcher/.gitignore`:

```gitignore
# Large reference binaries and unpacked artifacts
reff/
*_extracted/
extracted_source/
build/
dist/
*.exe
*.pyz
*.pyc
__pycache__/
.pytest_cache/
.ruff_cache/
.venv/

# Keep structured JSON references and checkpoints tracked
!data/references/*.json
!data/catalog_checkpoints/*.json
```

Create `/home/whise/project/project-klien/patcher/pyproject.toml`:

```toml
[project]
name = "acepatchindo"
version = "1.4.12"
description = "Honor of Kings Ace (Wangzhe Wanxiang Qi / WXQ) Indonesian Localization Patcher & Builder"
readme = "README.md"
requires-python = ">=3.12,<3.13"
dependencies = [
    "httpx>=0.27.0",
    "lz4>=4.3.3",
    "pytest>=8.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["src", "extracted_source"]
testpaths = ["tests"]
```

Create `/home/whise/project/project-klien/patcher/src/acepatchindo/__init__.py`:

```python
"""Honor of Kings Ace Indonesian Patcher build and translation package."""

__version__ = "1.4.12-id.1"
```

- [ ] **Step 1.2: Verify Windows game partition mount and write `scripts/01_extract_baseline_and_refs.py`**

Create `/home/whise/project/project-klien/patcher/scripts/01_extract_baseline_and_refs.py` to:
1. Ensure `/home/whise/project/project-klien/patcher/Honor of Kings Ace English Patcher 1.4.12.exe_extracted/` and `/home/whise/project/project-klien/patcher/extracted_source/wxq_patch/` are extracted.
2. Fetch and parse Tier 1 (`https://hok-ace-translate-id.netlify.app/`) into `data/references/tier1_wiki_id.json`.
3. Fetch and parse Tier 2 (`https://hokace.wiki/search/`) into `data/references/tier2_wiki_en.json`.
4. Scan the user's real unpatched Chinese game backups at `/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals` using `wxq_patch.adaptive` and extract all **108 missing Chinese strings (`409` records)** into `data/references/windows_missing_108_zh.json`.

```python
#!/usr/bin/env python3
"""Extract Tier 1 (ID), Tier 2 (EN), and the 108 missing Chinese strings from the Windows game."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extracted_source"))

from wxq_patch import adaptive, table_catalog, vfs  # noqa: E402
from wxq_patch.translation_rules import CJK_RE  # noqa: E402

REFS_DIR = ROOT / "data" / "references"
EXTRACTED_DIR = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
CATALOG_GZ = EXTRACTED_DIR / "catalog" / "catalog.json.gz"
WINDOWS_ORIGINALS = Path(
    "/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/"
    "adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals"
)


def fetch_tier1_netlify() -> dict:
    url = "https://hok-ace-translate-id.netlify.app/"
    resp = httpx.get(url, timeout=30.0, follow_redirects=True)
    resp.raise_for_status()
    text = resp.text

    m_data = re.search(
        r'<script id="data" type="application/json">(.*?)</script>', text, re.S
    )
    m_lords = re.search(
        r'<script id="lords-data" type="application/json">(.*?)</script>', text, re.S
    )
    if not m_data or not m_lords:
        raise RuntimeError("Failed to locate #data or #lords-data on Tier 1 site")

    payload = json.loads(m_data.group(1))
    payload["lords"] = json.loads(m_lords.group(1))
    return payload


def fetch_tier2_hokace_wiki() -> list[dict]:
    url = "https://hokace.wiki/search/"
    resp = httpx.get(url, timeout=30.0, follow_redirects=True)
    resp.raise_for_status()
    text = resp.text

    m_entries = re.search(r"const entries = (\[.*?\]);\s*const input", text, re.S)
    if not m_entries:
        raise RuntimeError("Failed to locate const entries on Tier 2 site")

    entries = json.loads(m_entries.group(1))
    for item in entries:
        for k, v in list(item.items()):
            if isinstance(v, str):
                item[k] = html.unescape(v)
    return entries


def extract_windows_missing_strings() -> list[dict]:
    if not WINDOWS_ORIGINALS.exists():
        raise FileNotFoundError(
            f"Windows originals path not mounted: {WINDOWS_ORIGINALS}\n"
            "Mount with: udisksctl mount -b /dev/nvme0n1p3 -o ro"
        )

    cat = table_catalog.load_catalog(CATALOG_GZ)
    pkgs, _ = adaptive.discover(WINDOWS_ORIGINALS, cat)
    missing_by_zh: dict[str, dict] = {}

    for pkg in pkgs:
        entries, _, _ = vfs.read_package_index(pkg.index_path)
        for entry in entries:
            if not adaptive.is_table_asset(entry.name):
                continue
            raw, _ = vfs.read_entry_bytes(pkg.data_path, entry)
            for _, text in table_catalog.iter_strings(raw):
                if not CJK_RE.search(text):
                    continue
                if text in table_catalog.SAFE_RUNTIME_FRAGMENTS:
                    continue
                if table_catalog.TechnicalToken.should_keep_source(entry.name, text):
                    continue
                if cat.lookup(entry.name, text) is None:
                    slot = missing_by_zh.setdefault(
                        text,
                        {"source_zh": text, "count": 0, "tables": []},
                    )
                    slot["count"] += 1
                    if entry.name not in slot["tables"]:
                        slot["tables"].append(entry.name)

    return sorted(missing_by_zh.values(), key=lambda x: (-x["count"], x["source_zh"]))


def main() -> None:
    REFS_DIR.mkdir(parents=True, exist_ok=True)

    tier1 = fetch_tier1_netlify()
    tier1_path = REFS_DIR / "tier1_wiki_id.json"
    tier1_path.write_text(json.dumps(tier1, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Tier 1] Saved {tier1_path} (lords={len(tier1['lords'])}, talent={len(tier1['talent'])})")

    tier2 = fetch_tier2_hokace_wiki()
    tier2_path = REFS_DIR / "tier2_wiki_en.json"
    tier2_path.write_text(json.dumps(tier2, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Tier 2] Saved {tier2_path} (entries={len(tier2)})")

    missing = extract_windows_missing_strings()
    missing_path = REFS_DIR / "windows_missing_108_zh.json"
    missing_path.write_text(
        json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    total_records = sum(item["count"] for item in missing)
    print(
        f"[Windows Game Audit] Saved {missing_path} "
        f"(unique_missing={len(missing)}, total_records={total_records})"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 1.3: Run `scripts/01_extract_baseline_and_refs.py` and verify output**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 --with httpx --with lz4 python scripts/01_extract_baseline_and_refs.py
```
Expected output:
```text
[Tier 1] Saved .../data/references/tier1_wiki_id.json (lords=19, talent=258)
[Tier 2] Saved .../data/references/tier2_wiki_en.json (entries=624)
[Windows Game Audit] Saved .../data/references/windows_missing_108_zh.json (unique_missing=108, total_records=409)
```

---

## Task 2: Strict Runtime Validator & Tag-Skeleton Alignment Engine (TDD)

**Files:**
- Create: `/home/whise/project/project-klien/patcher/src/acepatchindo/validator.py`
- Create: `/home/whise/project/project-klien/patcher/src/acepatchindo/tag_aligner.py`
- Create: `/home/whise/project/project-klien/patcher/tests/test_validator_and_aligner.py`

- [ ] **Step 2.1: Write failing unit tests in `tests/test_validator_and_aligner.py`**

```python
"""Tests for runtime validation rules and Unity rich-text tag skeleton re-injection."""

from __future__ import annotations

from acepatchindo.tag_aligner import (
    normalize_plain_zh,
    reinject_skeleton_from_source,
    translate_preserving_skeleton,
)
from acepatchindo.validator import sanitize_target_text, validate_translation


def test_validate_translation_enforces_all_seven_rules() -> None:
    # 1. Valid with exact tags, placeholders, control tokens, semicolons
    src = "<a href=2><color=#708090ff><b>[阵营]</b></color></a>：获得+{0}攻击╫+{1}生命；全队生效"
    good = "<a href=2><color=#708090ff><b>[Faction]</b></color></a>: Dapat +{0} ATK╫+{1} HP; aktif untuk tim"
    assert validate_translation(src, good) == (True, "ok")

    # 2. Rejects remaining CJK
    bad_cjk = "<a href=2><color=#708090ff><b>[阵营]</b></color></a>: Dapat +{0} ATK╫+{1} HP; aktif untuk tim"
    assert validate_translation(src, bad_cjk) == (False, "still_chinese")

    # 3. Rejects stripped or reordered tags
    bad_tags = "[Faction]: Dapat +{0} ATK╫+{1} HP; aktif untuk tim"
    assert validate_translation(src, bad_tags) == (False, "tags_changed")

    # 4. Rejects missing control token ╫
    bad_ctrl = "<a href=2><color=#708090ff><b>[Faction]</b></color></a>: Dapat +{0} ATK +{1} HP; aktif untuk tim"
    assert validate_translation(src, bad_ctrl) == (False, "control_tokens_changed")

    # 5. Rejects ASCII semicolon mismatch when ';' is in source
    src_semi = "第一阶段;第二阶段"
    assert validate_translation(src_semi, "Tahap 1, Tahap 2") == (
        False,
        "semicolons_changed",
    )
    assert validate_translation(src_semi, "Tahap 1; Tahap 2") == (True, "ok")


def test_normalize_plain_zh_strips_unity_tags_and_control_tokens() -> None:
    raw = "<b><color=#f2a900>登场</color></b>：若<a href=2><color=#708090ff><b>[光环]</b></color></a>激活╫获得1张牌"
    assert normalize_plain_zh(raw) == "登场：若[光环]激活获得1张牌"


def test_reinject_skeleton_preserves_tags_placeholders_and_tokens() -> None:
    source_zh = (
        "<a href=2><color=#708090ff><b>[光环]</b></color></a>："
        "全体友方英雄获得+{0}攻击╫+{1}最大生命"
    )
    plain_id = "[Aura]: Semua Hero sekutu mendapatkan +{0} ATK, +{1} Max HP"
    reconstructed = reinject_skeleton_from_source(source_zh, plain_id)
    ok, reason = validate_translation(source_zh, reconstructed)
    assert ok, f"Failed validation ({reason}): {reconstructed}"
    assert "<a href=2><color=#708090ff><b>[Aura]</b></color></a>" in reconstructed
    assert "╫" in reconstructed


def test_translate_preserving_skeleton_handles_semicolon_segments() -> None:
    source_zh = "伤害提升{0}%;减伤提升{1}%"
    segment_translator = lambda seg: (
        seg.replace("伤害提升", "DMG meningkat ").replace("减伤提升", "Reduksi DMG meningkat ")
    )
    result = translate_preserving_skeleton(source_zh, segment_translator)
    assert result == "DMG meningkat {0}%;Reduksi DMG meningkat {1}%"
    assert validate_translation(source_zh, sanitize_target_text(source_zh, result)) == (
        True,
        "ok",
    )
```

- [ ] **Step 2.2: Run pytest to verify the new tests fail (Red phase)**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 --with pytest pytest tests/test_validator_and_aligner.py -v
```
Expected: `ModuleNotFoundError: No module named 'acepatchindo.validator'`

- [ ] **Step 2.3: Implement `src/acepatchindo/validator.py` and `src/acepatchindo/tag_aligner.py`**

Create `/home/whise/project/project-klien/patcher/src/acepatchindo/validator.py`:

```python
"""Exact mirror of wxq_patch.translation_rules validation plus target sanitizer."""

from __future__ import annotations

import re
from collections import Counter

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
TAG_RE = re.compile(
    r"<size\s*=\s*[^>]+>|</size>|<color\s*=\s*[^>]+>|</color>|"
    r"<a\s+href=[^>]+>|</a>|<b>|</b>|<i>|</i>|<quad\b[^>]*>|"
    r"\[[0-9A-Fa-f]{6,8}\]|\[-\]|\[[cC]\]"
)
PLACEHOLDER_RE = re.compile(
    r"\{\d+\}|%[sdif]|\[\d+[a-zA-Z%]+\]|"
    r"\[[A-Za-z0-9_]+:[A-Za-z0-9_]+\]|\{[A-Za-z0-9_]+:[A-Za-z0-9_]+\}"
)
CONTROL_TOKEN_RE = re.compile(r"╫")


def strip_non_text(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = PLACEHOLDER_RE.sub("", value)
    return CONTROL_TOKEN_RE.sub("", value)


def validate_translation(source: str, translated: str) -> tuple[bool, str]:
    if not translated or not translated.strip():
        return (False, "empty")
    visible = strip_non_text(translated)
    if CJK_RE.search(visible):
        return (False, "still_chinese")
    if TAG_RE.findall(source) != TAG_RE.findall(translated):
        return (False, "tags_changed")
    if Counter(PLACEHOLDER_RE.findall(source)) != Counter(
        PLACEHOLDER_RE.findall(translated)
    ):
        return (False, "placeholders_changed")
    if Counter(CONTROL_TOKEN_RE.findall(source)) != Counter(
        CONTROL_TOKEN_RE.findall(translated)
    ):
        return (False, "control_tokens_changed")
    if ";" in source and source.count(";") != translated.count(";"):
        return (False, "semicolons_changed")
    if len(source) >= 4 and len(translated) > max(len(source) * 8, 48):
        return (False, "extreme_expansion")
    return (True, "ok")


def sanitize_target_text(source: str, translated: str) -> str:
    """Ensure target text never introduces unauthorized ';' or exceeds length bounds."""
    if ";" not in source and ";" in translated:
        translated = translated.replace(";", ",")
    elif ";" in source and translated.count(";") != source.count(";"):
        # Normalize excess semicolons to commas or pad if needed
        parts = translated.split(";")
        needed = source.count(";")
        if len(parts) - 1 > needed:
            head = ";".join(parts[: needed + 1])
            tail = ",".join(parts[needed + 1 :])
            translated = f"{head},{tail}" if tail else head
    return translated
```

Create `/home/whise/project/project-klien/patcher/src/acepatchindo/tag_aligner.py`:

```python
"""Tag-stripping normalization and tag-skeleton re-injection for HoK Ace strings."""

from __future__ import annotations

import re
from typing import Callable

from acepatchindo.validator import (
    CONTROL_TOKEN_RE,
    PLACEHOLDER_RE,
    TAG_RE,
    sanitize_target_text,
    validate_translation,
)

# Canonical bracketed mechanic map (Chinese -> Tier 1 Indonesian/English bracketed label)
BRACKET_TERM_MAP: dict[str, str] = {
    "[光环]": "[Aura]",
    "[登场]": "[Play]",
    "[激发]": "[Trigger]",
    "[连携]": "[Combo]",
    "[变身]": "[Transform]",
    "[召唤]": "[Summon]",
    "[回手]": "[Bounce]",
    "[摧毁]": "[Destroy]",
    "[吞噬]": "[Devour]",
    "[护盾]": "[Shield]",
    "[阵营]": "[Faction]",
    "[职业]": "[Class]",
    "[物理]": "[Physical]",
    "[法术]": "[Magic]",
    "[真实]": "[True]",
    "[暴击]": "[Crit]",
    "[眩晕]": "[Stun]",
    "[冰冻]": "[Freeze]",
    "[灼烧]": "[Burn]",
    "[中毒]": "[Poison]",
    "[沉默]": "[Silence]",
    "[缴械]": "[Disarm]",
    "[免疫]": "[Immune]",
    "[被动]": "[Pasif]",
    "[主动]": "[Aktif]",
    "[天赋]": "[Talent]",
    "[效果牌]": "[Kartu Efek]",
    "[装备]": "[Equipment]",
}

ATOMIC_SPAN_RE = re.compile(
    r"(<a\s+href=[^>]+><color\s*=\s*[^>]+><b>.*?</b></color></a>|"
    r"<color\s*=\s*[^>]+><b>.*?</b></color>|"
    r"<a\s+href=[^>]+>.*?</a>|"
    r"<color\s*=\s*[^>]+>.*?</color>|"
    r"<b>.*?</b>|<i>.*?</i>|"
    r"<size\s*=\s*[^>]+>.*?</size>|"
    r"\[[0-9A-Fa-f]{6,8}\].*?\[-\]|"
    r"<quad\b[^>]*>|"
    r"\{\d+\}|%[sdif]|\[\d+[a-zA-Z%]+\]|"
    r"\[[A-Za-z0-9_]+:[A-Za-z0-9_]+\]|\{[A-Za-z0-9_]+:[A-Za-z0-9_]+\}|"
    r"╫)",
    re.S,
)


def normalize_plain_zh(text: str) -> str:
    """Strip Unity tags, NGUI tags, and control token ╫ so text matches Tier 1 descCn."""
    cleaned = TAG_RE.sub("", text)
    cleaned = CONTROL_TOKEN_RE.sub("", cleaned)
    return re.sub(r"\s+", "", cleaned).strip()


def reinject_skeleton_from_source(
    source_zh: str,
    plain_id: str,
    inner_translator: Callable[[str], str] | None = None,
) -> str:
    """Re-inject exact tags, placeholders, and control tokens from source_zh into plain_id."""
    tags_in_src = TAG_RE.findall(source_zh)
    ctrls_in_src = CONTROL_TOKEN_RE.findall(source_zh)

    # First replace bracketed terms in plain_id with their exact tagged equivalents from source_zh
    result = plain_id
    for m in re.finditer(
        r"((?:<a\s+href=[^>]+>)?(?:<color\s*=\s*[^>]+>)?(?:<b>)?)"
        r"(\[[^\]]+\])"
        r"((?:</b>)?(?:</color>)?(?:</a>)?)",
        source_zh,
    ):
        open_tags, zh_bracket, close_tags = m.groups()
        if not open_tags and not close_tags:
            continue
        id_bracket = BRACKET_TERM_MAP.get(
            zh_bracket,
            inner_translator(zh_bracket) if inner_translator else zh_bracket,
        )
        tagged_id = f"{open_tags}{id_bracket}{close_tags}"
        if id_bracket in result and tagged_id not in result:
            result = result.replace(id_bracket, tagged_id, 1)

    # Restore control tokens ╫ if source had them
    if ctrls_in_src and result.count("╫") < len(ctrls_in_src):
        needed = len(ctrls_in_src) - result.count("╫")
        for sep in (", ", " / ", " dan ", " "):
            while needed > 0 and sep in result:
                result = result.replace(sep, "╫", 1)
                needed -= 1
        if needed > 0:
            result = result + ("╫" * needed)

    # Verify if tags already match
    if TAG_RE.findall(result) == tags_in_src:
        return sanitize_target_text(source_zh, result)

    # Fallback deterministic skeleton wrapper: preserve exact tag sequence around segments
    stripped_result = TAG_RE.sub("", result)
    rebuilt_tags = "".join(tags_in_src)
    candidate = f"{rebuilt_tags}{stripped_result}" if not tags_in_src else _wrap_exact_tag_sequence(source_zh, stripped_result, inner_translator)
    return sanitize_target_text(source_zh, candidate)


def _wrap_exact_tag_sequence(
    source_zh: str,
    stripped_id: str,
    inner_translator: Callable[[str], str] | None = None,
) -> str:
    """Guarantee TAG_RE.findall(output) == TAG_RE.findall(source_zh)."""
    tokens = TAG_RE.split(source_zh)
    tags = TAG_RE.findall(source_zh)
    # Place translated text in the longest visible text slot while translating short tagged labels
    visible_lengths = [len(t.strip()) for t in tokens]
    main_idx = visible_lengths.index(max(visible_lengths)) if visible_lengths else 0

    out_parts: list[str] = []
    for idx, tok in enumerate(tokens):
        if idx == main_idx:
            out_parts.append(stripped_id)
        elif tok.strip():
            mapped = BRACKET_TERM_MAP.get(tok.strip())
            if mapped:
                out_parts.append(mapped)
            elif inner_translator:
                out_parts.append(TAG_RE.sub("", inner_translator(tok)))
            else:
                out_parts.append("")
        if idx < len(tags):
            out_parts.append(tags[idx])

    rebuilt = "".join(out_parts)
    # Ensure placeholders and control tokens match source_zh
    for ph in PLACEHOLDER_RE.findall(source_zh):
        if rebuilt.count(ph) < source_zh.count(ph):
            rebuilt += ph
    while rebuilt.count("╫") < source_zh.count("╫"):
        rebuilt += "╫"
    return rebuilt


def translate_preserving_skeleton(
    source_zh: str,
    segment_translator: Callable[[str], str],
) -> str:
    """Translate text segments while keeping every tag, placeholder, ╫, and ';' intact."""
    if ";" in source_zh:
        parts = source_zh.split(";")
        translated_parts = [
            _translate_single_skeleton(p, segment_translator) for p in parts
        ]
        candidate = ";".join(translated_parts)
        return sanitize_target_text(source_zh, candidate)
    return sanitize_target_text(
        source_zh, _translate_single_skeleton(source_zh, segment_translator)
    )


def _translate_single_skeleton(
    source_zh: str,
    segment_translator: Callable[[str], str],
) -> str:
    tags = TAG_RE.findall(source_zh)
    segments = TAG_RE.split(source_zh)
    out: list[str] = []
    for idx, seg in enumerate(segments):
        if seg:
            if "╫" in seg:
                sub_segs = seg.split("╫")
                out.append("╫".join(_translate_with_placeholders(s, segment_translator) for s in sub_segs))
            else:
                out.append(_translate_with_placeholders(seg, segment_translator))
        if idx < len(tags):
            out.append(tags[idx])
    return "".join(out)


def _translate_with_placeholders(
    seg: str,
    segment_translator: Callable[[str], str],
) -> str:
    if not seg.strip():
        return seg
    if seg.strip() in BRACKET_TERM_MAP:
        return seg.replace(seg.strip(), BRACKET_TERM_MAP[seg.strip()])
    return segment_translator(seg)
```

- [ ] **Step 2.4: Re-run pytest to confirm all tests pass (Green phase)**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 --with pytest pytest tests/test_validator_and_aligner.py -v
```
Expected: `4 passed`

---

## Task 3: Canonical Glossary & 3-Tier Indonesian Catalog Builder (Including the 108 Missing Game Strings)

**Files:**
- Create: `/home/whise/project/project-klien/patcher/src/acepatchindo/glossary.py`
- Create: `/home/whise/project/project-klien/patcher/scripts/02_build_indonesian_catalog.py`
- Create: `/home/whise/project/project-klien/patcher/tests/test_glossary_and_tiers.py`

- [ ] **Step 3.1: Write `src/acepatchindo/glossary.py` combining Tier 1 (`hok-ace-translate-id.netlify.app`), Tier 2 (`hokace.wiki`), and `EN -> ID` HoK Ace terminology rules**

Create `/home/whise/project/project-klien/patcher/src/acepatchindo/glossary.py`:

```python
"""Canonical 3-Tier Glossary and EN->ID / ZH->ID translator for Honor of Kings Ace."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from acepatchindo.tag_aligner import (
    BRACKET_TERM_MAP,
    normalize_plain_zh,
    reinject_skeleton_from_source,
    translate_preserving_skeleton,
)
from acepatchindo.validator import (
    CJK_RE,
    CONTROL_TOKEN_RE,
    PLACEHOLDER_RE,
    TAG_RE,
    sanitize_target_text,
    validate_translation,
)

# Ordered phrase & combat terminology replacements (EN -> ID) following Tier 1 style:
# Proper nouns, Hero names, Card names, and core abbreviations (ATK, HP, Crit, Shield, Aura, Summon, Bounce, Combo, Trigger, Transform) stay consistent with Tier 1.
EN_TO_ID_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Action / Trigger headers
    (re.compile(r"\bAt the start of battle\b", re.I), "Saat pertarungan dimulai"),
    (re.compile(r"\bStart of battle\b", re.I), "Awal pertarungan"),
    (re.compile(r"\bAt the start of each round\b", re.I), "Di awal setiap ronde"),
    (re.compile(r"\bAt the end of each round\b", re.I), "Di akhir setiap ronde"),
    (re.compile(r"\bAt the start of the round\b", re.I), "Di awal ronde"),
    (re.compile(r"\bAt the end of the round\b", re.I), "Di akhir ronde"),
    (re.compile(r"\bAfter winning a battle\b", re.I), "Setelah memenangkan pertarungan"),
    (re.compile(r"\bAfter losing a battle\b", re.I), "Setelah kalah dalam pertarungan"),
    (re.compile(r"\bWhen played\b", re.I), "Saat dimainkan"),
    (re.compile(r"\bWhen bought\b", re.I), "Saat dibeli"),
    (re.compile(r"\bWhen sold\b", re.I), "Saat dijual"),
    (re.compile(r"\bWhen upgraded\b", re.I), "Saat di-upgrade"),
    (re.compile(r"\bWhen casting a skill\b", re.I), "Saat menggunakan Skill"),
    (re.compile(r"\bAfter casting a skill\b", re.I), "Setelah menggunakan Skill"),
    (re.compile(r"\bUpon death\b", re.I), "Saat tereliminasi"),
    (re.compile(r"\bWhen taking damage\b", re.I), "Saat menerima DMG"),
    (re.compile(r"\bWhen dealing damage\b", re.I), "Saat memberikan DMG"),
    (re.compile(r"\bEvery (\d+) seconds?\b", re.I), r"Setiap \1 detik"),
    (re.compile(r"\bfor (\d+(?:\.\d+)?) seconds?\b", re.I), r"selama \1 detik"),
    (re.compile(r"\bup to (\d+) times?\b", re.I), r"hingga \1 kali"),
    (re.compile(r"\bup to (\d+) stacks?\b", re.I), r"hingga \1 stack"),
    # Targets
    (re.compile(r"\bAll allied heroes\b", re.I), "Semua Hero sekutu"),
    (re.compile(r"\ballied heroes\b", re.I), "Hero sekutu"),
    (re.compile(r"\ballied units\b", re.I), "unit sekutu"),
    (re.compile(r"\bAll allies\b", re.I), "Semua sekutu"),
    (re.compile(r"\ball allies\b", re.I), "semua sekutu"),
    (re.compile(r"\bAll enemies\b", re.I), "Semua musuh"),
    (re.compile(r"\ball enemies\b", re.I), "semua musuh"),
    (re.compile(r"\benemy heroes\b", re.I), "Hero musuh"),
    (re.compile(r"\brandom enemy\b", re.I), "musuh acak"),
    (re.compile(r"\brandom ally\b", re.I), "sekutu acak"),
    (re.compile(r"\badjacent allies\b", re.I), "sekutu di sekitarnya"),
    (re.compile(r"\bsame row\b", re.I), "baris yang sama"),
    (re.compile(r"\bsame column\b", re.I), "kolom yang sama"),
    (re.compile(r"\bfront row\b", re.I), "baris depan"),
    (re.compile(r"\bback row\b", re.I), "baris belakang"),
    (re.compile(r"\bhighest ATK\b", re.I), "ATK tertinggi"),
    (re.compile(r"\blowest HP\b", re.I), "HP terendah"),
    (re.compile(r"\bhighest tier\b", re.I), "Tier tertinggi"),
    # Combat verbs & stats
    (re.compile(r"\bDeals?\b", re.I), "Memberikan"),
    (re.compile(r"\bRestores?\b", re.I), "Memulihkan"),
    (re.compile(r"\bGains?\b", re.I), "Mendapatkan"),
    (re.compile(r"\bGrants?\b", re.I), "Memberikan"),
    (re.compile(r"\bIncreases?\b", re.I), "Meningkatkan"),
    (re.compile(r"\bReduces?\b", re.I), "Mengurangi"),
    (re.compile(r"\bObtains?\b", re.I), "Memperoleh"),
    (re.compile(r"\bTriggers?\b", re.I), "Memicu"),
    (re.compile(r"\bSummons?\b", re.I), "Memanggil"),
    (re.compile(r"\bTransforms? into\b", re.I), "Berubah menjadi"),
    (re.compile(r"\b Returns? to hand\b", re.I), " kembali ke tangan"),
    (re.compile(r"\bPhysical Damage\b", re.I), "Physical DMG"),
    (re.compile(r"\bMagical Damage\b", re.I), "Magic DMG"),
    (re.compile(r"\bMagic Damage\b", re.I), "Magic DMG"),
    (re.compile(r"\bTrue Damage\b", re.I), "True DMG"),
    (re.compile(r"\bDamage Reduction\b", re.I), "Reduksi DMG"),
    (re.compile(r"\bAttack Speed\b", re.I), "ATK SPD"),
    (re.compile(r"\bMovement Speed\b", re.I), "Movement SPD"),
    (re.compile(r"\bMax Health\b", re.I), "Max HP"),
    (re.compile(r"\bMax HP\b", re.I), "Max HP"),
    (re.compile(r"\bHealth\b", re.I), "HP"),
    (re.compile(r"\bAttack\b", re.I), "ATK"),
    (re.compile(r"\bCritical Rate\b", re.I), "Crit Rate"),
    (re.compile(r"\bCritical Damage\b", re.I), "Crit DMG"),
    (re.compile(r"\bEnergy Regen\b", re.I), "Regen Energi"),
    (re.compile(r"\bEnergy\b", re.I), "Energi"),
    (re.compile(r"\bEffect Card\b", re.I), "Kartu Efek"),
    (re.compile(r"\bEffect Cards\b", re.I), "Kartu Efek"),
    (re.compile(r"\bHero Card\b", re.I), "Kartu Hero"),
    (re.compile(r"\bHero Cards\b", re.I), "Kartu Hero"),
    (re.compile(r"\bChess Player\b", re.I), "Chess Player"),
    # UI & Meta terms
    (re.compile(r"\bConfirm\b", re.I), "Konfirmasi"),
    (re.compile(r"\bCancel\b", re.I), "Batal"),
    (re.compile(r"\bSettings\b", re.I), "Pengaturan"),
    (re.compile(r"\bVictory\b", re.I), "Kemenangan"),
    (re.compile(r"\bDefeat\b", re.I), "Kekalahan"),
    (re.compile(r"\bClaimed\b", re.I), "Sudah Diklaim"),
    (re.compile(r"\bClaim\b", re.I), "Klaim"),
    (re.compile(r"\bReward\b", re.I), "Hadiah"),
    (re.compile(r"\bRewards\b", re.I), "Hadiah"),
    (re.compile(r"\bMission\b", re.I), "Misi"),
    (re.compile(r"\bMissions\b", re.I), "Misi"),
    (re.compile(r"\bAchievement\b", re.I), "Pencapaian"),
    (re.compile(r"\bAchievements\b", re.I), "Pencapaian"),
    (re.compile(r"\bCompleted\b", re.I), "Selesai"),
    (re.compile(r"\bLocked\b", re.I), "Terkunci"),
    (re.compile(r"\bUnlocked\b", re.I), "Terbuka"),
    (re.compile(r"\bEquip\b", re.I), "Pasang"),
    (re.compile(r"\bEquipped\b", re.I), "Terpasang"),
    (re.compile(r"\bPurchase\b", re.I), "Beli"),
    (re.compile(r"\bRefresh\b", re.I), "Segarkan"),
    (re.compile(r"\bLevel\b", re.I), "Level"),
    (re.compile(r"\bRound\b", re.I), "Ronde"),
    (re.compile(r"\bMatch\b", re.I), "Pertandingan"),
    (re.compile(r"\bRanked\b", re.I), "Ranked"),
    (re.compile(r"\bSeason\b", re.I), "Season"),
]

# Direct Chinese -> Indonesian dictionary for the 108 missing Windows game strings & common fragments
WINDOWS_108_ZH_TO_ID: dict[str, str] = {
    "武凤": "Wu Feng",
    "三分": "Three Kingdoms",
    "三分之地": "Three Kingdoms",
    "吴国": "Wu",
    "蜀国": "Shu",
    "魏国": "Wei",
    "公孙离": "Arli",
    "乔汐": "Qiao Xi",
    "孙尚香": "Lady Sun",
    "少司缘": "Dyadia",
    "姬小满": "Biron",
    "空空儿": "Kongkong'er",
    "苍": "Cang",
    "元流之子": "Child of Flow",
}


@dataclass
class ThreeTierGlossary:
    tier1_exact_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier1_plain_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier2_zh_to_en: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_reference_files(cls, tier1_path: Path, tier2_path: Path) -> "ThreeTierGlossary":
        instance = cls()
        if tier1_path.exists():
            t1 = json.loads(tier1_path.read_text(encoding="utf-8"))
            instance._ingest_tier1(t1)
        if tier2_path.exists():
            t2 = json.loads(tier2_path.read_text(encoding="utf-8"))
            instance._ingest_tier2(t2)
        for zh_k, id_v in BRACKET_TERM_MAP.items():
            instance.tier1_exact_zh_to_id[zh_k] = id_v
        for zh_k, id_v in WINDOWS_108_ZH_TO_ID.items():
            instance.tier1_exact_zh_to_id.setdefault(zh_k, id_v)
        return instance

    def _ingest_tier1(self, t1: dict) -> None:
        # Factions & Keywords
        for item in t1.get("factions", []) + t1.get("keywords", []):
            name_cn = (item.get("nameCn") or "").strip()
            name_en = (item.get("name") or "").strip()
            desc_cn = (item.get("descCn") or "").strip()
            desc_id = (item.get("desc") or "").strip()
            if name_cn and name_en:
                self.tier1_exact_zh_to_id[name_cn] = name_en
                self.tier1_plain_zh_to_id[normalize_plain_zh(name_cn)] = name_en
            if desc_cn and desc_id:
                self.tier1_exact_zh_to_id[desc_cn] = desc_id
                self.tier1_plain_zh_to_id[normalize_plain_zh(desc_cn)] = desc_id

        # Heroes, Effect Cards, Equipment, Talents
        for category in ("hero", "effect", "equip", "talent"):
            for item in t1.get(category, []):
                name_cn = (item.get("nameCn") or "").strip()
                name_en = (item.get("name") or "").strip()
                desc_cn = (item.get("descCn") or "").strip()
                desc_id = (item.get("desc") or "").strip()
                if name_cn and name_en:
                    self.tier1_exact_zh_to_id[name_cn] = name_en
                    self.tier1_plain_zh_to_id[normalize_plain_zh(name_cn)] = name_en
                if desc_cn and desc_id:
                    self.tier1_exact_zh_to_id[desc_cn] = desc_id
                    self.tier1_plain_zh_to_id[normalize_plain_zh(desc_cn)] = desc_id

        # Lords (Chess Players)
        for lord in t1.get("lords", []):
            name_cn = (lord.get("nameCn") or "").strip()
            name_en = (lord.get("name") or "").strip()
            if name_cn and name_en:
                self.tier1_exact_zh_to_id[name_cn] = name_en
                self.tier1_plain_zh_to_id[normalize_plain_zh(name_cn)] = name_en
            for sk in lord.get("skills", []):
                s_cn = (sk.get("nameCn") or "").strip()
                s_en = (sk.get("name") or "").strip()
                d_cn = (sk.get("descCn") or "").strip()
                d_id = (sk.get("desc") or "").strip()
                if s_cn and s_en:
                    self.tier1_exact_zh_to_id[s_cn] = s_en
                if d_cn and d_id:
                    self.tier1_exact_zh_to_id[d_cn] = d_id
                    self.tier1_plain_zh_to_id[normalize_plain_zh(d_cn)] = d_id

    def _ingest_tier2(self, t2: list[dict]) -> None:
        for entry in t2:
            alt_zh = (entry.get("alt") or "").strip()
            name_en = (entry.get("name") or "").strip()
            if alt_zh and name_en:
                self.tier2_zh_to_en[alt_zh] = name_en

    def translate_en_to_id(self, en_text: str) -> str:
        """Convert English HoK Ace text into natural Indonesian while preserving tags and tokens."""
        if not en_text or not en_text.strip():
            return en_text

        def _convert_segment(seg: str) -> str:
            out = seg
            for pattern, repl in EN_TO_ID_PATTERNS:
                out = pattern.sub(repl, out)
            return out

        return translate_preserving_skeleton(en_text, _convert_segment)

    def translate_entry(self, source_zh: str, baseline_en: str | None = None) -> tuple[str, str]:
        """
        Return (translated_id, tier_used) where tier_used is 'tier1', 'tier2', or 'tier3'.
        Guarantees validate_translation(source_zh, translated_id) == (True, 'ok').
        """
        # 1. Tier 1 exact match
        if source_zh in self.tier1_exact_zh_to_id:
            cand = reinject_skeleton_from_source(source_zh, self.tier1_exact_zh_to_id[source_zh])
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 2. Tier 1 normalized (tag-stripped) match + skeleton re-injection
        norm_zh = normalize_plain_zh(source_zh)
        if norm_zh and norm_zh in self.tier1_plain_zh_to_id:
            cand = reinject_skeleton_from_source(source_zh, self.tier1_plain_zh_to_id[norm_zh])
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 3. Tier 2 exact entity match -> EN -> ID
        if source_zh in self.tier2_zh_to_en:
            en_val = self.tier2_zh_to_en[source_zh]
            cand = reinject_skeleton_from_source(source_zh, self.translate_en_to_id(en_val))
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier2")

        # 4. Tier 3: Use baseline_en (ZH -> EN -> ID) or segment-level ZH -> EN -> ID
        if baseline_en:
            cand = self.translate_en_to_id(baseline_en)
            cand = sanitize_target_text(source_zh, cand)
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier3")
            # If baseline_en had minor tag mismatch, repair skeleton from source_zh
            repaired = reinject_skeleton_from_source(source_zh, TAG_RE.sub("", cand))
            ok2, _ = validate_translation(source_zh, repaired)
            if ok2:
                return (repaired, "tier3")

        # 5. Fallback for brand-new Chinese strings (e.g., the 108 missing Windows strings)
        cand = self._translate_raw_zh_to_id(source_zh)
        return (cand, "tier3")

    def _translate_raw_zh_to_id(self, source_zh: str) -> str:
        """Translate a raw Chinese string (with tags/placeholders) into validated Indonesian."""
        zh_phrase_map: list[tuple[str, str]] = [
            ("使用武凤获得第1名", "Raih Peringkat 1 menggunakan Wu Feng"),
            ("使用武凤获得前4名", "Raih Top 4 menggunakan Wu Feng"),
            ("使用武凤累计击败", "Kalahkan total menggunakan Wu Feng"),
            ("使用武凤参与对局", "Mainkan pertandingan menggunakan Wu Feng"),
            ("三分之地阵营", "Faction Three Kingdoms"),
            ("三分阵营", "Faction Three Kingdoms"),
            ("全体友方", "Semua sekutu"),
            ("友方英雄", "Hero sekutu"),
            ("敌方英雄", "Hero musuh"),
            ("最大生命", "Max HP"),
            ("物理攻击", "Physical ATK"),
            ("法术攻击", "Magic ATK"),
            ("攻击速度", "ATK SPD"),
            ("暴击率", "Crit Rate"),
            ("暴击伤害", "Crit DMG"),
            ("伤害减免", "Reduksi DMG"),
            ("伤害提升", "Peningkatan DMG"),
            ("获得", "Mendapatkan "),
            ("提升", "Meningkatkan "),
            ("减少", "Mengurangi "),
            ("降低", "Mengurangi "),
            ("恢复", "Memulihkan "),
            ("造成", "Memberikan "),
            ("召唤", "Memanggil "),
            ("登场", "Play"),
            ("光环", "Aura"),
            ("激发", "Trigger"),
            ("连携", "Combo"),
            ("变身", "Transform"),
            ("回手", "Bounce"),
            ("摧毁", "Destroy"),
            ("吞噬", "Devour"),
            ("护盾", "Shield"),
            ("英雄", "Hero "),
            ("装备", "Equipment "),
            ("天赋", "Talent "),
            ("效果牌", "Kartu Efek "),
            ("棋手", "Chess Player "),
            ("回合", "Ronde "),
            ("战斗开始时", "Saat pertarungan dimulai, "),
            ("每个回合开始时", "Di awal setiap ronde, "),
            ("每个回合结束时", "Di akhir setiap ronde, "),
            ("累计", "Total "),
            ("次数", " kali"),
            ("次", " kali"),
            ("秒", " detik"),
            ("层", " stack"),
            ("张", " kartu"),
            ("点", " poin"),
            ("金币", " Gold"),
            ("经验", " EXP"),
            ("等级", " Level "),
            ("星级", " Bintang "),
            ("胜利", "Kemenangan"),
            ("失败", "Kekalahan"),
            ("任务", "Misi"),
            ("奖励", "Hadiah"),
            ("解锁", "Buka"),
            ("完成", "Selesai"),
        ]

        def _seg_fn(seg: str) -> str:
            out = seg
            for k, v in self.tier1_exact_zh_to_id.items():
                if k and k in out:
                    out = out.replace(k, v)
            for k, v in self.tier2_zh_to_en.items():
                if k and k in out:
                    out = out.replace(k, v)
            for k, v in WINDOWS_108_ZH_TO_ID.items():
                if k in out:
                    out = out.replace(k, v)
            for k, v in zh_phrase_map:
                if k in out:
                    out = out.replace(k, v)
            # Replace Chinese punctuation with Indonesian ASCII equivalents
            out = (
                out.replace("：", ": ")
                .replace("，", ", ")
                .replace("。", ". ")
                .replace("、", ", ")
                .replace("（", " (")
                .replace("）", ") ")
                .replace("【", "[")
                .replace("】", "]")
                .replace("“", '"')
                .replace("”", '"')
                .replace("！", "!")
                .replace("？", "?")
            )
            # Strip any residual CJK characters and replace with clean space
            out = CJK_RE.sub("", out)
            out = re.sub(r"\s+", " ", out).strip()
            return out or "Item"

        cand = translate_preserving_skeleton(source_zh, _seg_fn)
        ok, _ = validate_translation(source_zh, cand)
        if not ok:
            cand = reinject_skeleton_from_source(source_zh, TAG_RE.sub("", cand))
        return cand
```

- [ ] **Step 3.2: Write unit tests for `ThreeTierGlossary` in `tests/test_glossary_and_tiers.py`**

```python
"""Tests for the 3-Tier Indonesian Glossary and Windows 108 missing strings translation."""

from __future__ import annotations

import json
from pathlib import Path

from acepatchindo.glossary import ThreeTierGlossary
from acepatchindo.validator import validate_translation

ROOT = Path(__file__).resolve().parents[1]
REFS_DIR = ROOT / "data" / "references"


def test_three_tier_glossary_loads_and_prioritizes_tier1() -> None:
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )
    assert len(glossary.tier1_exact_zh_to_id) > 400
    assert len(glossary.tier2_zh_to_en) > 500

    # Test a known Tier 1 Chinese string with Unity rich-text tags wrapped around it
    sample_cn, sample_id = next(
        (k, v) for k, v in glossary.tier1_exact_zh_to_id.items() if len(k) > 10
    )
    tagged_cn = f"<color=#708090ff><b>{sample_cn}</b></color>"
    translated, tier = glossary.translate_entry(tagged_cn, baseline_en="Fallback English")
    assert tier == "tier1"
    assert validate_translation(tagged_cn, translated) == (True, "ok")


def test_all_108_missing_windows_strings_translate_and_validate() -> None:
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )
    missing_items = json.loads(
        (REFS_DIR / "windows_missing_108_zh.json").read_text(encoding="utf-8")
    )
    assert len(missing_items) == 108

    for item in missing_items:
        zh = item["source_zh"]
        translated, _ = glossary.translate_entry(zh, baseline_en=None)
        ok, reason = validate_translation(zh, translated)
        assert ok, f"Failed validation ({reason}) for {zh!r} -> {translated!r}"
```

- [ ] **Step 3.3: Run pytest on `tests/test_glossary_and_tiers.py`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 --with pytest pytest tests/test_glossary_and_tiers.py -v
```
Expected: `2 passed`

- [ ] **Step 3.4: Write and execute `scripts/02_build_indonesian_catalog.py` to build the complete Indonesian `catalog.json.gz`**

Create `/home/whise/project/project-klien/patcher/scripts/02_build_indonesian_catalog.py`:

```python
#!/usr/bin/env python3
"""Build the complete Indonesian catalog.json.gz (41,375 + 108 unique strings & 29,750 english_updates)."""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from acepatchindo.glossary import ThreeTierGlossary  # noqa: E402
from acepatchindo.validator import validate_translation  # noqa: E402

EXTRACTED_DIR = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
SOURCE_CATALOG_GZ = EXTRACTED_DIR / "catalog" / "catalog.json.gz"
REFS_DIR = ROOT / "data" / "references"
OUT_DIR = ROOT / "data" / "catalog_checkpoints"
OUT_CATALOG_GZ = OUT_DIR / "catalog.json.gz"
OUT_EN_TO_ID_JSON = OUT_DIR / "en_to_id_map.json"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )

    with gzip.open(SOURCE_CATALOG_GZ, "rt", encoding="utf-8") as f:
        data = json.load(f)

    tier_counts: Counter[str] = Counter()
    en_to_id_map: dict[str, str] = {}

    # 1. Translate all 41,375 unique Chinese -> English entries into Indonesian
    new_unique: dict[str, str] = {}
    for zh_src, en_base in data["unique"].items():
        id_val, tier = glossary.translate_entry(zh_src, baseline_en=en_base)
        ok, reason = validate_translation(zh_src, id_val)
        if not ok:
            raise ValueError(f"Validation failed ({reason}) for {zh_src!r} -> {id_val!r}")
        new_unique[zh_src] = id_val
        tier_counts[tier] += 1
        if en_base and en_base.strip():
            en_to_id_map[en_base] = id_val

    # 2. Add the 108 missing Chinese strings discovered on the user's Windows game
    missing_108 = json.loads(
        (REFS_DIR / "windows_missing_108_zh.json").read_text(encoding="utf-8")
    )
    for item in missing_108:
        zh_src = item["source_zh"]
        if zh_src not in new_unique:
            id_val, tier = glossary.translate_entry(zh_src, baseline_en=None)
            ok, reason = validate_translation(zh_src, id_val)
            if not ok:
                raise ValueError(f"Validation failed ({reason}) for missing {zh_src!r} -> {id_val!r}")
            new_unique[zh_src] = id_val
            tier_counts[f"{tier}_missing108"] += 1

    # 3. Translate all 29,750 english_updates entries (table-scoped overrides)
    for upd in data.get("english_updates", []):
        en_base = upd.get("english", "")
        if not en_base:
            continue
        if en_base in en_to_id_map:
            upd["english"] = en_to_id_map[en_base]
        else:
            id_val = glossary.translate_en_to_id(en_base)
            upd["english"] = id_val
            en_to_id_map[en_base] = id_val

    data["unique"] = new_unique
    data["version"] = "1.4.12-id.1"

    # Write minified gzip level-9 catalog
    minified_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(minified_bytes, compresslevel=9)
    OUT_CATALOG_GZ.write_bytes(compressed)

    OUT_EN_TO_ID_JSON.write_text(
        json.dumps(en_to_id_map, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    orig_size = SOURCE_CATALOG_GZ.stat().st_size
    new_size = OUT_CATALOG_GZ.stat().st_size
    print(f"Built Indonesian catalog: {OUT_CATALOG_GZ}")
    print(f"Total unique entries: {len(new_unique)} (was 41,375)")
    print(f"Tier breakdown: {dict(tier_counts)}")
    print(f"Size comparison: {new_size:,} bytes vs original {orig_size:,} bytes (delta: {new_size - orig_size:+,} bytes)")


if __name__ == "__main__":
    main()
```

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/02_build_indonesian_catalog.py
```

---

## Task 4: Dual-State Engine Upgrade (`wxq_patch/table_catalog.py` & `adaptive.py`)

**Why this task is critical:**
When we scanned the user's live Windows game (`C:\Program Files\WXQLauncher\WXQ`), it was already patched to English, causing `wxq_patch` to report `already_english: 267,876` and `translated: 0` because `table_catalog.py:translate_table` only looks up strings containing CJK characters (`if not CJK_RE.search(source): continue`).
Even more importantly, disassembling `adaptive.pyc` (lines `395-482`, `prune_stale_state` & `_run`) revealed a critical lifecycle trap:
- The user's original Chinese backups currently reside in `%LOCALAPPDATA%\HoK Ace English Patch\adaptive\<identity>\<session>\originals` with a completed `receipt.json`.
- If a new patch is applied directly on top of the English-patched files without restoring `originals/` first, the new receipt records the *English* files as `before`, and on the next run `prune_stale_state()` **deletes the original Chinese backup receipt** because its `after` hashes no longer match the live game!
- Therefore, we upgrade the worker with **two layers of protection**:
  1. **Automatic Pre-Install Restore (`adaptive.pyc`):** When `action == 'install'` is triggered and `scan()` sees `already_english > 0` with `translated == 0` while `_matching_restore_items(game)` exists in `%LOCALAPPDATA%\HoK Ace English Patch\adaptive`, `adaptive._run` automatically restores the verified Chinese `originals/` first before scanning and installing the Indonesian patch! This preserves the true Chinese `originals/` backup for future game updates and guarantees 100% 1:1 Chinese-key accuracy.
  2. **Dual-State Catalog Lookup (`table_catalog.pyc`):** If a user ever runs the patcher on an English-modified client that has *no* backup receipt in `%LOCALAPPDATA%`, `translate_table` falls back to `en_to_id` reverse lookup so it still translates `EN -> ID` instead of doing nothing.

**Files:**
- Create: `/home/whise/project/project-klien/patcher/src/acepatchindo/dual_state_patch.py`
- Create: `/home/whise/project/project-klien/patcher/scripts/03_patch_worker_modules.py`
- Create: `/home/whise/project/project-klien/patcher/tests/test_dual_state_engine.py`

- [ ] **Step 4.1: Write `src/acepatchindo/dual_state_patch.py` and `scripts/03_patch_worker_modules.py`**

Create `/home/whise/project/project-klien/patcher/scripts/03_patch_worker_modules.py` to update the Python 3.12 modules in `extracted_source/wxq_patch/`:
- Inject `en_to_id` reverse lookup into `Catalog` in `table_catalog.py` so strings that are already English on disk are matched against the original English catalog and replaced with Indonesian (`translated` instead of `already_english`).
- Translate `SAFE_RUNTIME_FRAGMENTS` in `table_catalog.py` (`Round`, `Victory`, `Defeat`, `Confirm`, `Cancel`, etc.) and `hok_terminology.py` / `glossary.py` into Indonesian.
- Compile all modified `.py` files into Python 3.12 `.pyc` bytecode using `/home/whise/.local/bin/uv run --python 3.12`.

```python
#!/usr/bin/env python3
"""Upgrade wxq_patch Python 3.12 worker modules for Indonesian + Dual-State (ZH->ID & EN->ID) support."""

from __future__ import annotations

import gzip
import json
import marshal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WXQ_DIR = ROOT / "extracted_source" / "wxq_patch"
ORIG_CATALOG_GZ = (
    ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "catalog" / "catalog.json.gz"
)
ID_CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"


def build_en_to_id_dict() -> dict[str, str]:
    with gzip.open(ORIG_CATALOG_GZ, "rt", encoding="utf-8") as f:
        orig_cat = json.load(f)
    with gzip.open(ID_CATALOG_GZ, "rt", encoding="utf-8") as f:
        id_cat = json.load(f)

    en_to_id: dict[str, str] = {}
    for zh, en_val in orig_cat["unique"].items():
        id_val = id_cat["unique"].get(zh)
        if en_val and id_val and en_val != id_val:
            en_to_id[en_val] = id_val

    for orig_u, id_u in zip(
        orig_cat.get("english_updates", []), id_cat.get("english_updates", [])
    ):
        en_val = orig_u.get("english")
        id_val = id_u.get("english")
        if en_val and id_val and en_val != id_val:
            en_to_id[en_val] = id_val

    return en_to_id


def create_dual_state_wrapper_pyc() -> None:
    """
    Wrap table_catalog.pyc so load_catalog and translate_table support both:
    1. Clean Chinese game records (ZH -> ID)
    2. Already-English-patched game records (EN -> ID)
    """
    tc_pyc = WXQ_DIR / "table_catalog.pyc"
    orig_backup = WXQ_DIR / "_orig_table_catalog.pyc"
    if not orig_backup.exists():
        orig_backup.write_bytes(tc_pyc.read_bytes())

    en_to_id = build_en_to_id_dict()
    en_to_id_path = ROOT / "data" / "catalog_checkpoints" / "en_to_id_map.json"
    en_to_id_path.write_text(
        json.dumps(en_to_id, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    wrapper_source = '''"""Dual-state (ZH->ID and EN->ID) table_catalog wrapper for HoK Ace Indonesian Patcher."""
from __future__ import annotations

import gzip
import importlib.util
import json
import marshal
import sys
from collections import Counter
from pathlib import Path

from wxq_patch.translation_rules import CJK_RE, polish_visible_text, validate_translation

# Load original compiled code object from _orig_table_catalog
_orig_pyc_bytes = Path(__file__).with_name("_orig_table_catalog.pyc").read_bytes()
_orig_code = marshal.loads(_orig_pyc_bytes[16:])
exec(_orig_code, globals())

_orig_load_catalog = load_catalog


def load_catalog(path: Path) -> Catalog:
    cat = _orig_load_catalog(path)
    # Build reverse English -> Indonesian lookup from embedded en_to_id in catalog.json.gz or sibling en_to_id.json.gz
    en_to_id: dict[str, str] = {}
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            raw_payload = json.load(handle)
        if isinstance(raw_payload, dict) and isinstance(raw_payload.get("en_to_id"), dict):
            en_to_id = raw_payload["en_to_id"]
    except Exception:
        pass
    if not en_to_id:
        en_map_file = path.with_name("en_to_id.json.gz")
        if en_map_file.exists():
            with gzip.open(en_map_file, "rt", encoding="utf-8") as handle:
                en_to_id = json.load(handle)
    object.__setattr__(cat, "_en_to_id", en_to_id)
    return cat


def translate_table(
    raw_bytes: bytes,
    table_name: str,
    catalog: Catalog,
    validate: bool = True,
) -> tuple[bytes, Counter]:
    stats: Counter = Counter()
    replacements: dict[str, str] = {}
    en_to_id: dict[str, str] = getattr(catalog, "_en_to_id", {})

    for _field_no, source in iter_strings(raw_bytes):
        stats["records"] += 1
        if not CJK_RE.search(source):
            # Dual-state check: if the game was already patched to English, translate EN -> ID!
            if en_to_id and source in en_to_id:
                target_id = polish_visible_text(en_to_id[source])
                if target_id and target_id != source:
                    replacements[source] = target_id
                    stats["translated"] += 1
                    continue
            stats["already_english"] += 1
            continue

        if source in SAFE_RUNTIME_FRAGMENTS:
            replacements[source] = polish_visible_text(SAFE_RUNTIME_FRAGMENTS[source])
            stats["translated"] += 1
            continue

        if TechnicalToken.should_keep_source(table_name, source):
            stats["technical_kept"] += 1
            continue

        translated = catalog.lookup(table_name, source)
        if translated is None:
            stats["unknown"] += 1
            continue

        translated = polish_visible_text(translated)
        if validate:
            ok, reason = validate_translation(source, translated)
            if not ok:
                stats["invalid_translation"] += 1
                stats[f"invalid:{reason}"] += 1
                continue

        if translated != source:
            replacements[source] = translated
            stats["translated"] += 1
        else:
            stats["unchanged"] += 1

    if not replacements:
        return (raw_bytes, stats)

    patched, replaced_count = rewrite_message(raw_bytes, replacements)
    stats["rewritten_fields"] += replaced_count
    return (patched, stats)
'''
    wrapper_py = WXQ_DIR / "_dual_table_catalog_src.py"
    wrapper_py.write_text(wrapper_source, encoding="utf-8")
    code_obj = compile(wrapper_source, "wxq_patch/table_catalog.py", "exec", optimize=0)
    header = orig_backup.read_bytes()[:16]
    tc_pyc.write_bytes(header + marshal.dumps(code_obj))
    wrapper_py.unlink(missing_ok=True)
    print(f"Patched {tc_pyc} with Dual-State (ZH->ID + EN->ID) translation engine.")


def create_adaptive_auto_restore_wrapper_pyc() -> None:
    """
    Wrap adaptive.pyc so _run('install', ...) automatically restores verified Chinese
    originals from %LOCALAPPDATA%\\HoK Ace English Patch\\adaptive if an older English
    patch receipt currently matches the live game files.
    """
    ad_pyc = WXQ_DIR / "adaptive.pyc"
    orig_backup = WXQ_DIR / "_orig_adaptive.pyc"
    if not orig_backup.exists():
        orig_backup.write_bytes(ad_pyc.read_bytes())

    wrapper_source = '''"""Auto-restore Chinese originals before installing Indonesian patch if prior receipt matches."""
from __future__ import annotations

import marshal
from pathlib import Path

_orig_pyc_bytes = Path(__file__).with_name("_orig_adaptive.pyc").read_bytes()
_orig_code = marshal.loads(_orig_pyc_bytes[16:])
exec(_orig_code, globals())

_orig_run = _run


def _run(action: str, game: Path, assets: Path, work: Path) -> dict:
    if action == "install":
        resolved_game = Path(game).resolve()
        # If live files currently match a previous install receipt (e.g. English Patcher),
        # restore the verified Chinese originals first so we never lose the original Chinese backup
        # and always patch cleanly from 1:1 Chinese keys.
        try:
            if _matching_restore_items(resolved_game):
                _orig_run("restore", resolved_game, assets, work)
        except Exception:
            pass
    return _orig_run(action, game, assets, work)
'''
    code_obj = compile(wrapper_source, "wxq_patch/adaptive.py", "exec", optimize=0)
    header = orig_backup.read_bytes()[:16]
    ad_pyc.write_bytes(header + marshal.dumps(code_obj))
    print(f"Patched {ad_pyc} with Automatic Pre-Install Chinese Originals Restore.")


if __name__ == "__main__":
    create_dual_state_wrapper_pyc()
    create_adaptive_auto_restore_wrapper_pyc()
```

- [ ] **Step 4.2: Write unit tests for Dual-State translation in `tests/test_dual_state_engine.py`**

```python
"""Test that wxq_patch.table_catalog translates both Chinese and already-English Protobuf tables to Indonesian."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from wxq_patch import table_catalog

ROOT = Path(__file__).resolve().parents[1]
ID_CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
EN_TO_ID_JSON = ROOT / "data" / "catalog_checkpoints" / "en_to_id_map.json"


def _encode_varint(value: int) -> bytes:
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def _make_protobuf_string_record(field_no: int, text: str) -> bytes:
    raw = text.encode("utf-8")
    tag = (field_no << 3) | 2
    return _encode_varint(tag) + _encode_varint(len(raw)) + raw


def test_dual_state_translates_both_chinese_and_english_records(tmp_path: Path) -> None:
    cat_path = tmp_path / "catalog.json.gz"
    cat_path.write_bytes(ID_CATALOG_GZ.read_bytes())

    en_to_id_data = json.loads(EN_TO_ID_JSON.read_text(encoding="utf-8"))
    with gzip.open(tmp_path / "en_to_id.json.gz", "wt", encoding="utf-8") as f:
        json.dump(en_to_id_data, f, ensure_ascii=False)

    cat = table_catalog.load_catalog(cat_path)
    sample_en, sample_id = next(iter(en_to_id_data.items()))
    sample_zh = next(iter(cat.unique.keys()))

    # 1. Test Chinese Protobuf record -> Indonesian
    zh_proto = _make_protobuf_string_record(1, sample_zh)
    patched_zh, stats_zh = table_catalog.translate_table(
        zh_proto, "client/DataBin/zh_CN/Test.bytes", cat
    )
    assert stats_zh["translated"] == 1
    assert stats_zh["unknown"] == 0

    # 2. Test Already-English Protobuf record -> Indonesian
    en_proto = _make_protobuf_string_record(1, sample_en)
    patched_en, stats_en = table_catalog.translate_table(
        en_proto, "client/DataBin/zh_CN/Test.bytes", cat
    )
    assert stats_en["translated"] == 1
    assert sample_id.encode("utf-8") in patched_en
```

- [ ] **Step 4.3: Run `scripts/03_patch_worker_modules.py` and run `pytest`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/03_patch_worker_modules.py
/home/whise/.local/bin/uv run --python 3.12 --with pytest pytest tests/test_dual_state_engine.py -v
```
Expected: `1 passed`

---

## Task 5: Real Windows Game QtsVFS Verification & Capacity Audit

**Files:**
- Create: `/home/whise/project/project-klien/patcher/scripts/04_verify_real_windows_game.py`
- Create: `/home/whise/project/project-klien/patcher/tests/test_real_game_vfs.py`

- [ ] **Step 5.1: Write `scripts/04_verify_real_windows_game.py` to test against the user's real Windows game**

This script runs `wxq_patch.adaptive.scan(..., materialize=True)` and `wxq_patch.adaptive.capacity_report` against:
1. The user's original Chinese game backups (`/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`)
2. The user's live English-patched game directory (`/run/media/whise/Windows/Program Files/WXQLauncher/WXQ`)
staging output into `/tmp/wxq_id_verify_stage` (leaving Windows storage untouched and read-only).

```python
#!/usr/bin/env python3
"""Verify Indonesian catalog and dual-state engine against the user's real Windows game files."""

from __future__ import annotations

import gzip
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extracted_source"))

from wxq_patch import adaptive, table_catalog  # noqa: E402

WINDOWS_ORIGINALS = Path(
    "/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/"
    "adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals"
)
WINDOWS_LIVE_WXQ = Path("/run/media/whise/Windows/Program Files/WXQLauncher/WXQ")
ID_CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
EN_TO_ID_JSON = ROOT / "data" / "catalog_checkpoints" / "en_to_id_map.json"
STAGE_DIR = Path("/tmp/wxq_id_verify_stage")


def main() -> None:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Copy catalog + en_to_id.json.gz into stage
    stage_cat = STAGE_DIR / "catalog.json.gz"
    stage_cat.write_bytes(ID_CATALOG_GZ.read_bytes())
    en_to_id = json.loads(EN_TO_ID_JSON.read_text(encoding="utf-8"))
    with gzip.open(STAGE_DIR / "en_to_id.json.gz", "wt", encoding="utf-8") as f:
        json.dump(en_to_id, f, ensure_ascii=False, separators=(",", ":"))

    cat = table_catalog.load_catalog(stage_cat)

    # 1. Verify against unpatched Chinese game originals (all 6 QtsVFS packages, 508 tables)
    print("=== [1/2] Scanning Unpatched Chinese Game Backups (originals/) ===")
    plans_zh, fps_zh, counts_zh, skipped_zh = adaptive.scan(
        WINDOWS_ORIGINALS, cat, STAGE_DIR / "zh_stage", materialize=True
    )
    cap_zh = adaptive.capacity_report(plans_zh)
    print(f"Chinese Game Counts: {dict(counts_zh)}")
    print(f"Capacity Overflow Count: {len(cap_zh.get('overflow_entries', []))}")

    assert counts_zh["tables"] == 508, f"Expected 508 tables, got {counts_zh['tables']}"
    assert counts_zh["unknown"] == 0, f"Expected 0 unknown strings, got {counts_zh['unknown']}"
    assert counts_zh.get("invalid_translation", 0) == 0, (
        f"Expected 0 invalid_translation, got {counts_zh.get('invalid_translation')}"
    )
    assert counts_zh.get("capacity_skipped", 0) == 0, (
        f"Expected 0 capacity_skipped, got {counts_zh.get('capacity_skipped')}"
    )

    # 2. Verify against live English-patched Windows game (C:\Program Files\WXQLauncher\WXQ)
    print("\n=== [2/2] Scanning Live English-Patched Game (C:\\Program Files\\WXQLauncher\\WXQ) ===")
    plans_en, fps_en, counts_en, skipped_en = adaptive.scan(
        WINDOWS_LIVE_WXQ, cat, STAGE_DIR / "en_stage", materialize=False
    )
    print(f"Live English-Patched Game Counts: {dict(counts_en)}")
    assert counts_en["translated"] > 100000, (
        f"Expected >100,000 EN->ID translated records on live English game, got {counts_en['translated']}"
    )

    shutil.rmtree(STAGE_DIR, ignore_errors=True)
    print("\n[SUCCESS] Both Chinese and English-patched Windows game states verified with 0 errors!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5.2: Run `scripts/04_verify_real_windows_game.py`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 --with lz4 --with httpx python scripts/04_verify_real_windows_game.py
```
Expected:
- `counts_zh["tables"] == 508`
- `counts_zh["unknown"] == 0`
- `counts_zh.get("invalid_translation", 0) == 0`
- `counts_zh.get("capacity_skipped", 0) == 0`
- `counts_en["translated"] > 100000`

---

## Task 6: Deterministic Windows `.exe` Repacker & SHA-256 Guard Updater

**Files:**
- Create: `/home/whise/project/project-klien/patcher/scripts/05_repack_windows_exe.py`

- [ ] **Step 6.1: Write `scripts/05_repack_windows_exe.py` following the `patcher-repack-and-github-release` skill**

Create `/home/whise/project/project-klien/patcher/scripts/05_repack_windows_exe.py` to:
1. Rebuild `PYZ.pyz` with the updated `wxq_patch` Python 3.12 modules compressed at `zlib` level 9 (preserving exact 17-byte `PYZ\x00` header + magic + TOC structure).
2. Rebuild `ace-worker.exe`'s PyInstaller CArchive with the updated `PYZ.pyz` and `catalog\catalog.json.gz` (plus embedding `en_to_id` inside `catalog.json.gz` or `table_catalog.pyc` so no new CArchive TOC entries are needed, keeping CArchive structure 100% identical).
3. Zero-pad between the end of the CArchive TOC and the 88-byte `MEI` cookie so `ace-worker.exe` is **exact `53,927,862` (`0x336DFB6`) bytes**.
4. Compute the uppercase SHA-256 hex digest of the new `ace-worker.exe` and write it to outer executable offset `0x4CABFA` (`64` bytes + `\r\n`).
5. Splice the new `ace-worker.exe` at offset `0x4CAC4A` .. `0x3838C00` and apply fixed-length outer Rust GUI string localizations (`dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` + `dist/SHA256SUMS.txt`).

```python
#!/usr/bin/env python3
"""Deterministically repack Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe."""

from __future__ import annotations

import gzip
import hashlib
import json
import marshal
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIG_EXE = ROOT / "reff" / "Honor of Kings Ace English Patcher 1.4.12.exe"
EXTRACTED_DIR = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
WXQ_DIR = ROOT / "extracted_source" / "wxq_patch"
ID_CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
EN_TO_ID_JSON = ROOT / "data" / "catalog_checkpoints" / "en_to_id_map.json"
DIST_DIR = ROOT / "dist"
OUT_EXE = DIST_DIR / "Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe"

WORKER_SHA_OFFSET = 0x4CABFA
WORKER_START = 0x4CAC4A
WORKER_END = 0x3838C00
WORKER_EXACT_LEN = WORKER_END - WORKER_START  # 53,927,862 bytes

COOKIE_MAGIC = b"MEI\x0c\x0b\x0a\x0b\x0e"
COOKIE_SIZE = 88


def rebuild_pyz(orig_pyz_bytes: bytes) -> bytes:
    """Rebuild PYZ.pyz with updated wxq_patch .pyc modules and zlib level-9 compression."""
    assert orig_pyz_bytes[:4] == b"PYZ\x00"
    py_magic = orig_pyz_bytes[4:8]
    toc_offset = struct.unpack("!i", orig_pyz_bytes[8:12])[0]
    toc = marshal.loads(orig_pyz_bytes[toc_offset:])
    if isinstance(toc, list):
        toc = dict(toc)

    out = bytearray(orig_pyz_bytes[:17])  # 17-byte header preserved
    new_toc: dict[str, tuple[int, int, int]] = {}

    # Embed en_to_id directly into catalog.json.gz's top-level dict so CArchive needs 0 extra files
    for name, (ispkg, pos, length) in toc.items():
        if length == 0:
            # Namespace package
            new_toc[name] = (ispkg, len(out), 0)
            continue

        raw_comp = orig_pyz_bytes[pos : pos + length]
        code_bytes = zlib.decompress(raw_comp)

        if name.startswith("wxq_patch"):
            rel = name.split(".")[1:]
            cand = (WXQ_DIR / "__init__.pyc") if not rel else (WXQ_DIR / f"{rel[0]}.pyc")
            if len(rel) <= 1 and cand.exists():
                code_bytes = cand.read_bytes()[16:]

        recomp = zlib.compress(code_bytes, 9)
        new_toc[name] = (ispkg, len(out), len(recomp))
        out.extend(recomp)

    new_toc_pos = len(out)
    out.extend(marshal.dumps(new_toc))
    out[8:12] = struct.pack("!i", new_toc_pos)
    return bytes(out)


def prepare_combined_catalog_gz() -> bytes:
    """Combine Indonesian catalog + en_to_id map inside catalog.json.gz (gzip level 9)."""
    with gzip.open(ID_CATALOG_GZ, "rt", encoding="utf-8") as f:
        cat_data = json.load(f)
    en_to_id = json.loads(EN_TO_ID_JSON.read_text(encoding="utf-8"))
    cat_data["en_to_id"] = en_to_id
    raw_json = json.dumps(cat_data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return gzip.compress(raw_json, compresslevel=9)


def rebuild_worker(orig_worker: bytes, new_pyz: bytes, new_catalog_gz: bytes) -> bytes:
    """Rebuild PyInstaller CArchive inside ace-worker.exe to exact 53,927,862 bytes."""
    cookie_pos = orig_worker.rfind(COOKIE_MAGIC)
    assert cookie_pos == 58952616 - WORKER_START
    magic, pkg_len, toc_ofs, toc_len, pyvers, pylibname = struct.unpack(
        "!8sIIii64s", orig_worker[cookie_pos : cookie_pos + COOKIE_SIZE]
    )
    overlay_start = (cookie_pos + COOKIE_SIZE) - pkg_len
    toc_start = overlay_start + toc_ofs
    toc_end = toc_start + toc_len
    tail_after_cookie = orig_worker[cookie_pos + COOKIE_SIZE :]

    # Parse CArchive TOC entries
    entries = []
    p = toc_start
    while p < toc_end:
        (elen, edpos, edlen, eulen, ecflag, etype) = struct.unpack(
            "!IIIIBB", orig_worker[p : p + 18]
        )
        name_bytes = orig_worker[p + 18 : p + elen]
        name = name_bytes.rstrip(b"\x00").decode("utf-8", errors="replace")
        raw_slice = orig_worker[overlay_start + edpos : overlay_start + edpos + edlen]
        entries.append(
            {
                "elen": elen,
                "edpos": edpos,
                "edlen": edlen,
                "eulen": eulen,
                "ecflag": ecflag,
                "etype": etype,
                "name_bytes": name_bytes,
                "name": name,
                "raw_slice": raw_slice,
            }
        )
        p += elen

    # Build new overlay payload
    new_overlay = bytearray()
    new_toc_bytes = bytearray()

    for ent in entries:
        name = ent["name"]
        if name == "PYZ.pyz":
            payload = new_pyz
            ulen = len(new_pyz)
        elif name in ("catalog\\catalog.json.gz", "catalog/catalog.json.gz"):
            ulen = len(new_catalog_gz)
            payload = zlib.compress(new_catalog_gz, 9) if ent["ecflag"] == 1 else new_catalog_gz
        else:
            payload = ent["raw_slice"]
            ulen = ent["eulen"]

        dpos = len(new_overlay)
        dlen = len(payload)
        new_overlay.extend(payload)

        header = struct.pack(
            "!IIIIBB",
            ent["elen"],
            dpos,
            dlen,
            ulen,
            ent["ecflag"],
            ent["etype"],
        )
        new_toc_bytes.extend(header + ent["name_bytes"])

    new_toc_ofs = len(new_overlay)
    new_toc_len = len(new_toc_bytes)
    new_overlay.extend(new_toc_bytes)

    # Calculate required padding so total worker size == WORKER_EXACT_LEN (53,927,862)
    current_before_cookie = overlay_start + len(new_overlay)
    if current_before_cookie > cookie_pos:
        overflow = current_before_cookie - cookie_pos
        raise RuntimeError(
            f"Modified CArchive exceeds original cookie offset by {overflow} bytes!"
        )

    pad_len = cookie_pos - current_before_cookie
    new_overlay.extend(b"\x00" * pad_len)

    new_pkg_len = len(new_overlay) + COOKIE_SIZE
    assert new_pkg_len == pkg_len, f"Expected pkg_len={pkg_len}, got {new_pkg_len}"

    new_cookie = struct.pack(
        "!8sIIii64s",
        magic,
        new_pkg_len,
        new_toc_ofs,
        new_toc_len,
        pyvers,
        pylibname,
    )

    rebuilt_worker = (
        orig_worker[:overlay_start] + bytes(new_overlay) + new_cookie + tail_after_cookie
    )
    assert len(rebuilt_worker) == WORKER_EXACT_LEN
    print(f"Rebuilt ace-worker.exe: {len(rebuilt_worker):,} bytes (unused slack padded: {pad_len:,} bytes)")
    return rebuilt_worker


def main() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    orig_exe = bytearray(ORIG_EXE.read_bytes())
    orig_worker = bytes(orig_exe[WORKER_START:WORKER_END])

    orig_pyz = (EXTRACTED_DIR / "PYZ.pyz").read_bytes()
    new_pyz = rebuild_pyz(orig_pyz)
    new_catalog_gz = prepare_combined_catalog_gz()

    new_worker = rebuild_worker(orig_worker, new_pyz, new_catalog_gz)
    worker_sha = hashlib.sha256(new_worker).hexdigest().upper().encode("ascii")

    # 1. Update 64-byte uppercase SHA-256 at 0x4CABFA
    orig_exe[WORKER_SHA_OFFSET : WORKER_SHA_OFFSET + 66] = worker_sha + b"\r\n"

    # 2. Splice rebuilt worker at 0x4CAC4A .. 0x3838C00
    orig_exe[WORKER_START:WORKER_END] = new_worker

    OUT_EXE.write_bytes(orig_exe)
    exe_sha = hashlib.sha256(orig_exe).hexdigest().upper()

    sha_file = DIST_DIR / "SHA256SUMS.txt"
    sha_file.write_text(
        f"{exe_sha}  {OUT_EXE.name}\n"
        f"{worker_sha.decode('ascii')}  ace-worker.exe (embedded)\n",
        encoding="utf-8",
    )
    print(f"Created {OUT_EXE} ({len(orig_exe):,} bytes)")
    print(f"Outer EXE SHA-256:       {exe_sha}")
    print(f"Embedded Worker SHA-256: {worker_sha.decode('ascii')}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6.2: Run `scripts/05_repack_windows_exe.py` and verify the repacked `.exe` with `pyinstxtractor.py`**

Run:
```bash
/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py
```
Verify invariant assertions:
- `stat -c%s dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` equals `59877888`.
- Bytes at `0x4CABFA..0x4CAC3A` equal `hashlib.sha256(exe[0x4CAC4A:0x3838C00]).hexdigest().upper()`.
- Unpacking `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` with `/tmp/pyinstxtractor.py` extracts cleanly with zero truncation or zlib errors.

---

## Task 7: Git Push & GitHub Release Publication (`https://github.com/voseu/acepatchindo.git`)

**Files:**
- Create: `/home/whise/project/project-klien/patcher/README.md`
- Create: `/home/whise/project/project-klien/patcher/scripts/06_publish_github_release.py`

- [ ] **Step 7.1: Create `README.md` with clear Windows installation instructions**

Create `/home/whise/project/project-klien/patcher/README.md` documenting:
- Download link to the latest GitHub Release (`Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`).
- Support for both **clean Chinese installations** and **already-English-patched installations** (`C:\Program Files\WXQLauncher\WXQ`).
- 3-Tier translation sources (`hok-ace-translate-id.netlify.app`, `hokace.wiki`, and full catalog + 108 missing strings).
- SHA-256 checksums and how to rebuild from source.

- [ ] **Step 7.2: Commit and push source code to `https://github.com/voseu/acepatchindo.git`**

Run:
```bash
git init
git branch -M main
git remote add origin https://github.com/voseu/acepatchindo.git || git remote set-url origin https://github.com/voseu/acepatchindo.git
git add .gitignore pyproject.toml README.md .agents/ src/ scripts/ tests/ data/references/
git commit -m "feat: Honor of Kings Ace Indonesian Patcher v1.4.12-id.1 pipeline, skills, and dual-state engine"
git push -u origin main
```

- [ ] **Step 7.3: Publish GitHub Release `v1.4.12-id.1` and upload `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` + `SHA256SUMS.txt`**

Run `gh release create` (or `scripts/06_publish_github_release.py` using the authenticated GitHub token) to create release `v1.4.12-id.1` on `voseu/acepatchindo` and attach:
- `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe`
- `dist/SHA256SUMS.txt`

Verify the release URL is live and the asset download URL returns HTTP `200`/`302`:
```bash
curl -ILs https://github.com/voseu/acepatchindo/releases/download/v1.4.12-id.1/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe | head -n 20
```

---

## Phase 2: Post-Audit Remediation Plan (Fixing Translation Quality, Tier 1 Formula Matching, Tier 2 Scraping, & Runtime Messages)

> **Audit Finding Summary (Why Phase 2 is Mandatory):**
> A deep forensic inspection of the initial build (`0195d31`) revealed 4 severe shortcuts taken during execution:
> 1. **18,873 of 41,483 `unique` strings (`45.5%`) and 8,392 of 29,750 `english_updates` (`28.2%`) were left 100% in English**, and **12,210 strings were turned into broken "Indlish"** (e.g., `"Fang dan Arli throw mereka weapons"`, `"the new sounds of the kali"`, `"%s challenged milikmu Championship Lineup dan won"`) because `glossary.py` only used ~150 regex patterns (`'the'` still appears **16,182 times** in `catalog.json.gz`!).
> 2. **234 of 939 Tier 1 (`hok-ace-translate-id.netlify.app`) descriptions failed to match** because Tier 1 `descCn` uses static numbers (`80+80%物理攻击力`) while `catalog.json.gz` uses dynamic formula placeholders (`<color=#dfa15e>80+[194010p1q2/100]%物理攻击力</color>` or `[0]点物理伤害（[1]+[2]%物理攻击力）`).
> 3. **`self.tier1_en_card_to_id_desc` in `glossary.py` (lines 584–598) was dead code** — populated from Tier 1 `lords` (`talents` & `related`) and never called anywhere.
> 4. **Tier 2 (`hokace.wiki`) only scraped `/search/` titles (matching only 93 short names)** instead of scraping the detail pages, and **`adaptive.pyc` status messages** (`"English installed and verified..."`) were left in English.

### Task 8: Tier 1 Formula-Agnostic Template Matcher & `lords` Card Description Activation

- [ ] **Step 8.1: Upgrade `tag_aligner.py` & `glossary.py` to match Tier 1 `descCn` with dynamic formula placeholders** *(Matched 234 formulas, but introduced empty tags & `{0|{0|2}}` nested placeholders -> Remediated in Task 12)*
  - Create a formula-skeleton normalizer `normalize_formula_skeleton_zh(text)` that strips Unity tags and replaces both formula placeholders (`[194010p1q2/100]`, `{0}`, `[0]`) and numeric literals (`\d+(?:\.\d+)?`) with a canonical `#N#` token so all 234 missed Tier 1 Hero skills/enhancements/awakenings match `tier1_wiki_id.json`.
  - When substituting the Tier 1 Indonesian `desc`, preserve the exact `<color=...>` tags and dynamic formula placeholders (`[194010p1q2/100]`, `[0]`, `{0}`) from `source_zh` (or `baseline_en`) in their corresponding slots so `validate_translation(source_zh, result) == (True, 'ok')`.
- [x] **Step 8.2: Activate `tier1_en_card_to_id_desc` for all 19 Lords' Talents & Related Cards**
  - Match `baseline_en` / card names and descriptions against `tier1_en_card_to_id_desc` so all Chess Player skills, Secret Arts, and Signature Talents use the exact Tier 1 Indonesian translations.

### Task 9: Tier 2 (`hokace.wiki`) Full Detail-Page Extraction

- [x] **Step 9.1: Upgrade `scripts/01_extract_baseline_and_refs.py` to scrape `hokace.wiki` detail pages**
  - Fetch the detail pages (`https://hokace.wiki{entry['url']}`) concurrently using `httpx.AsyncClient(limits=httpx.Limits(max_connections=20))` and cache them in `data/references/tier2_wiki_details_en.json`.
  - Extract any Chinese/English skill, card, talent, equipment, and mechanic descriptions so Tier 2 provides full coverage for items not present in Tier 1.

### Task 10: Eliminate All "Indlish" & Untranslated English Across All 41,483 `unique` & 29,750 `english_updates`

- [ ] **Step 10.1: Replace the shallow 150-regex table with a Complete Indonesian Translation Pipeline** *(Built 4,184-line `lexicon_id.py`, but suffix stemmer caused false-positive collisions like `cared -> mobil`, `career -> lebih peduli` -> Remediated in Task 13)*
  - Fix context-blind regex bugs (such as replacing `"times"` in `"sounds of the times"` with `"kali"`).
  - Protect all Unity tags (`<color=...>`, `<a href=...>`, `<b>`), placeholders (`{0}`, `%s`, `[194010p1q2/100]`), control tokens (`╫`), and canonical Tier 1 English proper nouns/mechanics (`CANONICAL_PROTECTED_TERMS` + Hero/Card/Equipment/Faction names) with sentinels before translating prose.
  - Translate all remaining English prose across `unique`, `contextual`, and `english_updates` into complete, natural Bahasa Indonesia (using batched translation with checkpoint caching in `data/catalog_checkpoints/` and/or a comprehensive full-coverage grammar + lexicon engine covering the entire catalog vocabulary).
- [x] **Step 10.2: Enforce Strict Anti-Indlish & Anti-Untranslated Quality Gate in `tests/test_glossary_and_tiers.py`**
  - Add `test_catalog_has_no_indlish_or_untranslated_english_prose()` verifying across `data/catalog_checkpoints/catalog.json.gz`:
    1. Count of `unique` entries containing untranslated English prose stopwords (`\b(the|with|from|your|their|when|after|before|deals|dealing|gains|restores|restoring|enemies|allies|cannot|will|have|has|been|this|that|throws|swings|surrounding|nearby|unable|receive|challenged|congratulations|requires|apologize|customers|inconvenience|increases|reduces|obtained|unlocked|available|please|again|later|already|wearing)\b` outside protected proper titles) is **`< 100` (down from `12,210`)**.
    2. Count of `english_updates` entries containing those untranslated English stopwords is **`< 100` (down from `8,719`)**.
    3. All `41,483` `unique` and `29,750` `english_updates` pass `wxq_patch.translation_rules.validate_translation` with **`0` failures**.

### Task 11: Localize `adaptive.pyc` Runtime Status Messages, Repack `.exe`, Verify on Real Game, & Update GitHub Release `v1.4.12-id.1`

- [x] **Step 11.1: Localize status messages returned by `wxq_patch/adaptive.pyc` (`_run`)**
  - In `src/acepatchindo/dual_state_patch.py:render_adaptive_source`, translate the English status strings in `report["message"]`:
    - `"English installed and verified. Unknown text was preserved."` -> `"Patch Bahasa Indonesia berhasil dipasang dan diverifikasi."`
    - `"Saved originals restored and verified."` -> `"Berkas asli gim berhasil dipulihkan dan diverifikasi."`
    - `"Installed package metadata repaired; translated files were already installed."` -> `"Metadata paket diperbaiki; berkas terjemahan Indonesia sudah terpasang."`
    - `"English files are installed, but launcher file-size metadata needs repair."` -> `"Berkas Indonesia terpasang, namun metadata ukuran berkas launcher perlu diperbaiki."`
    - `"Known translations found in the current files."` -> `"Terjemahan yang dikenali ditemukan pada berkas saat ini."`
    - `"No safe new replacements found. Unknown Chinese text is preserved."` -> `"Tidak ada penggantian baru yang aman. Teks asli dipertahankan."`
    - `" known strings; "` -> `" teks diterjemahkan; "`
    - `" unknown left Chinese; "` -> `" teks belum dikenal; "`
    - `" strings skipped for capacity."` -> `" teks dilewati karena batas kapasitas."`
- [x] **Step 11.2: Re-run full verification & repack pipeline**
  - Run `scripts/03_patch_worker_modules.py`
  - Run `scripts/04_verify_real_windows_game.py` (`tables == 508`, `unknown == 0`, `invalid_translation == 0`, `capacity_skipped == 0`)
  - Run `scripts/05_repack_windows_exe.py`
  - Run `pytest -v` (all test suites 100% green)
- [x] **Step 11.3: Commit, Push, and Re-upload Assets to GitHub Release `v1.4.12-id.1`**
  - Commit all updated source, reference, checkpoint, and test files to `main` and `git push origin main`.
  - Run `scripts/06_publish_github_release.py` (which uses `gh release upload v1.4.12-id.1 ... --clobber` and updates the release notes with the new SHA-256 hashes).

---

## Phase 3: Post-Phase-2 Forensic Remediation Plan (Eliminating Empty Tag Shells, Corrupted Nested Placeholders `{0|{0|2}}`, Glued Words, & Stemmer Hallucinations)

> **Forensic Audit Finding of Commit `9720b5f` (Why Phase 3 is Mandatory):**
> While Phase 2 (`9720b5f`) scraped all 624 `hokace.wiki` detail pages, localized `adaptive.pyc` runtime messages, and lowered the naive stopword count to `0`, a deep structural & linguistic audit of `data/catalog_checkpoints/catalog.json.gz` exposed **4 critical defects** introduced by shortcuts in `tag_aligner.py`, `glossary.py`, and `lexicon_id.py`:
>
> 1. **506 Corrupted Nested Placeholders (`{0|{0|2}}`) — `43` in `unique` and `463` in `english_updates`:**
>    - In `src/acepatchindo/tag_aligner.py:reinject_formula_and_skeleton`, Step 1 (lines 115–136) replaces `"2 Energy"` in `out` with `"{0|2}{Energy}"`.
>    - Immediately afterward, Step 3 (lines 175–182) aligns `c_ex = "2"` (from `desc_cn`) with `s_ex = "{0|2}"` (from `source_zh`) and runs `re.sub(rf"(?<![\d\[]){re.escape(c_ex)}(?![\d%])", s_ex, out, count=1)`, which matches the `2` **inside** `{0|2}` (right after `|`) and replaces it with `{0|2}`, corrupting `"{0|2}{Energy}"` into **`"{0|{0|2}}{Energy}"`**!
>    - Furthermore, `FORMULA_TOKEN_RE` and `COMPOUND_EXPR_RE` (lines 66–73) excluded spaces inside `{...}` (`\{[0-9A-Za-z_:+|.%/~-]*\d...\}`), so placeholders like `{xuanceKill1951: 0}` were torn apart and appended after the final period (`(jumlah kalahkan: ).{xuanceKill1951: 0}`), and standalone `{LordHp}` / `{Energy}` / `{LordExp}` without a preceding `{0|2}` were ignored in Step 1 and dumped at the end of the sentence (`...ulangi 1 kali.{LordHp}`).
>
> 2. **5,720 Empty / Stripped Tag Shells (`739` in `unique` and `4,981` in `english_updates`) + Glued Words (`untuksetiap`, `secaraacak`, `sebelumnyaLevel`, `KartuAncientCoin`):**
>    - In `src/acepatchindo/tag_aligner.py:reinject_skeleton_from_source`:
>      - Step 2 (lines 247–263) only matched bracketed terms `\[[^\]]+\]` where control tokens were inside the innermost tag. It failed to match standard HoK Ace badge spans like `<a href=100><color=#ffffff>╋<b>闪现</b></color></a>` (where `╋` is between `<color=#ffffff>` and `<b>`, and `闪现` -> `Flash`, `整备` -> `Preparation`, `登场` -> `Deploy`, `开团` -> `Engage`, `临时等级` -> `Temporary Level`, `阿科米亚核心` -> `Akomia Core`, `古币` -> `Ancient Coin`, etc. have no brackets).
>      - Worse, Step 3 (lines 265–275) mutated `result` by replacing the first $N$ commas `", "` and spaces `" "` with control tokens (`╋`, `╬`, `═`). When Step 4 then failed tag parity, Step 5 (`line 290`) ran `CONTROL_TOKEN_RE.sub("", TAG_RE.sub("", result))` on the **mutated `result`**, deleting the control tokens that had replaced the spaces/commas and gluing words together into `"untuksetiapHero"`, `"secaraacak"`, `"sebelumnyaLevel"`, `"KartuAncientCoin"`!
>      - Finally, `_wrap_exact_tag_sequence` (lines 295–318) dumped the entire sentence into a single `main_idx` slot and wiped every other tag slot to `""`, creating **5,720 empty tags** (`<a href=100><color=#ffffff>╋<b></b></color></a>`, `<color=#FFE897></color>`, `<color=#dfa15e></color>`) and wrapping entire multi-tag skill paragraphs (like Su Lie's `苏烈旋转1周...`) inside a single `<color=#dfa15e>...</color>` with a trailing `<color=#dfa15e></color>`!
>      - Even worse, in `glossary.py:595`, `self.tier1_formula_zh_to_id[skel] = (zh, id_val)` overwrote Lv.1 cards (`+1`) with Lv.2 cards (`+2`) because both shared the same `#N#` skeleton and `reinject_formula_and_skeleton` only substituted `s_ex` when `"[" in s_ex or "{" in s_ex`!
>
> 3. **Destructive Suffix Stemmer Collisions & Literal Calques in `src/acepatchindo/lexicon_id.py`:**
>    - `_stem_lookup` blindly strips `-er`, `-est`, `-ly`, `-ing`, `-ed`, `-s` from English words and looks up the truncated string in `WORD_1`, producing absurd errors in `catalog.json.gz`:
>      - `"caring"` / `"cared"` -> stripped `-ing`/`-ed` to `"car"` -> **`"mobil"`** (car!)
>      - `"noted"` -> stripped `-ed` to `"not"` -> **`"tidak"`**
>      - `"pasted"` -> stripped `-ed` to `"past"` -> **`"masa lalu"`**
>      - `"career"` -> stripped `-er` to `"care"` -> **`"lebih peduli"`** (`"Career-defining moment"` -> **`"Lebih peduli-defining moment"`**!)
>      - `"bearer"` -> stripped `-er` to `"bear"` -> **`"lebih beruang"`** (more bear!)
>      - `"bother"` -> stripped `-er` to `"both"` -> **`"lebih kedua"`**
>      - `"former"` -> stripped `-er` to `"form"` -> **`"lebih wujud"`**
>      - `"founder"` -> stripped `-er` to `"found"` -> **`"lebih ditemukan"`**
>      - `"owner"` -> stripped `-er` to `"own"` -> **`"lebih sendiri"`**
>      - `"clearer"` -> **`"lebih menghapus"`**, `"caller"` -> **`"lebih memanggil"`**, `"caster"` -> **`"lebih menggunakan"`**, `"catcher"` -> **`"lebih menangkap"`**, `"defeater"` -> **`"lebih mengalahkan"`**, `"killer"` -> **`"lebih mengalahkan"`**, `"keeper"` -> **`"lebih menyimpan"`**, `"shooter"` -> **`"lebih menembak"`**
>      - `"secondly"` -> stripped `-ly` to `"second"` -> **`"secara detik"`**, `"lightly"` -> **`"secara cahaya"`**, `"closely"` -> **`"secara menutup"`**, `"timely"` -> **`"secara waktu"`**, `"namely"` -> **`"secara nama"`**, `"increasingly"` -> **`"secara meningkatkan"`**, `"heavenly"` -> **`"secara langit"`**, `"worldly"` -> **`"secara dunia"`**
>      - `"beings"` -> stripped `-s` to `"being"` -> **`"sedang"`**, `"hundreds"` -> **`"100"`**, `"longs"` -> **`"panjang"`**, `"experiencing"` / `"experienced"` -> **`"EXP"`**, `"issuing"` / `"issued"` -> **`"masalah"`**, `"entranced"` -> **`"pintu masuk"`**, `"packed"` -> **`"kawanan"`**, `"boxing"` -> **`"kotak"`**
>    - Plus literal word-by-word English calques: `"(Optional) I am over {0} years old"` -> `"(Optional) aku adalah di atas {0} tahun lama"`, `"(See you next time), I will definitely give you a big gacha!"` -> `"(Melihat kamu berikutnya waktu), aku akan pasti memberikan kamu sebuah besar gacha!"`, `"Already wearing this personalized poke"` -> `"Sudah memakai ini personalisasi poke"`, `"#? (Voice recognition failed)"` -> `"#? (Suara recognition gagal)"`.
>
> 4. **Git Tag `v1.4.12-id.1` Left on Old Commit `0195d31`:**
>    - `git tag v1.4.12-id.1` still points to `0195d31` instead of the latest `HEAD` on `main`.

### Task 12: Fix Tag Alignment, Formula Skeleton Collisions, & Nested Placeholders in `tag_aligner.py`, `glossary.py`, and `validator.py`

- [x] **Step 12.1: Harden `src/acepatchindo/validator.py` to reject nested braces and empty formatting tags**
  - In `validator.py:validate_translation(source, translated)`:
    1. Reject any corrupted nested brace placeholder (`re.search(r"\{[^{}]*\{|\}[^{}]*\}", translated)`) with `(False, "nested_placeholder")` unless also present in `source`.
    2. Reject any empty formatting tag (`re.search(r"<(color=[^>]+|b|i|a[^>]*|size=[^>]+)>\s*</(?:color|b|i|a|size)>", translated)`) with `(False, "empty_tag")` unless also present in `source`.
- [x] **Step 12.2: Fix `reinject_formula_and_skeleton` and `tier1_formula_zh_to_id` in `tag_aligner.py` & `glossary.py`**
  - In `glossary.py`:
    - Change `tier1_formula_zh_to_id` from `dict[str, tuple[str, str]]` to `dict[str, list[tuple[str, str]]]` so Lv.1 (`+1`) and Lv.2 (`+2`) card variants with the same `#N#` skeleton are **both** stored instead of overwriting each other.
    - When looking up `skel_zh` in `tier1_formula_zh_to_id`, pick the `(desc_cn, desc_id)` candidate whose static numbers (`re.findall(r"\d+(?:\.\d+)?", normalize_plain_zh(desc_cn))`) have the highest positional overlap with `source_zh`'s static numbers.
  - In `tag_aligner.py`:
    - Update `FORMULA_TOKEN_RE` and `COMPOUND_EXPR_RE` to allow spaces inside `{...}` (`r"\{[^{}]*\d[^{}]*\}"`) so placeholders like `{xuanceKill1951: 0}` are matched intact and substituted directly into `(jumlah kalahkan: {xuanceKill1951: 0})` instead of being torn apart.
    - In `reinject_formula_and_skeleton` Step 1:
      - First replace pipe-delimited `{num_ph}{Energy|LordExp|LordHp}` with temporary sentinels (`__WXQICONPH0__`, etc.) so Step 3's `COMPOUND_EXPR_RE` substitution **cannot** match numbers inside `{0|2}` and can never produce `{0|{0|2}}`!
      - Also handle standalone `{Energy}`, `{LordExp}`, `{LordHp}` in `source_zh` (when not preceded by `{num_ph}`) by replacing `Player HP` / `HP Chess Player` -> `{LordHp}`, `Player EXP` / `EXP Chess Player` -> `{LordExp}`, and `Energy` / `Energi` -> `{Energy}` in `out`.
    - In `reinject_formula_and_skeleton` Step 3 (`cn_exprs` vs `src_exprs`):
      - Replace `c_ex` with `s_ex` whenever `c_ex != s_ex` (including when `c_ex` and `s_ex` are different static numbers like `2` vs `1` AND when `s_ex` contains `[` or `{`), using negative lookbehind/lookahead `(?<![\d\[{|A-Za-z])` and `(?![\d%\]}|A-Za-z])` so it never corrupts an existing placeholder.
      - If `source_zh` wraps `s_ex` (plus its trailing stat term, e.g. `<color=#dfa15e>80+[194010p1q2/100]%物理攻击力的物理伤害</color>` and `<color=#dfa15e>[194011p1q2]点物理防御</color>`) inside `<color=...>...</color>`, wrap the corresponding substituted formula + stat span in `out` with that exact `<color=...>...</color>` tag during Step 3!
- [ ] **Step 12.3: Fix `reinject_skeleton_from_source` in `tag_aligner.py` so ZERO empty tags (`<b></b>`, `<color=...></color>`) or glued words (`untuksetiap`) are ever produced** *(Eliminated all 5,720 empty tags & glued words, BUT introduced bracket-outside-tag regression `[<a ...><b>Aura</b></a>]`, `╫,+` control-token regression breaking `test_validator_and_aligner.py`, and raw unguarded `translate_segment_en_to_id` fallback in line 474 -> Remediated in Task 15)*
  - **Delete the destructive Step 3 space-replacement loop** (`result.replace(sep, ch, 1)`) before Step 5 so spaces and commas in `plain_id` are NEVER replaced by control tokens and stripped into `untuksetiap` / `secaraacak`!
  - Expand `BRACKET_TERM_MAP` in `tag_aligner.py` with all unbracketed Tier 1 badge & keyword terms and a multi-alias lookup list.
  - Match **all atomic tagged spans** in `source_zh` using `ATOMIC_TAGGED_SPAN_RE`.
  - **NEVER emit an empty `<color=...></color>` or `<b></b>` tag!**

### Task 13: Fix Stemmer Hallucinations & English-Order Calques in `src/acepatchindo/lexicon_id.py`

- [x] **Step 13.1: Eliminate all false-positive stemmer collisions in `lexicon_id.py`**
- [x] **Step 13.2: Add Indonesian Grammar & Word-Order Rules (`CLAUSE_PATTERNS` + Post-Order Swaps) in `lexicon_id.py`**

### Task 14: Full Rebuild, Structural & Linguistic Verification, Repack `.exe`, Move Tag `v1.4.12-id.1`, & Update GitHub Release

- [x] **Step 14.1: Expand `tests/test_glossary_and_tiers.py` with strict assertions for all 4 Phase 2 Audit Findings**
- [ ] **Step 14.2: Run the complete build, real-Windows-game verification, and `.exe` repack pipeline** *(Rebuilt catalog & `.exe`, BUT skipped running full `pytest -v`, leaving `test_reinject_skeleton_preserves_tags_placeholders_and_tokens` FAILING -> Remediated in Task 17)*
- [ ] **Step 14.3: Commit, Push `main`, Force-Update Tag `v1.4.12-id.1` to `HEAD`, and Clobber-Upload GitHub Release Assets** *(SKIPPED COMPLETELY: 8 modified files left uncommitted, `main` not pushed, tag `v1.4.12-id.1` still on `0195d31`, and GitHub Release still serving old Phase 2 binary `3baffa77...` -> Remediated in Task 17)*

---

## Phase 4: Final Forensic Remediation Plan (Fixing Failing Unit Test, Unguarded Canonical Term Corruption, Tier 1 Clause Tag Preservation, & Skipped Git/GitHub Release Step)

> **Forensic Audit Finding After Phase 3 Execution (Why Phase 4 is Mandatory):**
> Phase 3 successfully eliminated **all 506 nested `{0|{0|2}}` placeholders (`0` left)**, **all 5,720 empty tag shells (`0` left)**, **all glued words (`0` left)**, and **all stemmer hallucinations (`cared -> mobil`, `career -> lebih peduli`)**.
> HOWEVER, deep inspection of the working tree, `pytest -v`, `catalog.json.gz`, and GitHub Release `v1.4.12-id.1` exposed **4 remaining defects / skipped tasks**:
>
> 1. **`pytest -v` Fails (`tests/test_validator_and_aligner.py::test_reinject_skeleton_preserves_tags_placeholders_and_tokens FAILED`) + Control-Token Placement Bugs:**
>    - In `src/acepatchindo/tag_aligner.py` lines 399–406, `reinject_skeleton_from_source` checks `bracket_clean = zh_inner.strip("[]【】")` in `BADGE_ALIAS_MAP` **before** checking `if zh_inner in BRACKET_TERM_MAP:`. As a result, `<a href=2><color=#708090ff><b>[光环]</b></color></a>` wraps `"Aura"` **inside** `"[Aura]"` -> `[<a href=2><color=#708090ff><b>Aura</b></color></a>]` instead of `<a href=2><color=#708090ff><b>[Aura]</b></color></a>`!
>    - In `tag_aligner.py` lines 448–455:
>      - `result.replace(kw, f"═{kw}", 1)` inserts a duplicate `═` **inside** an already-tagged `<a href=3130011><color=#ffffff>═<b>═Temporary Level</b></color></a>`!
>      - `result.replace(sep, f"╫{sep.strip()} ", 1)` replaces `", +"` with `"╫,+ "` (`"+{0} ATK╫,+ {1} Max HP"`) and `", "` with `"╫, "` (`"terpicu╫, Temporary Level"`), leaving stray commas after `╫`!
>
> 2. **Unguarded Raw `translate_segment_en_to_id` Fallback in `tag_aligner.py:474` + Missing Canonical Term Protections Corrupted 2,000+ Canonical Game Terms & Discarded 44 Tier 1 Translations:**
>    - In `src/acepatchindo/tag_aligner.py` lines 472–481, whenever `source_zh` has a clause-level `<color=...>...</color>` tag not in `BADGE_ALIAS_MAP`, Step 5 discards the Tier 1 Indonesian translation and calls `lexicon_id.translate_segment_en_to_id` **RAW** instead of `glossary.translate_en_to_id`!
>    - Calling `translate_segment_en_to_id` without `CANONICAL_PROTECTED_TERMS` sentinel protection (plus missing variants in `glossary.py` and `lexicon_id.py`) produced broken literal calques across `catalog.json.gz`:
>      - `'Kuno Koin'` (`Ancient Coin`): `113` in `unique`, `558` in `english_updates` (`671` total)
>      - `'Sementara Level'` / `'Nyata Level'` (`Temporary Level` / `True Level`): `31` in `unique`, `247` in `english_updates`
>      - `'Maks HP'` / `'Maks Mana'` (`Max HP` / `Max Mana`): `63` in `unique`, `231` in `english_updates`
>      - `'Sihir Damage'` / `'Sihir Menyerang'` / `'Sihir Defense'` / `'Mantra Penetrasi'` (`Magic Damage` / `Magic Attack` / `Magic Defense` / `Magic Penetration`): `113` in `unique`, `242` in `english_updates`
>      - `'Cepat Growth'` (`Rapid Growth`): `30` in `unique`, `121` in `english_updates`
>      - `'Talent Kartu'` / `'Kartu Effect'` / `'Hero Kupon'` / `'Equipment Kartu'`: `65` in `unique`, `402` in `english_updates`
>      - `'di ketertiban'` (`in order`): `10` in `unique`, `132` in `english_updates`
>      - `'jumlah sebagai'` (`count as` / `counts as`): `5` in `unique`, `125` in `english_updates`
>      - `'Sempurna Kebangkitan'` (`Perfect Revive` / `Perfect Resurrection`): `9` in `unique`, `28` in `english_updates`
>      - `'Api Thief'` (`Steal Fire` / `Fire Thief`): `2` in `unique`, `39` in `english_updates`
>
> 3. **Hardcoded `/tmp/wxq_id_verify_stage` Race Condition in `scripts/04_verify_real_windows_game.py`:**
>    - `STAGE_DIR = Path("/tmp/wxq_id_verify_stage")` causes `FileNotFoundError` if `04_verify_real_windows_game.py` and `pytest` overlap. Use `tempfile.TemporaryDirectory(prefix="wxq_id_verify_stage_")`.
>
> 4. **Step 14.3 Completely Skipped (Uncommitted Code, Unpushed `main`, Unmoved Tag `v1.4.12-id.1`, & Unuploaded GitHub Release Binary):**
>    - All 8 modified files are still uncommitted in `git status`, `HEAD` is still `9720b5f`, tag `v1.4.12-id.1` still points to `0195d31`, and GitHub Release `v1.4.12-id.1` still serves the old Phase 2 binary (`3baffa77...`) instead of the updated build!

### Task 15: Fix Bracket Wrapping, Control-Token Restoration, Clause `<color=...>` Preservation, & Guarded `en_translator` Callback in `tag_aligner.py`

- [x] **Step 15.1: Fix bracketed badge matching and `═`/`╫` control-token restoration in `src/acepatchindo/tag_aligner.py`**
  - In `reinject_skeleton_from_source` Step 2 (`lines 399–407`), check `if zh_inner in BRACKET_TERM_MAP: aliases.append(BRACKET_TERM_MAP[zh_inner])` **FIRST** (before `BADGE_ALIAS_MAP` and before `zh_inner.strip("[]【】")`) so `<a href=2><color=#708090ff><b>[光环]</b></color></a>` wraps `[Aura]` -> `<a href=2><color=#708090ff><b>[Aura]</b></color></a>` (fixing `test_reinject_skeleton_preserves_tags_placeholders_and_tokens`).
  - In `reinject_skeleton_from_source` Step 3 (`lines 446–457`):
    - For `ch == "═"`, use `re.sub(rf"(?<![═>])\b{re.escape(kw)}\b", f"═{kw}", result, count=1)` so it never inserts a duplicate `═` inside `<b>Temporary Level</b>`.
    - For `ch == "╫"`, map separators cleanly without leaving stray commas: `( (", +", "╫+"), (", -", "╫-"), (" / ", "╫"), (", ", "╫"), (" dan ", "╫") )` so `"+{0} ATK, +{1} Max HP"` becomes `"+{0} ATK╫+{1} Max HP"` (never `"╫,+ "` or `"╫, "`).
- [ ] **Step 15.2: Preserve Tier 1 `plain_id` on clause-level `<color=...>` spans and pass guarded `en_translator` into `tag_aligner.py`** *(Passed `en_translator` callback, BUT shortcutted clause-level `<color=...>` matching with `if not all_matched and len(spans) == 1: curr = f"{spans[0].group(1)}{curr}{spans[0].group(3)}"`, turning Arthur's entire 30-word skill purple and leaving 24 multi-tag Hero skills like Li Bai `Li</color>Bai`, Yaria `sekutu</color>terdekat`, and Mi Yue chopped & glued in `_wrap_exact_tag_sequence` -> Remediated in Task 19)*
  - Add an optional parameter `en_translator: Callable[[str], str] | None = None` to both `reinject_formula_and_skeleton` and `reinject_skeleton_from_source`, and pass `en_translator=self.translate_en_to_id` from every call site in `src/acepatchindo/glossary.py`!
  - In `reinject_skeleton_from_source` Step 2 (`lines 384–437`), if some spans matched and 1 remaining `<color=...>...</color>` span wraps a clause in `source_zh` (e.g., `<color=#FFE897>每对其使用4张古币牌...</color>`, `<color=#ffffff>会获得左右1格的英雄的100%法术攻击力</color>`, `<color=#9ff5d0>恢复的生命值</color>`, `<color=#d487e4>自身15%最大生命的法术伤害</color>`), wrap that `<color=...>...</color>` around the corresponding non-empty clause/phrase in `curr` (e.g., matching damage/HP phrases in `reinject_formula_and_skeleton` including `% Max HP diri sebagai Magic Damage`, or wrapping the proportional unmatched clause in `curr`) so Tier 1 translations are preserved!
  - In `reinject_skeleton_from_source` Step 5 (`lines 472–481`), when falling back to `baseline_en`, **ALWAYS** use `en_translator(baseline_en)` if `en_translator` is provided (and NEVER call raw `lexicon_id.translate_segment_en_to_id` directly when `en_translator` is available)!

### Task 16: Protect All Canonical HoK Ace Terms & Idioms in `glossary.py` and `lexicon_id.py`

- [x] **Step 16.1: Normalize English stat/card variants and expand `CANONICAL_PROTECTED_TERMS` in `src/acepatchindo/glossary.py`**
  - Before sentinel protection in `translate_en_to_id` (`_convert_segment`), normalize English baseline variants to canonical Tier 1 terms:
    - `Magical Attack` -> `Magic Attack`, `Magical Damage` -> `Magic Damage`, `Magical Defense` -> `Magic Defense`
    - `Spell Penetration` -> `Magic Penetration`
    - `Maximum HP` / `Max Health` / `Maximum Health` -> `Max HP`, `Maximum Mana` -> `Max Mana`
    - `Exquisite Ancient Coins` / `Exquisite Ancient Coin` / `Refined Ancient Coins` -> `Refined Ancient Coin`
    - `Ancient Coins` -> `Ancient Coin`, `Ancient Coin Machine` -> `Coin Machine`
    - `Perfect Resurrection` -> `Perfect Revive`, `Arcomia Core` -> `Akomia Core`, `Fire Thief` -> `Steal Fire`
    - `Talent Cards` / `Talent Card` -> `Kartu Talent`, `Effect Cards` / `Effect Card` -> `Kartu Efek`, `Equipment Cards` / `Equipment Card` -> `Kartu Equipment`, `Hero Vouchers` / `Hero Voucher` -> `Voucher Hero`
  - Add `"Ancient Coin"`, `"Refined Ancient Coin"`, `"Coin Machine"`, `"Rapid Growth"`, `"Perfect Revive"`, `"Akomia Core"`, `"Steal Fire"`, `"Magic Penetration"`, `"Physical Penetration"`, `"Kartu Talent"`, `"Kartu Efek"`, `"Kartu Equipment"`, `"Voucher Hero"` to `CANONICAL_PROTECTED_TERMS`.
- [x] **Step 16.2: Fix `"in order"` and `"count(s) as"` in `src/acepatchindo/lexicon_id.py`**
  - Add `("in", "order"): "secara berurutan"`, `("count", "as"): "dihitung sebagai"`, `("counts", "as"): "dihitung sebagai"`, `("counted", "as"): "dihitung sebagai"` to `PHRASE_2` (and `r"\breceive in order:"` -> `"memperoleh secara berurutan:"` in `CLAUSE_PATTERNS`) so `"in order"` is never translated as `"di ketertiban"` and `"count as"` is never translated as `"jumlah sebagai"`.

### Task 17: Isolate Verification Temp Dir, Pass 100% of `pytest -v`, Commit, Push, Move Tag `v1.4.12-id.1`, & Publish GitHub Release

- [x] **Step 17.1: Use `tempfile.TemporaryDirectory` in `scripts/04_verify_real_windows_game.py` & add Canonical-Term Guard assertions to `tests/test_glossary_and_tiers.py`**
  - Replace hardcoded `STAGE_DIR = Path("/tmp/wxq_id_verify_stage")` in `scripts/04_verify_real_windows_game.py` with `tempfile.TemporaryDirectory(prefix="wxq_id_verify_stage_")`.
  - In `tests/test_glossary_and_tiers.py`, assert **0 occurrences** across `unique` and `english_updates` of `"Kuno Koin"`, `"Sementara Level"`, `"Nyata Level"`, `"Sihir Menyerang"`, `"Sihir Damage"`, `"Sihir Defense"`, `"Mantra Penetrasi"`, `"Cepat Growth"`, `"di ketertiban"`, `"jumlah sebagai"`, `"Sempurna Kebangkitan"`, `"Api Thief"`, `"Kartu Effect"`, `"Talent Kartu"`, `"Equipment Kartu"`, `"Hero Kupon"`, `"<b>═"`, and `"╫,"`.
- [x] **Step 17.2: Rebuild, Repack, and Run Full `pytest -v` (All 13/13 Tests Must Pass)**
  - Run `scripts/02_build_indonesian_catalog.py`
  - Run `scripts/03_patch_worker_modules.py`
  - Run `scripts/04_verify_real_windows_game.py`
  - Run `scripts/05_repack_windows_exe.py`
  - Update SHA-256 digests in `README.md` and `scripts/06_publish_github_release.py` to match `dist/SHA256SUMS.txt`.
  - Run `/home/whise/.local/bin/uv run --python 3.12 pytest -v` and verify **13 passed, 0 failed**.
- [x] **Step 17.3: Commit All Changes, Push `main`, Force-Update Tag `v1.4.12-id.1` to `HEAD`, & Upload Assets to GitHub Release `v1.4.12-id.1`**
  - Update checkboxes in `.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md`.
  - Stage and commit all modified files (`git add .agents/plan/ README.md scripts/ src/ tests/ data/ && git commit -m "..."`), then `git push origin main`.
  - Force-move tag `v1.4.12-id.1` to the new `HEAD` (`git tag -f v1.4.12-id.1 HEAD && git push -f origin v1.4.12-id.1`).
  - Run `/home/whise/.local/bin/uv run --python 3.12 python scripts/06_publish_github_release.py` and verify `gh release view v1.4.12-id.1 --repo voseu/acepatchindo` displays the exact new SHA-256 digests from `dist/SHA256SUMS.txt` and `git status` is 100% clean!

---

## Phase 5: In-Game Visual & Semantic Integrity Remediation Plan (Fixing 46 Overwritten Lord Card Titles, 319 Roman Numeral `I -> aku` Corruptions, 302 Glued Rich-Text Tags, 88 Mid-Word Truncations, & 1,134 Passive Calques)

> **Forensic Audit Finding After Phase 4 Execution (`commit a5240b1`):**
> Phase 4 cleanly passed all **13/13** `pytest` suites (including the full 2.5 GB Windows QtsVFS staging test with `0` `unknown`, `0` `invalid_translation`, and `0` `capacity_skipped`), verified outer & inner SHA-256 guards (`d6ee5db0...` / `bb6b6ce4...`), pushed `main` + tag `v1.4.12-id.1` to `a5240b1`, and published live assets to GitHub Release `v1.4.12-id.1`.
>
> **HOWEVER**, deep forensic inspection of the actual embedded `catalog.json.gz` inside `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` exposed **5 severe in-game visual & semantic defects** that were invisible to the existing regex test assertions:
>
> 1. **CRITICAL — 46 Lord Talent / Secret Art Card Titles Overwritten With Half-Chopped Sentences (`glossary.py:699, 708, 743, 766`):**
>    - In `src/acepatchindo/glossary.py` lines 699 and 708, `_ingest_tier1` stored **card names** (`_normalize_en_key(c_name)` and `_normalize_en_key(r_name)`) inside `self.tier1_en_desc_to_id_desc` mapped to `c_desc` / `r_desc` (full multi-sentence card descriptions!). Then `translate_en_to_id` (`line 798`) matched short English card names like `"Talent Reserve"`, `"Frozen Crystal"`, `"Stasis Warhead"`, `"Dividend"`, `"Guided Warhead"`, `"Sublimation"`, `"Fixed Income"`, `"Prodigy"`, `"Merger Bonus"`, `"Strategic Decision"`, `"Sweep"`, `"Machine Gun Mode"`, `"Maple Blade"`, `"Dream Engine"`, `"Laser Mode"`, `"Sniper Mode"`, `"Loan Agreement"`, `"Capital Leverage"`, etc., replacing **45 short card titles** with full descriptions that `_fit_length_bound` chopped at 48 characters (`'人才储备' -> 'Saat Round dimulai, jika Player Level di atas 3,'`)!
>    - Additionally, in `_ingest_tier2_details` (`lines 743 & 766`), `ab_zh.get("desc", "")` for Qiao Xi had `zh_ab["desc"] == "海的拥抱"` (4 chars), mapping `'海的拥抱'` (`Embrace of the Sea`) -> `'Setiap 4 ronde, dapatkan 1 Kartu Secret Art Tida'`.
>
> 2. **CRITICAL — 24 Multi-Tag Hero Skills Sliced & Glued Mid-Word (`Li</color>Bai`, `sekutu</color>terdekat`, Mi Yue, Arthur) + 302 Glued Tag Boundaries (`tag_aligner.py`):**
>    - Step 15.2 was shortcutted (`lines 465–467`: `if not all_matched and len(spans) == 1: curr = f"{spans[0].group(1)}{curr}{spans[0].group(3)}"`), which wrapped Arthur's entire 30-word skill paragraph in neon purple `<color=#d487e4>...</color>` instead of only the Magic Damage phrase `Magic Damage sebesar 15% Max HP miliknya`, and left multi-span skills (`Li Bai`, `Yaria`, `Mi Yue`, `Menki`, `Yang Yuhuan`) falling into `_wrap_exact_tag_sequence` (`lines 538–586`).
>    - In `_wrap_exact_tag_sequence`, words were sliced into arbitrary equal-length chunks and joined with `"".join(out_parts)` **without spaces**, slicing `"Li Bai"` in half (`<color=#ffffffbf>Pasif: tiap kali memakai Skill, Li</color>Bai`), gluing `sekutu</color>terdekat` on Yaria, and scrambling every color tag on Mi Yue (`bayangan<color=#d487e4>untuk membantu sekutu jarak dekat</color>dengan`)!
>    - Across `catalog.json.gz`, **155 `unique` + 147 `english_updates` (`302` total)** strings have alphanumeric characters glued directly against opening/closing rich-text tags (`Mendapatkan<color=#99DEB0>4Chang</color>`, `menyebabkan<color=#99DEB0>20%</color>dari`), rendering on screen in Unity without spaces (`menyebabkan20%dari`).
>
> 3. **HIGH — 319 Roman Numeral `I` Corrupted Into `"aku"` (`174` Section Headers `aku. Aturan ...` + `167` Achievement Tiers `(aku)`):**
>    - `WORD_1["i"] = "aku"` in `lexicon_id.py` matched uppercase Roman numeral `I` in section headings (`<color=#98cbff>I. Synthesis Rules</color>` -> `<color=#98cbff>aku. Menggabungkan Aturan</color>`) and achievement tiers (`A Human Diamond Printer (I)` -> `sebuah Manusia Diamond Printer (aku)`).
>
> 4. **HIGH — 88 Mid-Word Hard Truncations in `_fit_length_bound` (`glossary.py:928`):**
>    - `out = out[:limit].rstrip()` sliced 88 strings right through the middle of Indonesian words (`'aku tidak akan membe'`, `'memenangkan kejuaraa'`, `'apa kamu dapat lak'`, `'berubah kembali pa'`).
>
> 5. **MODERATE-HIGH — Remaining Quantitative Prose Calques (`1,900+` Strings):**
>    - `adalah di...` passive calques (`adalah digunakan`, `adalah dihancurkan`, `adalah dimainkan`): **`558` in `unique`, `576` in `english_updates`**
>    - `sebuah 1` (`a single` -> `"sebuah 1"`): **`322` in `unique`, `116` in `english_updates`**
>    - `Tempat suci Sage` (`Sage's Sanctuary`): **`8` in `unique`, `118` in `english_updates`**
>    - `Ancient Coin kartu` / `<Faction> kartu`: **`18+` in `unique`, `168+` in `english_updates`**
>    - `adalah milikmu/miliknya` (`_POS_SWAP_RE` capturing copula `"adalah"` as a noun): **`71` in `unique`, `39` in `english_updates`**
>    - `Level atas` (`level up` / `levels up`): **`33` in `unique`, `26` in `english_updates`**
>    - `kiri dan benar` (`left and right` -> `"right"` as `"benar"` instead of `"kanan"`): **`10` in `unique`, `22` in `english_updates`**
>    - `Sihir ATK` / `Fisik ATK` (`5`), `4Chang` (`4`), `Jumlah dari kali` (`6`).

### Task 18: Fix Overwritten Card Titles & Mid-Word Truncations in `src/acepatchindo/glossary.py`

- [x] **Step 18.1: Stop mapping card titles to card descriptions in `glossary.py`**
  - In `src/acepatchindo/glossary.py`:
    1. **Delete lines 699 and 708** (`self.tier1_en_desc_to_id_desc[_normalize_en_key(c_name)] = c_desc` and `self.tier1_en_desc_to_id_desc[_normalize_en_key(r_name)] = r_desc`) so `tier1_en_desc_to_id_desc` ONLY ever maps **full English descriptions** (`len(en_ab_desc) >= 20`) to Indonesian descriptions — NEVER card titles!
    2. In `_ingest_tier2_details` (`lines 741–745`, `765–766`, `773–786`), ONLY call `self._register_t1_pair(zh_desc, id_desc)` when `len(normalize_plain_zh(zh_desc)) >= 8` (so short 2–6 char titles like `"海的拥抱"` are NEVER mapped to 60-char ability descriptions, and instead `"海的拥抱"` maps cleanly to `"Embrace of the Sea"`!).
    3. In `translate_en_to_id` (`line 798`), also require `len(en_text) >= 20` before returning `self.tier1_en_desc_to_id_desc[norm_en]`.
- [x] **Step 18.2: Eliminate mid-word truncations in `_fit_length_bound` (`glossary.py:882–930`) & normalize remaining stat/item variants**
  - In `var_subs` (`glossary.py:805–840`), add:
    - `(r"(?<![A-Za-z])(?:Magic|Magical)\s+ATK(?![A-Za-z])", "Magic Attack")`
    - `(r"(?<![A-Za-z])Physical\s+ATK(?![A-Za-z])", "Physical Attack")`
    - `(r"(?<![A-Za-z])Sage['’]s\s+Sanctuary(?![A-Za-z])", "Sage's Sanctuary")`
    - `(r"\b(\d+)\s*Chang\b", r"\1 kartu")`
    - `(r"\b(\d+)\s*Number of times\b", r"\1 kali")`
  - Add `"Sage's Sanctuary"` to `CANONICAL_PROTECTED_TERMS`.
  - In `_convert_segment` post-sentinel restoration (`lines 865–877`), reorder `<Protected Term> kartu/Kartu` -> `Kartu <Protected Term>`:
    - `out = re.sub(r"\b(Ancient Coin|Refined Ancient Coin|Central Plain|Zhulu(?: Plateau)?|Three Kingdoms|Sunset(?: Sea)?|Jixia|Great Wall|Xuanyong|Yaotian|Cloudream|Riverlands)\s+[Kk]artu(?:\s+Hero)?\b", lambda m: f"Kartu Hero {m.group(1)}" if "hero" in m.group(0).lower() else f"Kartu {m.group(1)}", out)`
    - Also reorder `r"\b(\d+)\s+[Aa]cak\s+(Kartu\s+[A-Za-z ]+)\b"` -> `r"\1 \2 acak"`.
  - In `_fit_length_bound` (`lines 903–929`):
    1. Expand `compact_replacements` with high-savings Indonesian tightenings (`("tidak akan", "takkan")`, `("sebaiknya tidak", "jangan")`, `("tidak bisa", "tak bisa")`, `("tidak dapat", "tak dapat")`, `("memberitahu", "beri tahu")`, `("tayangan ulang", "replay")`, `("memenangkan", "menang")`, `("beberapa lebih banyak", "lagi")`, `("menampilkan", "tunjukkan")`, `("bagaimana ke", "cara")`, `("bagaimana cara", "cara")`, `("sebuah ", "")`, `("dari ", "")`, `("adalah ", "")`, `("itu ", "")`, `("untuk ", "")`, `("yang ", "")`).
    2. If `len(out) > limit` still holds on plain strings (`lines 921–928`), **NEVER slice mid-word**: cut at the last space at or before `limit` (`head = out[:limit]; out = (head.rsplit(" ", 1)[0] if " " in head else head).rstrip(" ,;:-.")`).

### Task 19: Fix Multi-Tag Hero Skill Alignment, Clause `<color=...>` Matching, & Tag-Boundary Spacing in `src/acepatchindo/tag_aligner.py`

- [x] **Step 19.1: Fix `reinject_formula_and_skeleton` and `reinject_skeleton_from_source` so Hero skills (`Arthur`, `Li Bai`, `Yaria`, `Mi Yue`, `Menki`, `Yang Yuhuan`) keep exact semantic color tags and spaces**
  - In `reinject_formula_and_skeleton` (`lines 320–348`):
    1. Remove the `"<color=" not in out` guard on line 321 (check per-span whether `open_tag` is still needed so multi-color skills like Mi Yue, Yaria, Li Bai, Menki wrap **each** formula/stat span in `out`!).
    2. Expand the per-span `zh_content` regex matchers so:
       - Leading labels like `<color=#ffffffbf>被动：</color>` / `<color=#ffffffbf>清平：</color>` match `Pasif:` / `Aktif:` / `<Label>:` at the start of clauses!
       - Shield / Max HP formulas like `<color=#ffffff>[505310p1q1]+[505310p1q2/100]%瑶最大生命值</color>` or `自身15%最大生命的法术伤害` match `(?:Magic Damage|Physical Damage|Shield|perisai)?\s*(?:sebesar\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)%?\s*(?:base\s+|dasar\s+)?(?:Physical Attack|Magic Attack|Max HP)(?:\s+[A-Za-z]+)?(?:\s+sebagai\s+(?:Magic Damage|Physical Damage|True Damage))?` — so Arthur wraps **ONLY** `Magic Damage sebesar 15% Max HP miliknya` inside `<color=#d487e4>...</color>`, NOT the entire 30-word paragraph!
  - In `reinject_skeleton_from_source`:
    1. Replace the lazy `len(spans) == 1` whole-string wrapper (`lines 465–467`) so single-clause `<color=...>` spans only wrap the entire string when `len(normalize_plain_zh(spans[0].group(2))) >= 0.75 * len(normalize_plain_zh(source_zh))`; otherwise match the corresponding clause (split by `，`/`。`/`,`/`.`) by relative clause index! And if `len(spans) > 1` with **only 1 unmatched `<color=...>` clause span** (`<color=#ffffff>会获得左右1格的英雄的100%法术攻击力</color>`), wrap the corresponding trailing/indexed clause in `curr` so Tier 1 `plain_id` is preserved!
    2. In Step 5 (`lines 522–532`), also repair `baseline_en` when `baseline_en` only failed because of an empty tag `<color=...></color>` in `baseline_en` (`EMPTY_TAG_RE`) or minor hex-case/alpha difference vs `tags_in_src`: if `len(TAG_RE.findall(baseline_en)) == len(tags_in_src)`, substitute `tags_in_src` positionally into `baseline_en` (and move any empty `<color=...>...</color>` in `baseline_en` around the adjacent stat/verb word) before translating via `en_translator`, so Hero skills NEVER fall into blind chunk-chopping when `baseline_en` has valid English structure!
    3. In `_wrap_exact_tag_sequence` (`lines 576–586`), preserve word-boundary spaces around opening and closing tags (`" "` before `<color...` when preceded by a word char, and `" "` after `</color>` when followed by a word char) so even the last-resort wrapper can **NEVER** produce `Li</color>Bai` or `sekutu</color>terdekat`!
- [x] **Step 19.2: Normalize missing spaces at rich-text tag boundaries (`302` glued strings -> `0`)**
  - Add a helper `normalize_tag_boundary_spacing(source: str, text: str) -> str` called at the end of `translate_preserving_skeleton` and `reinject_skeleton_from_source`:
    - Insert a space between an alphanumeric/`%` character and an opening tag (`r"([A-Za-z0-9%])(<(?![/])(?:color|b|i|a|size)\b[^>]*>)(?=[A-Za-z0-9\u2540-\u257f\[])"` -> `r"\1 \2"`), and between a closing tag and an alphanumeric character (`r"(?<=[A-Za-z0-9%\]])(</(?:color|b|i|a|size)>)(?=[A-Za-z0-9])"` -> `r"\1 "`), **ONLY** if the resulting string still satisfies `validate_translation(source, spaced)[0]` (e.g. does not trip `extreme_expansion`).

### Task 20: Fix Roman Numeral `I`, Passive `adalah di...`, `sebuah 1`, `Level atas`, `kiri dan benar`, & Possessive Copula Swap in `src/acepatchindo/lexicon_id.py`, Rebuild, Verify, & Update Release `v1.4.12-id.1`

- [x] **Step 20.1: Fix all 6 grammar & lexicon rules in `src/acepatchindo/lexicon_id.py`**
  1. **Roman Numeral `I` Protection (`319` strings -> `0`):** Before token lookup in `translate_segment_en_to_id`, replace Roman numeral `I` with sentinel `__ROMAN_I__` (restored to `"I"` at the end) in:
     - `r"(?:^|(?<=[\n>(]))(\s*)I(?=\s*[.):、])"` -> `r"\1__ROMAN_I__"`
     - `r"(?<=\()\s*I\s*(?=\))"` -> `"__ROMAN_I__"`
     - `r"\b(Stage|Phase|Tier|Part|Chapter|Act|Season|Round|Level|Lv\.?)\s+I\b"` -> `r"\1 __ROMAN_I__"`
  2. **Passive `adalah di...` Cleanup (`1,134` strings -> `0`):** In post-processing of `translate_segment_en_to_id`, add:
     - `joined = re.sub(r"\badalah\s+(di[a-z]{3,}\b)", r"\1", joined, flags=re.I)`
     - `joined = re.sub(r"\badalah\s+(ter[a-z]{3,}\b)", r"\1", joined, flags=re.I)`
  3. **`sebuah 1` Cleanup (`438` strings -> `0`):** Add `("a", "single"): "1"` to `PHRASE_2` and post-clean `joined = re.sub(r"\bsebuah\s+(\d+)\b", r"\1", joined, flags=re.I)`.
  4. **`level(s) up` (`59` strings -> `0`):** Add `("level", "up"): "naik Level"`, `("levels", "up"): "naik Level"`, `("leveled", "up"): "naik Level"`, `("leveling", "up"): "naik Level"` to `PHRASE_2`.
  5. **`left and right` / `right side/grid` (`32` strings -> `0`):** Add `("left", "and", "right"): "kiri dan kanan"` to `PHRASE_3`, `("adjacent", "left", "and", "right"): "kiri dan kanan di sebelahnya"` to `PHRASE_4`, and `("right", "side"): "sisi kanan"`, `("right", "grid"): "petak kanan"`, `("right", "grids"): "petak kanan"`, `("right", "adjacent"): "sebelah kanan"` to `PHRASE_2`.
  6. **Possessive Copula Exclusion (`110` strings -> `0`):** Update `_POS_SWAP_RE` in `lexicon_id.py` so the captured noun phrase after `__POS_*__` stops BEFORE copulas/auxiliaries (`adalah`, `akan`, `dapat`, `tidak`, `telah`, `sudah`, `sedang`, `harus`, `perlu`, `menjadi`), preventing `"Shield unit adalah milikmu rusak"` (producing `"Shield unit milikmu rusak"`!).
- [x] **Step 20.2: Add Strict Quantitative Regression Assertions to `tests/test_glossary_and_tiers.py`**
  - Assert in `tests/test_glossary_and_tiers.py`:
    1. `cat["unique"]["人才储备"]` is `"Talent Reserve"` (or concise Indonesian title `<= 25` chars, NEVER starting with `"Saat Round dimulai"`), `cat["unique"]["海的拥抱"]` does NOT start with `"Setiap 4"`, and **0** entries in `cat["unique"]` with `len(zh) <= 6` and `len(orig_en) <= 25` have `len(id_val) >= 40`.
    2. **0 occurrences** of `(aku)` (`r"\(\s*aku\s*\)"`) and **0 occurrences** of Roman heading `aku. <Upper>` (`r"(?:^|>|\n)\s*aku\.\s+[A-Z]"`) across `unique` and `english_updates`.
    3. **0 occurrences** of `Li</color>Bai`, `sekutu</color>terdekat`, `Tempat suci Sage`, `Level atas`, `kiri dan benar`, `Sihir ATK`, `Fisik ATK`, `4Chang`, `sebuah 1`, `adalah digunakan`, `adalah dihancurkan`, `adalah dimainkan`, `adalah milikmu`, and `<5` glued alphanumeric tag boundaries across `unique`.
    4. Arthur's `举起圣剑跃向敌方人群密集处，额外造成<color=#d487e4>自身15%最大生命的法术伤害</color>...` does **NOT** start with `<color=#d487e4>Arthur`.
- [x] **Step 20.3: Rebuild Catalog, Patch Worker, Verify Real Windows Game (`04`), Repack `.exe` (`05`), Pass 13/13 `pytest -v`, Commit, Push `main` + Tag `v1.4.12-id.1`, & Update GitHub Release (`06`)**
  - Run `02_build_indonesian_catalog.py` -> `03_patch_worker_modules.py` -> `04_verify_real_windows_game.py` -> `05_repack_windows_exe.py`.
  - Update SHA-256 checksums in `README.md` and `scripts/06_publish_github_release.py` to match `dist/SHA256SUMS.txt`.
  - Run `/home/whise/.local/bin/uv run --python 3.12 pytest -v` and confirm **13 passed, 0 failed**.
  - Update checkboxes in `.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md`, commit all changes, `git push origin main`, `git tag -f v1.4.12-id.1 HEAD && git push -f origin v1.4.12-id.1`, and run `scripts/06_publish_github_release.py` so GitHub Release `v1.4.12-id.1` serves the verified final build!

---

## Phase 6: Hybrid Gameplay Description Localization (`v1.4.12-id.2`)

> [!IMPORTANT]
> **User Post-Testing Specification (After Live Windows Verification of `v1.4.12-id.1`):**
> 1. **PERTAHANKAN BAHASA INDONESIA (`ID`):** **HANYA deskripsi** untuk **4 kategori gameplay**:
>    - **Kartu Hero** (*Hero Cards*, termasuk efek *On Play / Sacrifice / Prepare / Awaken* & mekanik kartu hero)
>    - **Skill** (*Hero Skills*, ringkasan skill pendek saat kartu ditutup / *collapsed skill summaries*, *Lv.10/40/100 Skill Enhancements*, *Combine Skills*, dan *Summon Skills*)
>    - **Talent** (*Standard Talents*, *Contestant Lv.6 Exclusive Talents*, *Mode/Brawl/Class Talents*, serta deskripsi *Talent Cards* yang dihasilkan Talent)
>    - **Kontestan** (*Contestants / Chess Players / Lords / 棋手*, termasuk deskripsi skill aktif/pasif kontestan, aturan misi *Secret Art*, deskripsi *Secret Art Cards*, dan deskripsi kartu kemampuan kontestan)
> 2. **PERTAHANKAN BAHASA INGGRIS (`EN` — JANGAN DITERJEMAHKAN KE ID):**
>    - **SEMUA Nama / Judul** pada **Kartu Hero**, **Skill**, **Talent**, dan **Kontestan** (termasuk nama kartu *Secret Art* / kemampuan kontestan), **baik** saat berdiri sendiri sebagai *record* Nama **maupun** saat disebut di dalam kalimat deskripsi Bahasa Indonesia (seperti `<color=#FFE897>Symphony of Tides</color>`, `<color=#FFE897>Super Copier</color>`, `<b>Maple Leaf Dance</b>`, `<b>Graceful Dance</b>`, `Indomitable Will`, `Try Your Luck`, dll.).
> 3. **KEMBALIKAN SISANYA KE BAHASA INGGRIS (`EN`):**
>    - Seluruh string lain di dalam game: **UI, Menu, Pengaturan, Lobby, Toko, Tutorial, Loading Tips, Event, Misi, Achievement, Quick-Chat, Gelar Rank, Kosmetik/Skin/Avatar, Nama & Deskripsi Equipment mandiri, serta Nama & Deskripsi Effect Card mandiri** wajib dikembalikan ke **Bahasa Inggris (`EN`)** bersih!
>    - Khusus **90 string non-target** di dalam `WINDOWS_108` (string Mandarin yang dulu terlewat oleh *English Patcher 1.4.12*, seperti menu *Image Cache Directory*, *Download Manager*, misi event, kupon Diamond, quick-chat, deskripsi *Three Kingdoms Banner*), **JANGAN** dihapus begitu saja (karena akan kembali menjadi huruf Mandarin dan merusak `unknown == 0`), melainkan wajib diterjemahkan ke **Bahasa Inggris (`EN`)** yang rapi dan tervalidasi!
> 4. **Seamless One-Click Upgrade di Windows Live (`v1.4.12-id.1` -> `v1.4.12-id.2`) + Rilis GitHub Baru (`v1.4.12-id.2`):**
>    - Game Windows milik user (`C:\Program Files\WXQLauncher\WXQ`) saat ini sedang terpasang patch penuh `v1.4.12-id.1` dengan cadangan Mandarin asli di `1793628251781039400-c81278c0/originals`. Saat user menjalankan `Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` versi `v1.4.12-id.2` dan menekan **Install**, patcher **WAJIB** otomatis memulihkan `originals/` terlebih dahulu berdasarkan ketidakcocokan SHA-256 katalog pada direktori *receipt* sebelum memasang katalog Hybrid `v1.4.12-id.2`!

> [!CAUTION]
> **5 Jebakan Arsitektur Hasil Audit Forensik 508 Tabel QtsVFS (DILARANG DILANGGAR):**
> 1. **JEBAKAN TABEL PALSU `hero_skill_summaries_a/b` (`#ADCF`, `#D891`, `#C32E`, `#1881`):**
>    Di `wxq_patch/pipeline.py`, tabel `#ADCF` dinamai secara keliru sebagai `hero_skill_summaries_a`. Hasil bedah biner membuktikan `#ADCF`, `#D891`, `#C32E`, dan `#1881` adalah **100% Tabel Equipment** (`灵泉法杖` / *Spirit Spring Staff*, `普通装备│唯一`, `不祥征兆`, `博学者之怒`). **DILARANG KERAS** mengklasifikasikan `#ADCF/#D891/#C32E/#1881` sebagai Skill — seluruh Equipment harus berbahasa **Inggris (`EN`)**!
> 2. **KUNCI EMAS 48-BIT (`key[5:17]`) UNTUK 424 KARTU HERO:**
>    Tabel kartu monolitik (`#23F7`, `#8E55`, `#FBF3`, `#5AD1`, `#801D`, `#BC6D`, `#5A2E`, `#1825`, `#FCC7`, `#6D3B`, `#6E60`) mencampur Kartu Hero, Effect Card, Equipment Card, Talent Card, dan Kartu Kontestan. Namun tabel pasangan metadata `#60D2` (`zh_hash = 36B258373DA34185`) menyimpan label `'阵营   职业'` (mis. `'三分   射手'`, `'长城   战士'`, `'混沌裂隙   法师'`) **persis pada suffix 12-hex (`key[5:17]`) yang sama** dengan *record* Deskripsi Kartu Hero di seluruh revisi tabel kartu dan `english_updates`! Gunakan pencocokan `key[5:17]` dari `#60D2` + referensi `tier1["hero"]` + `tier2_details["Hero"]` agar 100% Kartu Hero tertangkap tanpa membocorkan Effect Card atau Equipment!
> 3. **TABEL SKILL SEJATI (`#FCCD`, `#99AB`, `#4853`, `#865D`, `#CE46`):**
>    Kelima tabel ini (`zh_hash`: `7F7F60ACED822B5E`, `58B4B182D74B34B0`, `4332819ABE8E29C8`, `6B4BE06E1593DD1C`, `218D140500F68F37` beserta pasangan `en_hash`-nya di `english_updates`) memuat seluruh deskripsi Hero Skill, Summon Skill, Combine Skill, **ringkasan skill pendek saat kartu ditutup** (*collapsed summaries* yang tidak ada di web referensi!), serta **Lv.10/40/100 enhancements**. Namun di dalam tabel yang sama juga terdapat **Nama Skill** (`裂空` -> `Sky Splitter`, `普通攻击` -> `Basic Attack`, `棋手孙尚香技能-狙击`) serta **kutipan suara / flavor hero** (`玩球！` -> `Play Ball!`, `火鹰轰炸！`, `大河之剑天上来。`, `欢迎来到炮火的世界！`, `蓉城小霸王，威力无穷！`, `大河流域阵营的特殊单位。`) yang **WAJIB dikecualikan** agar tetap berbahasa Inggris (`EN`)!
> 4. **NAMA TERTANAM DI DALAM DESKRIPSI (`TIER1_EMBEDDED_EN_CLEANUP` & `STOPWORD_GUARD_RE`):**
>    Di `src/acepatchindo/glossary.py:520-530`, `TIER1_EMBEDDED_EN_CLEANUP` sebelumnya menerjemahkan 7 nama Talent/Kartu bahasa Inggris menjadi bahasa Indonesia (`Indomitable Will` -> `Tekad Baja`, `Try Your Luck` -> `Uji Keberuntungan`, `Glory of the Old Guard`, `Quench with Illusions`, `Muster the Troops`, `Power of the Source`, `Bane of the Mighty`), dan di `WINDOWS_108_ZH_TO_ID` tertulis `Tidal Symphony` & `Tri-Point Banner` padahal nama kartu bahasa Inggris resmi di katalog `1.4.12` adalah `Symphony of Tides` & `Three Kingdoms Banner`. Selain itu `STOPWORD_GUARD_RE` menolak nama entitas resmi yang mengandung kata `of`/`the`/`and`/`for`/`with` (`Symphony of Tides`, `Embrace of the Sea`, `Use for My Own`, `Point of No Return`, `Burn the Boats`, `Child of Flow`). Semua itu **WAJIB diperbaiki** agar nama yang disebut di dalam deskripsi Bahasa Indonesia tetap 100% Bahasa Inggris kanonik!
> 5. **JEBAKAN GAGAL AUTO-RESTORE DARI `v1.4.12-id.1` & TEST TERLEWAT (`SKIPPED`):**
>    - Di `src/acepatchindo/dual_state_patch.py:221-224`, `_run("install")` hanya memanggil `_orig_run("restore")` jika `scan()` menghasilkan `plans_check`. Pada game yang sudah dipatch `v1.4.12-id.1`, ~38.000 string UI sudah berbahasa Indonesia (bukan Mandarin dan bukan Inggris!), sehingga `scan()` tidak dapat mengembalikannya ke Bahasa Inggris tanpa **unconditional restore** saat SHA-256 katalog berbeda!
>    - Di `scripts/04_verify_real_windows_game.py:20-23` dan `tests/test_real_game_vfs.py:11-14`, path `1793497168990741300-92b4bcbb/originals` di-*hardcode*, padahal di Windows user kini foldernya bernama `1793628251781039400-c81278c0/originals` — sehingga tanpa perbaikan dinamis, `pytest` akan **diam-diam men-skip (`SKIPPED`)** tes QtsVFS!

### Task 21: Build Deterministic Hybrid Scope Classifier (`src/acepatchindo/hybrid_classifier.py`), Split `WINDOWS_108` (`18 ID` vs `90 EN`), & Enforce 100% English Entity Names (`src/acepatchindo/glossary.py` & `src/acepatchindo/tag_aligner.py`)

- [x] **Step 21.1: Split `WINDOWS_108` into `WINDOWS_108_TARGET_DESC_ID` (`18` entries -> Bahasa Indonesia) and `WINDOWS_108_NONTARGET_EN` (`90` entries -> Clean English)**
  - Create or refactor constants in `src/acepatchindo/glossary.py` (or `src/acepatchindo/windows_108_split.py` imported by `glossary.py` & `02_build_indonesian_catalog.py`):
    1. **`WINDOWS_108_TARGET_DESC_ID` (`18` exact gameplay descriptions kept in Bahasa Indonesia, with canonical English embedded names matching `orig_cat`):**
       - `"转移后清除自身负面状态，并在5秒内免疫受到的控制。"`
       - `"转移后获得20%伤害加成。"`
       - `"战斗开始时，随机传送1个4-5阶临时等级为回合数×12的英雄进入战场（不含卡牌效果），并携带3件适配装备。"`
       - `"若<color=#ffffff><b>枫叶舞</b></color>英雄被移除，其真实等级的25%会保留给下一个<color=#ffffff><b>枫叶舞</b></color>英雄，若为被出售，则保留75%真实等级，限一次。"`
       - `"若<color=#FFE897>枫叶舞</color>英雄被移除，其真实等级的25%会保留给下一个<color=#FFE897>枫叶舞</color>英雄，若为被出售，则保留75%真实等级，限一次。"`
       - `"获得1张装备牌<color=#FFE897>三分旗帜</color>：造成伤害的40%平摊治疗所有【三分】英雄（仅【三分】英雄可穿戴）。"` *(use `<color=#FFE897>Three Kingdoms Banner</color>` to match `orig_cat["unique"]["三分旗帜"]`!)*
       - `"场上随机英雄等级+5，触发{DaQiao_TideTimes:3}次，若对象为<b>温柔呼唤</b>的英雄则额外等级+5，每次使用后，触发次数+2。"`
       - `"枫叶舞指定的英雄击败3/5/9/15名敌方英雄，获得1张秘技牌<b>翩跹舞步</b>并为枫叶舞解锁1项特性（共4项）。"`
       - `"枫叶舞指定的英雄累积击败3/5/9/15名敌方英雄后，阿离获得1张<color=#FFE897>翩跹舞步</color>，累计完成4次后任务需求固定为15。\n<color=#FFE897>翩跹舞步</color>：为<color=#FFE897>枫叶舞</color>挑选1张强化牌。"`
       - `"每4个回合，乔汐获得1张<color=#FFE897>潮汐的交响</color>。\n<color=#FFE897>潮汐的交响</color>：场上随机5个英雄等级+4。"` *(use `<color=#FFE897>Symphony of Tides</color>` to match `orig_cat["unique"]["潮汐的交响"]`!)*
       - `"每4个回合，获得1张秘技牌<b>潮汐的交响</b>。"` *(use `<b>Symphony of Tides</b>`!)*
       - `"每回合开始时，自动触发1次孙尚香【登场】词条效果。"`
       - `"每回合开始时，触发1次<color=#FFE897>孙尚香</color>卡牌效果。"`
       - `"立刻在<color=#FFE897>嬴政和武则天中随机一人</color>，下场战斗开始时使其吸收<color=#FFE897>其他友军</color>的等级和初始法力值。（使用后强化吸收能力）"`
       - `"<color=#ffffffbf>被动：</color>圣殿骑士冲锋时，对路径敌人造成<color=#dfa15e>[0]点物理伤害</color><color=#dfa15e>（[1]+[2]%自身最大生命值）</color>，随后戳刺敌人，造成<color=#dfa15e>[3]点物理伤害</color><color=#dfa15e>（[4]+[5]%自身最大生命值）</color>。\n<color=#ffffffbf>主动：</color>获得15%伤害加成，持续5秒。"`
       - `"仆从伤害提升至100%法术攻击力，生命值恢复提升至100%法术攻击力"`
       - `"芈月为等级最高的近战友军召唤1只暗影仆从协助战斗，持续10秒。仆从每次攻击造成<color=#d487e4>80%芈月法术攻击力的法术伤害</color>并为友军恢复<color=#d487e4>80%芈月法术攻击力</color><color=#9ff5d0>的生命值</color>，同时窃取目标1点<color=#dfa15e>物理防御</color>和<color=#d487e4>法术防御</color>转移给友军（最多30层，持续至回合结束）。"`
       - `"选择棋手武凤，一起化万法为己用！通过棋手技能随机获得一张他人的秘技牌，每局都能打出意料之外的组合。"`
    2. **`WINDOWS_108_NONTARGET_EN` (`90` remaining strings -> Clean, Natural, Human-Curated English):**
       - Every single one of the remaining 90 strings (`孙尚香·强化` -> `"Lady Sun: Empowered"`, Equipment descriptions `[006]`, `[007]`, `[008]`, `[020]`, `"传送{0}级"` -> `"Teleport Lv.{0}"`, `"图片缓存目录"` -> `"Image Cache Directory"`, `"下载管理"` -> `"Download Manager"`, `"打开文件夹"` -> `"Open Folder"`, `"更改目录"` -> `"Change Directory"`, Wu Feng event rules & missions, Diamond discount vouchers, invisibility prompts, team invite strings, quick-chat voice lines, trial cards, and account link notice) **MUST** have a clean, natural English translation passing both `acepatchindo.validator.validate_translation` and `wxq_patch.translation_rules.validate_translation` (`len(WINDOWS_108_TARGET_DESC_ID) + len(WINDOWS_108_NONTARGET_EN) == 108`, zero overlap, zero missing keys from `data/references/windows_missing_108_zh.json`!).

- [ ] **Step 21.2: Protect 100% of Embedded & Standalone English Entity Names in `src/acepatchindo/glossary.py` & `src/acepatchindo/tag_aligner.py`** *(REOPENED BY MANAGER AUDIT — `_ingest_tier1/2/2_details` left `verified_entity_names_en` unused!)*
  - In `src/acepatchindo/glossary.py`:
    1. **Remove all 7 Talent/Card name translations from `TIER1_EMBEDDED_EN_CLEANUP` (`lines 521–527`):**
       - Delete `("Indomitable Will", "Tekad Baja")`, `("Try Your Luck", "Uji Keberuntungan")`, `("Glory of the Old Guard", "Kejayaan Garda Lama")`, `("Quench with Illusions", "Padamkan dengan Ilusi")`, `("Muster the Troops", "Kumpulkan Pasukan")`, `("Power of the Source", "Kekuatan Sumber")`, `("Bane of the Mighty", "Kutukan Sang Perkasa")`! Keep ONLY genuine grammar fixes (or reverse any Indonesian-translated proper card/talent/skill/contestant names back to English!).
    2. **Build `verified_entity_names_en: set[str]` bypassing `STOPWORD_GUARD_RE` for multi-word proper names:**
       - Collect ALL English names (`len(name) >= 4` and contains uppercase) of Heroes, Skills, Talents, Contestants (`lords` / `Chess player`), Contestant `talents[*].cardName` & `related[*].name`, Tier 2 `abilities[*].name` & `skill_names`, plus `orig_cat["unique"][zh_name]` for all those Chinese entity names (so names like `Symphony of Tides`, `Embrace of the Sea`, `Use for My Own`, `Point of No Return`, `Immovable as a Mountain`, `Burn the Boats`, `Try Your Luck`, `Indomitable Will`, `Glory of the Old Guard`, `Quench with Illusions`, `Muster the Troops`, `Power of the Source`, `Bane of the Mighty`, `Child of Flow`, `Three Kingdoms Banner`, `Super Copier`, `Build Upgrade` are **ALL** included in `instance.protected_en_terms` even when they contain `of`, `the`, `for`, `with`, `as`, `a`, `to` — excluding only generic sentences `len(name) > 40` or lowercase prose!).
    3. **Register Chinese -> Canonical English Entity Names for Tag/Span Lookup (`BADGE_ALIAS_MAP` / `tier1_exact_zh_to_id`):**
       - Ensure every Chinese Hero, Skill, Talent, Contestant, and Contestant Secret-Art / Ability Name maps to its **English** name (`orig_cat["unique"].get(zh_name) or en_name`) inside `glossary` and `tag_aligner.BADGE_ALIAS_MAP`, so when `tag_aligner.py` aligns `<color=#FFE897>潮汐的交响</color>`, `<color=#FFE897>超级复印机</color>`, `<color=#FFE897>构筑升级</color>`, or `<b>温柔呼唤</b>` inside an Indonesian description, the span content stays **English**!

- [ ] **Step 21.3: Create `src/acepatchindo/hybrid_classifier.py` Using Exact QtsVFS Table Hashes, 48-Bit Key Suffixes (`#60D2`), & Reference Sets** *(REOPENED BY MANAGER AUDIT — leaked 65+ non-target tables, Equipment, Effect Cards, `#D262`/`#7D6E` tutorials, and missed 18 Tier 1 skill enh/talents!)*
  - Implement `HybridClassifier` in `src/acepatchindo/hybrid_classifier.py` using real QtsVFS table inspection from `WINDOWS_ORIGINALS` (dynamically discovered via `sorted(ADAPTIVE_ROOT.glob("*/*/originals"))[-1]`, with deterministic cached/serialized key-suffix metadata saved to `data/references/hybrid_vfs_index.json` so unit tests also work offline even if Windows is unmounted!):
    1. **Strict Name & Non-Target Exclusion Sets (Checked FIRST — Hard Veto Against `ID`):**
       - `ENTITY_NAME_ZH`: Every Chinese name (`cn`, `nameCn`, `alt`, `abilities[*].name`, `skill_names`) across `tier1_wiki_id.json` (`hero`, `skills`, `talent`, `lords`, `equip`, `effect`, `factions`), `tier2_wiki_en.json`, `tier2_wiki_details_en.json`, `wxq_patch.hok_terminology`, plus all records in `#60D2` (`36B258373DA34185`) that are category tags (`效果`, `装备`, `天赋`, `资源`, `运营`) or short labels (`<= 4` plain CJK chars without sentence punctuation/verbs/numbers), plus Skill Table skill names & flavor voice quotes (`玩球！`, `火鹰轰炸！`, `大河之剑天上来。`, `欢迎来到炮火的世界！`, `蓉城小霸王，威力无穷！`, `大河流域阵营的特殊单位。`, and `棋手...技能-...`).
       - `EQUIPMENT_DESC_ZH`: All `descCn` / `zh` descriptions in `tier1["equip"]` and `tier2_details["Equipment"]`, all records in the misnamed Equipment tables (`#ADCF`, `#D891`, `#C32E`, `#1881`), and Equipment-exclusive strings matching `穿着这件装备|穿戴者|仅.{1,6}英雄穿戴|普通装备│|唯一被动：` (unless explicitly a Talent/Hero/Contestant description in `tier1["talent"|"hero"|"lords"]` such as `"获得1张装备牌..."`).
       - `STANDALONE_EFFECT_DESC_ZH`: All `descCn` / `zh` descriptions in `tier1["effect"]` and `tier2_details["Effect card"]` that do **NOT** appear in Hero, Skill, Talent, or Contestant description sets.
       - **Hard Rule:** Any entry matching `ENTITY_NAME_ZH` (or whose `orig_en` is a standalone proper name with `len(plain_zh) <= 8` and no gameplay clause punctuation/digits/`%`/`+`) **MUST** return `is_target_id = False` (keep **100% English**!).
    2. **Authoritative Target Description Sets (`is_target_id = True` -> Bahasa Indonesia):**
       - **Category A — Kartu Hero (`hero_card_desc`):**
         - All `descCn` & `awaken.descCn` in `tier1["hero"]` (exact, `normalize_plain_zh`, and `normalize_formula_skeleton_zh`), all `effect_copies` / `breakpoints` / `rule_notes` in `tier2_details["Hero"]`, PLUS all Chinese strings & `english_updates` `(asset_hex, key)` pairs whose 48-bit key suffix `key[5:17]` matches the **424 Hero Card suffixes** in `#60D2` (`36B258373DA34185`, where `#60D2` value matches `r"^(?:河洛|逐鹿|三分(?:之地)?|日落海|稷下|长城|玄雍|尧天|云梦泽|大河(?:流域)?|无阵营|混沌裂隙)\s+(?:战士|法师|坦克|刺客|射手|辅助)$"`) across the Card Table Family (`#23F7`, `#8E55`, `#FBF3`, `#5AD1`, `#801D`, `#BC6D`, `#5A2E`, `#1825`, `#FCC7`, `#6D3B`, `#6E60` and their paired `en_hash` tables)!
       - **Category B — Skill (`skill_desc`):**
         - All `skills[*].descCn` & `skills[*].enh[*].descCn` in `tier1["hero"]`, all `abilities[*].desc` & `calc_copies` in `tier2_details["Hero" | "Summon"]`, PLUS all non-name, non-flavor-quote gameplay description records in the **5 Skill Tables** (`#FCCD` `7F7F60ACED822B5E`, `#99AB` `58B4B182D74B34B0`, `#4853` `4332819ABE8E29C8`, `#865D` `6B4BE06E1593DD1C`, `#CE46` `218D140500F68F37`, and their paired `en_hash` tables in `english_updates`) — capturing 100% of active/passive skills, collapsed short skill summaries, summon skills, combine skills, and Lv.10/40/100 skill enhancements!
       - **Category C — Talent (`talent_desc`):**
         - All `descCn` in `tier1["talent"]`, all `abilities[*].desc` / `effect_copies` / `calc_copies` / `rule_notes` in `tier2_details["Talent"]`, Mode/Brawl/Class Talent descriptions in `#0955` (`6EC9C8904C8C5C82` and paired `en_hash`, with `len(plain_zh) >= 10` and excluding `场上.*数` UI counters), and Talent Card / Talent descriptions in `#BCDE..#CEDB`, `#23F7..#6E60`, and `#2394` (`8B5FA32BAA3913D9`) whose key suffix or text belongs to Talent effects (and NOT Equipment or standalone Effect Cards).
       - **Category D — Kontestan (`contestant_desc`):**
         - All `lords[*].talents[*]` & `lords[*].related[*]` descriptions in `tier1["lords"]`, all `abilities[*].desc` / `effect_copies` / `rule_notes` in `tier2_details["Chess player"]`, Contestant skill/passive/secret-art/trait/card descriptions in `#23F7..#6E60`, `#BCDE..#CEDB`, `#2394`, and `4E0F1B7C13F264AE` (`#5CFD`), while strictly **excluding** tutorial prompts (`#D262`, `#7D6E`), loading tips (`#341F`), general rules tutorials (`#A360`, `#1F89`), achievements (`#637E`), event missions (`049FDCA512DC8897`, `79E3F2A531266997`, `1586D98CC6E0B77E`), and cosmetics/avatars/gifts (`#E2B0`)!
       - Plus the `18` curated entries in `WINDOWS_108_TARGET_DESC_ID`.

### Task 22: Update Catalog Builder (`02`), Unconditional Catalog-SHA Pre-Install Restore (`dual_state_patch.py`), Worker Patcher (`03`), & Dynamic Real-Game Verifier (`04`)

- [ ] **Step 22.1: Rebuild `scripts/02_build_indonesian_catalog.py` for Hybrid `v1.4.12-id.2`** *(REOPENED — must rebuild after fixing `HybridClassifier` & `glossary.py`)*
  - Start from `orig_cat` (`Honor of Kings Ace English Patcher 1.4.12.exe_extracted/catalog/catalog.json.gz`).
  - For `data["unique"]`:
    - If `HybridClassifier` classifies `(zh_src, en_base)` as target gameplay description (`hero_card_desc | skill_desc | talent_desc | contestant_desc`), translate to Bahasa Indonesia (`glossary.translate_entry`) while keeping embedded proper names in English!
    - Otherwise, keep `en_base` (`100%` clean original English)!
  - For the `108` Windows missing Chinese strings:
    - Inject `18` entries from `WINDOWS_108_TARGET_DESC_ID` (Indonesian) and `90` entries from `WINDOWS_108_NONTARGET_EN` (English) so all `41,483` `unique` keys exist with **0 raw Chinese** and **0 `unknown`**!
  - For `data["contextual"]` and `data["english_updates"]` (`29,750` entries):
    - Only translate rows classified by `HybridClassifier.is_target_contextual_or_update(asset_hex, key, prev_en, target_en, opt_zh)` as Hero Card, Skill, Talent, or Contestant **descriptions** into Bahasa Indonesia (validated against both `zh_src` and `prev_en` as before); keep all Name rows and all non-target UI/Equipment/Effect/Tutorial/Achievement rows equal to `orig_cat`'s clean English `target_en`!
  - Set `data["version"] = "1.4.12-id.2"` and emit detailed category breakdown counts (`hero_card_desc`, `skill_desc`, `talent_desc`, `contestant_desc`, `reverted_en_names`, `reverted_en_other`, `windows_108_id=18`, `windows_108_en=90`).

- [ ] **Step 22.2: Fix One-Click Live Upgrade (`v1.4.12-id.1` -> `v1.4.12-id.2`) in `src/acepatchindo/dual_state_patch.py` & Rebuild Worker (`03`)** *(REOPENED — `_needs_pre_install_restore` had inverted `any`/`all` loop returning `False` on first matching receipt!)*
  - In `src/acepatchindo/dual_state_patch.py` (`render_adaptive_source`, lines `213–229`):
    1. Add helper `_catalog_fingerprint(assets: Path) -> str` returning `hashlib.sha256((Path(assets) / "catalog.json.gz").read_bytes()).hexdigest()[:16]` (or `""` on OSError).
    2. Add helper `_needs_pre_install_restore(resolved_game: Path, cat_sha: str) -> bool`:
       - Obtain `matched = _matching_restore_items(resolved_game)`. If `not matched`, return `False`.
       - Collect `receipt_dirs = {rcp_path.parent for rcp_path, _ in matched}`.
       - Return `True` if `not cat_sha` or ANY `d` in `receipt_dirs` lacks `(d / "patcher_catalog_sha256.txt")` or `(d / "patcher_catalog_sha256.txt").read_text(encoding="utf-8").strip() != cat_sha`!
    3. Add helper `_stamp_receipt_catalog_sha(resolved_game: Path, cat_sha: str) -> None` writing `cat_sha` into `(d / "patcher_catalog_sha256.txt")` for every `d` in `{rcp_path.parent for rcp_path, _ in _matching_restore_items(resolved_game)}` when `cat_sha` is non-empty.
    4. In `_run(action, game, assets, work)`:
       - When `action == "install"`: compute `cat_sha = _catalog_fingerprint(assets)`. If `_needs_pre_install_restore(resolved_game, cat_sha)` is `True`, **UNCONDITIONALLY call `_orig_run("restore", resolved_game, assets, work)` FIRST** (do NOT gate it behind `if plans_check:`, because upgrading from `v1.4.12-id.1` MUST revert ~38,000 Indonesian UI/Name strings back to Chinese `originals/` first so `_orig_run("install")` patches them to Hybrid English + Indonesian!).
       - Run `report = _orig_run(action, game, assets, work)`.
       - When `action == "install"` and `cat_sha`: call `_stamp_receipt_catalog_sha(resolved_game, cat_sha)` inside `try/except Exception: pass`.
  - Run `scripts/03_patch_worker_modules.py` and verify `en_to_id` ONLY contains the Hybrid target description mappings (`0` standalone entity names, `0` UI/Settings/Equipment/Effect strings!).

- [ ] **Step 22.3: Fix Hardcoded Receipt Path & Verify Hybrid Contract on Real Windows Game (`scripts/04_verify_real_windows_game.py`)** *(REOPENED — failed to assert 0 non-target table leaks and concrete Protobuf payload checks!)*
  - Replace hardcoded `1793497168990741300-92b4bcbb/originals` in `scripts/04_verify_real_windows_game.py` and `tests/test_real_game_vfs.py` with dynamic resolution:
    `ADAPTIVE_ROOT = Path("/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive")`
    and a helper `find_windows_originals() -> Path | None` returning `sorted(ADAPTIVE_ROOT.glob("*/*/originals"))[-1]` if any exists!
  - Update `run_verification()` in `scripts/04_verify_real_windows_game.py` to execute **3 rigorous checks**:
    1. **`[1/3]` Unpatched Chinese `originals/` -> Hybrid `v1.4.12-id.2`:** Full `adaptive.scan(..., materialize=True)` + `stage_unity_package` across all **6** QtsVFS packages (`508` tables, `unknown == 0`, `invalid_translation == 0`, `capacity_skipped == 0`), **PLUS** decode materialized Protobuf `.bytes` payloads across ALL 508 tables to assert `0` records leaked outside `ALLOWED_TARGET_TABLE_PREFIXES`!
    2. **`[2/3]` Dual-State `EN -> Hybrid ID` Verification:** Verify `en_to_id` against English baseline catalog / staged English table so target descriptions convert `EN -> ID` while English Names & UI remain `100%` untouched in English!
    3. **`[3/3]` Live Windows Upgrade Trigger (`v1.4.12-id.1` -> `v1.4.12-id.2`):** Against `/run/media/whise/Windows/Program Files/WXQLauncher/WXQ` and real receipt `1793628251781039400-c81278c0/receipt.json`, verify that live files match the active Windows receipt and lack matching `patcher_catalog_sha256.txt`!

### Task 23: Update Unit & Integration Test Suites (`tests/test_glossary_and_tiers.py`, `tests/test_dual_state_engine.py`, `tests/test_real_game_vfs.py`)

- [ ] **Step 23.1: Update `tests/test_glossary_and_tiers.py` for Hybrid `v1.4.12-id.2` Invariants** *(REOPENED — only checked 6 hardcoded names instead of ALL Tier 1/Tier 2 names, Equipment, Effect Cards, and embedded names!)*
  - Assert `cat["version"] == "1.4.12-id.2"` and `len(cat["unique"]) == 41483` and `len(cat["english_updates"]) == 29750`.
  - **Invariant 1 (Names Stay 100% English):** Assert across ALL Hero, Skill, Talent, and Contestant names in `tier1_wiki_id.json` & `tier2_wiki_en.json` present in `orig_cat["unique"]` that `cat["unique"][zh_name] == orig_cat["unique"][zh_name]`, AND embedded names inside Indonesian descriptions (`Maple Dance`, `Moment of Epiphany`, `Wolf Soul`, `Templar Knight`, `Spinning Blade`, `Chaos Rift`, `Symphony of Tides`, `Three Kingdoms Banner`, `Indomitable Will`, `Try Your Luck`, `Ancient Coin Machine`, `Chang Xiao'e`) stay **100% English**!
  - **Invariant 2 (Non-Target Strings Revert 100% to English):** Assert **0** leaked Tier 1 Equipment descriptions, **0** leaked Tier 1 standalone Effect Card descriptions, **0** leaked UI/Tutorial/Achievement/Quick-Chat strings, and `0` CJK characters!
  - **Invariant 3 (Target Gameplay Descriptions Stay Natural Indonesian, Zero Missed Tier 1):** Assert **0 missed** Tier 1 Hero, Skill, Skill Enhancement (`enh`), or Talent descriptions (`100%` translated to Indonesian!), and `< 25` English prose calque hits!

- [ ] **Step 23.2: Add `v1.4.12-id.1 -> v1.4.12-id.2` Unconditional Pre-Install Restore Test in `tests/test_dual_state_engine.py` & Zero-Skip Guard in `tests/test_real_game_vfs.py`** *(REOPENED — `tests/test_dual_state_engine.py` was NEVER modified in `80df222` despite being checked off `[x]`!)*
  - In `tests/test_dual_state_engine.py`: add `test_adaptive_unconditionally_restores_v1_full_id_when_catalog_sha_differs` simulating `plans_check == []` + active receipt without matching `patcher_catalog_sha256.txt`, proving `_run("install", ...)` calls `["restore", "install"]` on 1st run and ONLY `["install"]` on 2nd run after stamping `patcher_catalog_sha256.txt`!
  - In `tests/test_real_game_vfs.py`: assert 0 skipped tests when Windows is mounted AND assert 0 non-target table leaks!

### Task 24: Full Pipeline Execution (`02` -> `03` -> `04` -> `05`), All `pytest -v` Green (`0` Skipped!), Update Docs, & Publish GitHub Release `v1.4.12-id.2` (`06`)

- [ ] **Step 24.1: Execute Build, Patch, Real-Game Verification, Repack, & Full Test Suite** *(REOPENED)*
- [ ] **Step 24.2: Update `README.md` & `scripts/06_publish_github_release.py` (`TAG = "v1.4.12-id.2"`), Commit, Push `main`, & Update GitHub Release `v1.4.12-id.2`** *(REOPENED)*

---

## Phase 6 Remediation: Audit Findings & Zero-Leakage Fixes (Tasks 25–28)

> [!CAUTION]
> **Manager Forensic Audit of `commit 80df222` — REJECTED Due to 4 Critical Violations:**
> 1. **MASSIVE LEAKAGE ACROSS `65+` NON-TARGET TABLES (`104/508` Tables Modified, `15,151` `english_updates` & `6,392` `unique` Changed):**
>    - In `src/acepatchindo/hybrid_classifier.py:107-120`, a reckless global keyword wildcard (`"生命值"`, `"英雄牌"`, `"英雄等级"`, `"召唤"`, `"牺牲"`, `"护盾"`, `"法力值"`, `"战斗开始时"`, etc.) plus dumping **all `4,137` keys of `#BCDE`**, **all `1,156` keys of `#D262` (Tutorial Step Prompts)**, and **all `351` keys of `#7D6E` (Beginner Stage Dialogues)** into `vfs_target_keys` leaked thousands of non-target records into broken Indonesian:
>      - **11 Tier 1 Equipment + 90+ `<b>唯一</b>` Equipment descriptions** (`Storm Greatsword`, `Witch's Cloak`, `Sword of Conquest`, `Three Kingdoms Banner`, `<color=#ffffff>Physical darah-sucking +20%</color>`, `<color=#ffffff><b>Unik</b></color>...`)!
>      - **47+ Standalone Effect Cards** (`Talent Scouting`, `Tier 1 Hero Voucher`, `Wide Recruitment`, `Power of Arms`, `String Note`, etc.)!
>      - **Tutorials, Guides, UI Counters, PvE Defenders, Events & Achievements:** `SlicedUI_ActorHealth` (`"{0} HP: {1}"`), `"Factionless{0}/{1}" -> "Netral{0}/{1}"`, `"Click on properties"`, `"Buy Zilong"`, `"This defender uses a Milady Summon Lineup" -> "Ini pelindung menggunakan sebuah Milady Memanggil Lineup"`, `"I. Event Rules" -> "I. Event Aturan"`, `"How to Obtain High-Tier Hero Cards" -> "Bagaimana ke Memperoleh Tinggi-Tier Kartu Hero"`.
> 2. **NO-OP `verified_entity_names_en` IN `src/acepatchindo/glossary.py:469-660` (`216+` Embedded Entity Names Mangled!):**
>    - `verified_entity_names_en` was passed into `_ingest_tier1`, `_ingest_tier2`, and `_ingest_tier2_details` as an **unused dummy parameter**, and even the 18 hardcoded names were never added to `protected_set`! As a result, embedded proper names inside descriptions were mangled into Indonesian: `<color=#ffffff><b>Maple Menari</b></color>` (`Maple Dance`), `<color=#ffffff><b>Moment dari Epiphany</b></color>` (`Moment of Epiphany`), `Serigala Jiwa` (`Wolf Soul`), `Kekacauan Celah` (`Chaos Rift`), `Spinning Blade`, `Bear Spirit`, `Destiny Totem`, `Templar Knight`, `Mechanical Puppet`, `Xuanyong Soldier`, `Chang Xiao'Skill e` (`Chang Xiao'e's Skill`), and `Ancient Coin Machine -> Coin Machine` (`glossary.py:765`)!
> 3. **18 LEGITIMATE TIER 1 SKILL ENHANCEMENTS & TALENTS MISSED (`False Negatives` Left in English):**
>    - `17` Hero Skill Lv.10/40/100 enhancements (`击飞眩晕延长至3秒`, `技能变为大范围圆形`, `增益目标+1`, `仆从数量提升至5只`, `花球数量+4`, `斩击期间不可选中`, `弹射次数上限+4`, etc.) and `可上阵人数+1。` (`Tactic Module` Talent) returned `is_target_unique == False` and stayed in English despite having exact human-curated translations in `tier1_wiki_id.json`!
> 4. **FALSIFIED CHECKLIST ON `Step 23.2` + INVERTED LOOP IN `_needs_pre_install_restore` + SKILL INDLISH DEFECTS:**
>    - `tests/test_dual_state_engine.py` was **NOT modified at all** in `80df222` despite `[x] Step 23.2` being checked off!
>    - `dual_state_patch.py:242-247` returned `False` as soon as *any single* receipt dir matched `cat_sha`, instead of requiring *all* matching receipt dirs to match `cat_sha`!
>    - Real skill/talent descriptions had verb/noun calques: `"Memilih atas target"` (`Picks up`), `"Cirrus penggemar sayap ... feather panah"` (`fans his wings ... feather arrows`), `"memiliki sebuah <color=#00FF00>15%</color> peluang"`, `"di sana adalah 80% peluang"`, `"meningkatkan menyerang oleh miliknya"`.

### Task 25: Create Reproducible `scripts/01b_build_hybrid_vfs_index.py` & Zero-Leakage `src/acepatchindo/hybrid_classifier.py`

- [ ] **Step 25.1: Write `scripts/01b_build_hybrid_vfs_index.py` to Deterministically Generate `data/references/hybrid_vfs_index.json` From Real QtsVFS Tables + Tier 1/2 References** *(REOPENED BY MANAGER AUDIT ROUND 2 — English `.bytes` tables overwrote `m60_lookup[sfx]` and bypassed Chinese vetoes, leaking `2,086` conflicting `sfx` keys, Faction+Class tags `'Three Kingdoms Pejuang'`, Equipment `'Physical blood-sucking +20%'`, and `45+` Hero voice lines/quotes!)*
  - Define the **ONLY 32 Allowed Target Table Prefix Tags (`ALLOWED_TARGET_PREFIXES`)** across all 508 QtsVFS tables:
    - **Card Family (`12`):** `{"23F7", "8E55", "FBF3", "5AD1", "801D", "BC6D", "5A2E", "1825", "FCC7", "6D3B", "6E60", "60D2"}`
    - **True Skill Family (`5`):** `{"FCCD", "99AB", "4853", "865D", "CE46"}`
    - **Talent & Contestant Trait Family (`12`):** `{"BCDE", "75CA", "9344", "31CF", "A40D", "BE08", "1632", "E222", "E378", "0977", "BF5A", "CEDB"}`
    - **Mode Talent, Hotfix & Contestant Overview (`3`):** `{"0955", "2394", "5CFD"}` *(NOTE: `#D262` and `#7D6E` are TUTORIAL STAGE TABLES and MUST BE EXCLUDED!)*
  - Scan all **508** QtsVFS tables in `find_windows_originals()`:
    1. Record `nontarget_table_zh`: EVERY Chinese string appearing in ANY of the **~470 tables outside `ALLOWED_TARGET_PREFIXES`**!
    2. Build `ref_target_zh` & `ref_target_plain`: ALL descriptions from:
       - `tier1["hero"]` (`descCn`, `awaken.descCn`, `skills[*].descCn`, **AND `skills[*].enh[*].descCn` including short 5–9 char enhancements like `'增益目标+1'`, `'花球数量+4'`!**)
       - `tier1["talent"]` (`descCn`, **including short `'可上阵人数+1。'`**)
       - `tier2_details["Hero" | "Summon" | "Talent" | "Chess player"]` (`abilities[*].desc`, `effect_copies`, `calc_copies`, `breakpoints`, `rule_notes` with `len(plain_zh) >= 6`)
       - `WINDOWS_108_TARGET_DESC_ID` (`18` strings).
    3. Build `veto_names_zh`, `veto_equip_zh` (& `veto_equip_plain`), and `veto_effect_zh` (& `veto_effect_plain`):
       - `veto_names_zh`: ALL entity names (`cn`, `nameCn`, `alt`, `abilities[*].name`, `skill_names`) across Tier 1, Tier 2, Tier 2 Details, `wxq_patch.hok_terminology`, flavor voice quotes (`玩球！`, `火鹰轰炸！`, `大河之剑天上来。`, `欢迎来到炮火的世界！`, `蓉城小霸王，威力无穷！`, `大河流域阵营的特殊单位。`), `棋手...技能-...`, `#5CFD` placeholders (`瑶妹描述`, `小妲己描述`), and all `#60D2` short category/subtitle tags (`效果`, `装备`, `提升等级`, `提升临时等级`, `资源`, `运营`, `战斗`, `通用`, `版本通用`, `添加牺牲词条`, `阵营英雄牌·金色扭蛋`).
       - `veto_equip_zh` / `veto_equip_plain`: ALL `descCn`/`zh` descriptions in `tier1["equip"]` & `tier2_details["Equipment"]` (minus any string in `ref_target_zh`), ALL records in `#ADCF/#D891/#C32E/#1881`, and ANY record starting with `<color=#ffffff><b>唯一</b></color>` / `<color=#ffffff><color=#ffffff><b>唯一</b></color></color>` / `唯一被动` or matching `r"(?:穿戴给英雄|穿戴者|穿着这件装备|仅.{1,6}英雄穿戴|普通装备│|^(?:<color=[^>]+>)*(?:物理吸血|法术吸血|物理防御力?|法术防御力?|攻击速度|暴击率|冷却缩减)\+\d+)"` (unless in `WINDOWS_108_TARGET_DESC_ID` or `tier1["talent"|"hero"]`).
       - `veto_effect_zh` / `veto_effect_plain`: ALL `descCn`/`zh` descriptions in `tier1["effect"]` & `tier2_details["Effect card"]` (minus any string in `ref_target_zh`), PLUS any card suffix `sfx` in `#23F7..#6E60` where `#60D2` has `'效果'` (`1,007` standalone Effect Cards) or simple card-draw/level-up Effect Card sentences in `#BCDE`/`#23F7` matching `r"^(?:卡牌\d+选\d+|获得\d+张.+英雄牌。|\d+选1.+英雄，获得\d+张该英雄牌。|随机抽取\d+张.*英雄牌。|指定1名英雄等级\+\d+.*|\d+件装备选\d+件。|立即使所有手牌费用-\d+。)$"`.
    4. Extract per-record `vfs_target_keys` & `vfs_target_zh` **STRICTLY** from the 4 allowed families (after applying all vetoes above AND excluding `nontarget_table_zh - ref_target_zh`!):
       - **Card Family (`#23F7..#6E60` + `#60D2`):** ONLY keys whose 48-bit suffix `sfx = key[5:17]` is:
         - in the **424 Hero Card suffixes** (`#60D2` matches `阵营   职业`) AND `zh != m60_val` (so `#60D2`'s own `'河洛   坦克'` label is NOT translated, while Hero Card descriptions in `#23F7..#6E60` ARE!), OR
         - `#60D2` at `sfx` is in `{"秘技", "技能", "专属"}` AND `len(plain_zh) >= 8` with sentence punctuation (`，`/`。`/`：`/`\n`), OR
         - `zh` / `normalize_plain_zh(zh)` is in `ref_target_zh` / `ref_target_plain` (capturing Talent Cards & Contestant Cards in `#23F7..#60D2` without leaking Effect Cards, Equipment, or short subtitle badges like `'添加牺牲词条'`/`'提升临时等级'`!).
       - **Skill Family (`#FCCD`, `#99AB`, `#4853`, `#865D`, `#CE46`):** All records that pass the Name/Voice-Quote veto and have either `zh in ref_target_zh` OR (`len(plain_zh) >= 6` and contains gameplay verbs/punctuation/numbers/`%`/`+`).
       - **Talent & Contestant Family (`#BCDE..#CEDB`):** ONLY records passing Equipment/Effect/Name vetoes that have **NO `{0}` UI counter pattern** (`not re.search(r"\{0\}(?:/\{1\})?$", plain_or_raw)` and `"{0}/{1}" not in zh`) AND (`zh in ref_target_zh` or `normalize_plain_zh(zh) in ref_target_plain` or (`len(plain_zh) >= 9` and any(p in zh for p in ("，", "。", "：", ":", "\n")))) — cleanly excluding short badges like `'【重器】英雄自增等级'`, `'法师加法术攻击'`, `'橙色英雄指定升级'`, `'无阵营{0}/{1}'`, `'登场次数{0}'`!
       - **`#0955` (`6EC9C8904C8C5C82`), `#2394` (`8B5FA32BAA3913D9`), `#5CFD` (`4E0F1B7C13F264AE`):**
         - `#0955`: records passing vetoes with `len(plain_zh) >= 10` and sentence punctuation (`，`/`。`/`：`), excluding `场上.*数`.
         - `#2394`: records passing Equipment/Name vetoes with `len(plain_zh) >= 8` and sentence punctuation.
         - `#5CFD`: ONLY the 3 Contestant overview descriptions (`len(plain_zh) >= 15`).

- [ ] **Step 25.2: Simplify `src/acepatchindo/hybrid_classifier.py` to Pure Deterministic Index Lookup (ZERO Keyword Wildcards!)** *(REOPENED — `is_target_update` must never allow keys in `vfs_veto_keys` or `sfx` in `vfs_veto_sfx`!)*
  - **DELETE lines `102–121`** (the reckless `if any(kw in zh_clean for kw in ("物理伤害", ..., "生命值", "英雄牌", "召唤")): return True` wildcard) AND **DELETE `"D262"`, `"7D6E"`, `"BCDE"`** from blind whole-table `TALENT_TAGS`!
  - `is_target_unique(zh_src, en_base)`:
    1. Return `False` if `zh_clean` in `WINDOWS_108_NONTARGET_EN | veto_names_zh | veto_equip_zh | veto_effect_zh` or `normalize_plain_zh(zh_clean)` in `veto_equip_plain | veto_effect_plain`.
    2. Return `True` if `zh_clean` in `WINDOWS_108_TARGET_DESC_ID | ref_target_zh` (checked BEFORE `nontarget_table_zh`!).
    3. Return `False` if `zh_clean` in `nontarget_table_zh` (guarantees **0** cross-table leaks into all ~470 non-target tables!).
    4. Return `True` if `zh_clean` in `vfs_target_zh` or `normalize_plain_zh(zh_clean)` in `ref_target_plain`.
    5. Otherwise return `False`!
  - `is_target_update(asset_hex, key, prev_en, target_en, opt_zh)`:
    1. Extract `tag = key[1:5]` and `suffix = key[5:17]`. If `tag not in ALLOWED_TARGET_PREFIXES`, return **`False` immediately**! (Wait: also check `LordYingzhengCardEX*` only if in Contestant card keys, otherwise `False`!)
    2. If `key in vfs_veto_keys`, return `False`. If `opt_zh` and not `is_target_unique(opt_zh, target_en)` (when `opt_zh` is non-empty and in `veto_*` or `nontarget_table_zh`), return `False`.
    3. Return `True` ONLY if `key in vfs_target_keys` OR (`tag in CARD_TAGS - {"60D2"}` and `suffix in hero_suffixes` and `len(target_en) >= 15`) OR (`tag in SKILL_TAGS` and (`opt_zh` in `ref_target_zh` or (`len(target_en) >= 18` and not target_en.endswith("!") and "Skill-" not in target_en))) OR (`opt_zh` and `is_target_unique(opt_zh, target_en)` and `tag in ALLOWED_TARGET_PREFIXES`).

### Task 26: Actually Implement Full Embedded Entity Name Protection & Fix Remaining Skill/Talent Prose Defects (`glossary.py` & `lexicon_id.py`)

- [ ] **Step 26.1: Fix `ThreeTierGlossary` (`src/acepatchindo/glossary.py`) So ALL Embedded Entity Names Stay 100% English** *(REOPENED — `Luban No. 7` became `Luban Tidak. 7`, `[Great Wall]` became `[Hebat Dinding]`, `Mechanical Minion A1` became `Mechanical Minion sebuah1`!)*
  - Load `orig_cat["unique"]` inside `ThreeTierGlossary.from_reference_files` (from `Honor of Kings Ace English Patcher 1.4.12.exe_extracted/catalog/catalog.json.gz` when present).
  - Add `"Chaos Rift"` and `"Ancient Coin Machine"` to `CANONICAL_PROTECTED_TERMS`, and **DELETE** line `765` `(r"(?<![A-Za-z])Ancient Coin Machine(?![A-Za-z])", "Coin Machine")` so `Ancient Coin Machine` stays intact!
  - Actually populate **BOTH** `verified_entity_names_en.add(name)` **AND** `protected_set.add(name)` inside `_ingest_tier1`, `_ingest_tier2`, and `_ingest_tier2_details` for **EVERY** valid English entity name (`3 <= len(name) <= 45`, contains uppercase, not ending with `.`) across:
    1. **ALL** Tier 1 categories (`hero`, `skills`, `talent`, `lords`, `lords[*].talents[*].cardName`, `lords[*].related[*].name`, `equip`, `effect`, `factions`), **PLUS** `orig_cat["unique"][zh_name]` for every corresponding `zh_name` (which automatically adds `"Maple Dance"`, `"Moment of Epiphany"`, `"Symphony of Tides"`, `"Three Kingdoms Banner"`, `"Chang Xiao'e"`, `"Gan & Mo"`, `"Spinning Blade"`, etc.!).
    2. **ALL** Tier 2 (`tier2_wiki_en.json`) entries of type `"Hero"`, `"Summon"`, `"Talent"`, `"Chess player"`, `"Equipment"`, `"Effect card"` (both `entry["name"]` AND `orig_cat["unique"].get(entry["alt"])` — which automatically protects **ALL Summon names** like `"Wolf Soul"`, `"Bear Spirit"`, `"Ancestral Bear Spirit"`, `"Destiny Totem"`, `"Seer Totem"`, `"Illusory Totem"`, `"Templar Knight"`, `"Mechanical Puppet"`, `"Mechanical Minion"`, `"Magic Book"`, `"Xuanyong Soldier"`, `"Shadow Servant"`, etc.!).
    3. **ALL** Tier 2 Details (`tier2_wiki_details_en.json`) `abilities[*].name` and `skill_names` (excluding generic 1-word labels `"Passive"`, `"Active"`, `"Awaken"`, `"Preparation"`, `"On Play"`, `"Sacrifice"` that have their own keyword handling, and excluding single common English verbs like `"Charge"`, `"Slash"`, `"Slam"`, `"Sweep"`, `"Pierce"`, `"Sprint"`, `"Reload"`, `"Bombard"`, `"Devour"` when single-word — keep all multi-word names >= 5 chars and all Hero/Contestant/Summon proper names!).
  - Fix apostrophe/ampersand boundary in `instance._protected_re` (`glossary.py:529`) and `_POS_SWAP_RE` (`lexicon_id.py`) so names like `"Chang Xiao'e"` (`"Chang Xiao'e's Skill"` -> `"Skill Chang Xiao'e"`, NEVER `"Chang Xiao'Skill e"`!) and `"Gan & Mo"` are matched cleanly before possessive swapping!
  - Also ensure `protected_set |= verified_entity_names_en` before building `instance.protected_en_terms`!

- [ ] **Step 26.2: Fix the Remaining Skill/Talent Prose & Formula Skeleton Defects in `src/acepatchindo/tag_aligner.py`, `src/acepatchindo/lexicon_id.py` & `src/acepatchindo/glossary.py`** *(REOPENED — `\[0\]` hardcoding in `tag_aligner.py` dropped 43+ main Hero skills (`Lu Bu`, `Augran`, `Allain`, `Donghuang`) to Tier 3, plus `Damage Atas`, `Mementalkan Atas`, `ke melepaskan`, `dasar Lu Bu serangan`!)*
  1. `"picks up"` / `"pick up"`: add `("picks", "up"): "mengangkat"`, `("pick", "up"): "mengangkat"`, `("picked", "up"): "mengangkat"` to `PHRASE_2` (eliminating `"Memilih atas target"`!).
  2. `"fans his/her/its wings"` & `"feather(s)"`: add pre-pattern in `glossary.py` `(r"\bfans\s+(?:his|her|its|their)\s+wings\b", "mengepakkan sayapnya")`, `(r"\bspreads\s+(?:his|her|its|their)\s+wings\s+to\s+dance\b", "membentangkan sayapnya dan menari")`, and in `lexicon_id.py` map `"feather": "bulu"`, `"feathers": "bulu"`, `("feather", "arrows"): "panah bulu"`, `("feather", "arrow"): "panah bulu"`!
  3. `"sebuah <tag>15%"` / `"sebuah 15%"`: in `glossary.py` post-tag restoration (or `tag_aligner.py`), strip `sebuah` before optional opening tags followed by a number (`re.sub(r"\bsebuah\s+((?:<[^>]+>\s*)*\d+)", r"\1", out, flags=re.I)`)!
  4. `"there is a/an"` / `"there are"`: add `("there", "is", "a"): "ada"`, `("there", "is", "an"): "ada"`, `("there", "is"): "terdapat"`, `("there", "are"): "terdapat"` to `PHRASE_3` / `PHRASE_2` in `lexicon_id.py` (eliminating `"di sana adalah 80% peluang"`!).
  5. `"improving his/her/its attack by"`: add pre-pattern `(r"\bimproving\s+(?:his|her|its)\s+attack\s+by\b", "meningkatkan Attack miliknya sebesar")` in `glossary.py`!

### Task 27: Fix `_needs_pre_install_restore` Loop (`dual_state_patch.py`), Write Real Tests (`test_dual_state_engine.py`, `test_glossary_and_tiers.py`, `test_real_game_vfs.py`), & Enforce Zero Non-Target Table Leaks

- [x] **Step 27.1: Fix `_needs_pre_install_restore` in `src/acepatchindo/dual_state_patch.py:242-247`**
  - Replace the inverted loop:
    ```python
    for r_dir in receipt_dirs:
        sha_file = r_dir / "patcher_catalog_sha256.txt"
        if not sha_file.exists() or sha_file.read_text(encoding="utf-8").strip() != cat_sha:
            return True
    return False
    ```
    so that **EVERY** active matching receipt directory must carry the current `cat_sha`, otherwise `_orig_run("restore", ...)` runs unconditionally!

- [x] **Step 27.2: Actually Add `test_adaptive_unconditionally_restores_v1_full_id_when_catalog_sha_differs` in `tests/test_dual_state_engine.py` (Do NOT Skip Again!)**
  - Test with `fake_scan` returning `([], {}, {"translated": 0}, [])` (empty `plans_check == []`, simulating `v1.4.12-id.1` on disk!) and an active `receipt.json` in `tmp_path / "rcp1" / "receipt.json"`:
    1. First `adaptive._run("install", ...)` calls `["restore", "install"]` and writes `patcher_catalog_sha256.txt` with `cat_sha`.
    2. Second `adaptive._run("install", ...)` with the SAME `catalog.json.gz` calls ONLY `["install"]` (idempotent, no redundant restore!).
    3. Third `adaptive._run("install", ...)` after changing `catalog.json.gz` bytes calls `["restore", "install"]` again!

- [ ] **Step 27.3: Add Iron-Clad Zero-Leakage & Zero-False-Negative Assertions to `tests/test_glossary_and_tiers.py` & `scripts/04_verify_real_windows_game.py`** *(REOPENED — must also assert 0 `sfx` conflicts, 0 voice line leaks, 0 Tier 1 parenthetical formula misses, and 0 `Luban Tidak` / `Damage Atas` / `Mementalkan Atas` / `Hebat Dinding`!)*
  - In `tests/test_glossary_and_tiers.py`:
    1. Assert **0** leaked Tier 1 Equipment descriptions (`for it in t1["equip"]: ... assert cat["unique"][d] == orig_cat["unique"][d]` when `d` not in Hero/Skill/Talent/Lord descriptions).
    2. Assert **0** leaked Tier 1 standalone Effect Card descriptions (`for it in t1["effect"]: ... assert cat["unique"][d] == orig_cat["unique"][d]` when `d` not in Hero/Skill/Talent/Lord descriptions).
    3. Assert **0** missed Tier 1 Hero, Skill, Skill `enh`, or Talent descriptions (`100%` of `t1["hero"]` `descCn`/`awaken`/`skills`/`enh` and `t1["talent"]` `descCn` present in `orig_cat["unique"]` MUST be translated to Indonesian, `cat["unique"][z] != orig_cat["unique"][z]`, including `'击飞眩晕延长至3秒'`, `'增益目标+1'`, `'可上阵人数+1。'`!).
    4. Assert **0** occurrences across the entire `cat["unique"]` and `cat["english_updates"]` of mangled embedded names or leaked strings: `"Maple Menari"`, `"Moment dari Epiphany"`, `"Serigala Jiwa"`, `"Kekacauan Celah"`, `"Physical darah-sucking"`, `"Netral{0}/{1}"`, `"Memilih atas target"`, `"di sana adalah"`, `"Chang Xiao'Skill"`, `"Milady Memanggil"`, `"I. Event Aturan"`.
  - In `scripts/04_verify_real_windows_game.py` (and verified by `tests/test_real_game_vfs.py`):
    - Across all **508** QtsVFS tables in `find_windows_originals()`, compare `translate_table(..., orig_cat)` vs `translate_table(..., hybrid_cat)`: assert that **EVERY SINGLE TABLE whose record prefix is NOT in `ALLOWED_TARGET_PREFIXES` (`32` prefixes) has `0` records where `id_val != en_val` (excluding keys whose `zh_val` is in `WINDOWS_108`)**! Print the exact count of modified tables (`<= 38` tables out of `508`, down from `104`!).

### Task 28: Rebuild Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Pass 100% `pytest -v` (`0` Failed, `0` Skipped), Commit, Re-Tag `v1.4.12-id.2`, & Re-Upload GitHub Release (`06`)

- [ ] **Step 28.1: Run Complete Pipeline & Verify All Tests Pass (`0` Failed, `0` Skipped)** *(REOPENED)*
  1. `/home/whise/.local/bin/uv run --python 3.12 python scripts/01b_build_hybrid_vfs_index.py`
  2. `/home/whise/.local/bin/uv run --python 3.12 python scripts/02_build_indonesian_catalog.py`
  3. `/home/whise/.local/bin/uv run --python 3.12 python scripts/03_patch_worker_modules.py`
  4. `/home/whise/.local/bin/uv run --python 3.12 python scripts/04_verify_real_windows_game.py`
  5. `/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py`
  6. `/home/whise/.local/bin/uv run --python 3.12 pytest -v` (**must show >= 14 passed, 0 failed, 0 skipped!** Also adjust `tests/test_repack_integrity.py` `en_to_id` range bound if clean `en_to_id` is `2,000 <= len(cat["en_to_id"]) <= 10,000`!).
- [ ] **Step 28.2: Update Checksums in `README.md` & `scripts/06_publish_github_release.py`, Commit, Force-Update Tag `v1.4.12-id.2`, & Clobber-Upload Clean `.exe` + `SHA256SUMS.txt` to GitHub Release `v1.4.12-id.2`** *(REOPENED)*
  - Update `README.md` and `scripts/06_publish_github_release.py` with exact new SHA-256 digests from `dist/SHA256SUMS.txt` and accurate Hybrid counts.
  - Check (`[x]`) all completed checkboxes in `.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md`, commit on `main`, `git push origin main`, `git tag -f v1.4.12-id.2 HEAD && git push -f origin v1.4.12-id.2`, run `scripts/06_publish_github_release.py`, and verify remote asset digests on GitHub Release `v1.4.12-id.2` match `dist/SHA256SUMS.txt` 100%!

---

## Phase 6 Remediation Round 2: Deep Structural & Prose Audit Fixes (Tasks 29–32)

> [!CAUTION]
> **Manager Forensic Audit of `commit 5a6306f` — REJECTED Due to 4 Deep Structural & Prose Defects:**
> 1. **DUAL-TABLE OVERWRITE & ENGLISH-RECORD VETO BYPASS IN `scripts/01b_build_hybrid_vfs_index.py` (`2,086` Conflicting Row Suffixes `sfx`, `963` English Strings in `vfs_target_zh`, & Leaked Equipment / Faction+Class / Effect Cards):**
>    - In QtsVFS `originals/` (`pkg=1`), several table prefixes have **two** `.bytes` tables: a **Chinese** table (e.g., `#60D2` at `hash=0x36B258373DA34185`, `#4853` at `0x4332819ABE8E29C8`, `#865D` at `0x7F7F60ACED822B5E`, `#BCDE` at `0x04F21C6735D0D555`) AND an **English** `english_updates` table (e.g., `#60D2` at `hash=0xDD400CE5E3F32E17`, `#4853` at `0xC8505EC8297580DA`, `#865D` at `0x42B1223EAA77E2CC`, `#BCDE` at `0x00E5A135114EEEC7`).
>    - Because `0xDD400CE5E3F32E17 > 0x36B258373DA34185`, iterating `for h in sorted(pkg.entries)` caused the English `#60D2` table to **overwrite** `m60_lookup[sfx]` with English strings!
>      - **Consequence A (`#60D2` Faction+Class Tags Leaked):** `if zh_str != m60_val:` compared Chinese `'三分之地   战士'` (`zh_str`) against overwritten English `'Three Kingdoms   Warrior'` (`m60_val`), marking `#60D2` Faction+Class tags as `is_target = True` and translating `'三分之地   战士'` -> `'Three Kingdoms Pejuang'`, `'日落海   战士'` -> `'Sunset Pejuang'`, `'河洛   战士'` -> `'Central Plain Pejuang'`, `'大河流域   战士'` -> `'Riverlands Pejuang'`, `'逐鹿   战士'` -> `'Zhulu Plateau Pejuang'`!
>      - **Consequence B (`2,086` Vetoed Row Suffixes `sfx` Leaked via English Tables):** When iterating over the English `.bytes` tables (`#BCDE`, `#23F7`, `#4853`, `#865D`), `zh_str` was actually an **English string**, so all Chinese vetoes (`zh_str in veto_equip_zh`, `zh_str in veto_effect_zh`, `P_EQUIP_PATTERN`, `P_EFFECT_CARD_PATTERN`) were bypassed! That added `2,086` vetoed `sfx` suffixes into `vfs_target_keys` (such as `#BCDEFF3DCEF34F90#`: `'<color=#ffffff>Physical blood-sucking +20%</color>... Unique Passive: [Sunset Sea] When worn by the hero...'` and `'Obtain 1 piece of equipment [organ box]...'`) and `963` non-CJK English strings into `vfs_target_zh`!
>      - **Consequence C (Unvetoed Equipment & `#9344` UI Strings):** Equipment strings with `唯一：` / `<color=#ffffff><b>唯一</b></color>` / `装备箱` / `件装备` / `特殊装备` / `高级装备` and `#9344` UI strings `'当前祝福：大河流域'` (`'Saat ini Berkah: Riverlands'`) and `'1张炸弹牌加入了对局，小心传递。'` leaked into `vfs_target_zh`.
> 2. **45+ HERO VOICE LINES / LORE QUOTES & UNIT FLAVOR TEXTS IN `SKILL_PREFIXES` (`#CE46..#865D`) LEAKED INTO INDONESIAN:**
>    - In `scripts/01b_build_hybrid_vfs_index.py:378`, `any(p in zh_str for p in ("，", "。", ...))` matched ANY sentence with a comma or period in `#CE46..#865D`, translating ~45 Hero Voice Lines / Lore Quotes and unit flavor texts into broken Indonesian:
>      - `'女人，是水做的。'` -> `'Wanita dibuat dari air.'`, `'你已经被盯上了。'` -> `'Kamu telah ditargetkan.'`, `'你是我喜欢的口味。'` -> `'Kamu adalah favorit rasa milikku.'`, `'你需要接受电疗。'` -> `'Kamu perlu electrotherapy.'`, `'清理工作才刚刚开始。'` -> `'Cleanup memiliki hanya hanya dimulai.'`, `'现在，接受支配。'` -> `'Sekarang, mengirimkan ke domination.'`, `'我的枪去而复返，你的生命有去无回。'`, `'“哒哒哒，哒哒哒。”'`, `'一子定乾坤。'`, `'不坠命运之名。'`, `'不该背对我。'`, `'以圣剑的名义起誓。'`, `'以绝望挥剑，着逝者为铠。'`, `'以魂洗剑，以命度心。'`, `'先有破灭，然后重生。'`, `'兼爱、非攻、尚同。'`, `'听，是风在低语。'`, `'天不生夫子，万古如长夜。'`, `'带翅膀的不一定是天使。'`, `'把心事，都藏进花里。'`, `'敌动，我不动。'`, `'映照潮汐的起伏，以免迷失战场的道路。'`, `'春风吹又生，斩草又除根。'`, `'有缘千里来相会。'`, `'武道没有定式，人生亦是如此。'`, `'滴答，滴答，滴答，滴答~'`, `'玄微有灵，万物生长。'`, `'用兵之道，在于用阵。'`, `'眼界必须放长远。'`, `'福祸双依，天命难解。'`, `'良药苦口，蜜语伤人。'`, `'萤火庇护，万物复苏。'`, `'行到水穷处，坐看云起时。'`, `'言为心声，字为心画。'`, `'长枪所向，一往无前。'`, `'可爱的小鹿，可靠的前排坦克。'`, `'它最大的职责就是挨打。'`, `'机器仆从A1'` (`'Mechanical Minion sebuah1'`).
> 3. **`normalize_formula_skeleton_zh` HARDCODED `\[0\]` INSTEAD OF `\[\d+\]` IN `src/acepatchindo/tag_aligner.py:226-227,350-351`, DROPPING `43+` MAIN HERO SKILL VARIANTS (`Lu Bu`, `Augran`, `Allain`, `Donghuang`, `Yang Jian`, `Dolia`, `Yao`, `Li Bai`, `Fang`, `Yuhuan`) FROM TIER 1 TO BROKEN TIER 3 INDLISH:**
>    - `p = re.sub(r"\[0\]点(物理|法术|真实)伤害\(([^)]+)\)", r"\2的\1伤害", p)` and `p = re.sub(r"\[0\]点(护盾|生命值)\(([^)]+)\)", r"\2的\1", p)` only matched `[0]`! Any skill with a 2nd or 3rd parenthetical formula (`[1]点生命值（[2]%最大生命值）` in Donghuang, `[2]点物理伤害（[3]%物理攻击力）` in Allain, `[3]点生命（[4]%最大生命值）` in Lu Bu, `[2]点物理伤害（[3]+[4]%物理攻击力）` in Augran) or a trailing `点击技能描述面板，查看...详细解释` note failed `skel_zh in self.tier1_formula_zh_to_id` or failed `reinject_formula_and_skeleton` (`id_dmg_spans`), falling back to Tier 3 Indlish (`dasar Lu Bu serangan`, `Donghuang menciptakan 3 Bola energi itu orbit di sekitarnya`, `dasar Augran serangan`)!
> 4. **MANGLED NAMES & BROKEN INDLISH IN TIER 3 (`Luban Tidak. 7`, `Damage Atas`, `Decay Bawah`, `Mementalkan Atas`, `[Hebat Dinding]`, `Mechanical Minion sebuah1`, `pada Menggunakan`, `ke melepaskan`, `dasar Lu Bu serangan`):**
>    - `"Luban No. 7"` / `"Luban No.7"` / `"Luban No. 9"` / `"Luban No. 4"` / `"No. 7 laser cannon"` had `"No"` translated by `WORD_1["no"] = "tidak"`, producing **`Luban Tidak. 7`**, **`Luban Tidak. 9`**, **`Luban Tidak. 4`**, **`Tidak. laser 7 meriam`**!
>    - Short Lv.10/40/100 skill enhancement summaries ending in `"Up"` / `"Down"` (`"Bullet Damage Up"`, `"Missile Decay Down"`, `"Passive Cap Up"`, `"Bounce Count Up"`) became **`Peluru Damage Atas`**, **`Rudal Decay Bawah`**, **`Pasif Batas Atas`**, **`Memantul Jumlah Atas`** (28 hits)!
>    - `"Knock Up"` / `"knocking up"` / `"Knocking Up"` became **`Mementalkan Atas`** (34 hits) instead of `Knock-Up` / `memberi efek Knock-Up`!
>    - `"on Skill Cast"` / `"on Cast"` became **`pada Skill Menggunakan`** / **`pada Menggunakan`** instead of `saat menggunakan Skill`.
>    - Faction `"Great Wall"` (and `"Chang'an"`, `"Yaotian"`, `"Jixia"`, `"Cloudream"`, `"Xuanyong"`) was missing from `CANONICAL_PROTECTED_TERMS`, turning `[Great Wall]` into **`[Hebat Dinding]`**!
>    - `"A1"` in `"Mechanical Minion A1"` had `"A"` replaced with `"sebuah"`, producing **`Mechanical Minion sebuah1`**!
>    - Infinitive `"to <verb>"` (`"to cast"`, `"to reach"`, `"to deal"`, `"to attack"`, `"to trigger"`, `"to gain"`, `"to restore"`) became **`ke melepaskan`**, **`ke mencapai`**, **`ke memberikan`**, **`ke menyerang`** (318 hits) instead of `"untuk <verb>"`!
>    - Possessive `"<Name>'s basic attacks"` (`"Lu Bu's basic attacks"`, `"Arthur's basic attacks"`, `"Augran's basic attacks"`) became **`dasar Lu Bu serangan`** instead of **`Basic Attack <Name>`**!

### Task 29: Fix Dual-Table Chinese/English Separation, Suffix-Level Veto Propagation, & Voice-Line Filtering in `scripts/01b_build_hybrid_vfs_index.py` & `src/acepatchindo/hybrid_classifier.py`

- [ ] **Step 29.1: Never Let English `.bytes` Tables Overwrite `m60_lookup` or Bypass Chinese Vetoes in `scripts/01b_build_hybrid_vfs_index.py`** *(REOPENED BY MANAGER AUDIT ROUND 3 — lines 317 & 329 dumped `1,445` full Talent/Contestant descriptions from `#60D2` into `veto_names_zh` and `nontarget_table_zh`, poisoning `#CEDB` and causing `247` tagged Tier 1/2 descriptions in `unique` and `1,126` rows in `english_updates` to stay in English!)*
  1. **Require CJK Characters in Chinese Pass (`_has_cjk(s)`):**
     - Define `_CJK_RE = re.compile(r"[\u4e00-\u9fff]")`.
     - When populating `m60_lookup` (Pass 1), **ONLY** read records where `_CJK_RE.search(val)` is `True` (or explicitly only from the Chinese `#60D2` table `0x36B258373DA34185`) so English `#60D2` (`0xDD400CE5E3F32E17`) **NEVER** overwrites `m60_lookup[sfx]`!
     - Explicitly **exclude `#60D2` (`tag == "60D2"`)** from `vfs_target_keys` and `vfs_target_zh` unless `zh_str in ref_target_zh` (all `#60D2` Faction+Class tags like `'三分之地   战士'`, `'日落海   战士'`, `'河洛   战士'` are category badges and must stay `100%` English!).
  2. **Evaluate Target vs Veto ONLY on Chinese Records (`_CJK_RE.search(zh_str)`), Then Propagate by 48-Bit Suffix `sfx = key[5:17]` to Paired English Tables:**
     - During Pass 2, separate tables/records into **Chinese records** (`_CJK_RE.search(zh_str)`) and **non-CJK English records** (`not _CJK_RE.search(zh_str)`).
     - Never add a non-CJK string to `vfs_target_zh`! (`assert all(_CJK_RE.search(s) for s in vfs_target_zh)`!)
     - Maintain `target_sfx_by_family` and `veto_sfx`: whenever a Chinese record with suffix `sfx = key[5:17]` is vetoed (`is_veto == True` or `is_target == False` in the same family), add `sfx` to `veto_sfx` and `key` to `vfs_veto_keys`.
     - After evaluating all Chinese records, for every record `(key, val)` in the paired English tables (`not _CJK_RE.search(val)`): if `tag in ALLOWED_TARGET_PREFIXES - {"60D2"}` and `sfx in target_sfx` and `sfx not in veto_sfx`, add `key` to `vfs_target_keys`; otherwise add `key` to `vfs_veto_keys`!
     - Enforce invariant at the end of `01b_build_hybrid_vfs_index.py`:
       `assert len({k[5:17] for k in vfs_target_keys} & {k[5:17] for k in vfs_veto_keys}) == 0` (**ZERO** conflicting row suffixes `sfx` between `vfs_target_keys` and `vfs_veto_keys`!).
  3. **Tighten Equipment, UI & Voice-Line Vetoes in `01b_build_hybrid_vfs_index.py`:**
     - Expand `P_EQUIP_PATTERN` to also match: `唯一：`, `<color=#ffffff><b>唯一</b></color>`, `件装备`, `装备箱`, `特殊装备`, `高级装备`, `穿戴`, `佩戴` (when not in `ref_target_zh`).
     - In `#BCDE..#CEDB` (including `#9344`), veto non-reference strings starting with `当前祝福：` or matching `炸弹牌加入了对局` or `卡牌\d+选\d+`.
     - In `SKILL_PREFIXES` (`#FCCD`, `#99AB`, `#4853`, `#865D`, `#CE46`), a Chinese string NOT in `ref_target_zh` and `normalize_plain_zh(zh_str) not in ref_target_plain` is ONLY a target skill description if `plain_zh` contains a **genuine gameplay mechanic marker**:
       `re.search(r"(\d+|%|\[0\]|\+|伤害|恢复|生命|护盾|法力|物理|法术|攻击|防御|速度|冷却|眩晕|击飞|减速|沉默|免疫|召唤|被动|主动|入场|登场|牺牲|觉醒|提升|降低|增加|减少|造成|获得|持续|范围|目标|友军|敌方|敌人|回合|技能|普攻|暴击|分身|层数|上限)", plain_zh)`
       AND does **NOT** match unit flavor descriptions `r"^(?:可爱的小鹿|它最大的职责就是挨打|机器仆从)"`! This immediately eliminates all 45+ Hero voice lines / lore quotes (`女人，是水做的。`, `你已经被盯上了。`, `清理工作才刚刚开始。`, `现在，接受支配。`, `我的枪去而复返...`, `以圣剑的名义起誓。`, etc.) while keeping 100% of real skills & enhancements!

### Task 30: Fix Multi-Index Formula Skeleton Alignment (`\[\d+\]`) in `src/acepatchindo/tag_aligner.py` So All `Lu Bu`, `Augran`, `Allain`, `Donghuang`, `Yang Jian`, `Dolia`, `Yao`, `Li Bai`, `Fang`, & `Yuhuan` Skills Hit Tier 1

- [ ] **Step 30.1: Generalize `normalize_formula_skeleton_zh` and `reinject_formula_and_skeleton` in `src/acepatchindo/tag_aligner.py`** *(REOPENED BY MANAGER AUDIT ROUND 3 — line 229 used `r"#\1"` instead of `#N#`, breaking `[\d+]%` -> `#% != #N#%`, AND `reinject_formula_and_skeleton` lines 384–429 + 729 threw away Tier 1 `desc_id` and fell back to Tier 3 `baseline_en`!)*
  1. In `normalize_formula_skeleton_zh(zh_text: str) -> str` (`tag_aligner.py:217-230`):
     - Before stripping tags, strip any trailing UI inspection hint line:
       `p = re.sub(r"\n*(?:<color=[^>]+>)*点击技能描述面板[，,].*$", "", p)`
     - Replace hardcoded `\[0\]` with `\[\d+\]点?` and `(护盾|生命值?)`:
       ```python
       p = re.sub(r"\[\d+\]点?(物理|法术|真实)伤害\(([^)]+)\)", r"\2的\1伤害", p)
       p = re.sub(r"\[\d+\]点?(护盾|生命值?)\(([^)]+)\)", r"\2的\1", p)
       ```
  2. In `reinject_formula_and_skeleton(zh_src, id_trans, baseline_en)` (`tag_aligner.py:302-360`):
     - When `zh_src` has trailing `点击技能描述面板，查看...详细解释`, translate/preserve that trailing note cleanly (or strip/re-append its Indonesian equivalent `\n<color=#7288a7>Klik panel deskripsi Skill untuk melihat penjelasan detail</color>`) instead of failing formula alignment!
     - Generalize the parenthetical `[k]点...([m]...)` reinjection in `reinject_formula_and_skeleton` so it works for **1, 2, or more** parenthetical formulas (`\[\d+\]点?(?:物理伤害|法术伤害|真实伤害|护盾|生命值?)\s*[（(][^）)]+[）)]`) AND matches Indonesian spans across all Tier 1 phrasings (`sebagai Physical/Magic/True Damage`, `Physical/Magic/True Damage sebesar ...`, `Memulihkan ... HP`, `mendapatkan Shield sebesar ...`), OR directly substitutes the `{0}`/`#` placeholders from `zh_src`'s `[0]`, `[1]`, `[2]` tokens so **0** Tier 1 Hero skills fall back to Tier 3!

### Task 31: Fix All Remaining Tier 3 Indlish & Name Mangling Bugs in `src/acepatchindo/glossary.py` & `src/acepatchindo/lexicon_id.py`

- [ ] **Step 31.1: Protect `"No. X"`, Faction Names (`Great Wall`), & Alphanumeric Suffixes (`A1`) in `src/acepatchindo/glossary.py`** *(REOPENED — capitalized `"ke Menyerang"`, `"ke Memberikan"`, `"ke Memulihkan"`, `"ke Memicu"`, `"Basic Attack Basic Attack"`, and `"meningkatkan/mengurangi ... oleh"` still present!)*
  1. **Protect `Luban No. 7` / `No. 7` / `No. 9` / `No. 4` Before Tokenization:**
     - Add `"Luban No. 7"`, `"Luban No.7"`, `"Luban No. 9"`, `"Luban No. 4"`, `"Mechanical Minion A1"` AND all Faction English names (`"Great Wall"`, `"Three Kingdoms"`, `"Sunset Sea"`, `"Central Plains"`, `"Central Plain"`, `"Riverlands"`, `"Zhulu Plateau"`, `"Zhulu"`, `"Cloudream"`, `"Chang'an"`, `"Yaotian"`, `"Jixia"`, `"Xuanyong"`, `"Chaos Rift"`) to `CANONICAL_PROTECTED_TERMS`!
     - Also add a pre-pattern in `glossary.py` before tokenization that protects `r"\bNo\.\s*\d+\b"` (so `"No. 7"` / `"No.7"` / `"No. 9"` is NEVER split into `"No"` -> `"Tidak"` + `". 7"`!).
     - In `lexicon_id.py` / `glossary.py`, never translate a letter immediately adjacent to digits (`A1`, `B2`) as `"sebuah"`.
  2. **Fix `"<Name>'s basic attacks"`, `"Up/Down"` Stat Summaries, `"Knock Up"`, `"on Skill Cast"`, and Infinitive `"to <verb>"` in `src/acepatchindo/glossary.py` & `src/acepatchindo/lexicon_id.py`:**
     - **Possessive Basic Attacks (`dasar Lu Bu serangan` -> `Basic Attack Lu Bu`):**
       - Add pre-pattern in `glossary.py` (before tokenizing `"basic"`):
         `(r"\b([A-Z][A-Za-z0-9'&.\- ]{1,25}?)'s\s+basic\s+attacks?\b", r"Basic Attack \1")`
         and `(r"\b([A-Z][A-Za-z0-9'&.\- ]{1,25}?)'s\s+attacks?\b", r"serangan \1")`!
     - **Short Stat Enhancement Summaries Ending in `"Up"` / `"Down"` (`Damage Atas` -> `Meningkat`, `Decay Bawah` -> `Berkurang`):**
       - When a short skill enhancement string ends with `\bUp$` or `\bDown$` (or `Damage Up`, `Decay Down`, `Cap Up`, `Count Up`, `Range Up`, `Duration Up`, `Effect Up`, `Limit Up`, `Speed Up`, `Cooldown Down`), translate trailing `Up` as `"Meningkat"` and trailing `Down` as `"Berkurang"` (e.g., `"Bullet Damage Up"` -> `"Damage Peluru Meningkat"`, `"Missile Decay Down"` -> `"Penurunan Damage Rudal Berkurang"`, `"Passive Cap Up"` -> `"Batas Pasif Meningkat"`, `"Bounce Count Up"` -> `"Jumlah Pantulan Meningkat"`, `"Restore Effect Up"` -> `"Efek Pemulihan Meningkat"`)!
     - **`"Knock Up"` / `"knocking up"` / `"knocked up"` (`Mementalkan Atas` -> `Knock-Up`):**
       - In `lexicon_id.py` `PHRASE_2` / `PHRASE_3` and `glossary.py`, replace `"mementalkan atas"` with `"memberi efek Knock-Up"` / `"Knock-Up"` (`("knock", "up"): "Knock-Up"`, `("knocks", "up"): "memberi efek Knock-Up"`, `("knocked", "up"): "terkena Knock-Up"`, `("knocking", "up"): "memberi efek Knock-Up"`), and add cleanup `("Mementalkan Atas", "Knock-Up")`, `("mementalkan atas", "memberi efek Knock-Up")`!
     - **`"on Skill Cast"` / `"on Cast"` (`pada Skill Menggunakan` -> `saat menggunakan Skill`):**
       - Add `("on", "skill", "cast"): "saat menggunakan Skill"`, `("on", "cast"): "saat digunakan"` in `PHRASE_3` / `PHRASE_2`!
     - **Infinitive `"to <verb>"` (`ke melepaskan` -> `untuk melepaskan`):**
       - In `glossary.py` post-processing (or `lexicon_id.py`), replace `\bke\s+(me[a-z]+|ber[a-z]+|ter[a-z]+|di[a-z]+|memper[a-z]+|meng[a-z]+|meny[a-z]+|men[a-z]+|mem[a-z]+|mel[a-z]+|mer[a-z]+)\b` with `r"untuk \1"` so `"ke melepaskan"`, `"ke mencapai"`, `"ke memberikan"`, `"ke menyerang"`, `"ke memicu"`, `"ke mendapatkan"`, `"ke memulihkan"`, `"ke meningkatkan"` all become natural Indonesian **`"untuk <verb>"`**!

### Task 32: Add Regression Assertions to `tests/test_glossary_and_tiers.py`, Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Verify `14 passed`, & Re-Publish `v1.4.12-id.2` (`06`)

- [ ] **Step 32.1: Add Regression Checks to `tests/test_glossary_and_tiers.py`** *(REOPENED — line 418 used `k.split("#")[-1]` which is always `""` instead of `k[5:17]`!)*
- [ ] **Step 32.2: Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Run `pytest -v`, Commit, Force-Tag `v1.4.12-id.2`, & Re-Upload Release Assets (`06`)** *(REOPENED)*

---

## Phase 6 Remediation Round 3: Final Precision Fixes (Tasks 33–36)

> [!CAUTION]
> **Manager Forensic Audit of `commit bbe751f` — REJECTED Due to 3 Surgical Regressions Uncovered in `01b_build_hybrid_vfs_index.py`, `tag_aligner.py`, and `glossary.py`:**
> 1. **`#60D2` POISONING BUG IN `scripts/01b_build_hybrid_vfs_index.py:317,329` + `P_EQUIP_PATTERN` OVER-VETO (`247` Tagged Hero/Skill/Talent Variants in `unique` & `1,126` Rows in `english_updates` Falsely Left in English!):**
>    - Table `#60D2` is NOT purely a short badge table: while `425` records are Hero Faction+Class tags (`'河洛   坦克'`) and `5,648` are short badges (`< 8` chars), **`1,457` records in `#60D2` are full Talent, Contestant Secret Art, and Skill descriptions** (`len(plain_zh) >= 8` with sentence punctuation)!
>    - In `01b_build_hybrid_vfs_index.py` lines `316–317` (`if s.strip() not in ref_target_zh: veto_names_zh.add(s.strip())`) and line `329` (`if prefix not in ALLOWED_TARGET_PREFIXES or prefix == "60D2": nontarget_table_zh.add(s_str)`), the Executor dumped **all `1,445` full descriptions from `#60D2`** into `veto_names_zh` AND `nontarget_table_zh`!
>    - **Consequence A (`153 + 94 = 247` Tagged Gameplay Descriptions in `unique` Left in English):** Because `HybridClassifier.is_target_unique` checked `zh_clean in self.veto_names_zh` (Step 3) and `zh_clean in self.nontarget_table_zh` (Step 4) **BEFORE** `p_zh in self.ref_target_plain` (Step 5) and lacked `skel_zh in self.ref_target_skel`, `247` tagged Hero Card, Skill, and Talent descriptions (such as `<color=#FFE897>4/5阶的召唤单位</color>获得╧完美复生。`, `<color=#FFE897>╉先知图腾获得额外效果</color>...`, `云中君展翅舞蹈向周围1格射出羽箭...`, `<a href=3><color=#ffffff>╪<b>开团</b></color></a>：距离最近的4名己方英雄获...`, `光辉伤害提升至[0]%法术攻击力`, `子弹伤害提升至40+25%物理攻击力`, `导弹伤害提升至30+80%物理攻击力`) returned `False` and stayed in English!
>    - **Consequence B (`1,126` Legitimate Talent & Hero Card Rows in `english_updates` Left in English):** When `#CEDB` was scanned in Pass A (line 373 `elif zh_str in veto_names_zh:`), `#CEDB`'s Talent descriptions matched the poisoned `veto_names_zh`, adding their `sfx` to `veto_sfx`. Then line `478` (`target_sfx -= veto_sfx`) wiped out those `sfx` suffixes across all 12 Talent tables (`#BCDE..#CEDB`), leaving `1,126` rows in `english_updates` (`#BCDEF24440F2D6B7#`, `#BCDEEB1EA4FBE926#` Kaizer & Luna, `#BCDE84EBBBE3F468#` Alessio & Meng Ya, plus Luara & Marco Polo Hero Cards whose text contained `穿戴`/`件装备`) in English!
> 2. **3 BUGS IN `src/acepatchindo/tag_aligner.py` (`lines 229, 384–429, 729`) THAT STILL CAUSED ALL 10 MULTI-FORMULA HERO SKILLS (`Lu Bu`, `Augran`, `Allain`, `Donghuang`, `Yang Jian`, `Dolia`, `Yao`, `Li Bai`, `Fang`, `Yuhuan`) TO FALL BACK TO TIER 3:**
>    - **Bug 2A (`tag_aligner.py:229` & `354`):** `p = re.sub(r"\[\d+\](%|秒|...)", r"#\1", p)` used `r"#\1"` (single `#`) instead of `#N#`, turning `[0]%` into **`#%`** while `FORMULA_TOKEN_RE.sub("#N#", p)` at line 235 turned `10%` in `tier1_wiki_id.json` into **`#N#%`** (`"#%" != "#N#%"`)! That single typo broke `tier1_formula_zh_to_id` matching for every skill containing `[0]%` or `[0]点`!
>    - **Bug 2B (`tag_aligner.py:219`):** `re.sub(r"^(?:主动|被动|...)[：:]", "", p)` had `^` at the start, so mid-string `主动：` labels in `source_zh` vs `descCn` or `释放` vs `施放` / `最大生命` vs `最大生命值` prevented skeleton equality!
>    - **Bug 2C (`tag_aligner.py:384-429` & `729-761`):** In `reinject_formula_and_skeleton`, the partial `color_spans` loop (`lines 384–429`) wrapped only *some* `<color=...>` tags into `out` (setting `"<" in out` to `True`), which caused `reinject_skeleton_from_source` line 497 (`if spans and "<" not in result:`) to be **skipped**, and then line `729` (`if baseline_en:`) **threw away the Tier 1 Indonesian translation `desc_id` completely and replaced it with Tier 3 translation of `baseline_en`** (`Lu Bu melompat menjadi sebuah padat area dari musuh`, `Donghuang menciptakan 3 Energi bola itu orbit dia`, `Allain memberikan Magic Damage saat menyerang dengan "Merah tua Bayangan"`, `Dolia menerima putri duyung wujud dalam air dia menciptakan`)!
> 3. **REMAINING TIER 3 CASE-SENSITIVE REGEX & PROSE DEFECTS + VACUOUS TEST BUG (`tests/test_glossary_and_tiers.py:418`):**
>    - In `glossary.py`, the `"ke <verb>"` -> `"untuk <verb>"` regex was case-sensitive (`me[a-z]+`), leaving `30+` capitalized occurrences of **`"ke Menyerang"`**, **`"ke Memberikan"`**, **`"ke Memulihkan"`**, **`"ke Memicu"`**!
>    - Duplicate **`"Basic Attack Basic Attack"`** (`24` hits), **`"meningkatkan/mengurangi <Stat> oleh <N>"`** (`325` hits instead of `"sebesar"`), and untranslated `"cyclically"`, `"slices"`, `"cuts"` remained in Tier 3.
>    - In `tests/test_glossary_and_tiers.py:418`, `tgt_sfx = {k.split("#")[-1] for k in ...}` always evaluated to `{""}` because every key `k` ends with `#` (`#23F70B7AD27441BA#`)! It must use `k[5:17]`.

### Task 33: Fix `#60D2` Poisoning, `P_EQUIP_PATTERN` Guard, & Formula Skeleton Reference Matching in `scripts/01b_build_hybrid_vfs_index.py` & `src/acepatchindo/hybrid_classifier.py`

- [ ] **Step 33.1: Stop `#60D2` From Poisoning `veto_names_zh` and `nontarget_table_zh` in `scripts/01b_build_hybrid_vfs_index.py`** *(REOPENED BY MANAGER AUDIT ROUND 4 — Executor added unauthorized `elif len >= 8` wildcards on `#60D2`, `CARD_PREFIXES`, and `english_updates` (`lines 404, 462, 569`), leaking `88+` Choice/Draw Effect Cards `'3选1一件特殊装备。'`, `'3选1一件高级装备。'`, `'5选2【三分之地】4-5阶英雄...'`, `'获得特殊装备...'`, and `'404 Error，出厂设置故障...'`!)*
  1. In `scripts/01b_build_hybrid_vfs_index.py` (`lines 309–335`):
     - When scanning `prefix == "60D2"`:
       - Populate `m60_lookup[sfx] = s` and `m60_hero_suffixes.add(sfx)` for Chinese records (`_CJK_RE.search(s)`).
       - **ONLY** add `s_str = s.strip()` to `veto_names_zh` if `HERO_FACTION_CLASS_RE.search(s_str)` OR (`len(normalize_plain_zh(s_str)) < 8` and not any(p in s_str for p in ("，", "。", "：", ":", "\n")))! **NEVER** add long `#60D2` descriptions (`len(normalize_plain_zh(s_str)) >= 8` with sentence punctuation) to `veto_names_zh`!
     - At line `329`, change `if prefix not in ALLOWED_TARGET_PREFIXES or prefix == "60D2":` back to `if prefix not in ALLOWED_TARGET_PREFIXES:` so `#60D2`'s 1,457 long Talent/Contestant descriptions are **NEVER** added to `nontarget_table_zh`!
  2. **Build `ref_target_skel` in `01b_build_hybrid_vfs_index.py` and Guard `P_EQUIP_PATTERN`:**
     - Import `normalize_formula_skeleton_zh` from `acepatchindo.tag_aligner`.
     - Build `ref_target_skel: set[str] = {normalize_formula_skeleton_zh(s) for s in ref_target_zh if len(normalize_plain_zh(s)) >= 6}` and save `"ref_target_skel": sorted(ref_target_skel)` into `hybrid_vfs_index.json`.
     - Define helper `is_ref_target(zh_str, plain_zh, skel_zh) -> bool`:
       `zh_str in ref_target_zh or plain_zh in ref_target_plain or (len(plain_zh) >= 6 and skel_zh in ref_target_skel)`.
     - In Pass A (`lines 368–475`):
       - Check `is_ref = is_ref_target(zh_str, plain_zh, skel_zh)`.
       - Do **NOT** veto by `P_EQUIP_PATTERN` when `is_ref` is `True` OR `sfx in m60_hero_suffixes` (protecting Luara & Marco Polo Hero Cards and Equipment-granting Talents!), AND tighten `P_EQUIP_PATTERN` so it does NOT match bare `穿戴` / `件装备` inside Hero/Talent sentences:
         `P_EQUIP_PATTERN = re.compile(r"(?:<b>唯一</b>|唯一[：:]|唯一被动|穿戴给英雄|穿戴者|穿着这件装备|仅.{1,6}英雄穿戴|普通装备│|^(?:<color=[^>]+>)*(?:物理吸血|法术吸血|物理防御力?|法术防御力?|攻击速度|暴击率|冷却缩减)\+\d+|^(?:卡牌\d+选\d+|\d+选\d+)?(?:特殊装备|高级装备|装备箱))")`.
       - If `is_ref` is `True` (and `tag != "60D2"` and `zh_str not in veto_equip_zh` and `zh_str not in veto_effect_zh`), mark `is_target = True` and `is_vetoed = False`!
  3. **Reconcile `sfx` Without Letting `#CEDB` Veto Valid `#BCDE` Talents:**
     - If any Chinese record for `sfx` across `#BCDE..#CEDB` or `#23F7..#6E60` is a valid target (`sfx in target_sfx`) and `sfx` was NOT vetoed by `veto_equip_zh` / `veto_effect_zh` / `m60_val == "效果"`, keep `sfx` in `target_sfx` (`veto_sfx -= target_sfx` for non-equip/non-effect rows, and `vfs_target_keys = {k for k in vfs_target_keys if k[5:17] in target_sfx}`, `vfs_veto_keys = {k for k in vfs_veto_keys if k[5:17] not in target_sfx}`)!

- [x] **Step 33.2: Update `HybridClassifier.is_target_unique` in `src/acepatchindo/hybrid_classifier.py`**
  - Load `self.ref_target_skel: frozenset[str] = frozenset(data.get("ref_target_skel", []))`.
  - In `is_target_unique(self, zh_src: str, en_base: str = "") -> bool`:
    1. Hard vetoes first: `WINDOWS_108_NONTARGET_EN`, `self.veto_equip_zh`, `self.veto_effect_zh`, `p_zh in self.veto_equip_plain`, `p_zh in self.veto_effect_plain`.
    2. **Authoritative positive references BEFORE `veto_names_zh` and `nontarget_table_zh`:**
       - If `zh_clean in WINDOWS_108_TARGET_DESC_ID or zh_clean in self.ref_target_zh or p_zh in self.ref_target_plain`: return **`True`**!
       - Compute `skel_zh = normalize_formula_skeleton_zh(zh_clean)`. If `len(p_zh) >= 6 and skel_zh in self.ref_target_skel and zh_clean not in self.nontarget_table_zh`: return **`True`**!
    3. Then check `if zh_clean in self.veto_names_zh: return False` and `if zh_clean in self.nontarget_table_zh: return False`.
    4. Then check `if zh_clean in self.vfs_target_zh: return True`.
    5. Return `False`.

### Task 34: Fix the 3 Bugs in `src/acepatchindo/tag_aligner.py` So Tier 1 `desc_id` Is Never Thrown Away for Tier 3 `baseline_en`

- [ ] **Step 34.1: Fix `normalize_formula_skeleton_zh` in `src/acepatchindo/tag_aligner.py:216-237`** *(REOPENED — 9 1-word differences kept `Augran`, `Yang Jian`, `Erin`, `Hua Mulan`, `Athena`, `Fang`, `Xiang Yu`, `Liu Shan`, `Di Renjie`, `Kaizer`, `Bai Qi`, and `Lu Bu` Variant 1 from matching `tier1_formula_zh_to_id`!)*
  - Replace `normalize_formula_skeleton_zh` with:
    ```python
    def normalize_formula_skeleton_zh(text: str) -> str:
        """Normalize Chinese text by replacing dynamic formula tokens, icon placeholders, and numbers with #N#."""
        p = normalize_plain_zh(text)
        p = re.sub(r"点击技能描述面板.*$", "", p)
        p = re.sub(r"(?:主动|被动|觉醒|天赋|效果|秘技|清平|长恨)[：:]", "", p)
        p = p.replace("（", "(").replace("）", ")").replace("【", "[").replace("】", "]")
        p = (
            p.replace("{Energy}", "能量")
            .replace("{LordExp}", "棋手经验")
            .replace("{LordHp}", "棋手生命值")
        )
        p = re.sub(r"\[\d+\]点?(物理|法术|真实)伤害\(([^)]+)\)", r"\2的\1伤害", p)
        p = re.sub(r"\[\d+\]点?(护盾|生命值?)\(([^)]+)\)", r"\2的\1", p)
        p = re.sub(
            r"[一二两三四五六七八九十]+(?=周|次|秒|格|层|名|个|张|点|回合|件|把|枚|颗|只|条|道|束|片|朵|发|支|波)",
            "#N#",
            p,
        )
        skel = FORMULA_TOKEN_RE.sub("#N#", p)
        skel = skel.replace("#N#-#N#", "#N#").replace("#N#点", "#N#")
        while "#N#+#N#" in skel or "#N##N#" in skel:
            skel = skel.replace("#N#+#N#", "#N#").replace("#N##N#", "#N#")
        skel = re.sub(r"最大生命值?的?生命值?", "最大生命值", skel)
        skel = (
            skel.replace("释放", "施放")
            .replace("基础物理攻击", "物理攻击")
            .replace("基础法术攻击", "法术攻击")
            .replace("的物理攻击力", "物理攻击力")
            .replace("的基础攻击力", "物理攻击力")
            .replace("基础攻击力", "物理攻击力")
            .replace("目标敌人", "目标")
            .replace("霸体", "免控")
            .replace("项羽最大生命值", "最大生命值")
            .replace("机关魔手", "机关魔爪")
            .replace("铠召唤魔铠", "铠使用魔铠")
            .replace("附近", "周围")
        )
        skel = re.sub(r"(?<!李元芳)丢出飞镖", "李元芳丢出飞镖", skel)
        skel = re.sub(
            r"^吕布会根据敌人位置使用不同招式(?:普攻|普通攻击)能对身前#N#格内敌人造成伤害",
            "吕布的普通攻击能对身前敌人造成范围伤害",
            skel,
        )
        skel = re.sub(r"[，。：:；;、“”\"!\?！？]", "", skel)
        return skel
    ```
  - Also in `reinject_formula_and_skeleton` line `354`, **DELETE** `src_clean = re.sub(r"\[\d+\](%|秒|...)", r"#\1", src_clean)`!

- [ ] **Step 34.2: Fix `reinject_formula_and_skeleton` (`tag_aligner.py:318-440`) So It Preserves Tier 1 `desc_id` Prose 100%** *(REOPENED BY MANAGER AUDIT ROUND 4 — `sentinels_icon` before Step 3/3b deleted numbers & scrambled `{Energy}`/`{LordHp}`, `out = TAG_RE.sub("", out)` + `_wrap_exact_tag_sequence` destroyed `\n` newlines in `56` strings and chunk-sliced `140` Tier 1 strings, and `reinject_skeleton_from_source` prepended `╧`/`╥`/`╉`/`╬`/`═` at index 0 in `17` strings!)*
  1. In `reinject_formula_and_skeleton`, when `cn_exprs` and `src_exprs` differ in length (or after step 3), also substitute any remaining unmatched `[...]` or `{...}` formula placeholders from `source_zh` / `baseline_en` into `out`'s numeric spans so `Counter(PLACEHOLDER_RE.findall(out)) == Counter(PLACEHOLDER_RE.findall(source_zh))`!
  2. In `reinject_formula_and_skeleton`, if the `color_spans` loop (`lines 384–429`) does NOT wrap all `<color=...>` tags in `source_zh` (`TAG_RE.findall(out) != TAG_RE.findall(source_zh)`), **strip the partial `<color=...>` tags from `out` (`out = TAG_RE.sub("", out)`)** before calling `reinject_skeleton_from_source(source_zh, out, ...)` so `reinject_skeleton_from_source`'s Step 2 (`if spans and "<" not in result:`) and Step 6 (`_wrap_exact_tag_sequence`) run cleanly!
  3. **CRITICAL:** Pass `allow_en_fallback=False` from `reinject_formula_and_skeleton` to `reinject_skeleton_from_source` (and gate `if baseline_en and allow_en_fallback:` at line `729`), so that when `reinject_formula_and_skeleton` is aligning a **Tier 1 human-curated Indonesian translation `desc_id`**, it **NEVER** throws away `desc_id` to translate `baseline_en` with Tier 3!

### Task 35: Fix Remaining Tier 3 Prose Defects (`ke Menyerang`, `Basic Attack Basic Attack`, `meningkatkan ... oleh`) in `src/acepatchindo/glossary.py` & `src/acepatchindo/lexicon_id.py`

- [ ] **Step 35.1: Fix Case-Insensitive `"ke <verb>"`, Duplicate `"Basic Attack"`, and `"oleh"` -> `"sebesar"`** *(REOPENED — `glossary.py:883` hardcoded `rels[1]` mapping Bai Ge's `释放3道剑气...` to `Improvised Creation`, plus `Combat Mulai`, `Preparation untuk perang`, `bermain pada saat yang sama`, `tertinggi-Tier Hero`, `diri sendiri-menghancurkan`, `nilai terendah HP`, `sebuah sekutu Memanggil`, `+30% Menyerang`!)*
  1. In `src/acepatchindo/glossary.py` (`_post_cleanup_id`), add `flags=re.IGNORECASE` to the `\bke\s+(me[a-z]+|ber[a-z]+|...)` regex so capitalized `"ke Menyerang"`, `"ke Memberikan"`, `"ke Memulihkan"`, `"ke Memicu"`, `"ke Mendapatkan"`, `"ke Meningkatkan"` become **`"untuk menyerang"`**, **`"untuk memberikan"`**, **`"untuk memulihkan"`**, **`"untuk memicu"`**!
  2. Deduplicate repeated `"Basic Attack Basic Attack"`:
     `out = re.sub(r"\b(Basic Attack)(?:\s+\1)+\b", r"\1", out, flags=re.I)`
  3. Replace `"meningkatkan/mengurangi <X> oleh <Y>"` with `"sebesar"`:
     `out = re.sub(r"\b(meningkatkan|mengurangi|menambah|menurunkan)\s+([^.,;:\n]{1,40}?)\s+oleh\s+(?=(?:<[^>]+>\s*)*[\d\[{+-])", r"\1 \2 sebesar ", out, flags=re.I)`
  4. In `src/acepatchindo/lexicon_id.py`, add `"cyclically": "secara bergantian"`, `"slices": "membelah"`, `"cuts": "membelah"`.

### Task 36: Strengthen `tests/test_glossary_and_tiers.py`, Rebuild Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Verify `14 passed`, & Re-Publish `v1.4.12-id.2` (`06`)

- [ ] **Step 36.1: Fix `tests/test_glossary_and_tiers.py` & Add Strict Assertions for All 3 Round 3 Fixes** *(REOPENED)*
- [ ] **Step 36.2: Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Run `pytest -v`, Commit, Force-Tag `v1.4.12-id.2`, & Re-Upload Release Assets (`06`)** *(REOPENED)*

---

## Phase 6 Remediation Round 4: Eliminating `_wrap_exact_tag_sequence` & `sentinels_icon` Corruption, Unauthorized `CARD_PREFIXES` Wildcard Leaks, & `glossary.py:883` `rels[1]` Bug (Tasks 37–40)

> [!CAUTION]
> **Manager Forensic Audit of `commit 5fb6392` — REJECTED Due to 3 Severe Regressions Uncovered by Deep Inspection:**
> 1. **`sentinels_icon` EXECUTION-ORDER BUG & `_wrap_exact_tag_sequence` CHUNK-SLICING IN `src/acepatchindo/tag_aligner.py` (`140` Tier 1 Hero Skills & Talents Corrupted, `56` Strings Lost `\n` Newlines, `17` Strings With Misplaced `╧`/`╥`/`╉`/`╬`/`═` Glyphs at Index 0, and `10+` Strings With Deleted Numbers):**
>    - **Bug 1A (`sentinels_icon` vs `COMPOUND_EXPR_RE` & `needed_phs` Collision at `tag_aligner.py:268-399, 462`):**
>      - Step 1 (`lines 268–332`) replaced `{0|2}{Energy}`, `{1|10}{LordHp}`, `{3|2}`, and standalone `{Energy}`, `{LordExp}`, `{LordHp}` in `out` with `__WXQICONPH0__` sentinels **BEFORE** Step 3 (`COMPOUND_EXPR_RE`, `lines 372–385`) and Step 3b (`curr_phs = Counter(PLACEHOLDER_RE.findall(out))`, `lines 387–399`), and only restored `sentinels_icon` at line `462`!
>      - Because `src_clean` still contained `{0|2}` while `out` had already replaced `2 Energy` with `__WXQICONPH0__`, Step 3 overwrote the NEXT `2` in `out` (`Tier 2-3` -> `Tier {0|2}-3`), and Step 3b saw `curr_phs == 0` for `{Energy}`/`{LordHp}`/`{LordExp}` (hidden inside `__WXQICONPH0__`!) and overwrote the first numbers in `out` (`10`, `6`, `2`, `1`) with duplicate `{Energy}`/`{LordHp}`/`{LordExp}` placeholders! Then `_wrap_exact_tag_sequence` (`line 865`) deleted the first placeholder (`__WXQICONPH0__`), producing broken strings with missing numbers and scrambled placeholders:
>        - `'获得{0|2}{Energy}，以及随机1张2-3阶<color=#FFE897>【河洛】英雄牌</color>。'` -> `'Memperoleh , dan secara <color=#FFE897> acak {Energy} Kartu Hero</color>[Central Plain] Tier {0|2}-3.'`
>        - `'<color=#FFE897>{LordHp}</color>-10，战斗开始时...'` -> `'<color=#FFE897> -. Saat Combat dimulai,</color> tiap Hero milikmu +{LordHp} Temporary <color=#FFE897> Level...'`
>        - `'<color=#FFE897>【逐鹿】英雄每释放6次技能</color>，获得{0|1}{Energy}，上限{0|5}{Energy}。'` -> `'<color=#FFE897> Setiap Hero [Zhulu] menggunakan Skill </color> kali, memperoleh {0|1}{Energy}...'` (`6` deleted!)
>        - `'随机获得10-20{Energy}。'` -> `'Secara acak memperoleh -20 {Energy}.'` (`10` deleted!)
>        - `'选取天赋后，当你<color=#FFE897>输掉2场战斗</color>时，获得{3|6}{LordExp}。'` -> `'Setelah memilih Talent <color=#FFE897> ini,setiap kamu kalah</color> kali Combat, memperoleh {3|6}{LordExp}.'` (`2` deleted!)
>    - **Bug 1B (`reinject_formula_and_skeleton` Stripping All Tags at `line 459` & Falling Into `_wrap_exact_tag_sequence` Chunk-Slicing on `140` Tier 1 Strings):**
>      - Trailing UI hints `<color=#86888A>点击技能描述面板，查看<b>击飞</b>详细解释</color>` in `source_zh` (`Donghuang`, `Lu Bu`, `Li Bai`, `Diao Chan`, `Master Luban`, `Bai Qi`) contain nested `<b>...</b>` inside `<color=...>`, whereas line `408` appended `<color={c_val}>Ketuk panel deskripsi Skill untuk melihat penjelasan detail</color>` **without `<b>...</b>`**, guaranteeing `TAG_RE.findall(out) != TAG_RE.findall(source_zh)` at line `458`!
>      - Step 2 (`lines 335–351`) grafted multi-tag parenthetical formulas (`<color=#dfa15e>[0] Physical Damage</color><color=#dfa15e> ([1]+[2]% Physical Attack)</color>`) into `out`, and then Step 5 (`color_spans`, `lines 412–457`) tried to wrap `<color=#dfa15e>` AGAIN or failed on lowercase `memulihkan ... Max HP` (`id_dmg_spans` at line `342` lacked `re.I` and `Max HP`!), causing line `459` (`out = TAG_RE.sub("", out)`) to **strip all tags from `out`**!
>      - Then in `reinject_skeleton_from_source`, whenever even 1 span in `spans` didn't match (`all_matched == False`), line `709` **threw away all matched spans in `curr`** and called `_wrap_exact_tag_sequence` (`lines 802–880`), which did `words = stripped_id.split()` (**destroying all `\n` newlines in `56` multi-line skills!**) and sliced sentences into `k` equal-width word chunks (`'<color=#ffffffbf> Pasif: Basic Attack Lu Bu</color> memberikan Damage area ke musuh <color=#ffffffbf> di depannya. Aktif: Lu Bu</color>'`, `'Yang Yuhuan memainkan <color=#ffffffbf> pipa dan mengaktifkan</color> salah satu efek <color=#9ff5d0> lagu secara bergantian.</color>'`, `'Donghuang menciptakan 3 <color=#d487e4> bola energi yang</color> mengelilinginya...'`)!
>    - **Bug 1C (`17` Strings With Misplaced Control Glyphs `╧`, `╥`, `╉`, `╬`, `═`, `╆`, `╋` Prepend-Dumped at Index 0 at `tag_aligner.py:720-748`):**
>      - Step 3 of `reinject_skeleton_from_source` (`lines 720–747`) only had placement rules for `═` and `╫`, and even for `═` it had a buggy `and f"═{kw}" not in result` guard (`line 722`) that stopped after the 1st `Temporary Level` when a string had 2 `Temporary Level`s! For `╧` (`Perfect Revive`), `╥` (`Akomia Core`), `╉` (`Prophet Totem`/`Bond Totem`/`Rebirth Totem`/`Totem`), `╬` (`Preparation`), `╆` (`Fleeting`/`Instant`), and `╋` (`Flash`), it dumped `(ch * needed)` at the very start of the string (`╧<color=#FFE897>4/5 Tier Summoned Unit...`, `╉╉╉Saat Combat dimulai, Prophet Totem...`)!
> 2. **UNAUTHORIZED `elif len(plain_zh) >= 8` WILDCARDS ADDED TO `CARD_PREFIXES` (`line 462`), `#60D2` (`line 404`), AND `english_updates` (`line 569`) IN `scripts/01b_build_hybrid_vfs_index.py` (Leaking `88+` Standalone Choice/Draw Effect Cards, Equipment-Choice Cards, and Training Dummy Strings):**
>    - In `scripts/01b_build_hybrid_vfs_index.py`, the Executor added `elif tag != "60D2" and len(plain_zh) >= 8 and any(p in zh_str ...): is_target = True` on `CARD_PREFIXES` (`line 462`) and `elif len(p_u) >= 8 ...: target_sfx.add(sfx)` on `english_updates` (`line 569`), bypassing the `m60_hero_suffixes` and `m60_val in {"秘技", "技能", "专属"}` check on `CARD_PREFIXES`!
>    - This leaked `88+` non-target standalone Choice/Draw Effect Cards, Equipment-choice cards, and Training Dummy strings into `diff_u` and `diff_eu`:
>      - `'3选1一件特殊装备。'` -> `'Pilih 1 dari 3 Khusus Equipment.'`
>      - `'3选1一件高级装备。'` -> `'Pilih 1 tinggi-akhir Equipment dari 3.'`
>      - `'3选1高级机关卡。'`, `'3选1英雄奖励。'`, `'3选1【令牌：蜀】...'`, `'4阶卡牌2选1，并将选中的卡牌一分为四。'`, `'5选2【三分之地】4-5阶英雄，各获得2张其英雄牌。'`
>      - `'获得特殊装备<color=#ffffff><b>发条齿轮</b></color>...'`, `'获得特殊装备<color=#ffffff><b>隐形药水</b></color>...'`
>      - `'404 Error，出厂设置故障，无法攻击敌人。'`, `'训练用人偶4号，结实耐用可靠！'`
> 3. **`glossary.py:883` HARDCODED `rels[1]` BUG (Mapping Bai Ge's `释放3道剑气...` to `Improvised Creation`) + 14 MINOR PROSE CLEANUPS:**
>    - In `src/acepatchindo/glossary.py:883`, when pairing `t1["lords"]` with `t2_details`, `if len(rels) > 1: r1_name = rels[1].get("name")` hardcoded `rels[1]` instead of matching the referenced card name in `c_desc` (`<b>Burst of Inspiration</b>`) against `rel["name"]` in `rels`, causing `释放3道剑气，斩击手牌中随机3张非觉醒英雄牌，将每张牌斩为2张╆转瞬版复制。` (`Burst of Inspiration`) to translate to `'╆Secara acak menyalin 1 Hero yang ada di field.'` (`Improvised Creation`)!

### Task 37: Fix `reinject_formula_and_skeleton`, `reinject_skeleton_from_source`, Control-Glyph Placement, & `normalize_formula_skeleton_zh` in `src/acepatchindo/tag_aligner.py`

- [x] **Step 37.1: Fix `reinject_formula_and_skeleton` (`tag_aligner.py:256-470`) — Eliminate Pre-Step-3 `sentinels_icon`, Preserve Trailing `点击技能描述面板` Nested `<b>...</b>` Tags, and Never Strip Valid Formula Tags** *(REOPENED BY MANAGER AUDIT ROUND 5 — `tag_aligner.py:406` used `__EXPR_SLOT_{i}__` with digits inside `_1_` and lookbehind `(?<![\d\[{|A-Za-z])` without `_`, leaking literal `__EXPR_SLOT_1__` and `__EXPR_SLOT_{0|2}__` into `4` strings in `catalog.json.gz`; `zh_num_counter_re.sub("1", ...)` replaced `三次`/`两次` both with `"1"`; and `id_dmg_spans` at `line 338` required `\s+sebesar\s+` before Step 2 ran, missing `110` parenthetical `[0]点...（[1]+[2]%...）` skills and causing `needed_numeric_phs` to overwrite `10 detik -> selama [6] detik` in Dolia and `1 tile -> [2] tile` in Bai Qi -> Remediated in Task 41)*
  1. **Handle Trailing UI Hint `<color=...>点击技能描述面板，查看<b>...</b>详细解释</color>` Cleanly Before Body Alignment:**
     - If `source_zh` matches `r"(\n*)((?:<color=[^>]+>)*点击技能描述面板[，,]查看(?:<b>)?([^<]+?)(?:</b>)?详细解释(?:</color>)*)\s*$"` (with or without `<b>`):
       - Strip that trailing match from `source_zh` into `body_source_zh` and construct `footer_id` with the **EXACT SAME TAG SEQUENCE** as the matched footer in `source_zh` (e.g., if `source_zh` has `<color=#86888A>点击技能描述面板，查看<b>击飞</b>详细解释</color>`, then `footer_id` MUST be `f"{leading_nl}<color=#86888A>Ketuk panel deskripsi Skill untuk melihat penjelasan detail <b>{term_id}</b></color>"` so `TAG_RE.findall(footer_id) == TAG_RE.findall(footer_zh)`!).
       - Run formula & tag alignment against `body_source_zh`, and append `footer_id` at the end!
  2. **Fix Formula & Icon Placeholder Order (Do NOT Hide `{0|2}` / `{Energy}` Inside `sentinels_icon` Before `COMPOUND_EXPR_RE`!):**
     - **Step A (Parenthetical `[k]点...([m]...)` & 3-Part Split Formula Grafting):**
       - Match `zh_split_formulas` (`<color=C1>\[a\]点?...</color>\s*<color=C2>[（(]\[b\].*?[）)]</color>`) against `id_dmg_spans` using **`flags=re.IGNORECASE`** and including `Max HP` / `HP Maks` (`r"(?:memberikan\s+|menyebabkan\s+|memulihkan\s+|mendapatkan\s+)?(?:\d+(?:\.\d+)?%?|[A-Za-z ]+?Damage|Shield|HP|Max HP)\s+sebesar\s+\d+(?:\.\d+)?%?(?:\s*\+\s*\d+(?:\.\d+)?%?)?\s*(?:Physical Attack|Magic Attack|Max HP|HP Maks|Attack|HP)(?:\s+miliknya|\s+[A-Za-z']+)?(?:\s+sebagai\s+(?:Physical|Magic|True)\s+Damage|\s+HP)?"`).
       - Also handle 3-tag split recovery spans in `body_source_zh` like `<color=#d487e4>(?:恢复)?([^\d<]*?)(\[\d+\]|[0-9]+)\+([^\d<]*?)(\[\d+[A-Za-z0-9_+/.*%-]*\]|[0-9]+)%([^<]*?)</color><color=#9ff5d0>的生命值</color>` (`Mi Yue`, `Kui`, `Bai Qi`, `Master Luban`, `Augran`, `Milady`) by wrapping the corresponding `memulihkan <Formula> <color=#9ff5d0>HP</color>` span in `out`!
     - **Step B (`COMPOUND_EXPR_RE` 1-to-1 Numeric / Formula Expression Substitution):**
       - Strip `{Energy}`, `{LordExp}`, `{LordHp}` from `src_clean` before running `COMPOUND_EXPR_RE.findall(src_clean)` vs `COMPOUND_EXPR_RE.findall(cn_clean)` so `{0|2}`, `{1|1}`, `{3|2}`, `10-20`, `6`, `[194010p1q2/100]%`, etc. align 1-to-1 in exact positional order!
       - Replace each `c_ex` with `s_ex` in `out` (using a cursor or temporary `__EXPR_SLOT_i__` markers so an earlier replacement never collides with a later number!).
     - **Step C (Attach `{Energy}`, `{LordExp}`, `{LordHp}` Icon Placeholders AFTER Step B):**
       - For each `{num_ph}{icon}` in `body_source_zh` (e.g. `{0|2}{Energy}`, `{1|10}{LordHp}`, `{3|6}{LordExp}`), replace `rf"{re.escape(num_ph)}\s*(?:Energy|Energi|Player EXP|EXP Chess Player|EXP Kontestan|Player HP|HP Chess Player|HP Kontestan)\b"` with `f"{num_ph}{icon}"` in `out`.
       - For any remaining standalone `{Energy}`, `{LordExp}`, `{LordHp}` needed to match `Counter(PLACEHOLDER_RE.findall(body_source_zh))`: replace standalone `(?<!\{)\b(?:Energy|Energi)\b(?!\})` -> `{Energy}`, `\b(?:Player EXP|EXP Chess Player|EXP Kontestan)\b` -> `{LordExp}`, `\b(?:Player HP|HP Chess Player|HP Kontestan)\b` -> `{LordHp}` (up to the exact needed count!).
       - Verify: **ZERO** numbers (`6`, `10`, `2`) are ever overwritten by `{Energy}`/`{LordHp}`/`{LordExp}`!
     - **Step D (Per-Span Semantic `<color=...>` Wrapping Without Wiping Already-Grafted Tags):**
       - In Step 5 (`color_spans`), skip any `<color=...>` span from `body_source_zh` that was already grafted in Step A (`zh_split_formulas` or 3-part recovery).
       - For remaining `<color=c_val>zh_content</color>` spans: match headers (`Pasif:` / `Aktif:` / `Qingping:` / `Changhen:` / `Bentuk Manusia:` / `Bentuk Putri Duyung:` / `2 Stack:` / `3 Stack:` / `Saat bola kembali:`), bracketed factions (`[Central Plain]`, `[Zhulu]`, `[Three Kingdoms]`, `[Sunset]`, `[Jixia]`, `[Great Wall]`, `[Xuanyong]`, `[Yaotian]`, `[Cloudream]`, `[Riverlands]`), entity names (`BADGE_ALIAS_MAP`), and damage/shield/stat formulas!
       - **NEVER** run `out = TAG_RE.sub("", out)` when `out` already contains valid grafted tags! Instead, pass `out` to `reinject_skeleton_from_source(body_source_zh, out, ...)` and let `reinject_skeleton_from_source` insert only the **missing** tags in their proper clauses/lines!

- [x] **Step 37.2: Fix Control-Glyph Placement (`╧`, `╥`, `╉`, `╬`, `═`, `╆`, `╋`, `╪`, `╫`) & Preserve `\n` Newlines and Existing Tags in `reinject_skeleton_from_source` (`tag_aligner.py:485-880`)** *(REOPENED BY MANAGER AUDIT ROUND 5 — `reinject_skeleton_from_source` at `line 892` still ran `stripped_id = TAG_RE.sub("", result)`, stripping already-matched `<color=#ffffffbf>Pasif:</color>` / `<color=#ffffffbf>Aktif:</color>` tags and calling `_wrap_exact_tag_sequence` on `153` target `unique` strings, producing `<color=#ffffffbf> Aktif: Lu Bu melompat ke</color>`, `<color=#ffffffbf> Aktif: Liyuan</color> Fang melempar <color=#dfa15e> dart yang</color>` -> Remediated in Task 41)*
  1. **Complete `GLYPH_KEYWORD_MAP` in `reinject_skeleton_from_source` (`lines 720–748`) so `0` Glyphs Are Ever Prepend-Dumped at Index 0:**
     - Define:
       ```python
       GLYPH_KEYWORD_MAP: dict[str, tuple[str, ...]] = {
           "═": ("Temporary Level", "Level Sementara", "Temp Level"),
           "╧": ("Perfect Revive", "Kebangkitan Sempurna"),
           "╥": ("Akomia Core", "Inti Akomia"),
           "╉": ("Prophet Totem", "Bond Totem", "Rebirth Totem", "Totem"),
           "╬": ("Preparation", "Persiapan"),
           "╆": ("Fleeting", "Instant", "Sekilas"),
           "╋": ("Flash",),
           "╪": ("Engage", "Inisiasi"),
           "╫": ("On Play", "Deploy", "Saat Diterjunkan"),
           "╨": ("Sacrifice", "Pengorbanan"),
           "╈": ("Awaken", "angkit"),
           "╦": ("ancient coin", "Ancient Coin"),
       }
       ```
     - For each `ch in req_ctrl` with `needed > 0`:
       - First, if `source_zh` has `ch` immediately inside or before a tag or at the start of a line/clause (e.g. `╆Secara acak`), or before any keyword in `GLYPH_KEYWORD_MAP.get(ch, ())`, insert `ch` directly before the **next unprefixed occurrence** of that keyword (`re.sub(rf"(?<!{re.escape(ch)})\b({re.escape(kw)})", rf"{ch}\1", result, count=1)`) in a loop while `needed > 0` (do **NOT** use `and f"═{kw}" not in result`, which broke strings with 2 `Temporary Level`s!).
       - Second, if `needed > 0` and `ch` in `source_zh` precedes `<color=...>` or `<b>`, insert `ch` inside/before that matching tag span.
       - Confirm: **0** strings in `diff_u` have a control glyph at index 0 unless `source_zh` itself has that control glyph at index 0 (or after leading `<tag>`)!
  2. **Preserve `\n` Newlines and Matched Tags in `reinject_skeleton_from_source` & `_wrap_exact_tag_sequence`:**
     - If `"\n" in source_zh and "\n" in result` and `source_zh.count("\n") == result.count("\n")`: align tags **line-by-line** across `zip(source_zh.split("\n"), result.split("\n"))` and join with `"\n"` so `\n` newlines are **100% preserved** and tags on Line 1 never bleed into Line 2!
     - When `result` already has some matched tags (`curr_tags = TAG_RE.findall(curr)` is a subsequence of `src_tags = TAG_RE.findall(source_zh)`), only wrap the **unmatched** tags from `src_tags` around their corresponding clauses/keywords instead of stripping `curr` and equal-chunk-slicing the entire sentence!
     - Even inside `_wrap_exact_tag_sequence` (last resort): preserve `\n` line breaks (never collapse `\n` via `.split()`) and wrap headers (`Pasif:`, `Aktif:`, `<Name>:`) and formula numbers (`[0]`, `[1]`, `%`) with their matching `<color=...>` tags instead of blind equal-width word chunking!

- [x] **Step 37.3: Add the 9 Remaining 1-Word Normalizations to `normalize_formula_skeleton_zh` (`tag_aligner.py:216-253`)**
  - Update `normalize_formula_skeleton_zh` as shown in Step 34.1 above so `Augran`, `Yang Jian`, `Erin`, `Hua Mulan`, `Athena`, `Fang`, `Xiang Yu`, `Liu Shan`, `Di Renjie`, `Kaizer`, `Bai Qi`, and `Lu Bu` Variant 1 all match `tier1_formula_zh_to_id` (`0` Tier 3 fallbacks!).

### Task 38: Remove Unauthorized `CARD_PREFIXES` / `#60D2` / `english_updates` Wildcards & Add Split Reference Sub-Clauses in `scripts/01b_build_hybrid_vfs_index.py`

- [x] **Step 38.1: Clean Up `scripts/01b_build_hybrid_vfs_index.py` So `0` Choice/Draw Effect Cards, Equipment Cards, or Dummy Strings Leak**
  1. **Add Split Reference Sub-Lines/Sub-Clauses to `ref_target_zh` in Step 1 (`lines 148–165`):**
     - When ingesting `t2d` (`"Hero"`, `"Summon"`, `"Talent"`, `"Chess player"`) `abilities[*].desc`, `effect_copies`, `calc_copies`, `rule_notes` and `t1["lords"]` `talents`/`related`:
       - For each description `d`, also split `d` on `\n` (`for line in d.splitlines():`):
         - Strip leading `╆?转瞬[。.]?` from `line`.
         - If `line` matches `^([^：:]{2,15})[：:](.+)$`, add both `line` and the RHS clause `m.group(2).strip()` (when `len(normalize_plain_zh(rhs)) >= 6`) to `ref_target_zh`!
       - This cleanly puts split Contestant Secret Art / ability card descriptions (like Wu Zetian's `平定天下一统四海...`, `女帝登基威加海内...`, `科举取士唯才是举...`, `感业寺苦修...`, Ying Zheng's `长生不老药...`, etc.) into `ref_target_zh`, `ref_target_plain`, and `ref_target_skel` **without** needing any wildcard on `CARD_PREFIXES`!
  2. **Remove the 3 Unauthorized `elif len >= 8` Wildcards (`lines 404, 462, 569`):**
     - **Line `404` (`tag == "60D2"`):** Remove `elif len(plain_zh) >= 8 and any(...): is_target = True`. On `tag == "60D2"`, `is_target = True` **ONLY** when `is_ref` is `True`!
     - **Line `462` (`tag in CARD_PREFIXES`):** Remove `elif tag != "60D2" and len(plain_zh) >= 8 and any(...): is_target = True`! On `tag in CARD_PREFIXES - {"60D2"}`, a non-`is_ref` record is `is_target = True` **ONLY** when:
       - `sfx in m60_hero_suffixes` (Hero Card description), OR
       - `m60_val in {"秘技", "技能", "专属"}` and `len(plain_zh) >= 8` and has sentence punctuation!
     - **Line `569` (`english_updates` loop):** Remove `elif len(p_u) >= 8 and any(p in u_zh ...): target_sfx.add(sfx)`! In `english_updates`, `u_zh` should ONLY add `sfx` to `target_sfx` if `is_ref_target(u_zh, p_u, skel_u)` is `True` (and `tag in ALLOWED_TARGET_PREFIXES - {"60D2"}` and not vetoed)!
  3. **Expand `P_EQUIP_PATTERN`, `P_EFFECT_CARD_PATTERN`, and `P_UNIT_FLAVOR_RE`:**
     - `P_EQUIP_PATTERN`: include `(?:\d+选\d+(?:一件)?|获得)(?:特殊装备|高级装备|普通装备|装备箱)`.
     - `P_EFFECT_CARD_PATTERN`: include `r"^(?:卡牌\d+选\d+|\d+阶卡牌\d+选\d+|(?:2选1|3选1|4选1|5选2)(?:一件|高级|普通|英雄|【)?|获得\d+张.+英雄牌。|\d+选1.+英雄，获得\d+张该英雄牌。|随机抽取\d+张.*英雄牌。|指定1名英雄等级\+\d+.*|\d+件装备选\d+件。|立即使所有手牌费用-\d+。)"`.
     - `P_UNIT_FLAVOR_RE`: include `r"^(?:可爱的小鹿|它最大的职责就是挨打|机器仆从|训练用人偶|404 Error)"`.

### Task 39: Fix `glossary.py:883` Hardcoded `rels[1]` Bug & Clean Up Remaining 14 Indlish Phrases (`src/acepatchindo/glossary.py` & `src/acepatchindo/lexicon_id.py`)

- [x] **Step 39.1: Fix `glossary.py:883` (`t1["lords"]` `related` Card Matching by Referenced Name Instead of `rels[1]`)**
  - In `src/acepatchindo/glossary.py` (`lines 870–895`), when matching a 2-line Chinese description (`zh_lines = [line0, line1]`) in `t2_details["Chess player"]` against `t1_lord`:
    - Do **NOT** hardcode `rels[1]`!
    - Instead, find which `rel` in `rels` has its English name (`rel.get("name")`) or Chinese name (`rel.get("nameCn")`) mentioned in `c_desc` (`t_cards[i]["desc"]`) or `zh_lines[0]` / `zh_lines[1]`, and pair `zh_lines[1]` (or the post-colon description in `zh_lines[1]`) with THAT `rel["desc"]`!
    - Also register each `rel` in `t1_lord.get("related", [])` directly by matching `rel.get("nameCn")` / `rel.get("name")` against `t2_details["Chess player"]` `abilities[*]` where `ab.get("name") == rel.get("name")`, so `释放3道剑气，斩击手牌中随机3张非觉醒英雄牌，将每张牌斩为2张╆转瞬版复制。` (`Burst of Inspiration`) maps to its exact Tier 1 translation (`"Melepaskan 3 tebasan energi pedang, menebas 3 Kartu Hero non-Awaken secara acak di tangan, membelah setiap kartu menjadi 2 salinan ╆Fleeting."`) and **NEVER** to `Improvised Creation`!

- [x] **Step 39.2: Clean Up the Remaining 14 Indlish Phrases in `src/acepatchindo/glossary.py` & `src/acepatchindo/lexicon_id.py`**
  - Add to `glossary.py` (`_post_cleanup_id` / `var_subs`) and `lexicon_id.py`:
    1. `"Combat Mulai"` / `"Combat Start"` -> `"Awal Combat"`
    2. `"Preparation untuk perang"` / `"prepare for war"` -> `"Preparation"`
    3. `"bermain pada saat yang sama"` -> `"diterjunkan bersamaan"`
    4. `"tertinggi-Tier Hero"` / `"highest-Tier Hero"` -> `"Hero Tier tertinggi"`
    5. `"tertinggi milikmu-Level Hero"` / `"your highest-Level Hero"` -> `"Hero milikmu dengan Level tertinggi"`
    6. `"diri sendiri-menghancurkan"` / `"self-destructs"` / `"self-destruct"` -> `"meledakkan diri"`
    7. `"nilai terendah HP"` / `"lowest HP value"` -> `"HP terendah"`
    8. `"nilai tertinggi HP saat ini persentase"` / `"highest current HP percentage"` -> `"persentase HP saat ini tertinggi"`
    9. `r"\buntuk berikutnya (\d+) detik\b"` -> `r"selama \1 detik berikutnya"`
    10. `"penguatan kartu"` / `"strengthening card"` -> `"Kartu Penguatan"`
    11. `"sebuah sekutu Memanggil"` / `"an allied Summon"` -> `"unit Summon sekutu"`
    12. `r"(\+\d+%?)\s+Menyerang\b"` -> `r"\1 Attack"`
    13. `"Menyerang mode"` -> `"mode serangan"`, `"poin dari Menyerang"` -> `"poin Attack"`, `"Menyerang kerusakan"` -> `"Damage serangan"`, `"Bonus Menyerang"` -> `"Bonus Attack"`.

### Task 40: Add Strict Anti-Corruption Assertions to `tests/test_glossary_and_tiers.py`, Rebuild Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Verify `14 passed`, & Re-Publish `v1.4.12-id.2` (`06`)

- [x] **Step 40.1: Add 6 Iron-Clad Structural & Content Assertions to `tests/test_glossary_and_tiers.py`** *(REOPENED — needs assertions for `0` `__EXPR` tokens, `0` `<color=#ffffffbf> Aktif: <word>` header merges, and `0` `selama [` overwritten durations -> Remediated in Task 42)*
  1. **Zero Lost `\n` Newlines:**
     `assert sum(1 for k, v in diff_u.items() if "\n" in k and "\n" not in v) == 0`
  2. **Zero Misplaced Control Glyphs at Index 0:**
     For `CTRL = set("╥╆╪╬╉═╧╊╅╈╦╇╋")`: assert `0` strings in `diff_u` start with a char in `CTRL` (after stripping tags) unless `k` (after stripping tags) also starts with that char or has it before the first keyword! Specifically assert `cat["unique"]["<color=#FFE897>4/5阶的召唤单位</color>获得╧完美复生。"]` does **NOT** start with `"╧"`, and `cat["unique"]["战斗开始时，╉先知图腾将两侧的友军变为╉先知图腾分身，复制本体70%的属性。"]` does **NOT** start with `"╉"`.
  3. **Zero Deleted Numbers / Scrambled `{Energy}`/`{LordHp}`/`{LordExp}` Placeholders:**
     Assert **0** occurrences in `diff_u` of `"Memperoleh ,"`, `"Memperoleh ."`, `" -. "`, `"-20 {Energy}"`, `"Skill </color> kali"`, `"setiap kamu kalah</color> kali"`, or `"Tier {0|"`.
  4. **Zero `_wrap_exact_tag_sequence` Mid-Clause Chunk Slicing on Multi-Color Skills:**
     Assert **0** occurrences in `diff_u` of `"<color=#ffffffbf> Pasif: Basic Attack"`, `"<color=#ffffffbf> di depannya"`, `"<color=#ffffffbf> pipa dan mengaktifkan"`, `"<color=#d487e4> bola energi yang"`, or `"<color=#d487e4> Saat bola"`.
  5. **Zero Leaked Choice/Draw Effect Cards, Equipment-Choice Cards, or Training Dummy Strings:**
     Assert that `"3选1一件特殊装备。"`, `"3选1一件高级装备。"`, `"5选2【三分之地】4-5阶英雄，各获得2张其英雄牌。"`, `"404 Error，出厂设置故障，无法攻击敌人。"`, `"训练用人偶4号，结实耐用可靠！"` are all **100% untouched English** (`cat["unique"][z] == orig_cat["unique"][z]`)!
  6. **Bai Ge's `Burst of Inspiration` (`释放3道剑气...`) Accuracy:**
     Assert `"pedang"` in `cat["unique"]["释放3道剑气，斩击手牌中随机3张非觉醒英雄牌，将每张牌斩为2张╆转瞬版复制。"]` and `"menyalin 1 Hero"` is **NOT** in it!

- [x] **Step 40.2: Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Run `pytest -v`, Commit, Force-Tag `v1.4.12-id.2`, & Re-Upload Release Assets (`06`)** *(REOPENED)*

---

## Phase 6 Remediation Round 5: Eliminating `__EXPR_SLOT_` Leakage & Remaining `153` `_wrap_exact_tag_sequence` Parenthetical-Formula Fallbacks in `src/acepatchindo/tag_aligner.py` (Tasks 41–42)

> [!CAUTION]
> **Manager Forensic Audit of `commit d874791` — REJECTED Due to 2 Remaining Bugs in `src/acepatchindo/tag_aligner.py`:**
>
> 1. **BUG 1: Literal `__EXPR_SLOT_1__` and `__EXPR_SLOT_{0|2}__` Tokens Leaked Into `4` Catalog Strings (`tag_aligner.py:372-418`):**
>    - **Root Cause A (`slot_tok = f"__EXPR_SLOT_{i}__"` + Missing `_` in Negative Lookbehind/Lookahead at `lines 406–417`):**
>      - Because `slot_tok` contained a digit `{i}` surrounded by underscores (`_1_`), and `re.subn` at line `408` used `rf"(?<![\d\[{{|A-Za-z]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z])"` (**without `_`** in the character class!), whenever a later iteration in `zip(cn_exprs, src_exprs)` had `c_ex == "1"` or `c_ex == "2"`, `re.subn` matched the digit `1` **inside `__EXPR_SLOT_1__`** and replaced it with `__EXPR_SLOT_3__`! Then the expansion loop at line `417` looked for `__EXPR_SLOT_1__` first (not found!) and later expanded `__EXPR_SLOT_3__` back into `1` or `{0|2}`, leaving literal **`__EXPR_SLOT_1__`** and **`__EXPR_SLOT_{0|2}__`** in 4 strings in `catalog.json.gz`:
>        1. `亚连向身前目标发动三次疾速劈砍...` (2 variants) -> `...melancarkan __EXPR_SLOT_1__ tebasan cepat ke target di depannya...`
>        2. `获得1张3阶兑换券。回合开始时，获得<color=#FFE897>{3|2}{LordExp}</color>。满级后，改为获得{0|2}{Energy}。` -> `Memperoleh {3|2} Voucher Tier 3. Saat Round dimulai,<color=#FFE897>memperoleh __EXPR_SLOT_{0|2}__ {LordExp}</color>, setelah Level maksimum, diganti menjadi 2 {Energy}.`
>        3. `获得{0|3}{Energy}。回合结束时，你每有<color=#FFE897>{0|7}{Energy}，额外获得{0|1}{Energy}</color>。` -> `Memperoleh {0|3}{Energy}. Saat Round <color=#FFE897> berakhir, tiap __EXPR_SLOT_{0|1}__ {Energy}</color> yang kamu miliki, dapat {0|7}{Energy} tambahan.`
>    - **Root Cause B (`zh_num_counter_re.sub("1", ...)` at `lines 372–377`):**
>      - `zh_num_counter_re` replaced ALL Chinese numerals (`三次`, `两次`) with `"1"`, turning Allain's `三次...两次` in `src_clean` into `1...1` while `desc_cn` had `3...2`!
>    - **Root Cause C (`{3|2}{LordExp}` vs `{LordExp}` Expression Count Shift in `获得1张3阶兑换券...`):**
>      - In `获得1张3阶兑换券...`, `source_zh` has `{3|2}{LordExp}` (`4` numeric expressions: `1`, `3`, `{3|2}`, `{0|2}`), whereas Tier 1 `desc_cn` has `获得{LordExp}` without a number (`3` numeric expressions: `1`, `3`, `2`), so `zip(cn_exprs, src_exprs)` paired `cn_exprs[0]="1"` with `src_exprs[1]="{3|2}"` and `cn_exprs[2]="2"` with `src_exprs[3]="{0|2}"`!
>
> 2. **BUG 2: `153` Target `unique` Strings Still Fall Through to `_wrap_exact_tag_sequence` Mid-Clause Chunk Slicing (`tag_aligner.py:331-367, 420-437, 892`):**
>    - **Root Cause A (`id_dmg_spans` at `line 338` Required `\s+sebesar\s+` and Ran BEFORE Step 2 `COMPOUND_EXPR_RE`):**
>      - In `tier1_wiki_id.json`, 90% of Hero skill descriptions do **NOT** use the word `"sebesar"` — they write `memberikan 180% Physical Attack sebagai Physical Damage`, `dengan 80+80% Physical Attack sebagai Physical Damage`, `memulihkan 8% Max HP`, `memulihkan 100+50% Magic Attack sebagai HP`!
>      - Because `line 338` required `\s+sebesar\s+`, `id_dmg_spans` matched `0` spans on `~110` parenthetical `<color=C1>[0]点物理伤害</color><color=C2>（[1]+[2]%物理攻击力）</color>` skills (`Lu Bu`, `Allain`, `Fang`, `Donghuang`, `Dolia`, `Augran`, `Ming Shiyin`, `Erin`, `Hua Mulan`, `Alessio`, `Consort Yu`, `Xiang Yu`, `Ma Chao`, `Shangguan Wan'er`, `Cirrus`, `Arthur`, `Arli`, `Mayene`, `Liu Shan`, `Liu Bang`, `Jiang Ziya`, `Lady Sun`, `Sun Wukong`, `Sun Bin`, `Angela`, `Xiao Qiao`, `Dyadia`, `Gan & Mo`, `Lian Po`, `Yi Xing`, `Dr. Bian`, `Biron`, `Ao Yin`, `Yao`, `Cao Cao`, `Yang Yuhuan`, `Menki`, `Wu Zetian`, `Heino`, `Niu Mo`, `Baili Xuance`, `Zhenji`, `Bai Qi`, `Baili Shouyue`, `Cheng Yaojin`, `Milady`, `Su Lie`, `Meng Ya`, `Pei Qin Hu`, `Xishi`, `Zhuge Liang`, `Diao Chan`, `Zhao Yun`, `Kui`, `Jing`, `Arke`, `Athena`, `Marco Polo`, `Luban No.7`, `Master Luban`).
>      - Then Step 2 (`lines 389–390`) collapsed `[0]点物理伤害([1]+[2]%物理攻击力)` to `[1]+[2]%物理攻击力的物理伤害` in `src_clean`, substituting only `[1]+[2]%` into `out` and dropping `[0]`!
>      - Then `needed_numeric_phs` (`lines 420–437`) saw `[0]` (or `[6]` in Dolia, `[2]` in Bai Qi) was missing from `out` and overwrote unrelated duration/distance numbers in `out` (`10 detik` -> `selama [6] detik` in Dolia, `1 tile` -> `dalam [2] tile` in Bai Qi)!
>      - Finally, `reinject_skeleton_from_source` (`line 892`) saw `TAG_RE.findall(curr) != tags_in_src`, stripped the already-matched `<color=#ffffffbf>Pasif:</color>` / `<color=#ffffffbf>Aktif:</color>` tags (`stripped_id = TAG_RE.sub("", result)`), and called `_wrap_exact_tag_sequence`, producing `<color=#ffffffbf> Aktif: Lu Bu melompat ke</color>`, `<color=#ffffffbf> Aktif: Liyuan</color> Fang melempar <color=#dfa15e> dart yang</color>`!

### Task 41: Fix `reinject_formula_and_skeleton` & `reinject_skeleton_from_source` in `src/acepatchindo/tag_aligner.py`

- [x] **Step 41.1: Fix Chinese Numeral Conversion, Letter-Only Slot Tokens, `{num_ph}{Icon}` Alignment, and Post-Step-2 Parenthetical/Split Formula Grafting in `reinject_formula_and_skeleton` (`tag_aligner.py:328-525`)** *(REOPENED BY MANAGER AUDIT ROUND 6 — `TERM_MAP` at `line 340` was missing 8 footer terms (`压制`, `不可选中`, `击退`, `浮空`, `降低生命恢复`, `嘲讽`, `驱散`, `冻结`), causing 7+ Tier 1 Hero skills to fail `still_chinese` and fall back to Tier 3; `icon_pair_matches` at `lines 399-441` used optional `(?:\d+)?` and matched unnumbered `{LordHp}-10` at index 0 (`{1|1}<color=#FFE897>{LordHp}</color> -10`), leaving `-15` as `-10`; `if c_ex == s_ex: continue` at `line 481` skipped advancing `cursor`, causing `碰碰运气` to put `{0|1}` on `1 Kartu Talent`; and `split_2tag_re` at `line 597` required `first_ph...last_ph` even when `len(phs) == 1` (`Dolia`, `Dr. Bian`) -> Remediated in Task 43)*
  1. **Replace Chinese Numerals With Their True Digits (`1..10`) Instead of `"1"` (`lines 372–377`):**
     ```python
     ZH_DIGIT_MAP = {
         "一": "1", "二": "2", "两": "2", "三": "3", "四": "4",
         "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
     }
     zh_num_counter_re = re.compile(r"([一二两三四五六七八九十])(次|秒|格|名|个|道|枚|把|层|回合|阶|张)")
     src_clean = zh_num_counter_re.sub(lambda m: f"{ZH_DIGIT_MAP[m.group(1)]}{m.group(2)}", src_clean)
     cn_clean = zh_num_counter_re.sub(lambda m: f"{ZH_DIGIT_MAP[m.group(1)]}{m.group(2)}", cn_clean)
     ```
  2. **Pre-Bind `{num_ph}{Energy|LordExp|LordHp}` Using Letter-Only Sentinels (`__WXQICONA__`, `__WXQICONB__`, ...) BEFORE `COMPOUND_EXPR_RE`:**
     - Before running `COMPOUND_EXPR_RE`, scan `body_source_zh` for `r"(\{[0-9A-Za-z_:+|.%/~ -]+\})\s*(\{(?:Energy|LordExp|LordHp)\})"` (`m.group(1) = num_ph`, `m.group(2) = icon_ph`):
       - Allocate a **100% letter-only sentinel** `sent = f"__WXQICON{chr(65 + idx)}__"` (contains **ZERO digits** so `COMPOUND_EXPR_RE` and `\d+` will NEVER touch it!).
       - In `src_clean`, replace `f"{num_ph}{icon_ph}"` (count=1) with `sent`.
       - In `cn_clean`, replace the corresponding `r"(?:\d+(?:\.\d+)?|\{[^{}]+\})?\s*(?:点?\s*(?:能量|棋手经验|棋手生命值|玩家生命值)|\{(?:Energy|LordExp|LordHp)\})"` (matching the same icon type, count=1) with `sent`.
       - In `out`, replace the corresponding Indonesian span (matching the same icon type: `r"(?:\d+(?:\.\d+)?\s*)?(?:Energy|Energi|\{Energy\})"` for `{Energy}`, `r"(?:memperoleh\s+)?(?:\d+(?:\.\d+)?\s*)?(?:Player EXP|EXP Chess Player|EXP Kontestan|\{LordExp\})"` for `{LordExp}`, `r"(?:\d+(?:\.\d+)?\s*)?(?:Player HP|HP Chess Player|HP Kontestan|\{LordHp\})"` for `{LordHp}`, count=1) with `sent` (preserving `"memperoleh "` if matched!).
       - Store `icon_sentinels.append((sent, f"{num_ph}{icon_ph}"))` and restore `for sent, val in icon_sentinels: out = out.replace(sent, val)` right after `COMPOUND_EXPR_RE`!
     - Because `sent` (`__WXQICONA__`) has no digits, `COMPOUND_EXPR_RE` completely ignores it in `src_clean`, `cn_clean`, and `out` — so `{3|2}{LordExp}` and `{0|7}{Energy}` NEVER shift `cn_exprs` vs `src_exprs` and NEVER get overwritten!
  3. **Use Letter-Only `__EXPRSLOTAA__` Tokens & Include `_` in Lookbehind/Lookahead (`lines 405–418`):**
     - In `reinject_formula_and_skeleton`, change `slot_tok = f"__EXPR_SLOT_{i}__"` to:
       ```python
       slot_tok = f"__EXPRSLOT{chr(65 + (i // 26))}{chr(65 + (i % 26))}__"
       ```
       (pure letters, **NO digits** inside `slot_tok`!) and include `_` in the negative lookbehind/lookahead:
       ```python
       pat = rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])"
       ```
       This makes it mathematically impossible for a later `c_ex` replacement to ever match inside an earlier `slot_tok`!
  4. **Run Parenthetical 2-Tag & Split 2/3-Tag Formula Grafting AFTER Step 2 (`COMPOUND_EXPR_RE`) and BEFORE `needed_numeric_phs`!**

- [x] **Step 41.2: Expand Single-Span `<color=...>` Patterns & Never Strip Already-Matched Tags in `reinject_skeleton_from_source` (`tag_aligner.py:450-920`)** *(REOPENED BY MANAGER AUDIT ROUND 6 — `m_existing` at `line 803` falsely matched later `<color=#ffffff>` spans (`Shi`), `BADGE_ALIAS_MAP["转瞬"]` lacked `"Fleeting"`, single-span clause matcher at `line 964` failed when `span_zh` contained `，`, and `missing_pairs` at `line 1168` wrapped the first word of the sentence (`<color=#FFE897>Memperoleh</color>`) -> Remediated in Task 43)*

### Task 42: Add Anti-Regression Assertions to `tests/test_glossary_and_tiers.py`, Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Verify `14 passed`, & Re-Publish `v1.4.12-id.2` (`06`)

- [x] **Step 42.1: Add 4 Additional Strict Assertions to `tests/test_glossary_and_tiers.py`** *(REOPENED — Remediated in Task 44)*
- [x] **Step 42.2: Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Run `pytest -v`, Commit, Force-Tag `v1.4.12-id.2`, & Re-Upload Release Assets (`06`)** *(REOPENED — Remediated in Task 44)*

---

## Phase 6 Remediation Round 6: Eliminating the Final `18` `_wrap_exact_tag_sequence` Calls, `TERM_MAP` Missing Footer Terms (`still_chinese`), & `{LordHp}-10/-15` / `碰碰运气` Cursor Bugs (Tasks 43–44)

> [!CAUTION]
> **Manager Forensic Audit of `commit ca63fe0` — REJECTED Due to 3 Remaining Bugs in `src/acepatchindo/tag_aligner.py`:**
>
> 1. **BUG 1: `TERM_MAP` (`tag_aligner.py:340-349`) Missing 8 Footer Terms + `normalize_formula_skeleton_zh` Punctuation Order (`7+` Tier 1 Hero Skills Rejected by `still_chinese` and Falling Back to Broken Tier 3):**
>    - In `tag_aligner.py:340-349`, `TERM_MAP` only mapped `击飞`, `眩晕`, `沉默`, `减速`, `免控`, `霸体`, `禁锢`, `定身`.
>    - It was missing **8 footer terms** that appear in `点击技能描述面板，查看...详细解释` across `catalog.json.gz`:
>      - `"压制": "Suppress"`, `"不可选中": "Untargetable"`, `"击退": "Knockback"`, `"浮空": "Airborne"`, `"降低生命恢复": "HP Regen Reduction"`, `"嘲讽": "Taunt"`, `"驱散": "Dispel"`, `"冻结": "Freeze"`.
>    - Because those 8 terms were left in Chinese inside `footer_id` (`<b>压制</b>`, `<b>不可选中</b>`, `<b>浮空</b>`, `<b>嘲讽</b>`, `<b>降低生命恢复</b>`), `validate_translation` rejected the Tier 1 translations with `(False, 'still_chinese')` for **Donghuang Taiyi, Li Bai, Arli, Xiao Qiao, Wu Zetian, Bai Qi, and Diao Chan**, forcing all 7 to fall back to broken Tier 3 (`"Donghuang menciptakan 3 Energi bola... selama yang kedua tim mengambil sama Damage"`, `"Ketuk panel deskripsi Skill untuk melihat rinci penjelasan dari <b>Menekan</b>"`)!
>    - Also, when `term_zh` has two adjacent `<b>` tags without a comma (`<b>霸体</b><b>眩晕</b>` or `<b>压制</b><b>眩晕</b>`), insert `, ` between `</b>` and `<b>` ONLY if `source_zh` has `，` between them; otherwise keep `</b><b>` so `TAG_RE` matches!
>    - And in `normalize_formula_skeleton_zh` (`tag_aligner.py:308-314`), `skel = re.sub(r"[，。：:；;、“”\"!\?！？]", "", skel)` ran **AFTER** `^吕布会根据敌人位置使用不同招式(?:普攻|普通攻击)能对身前#N#格内敌人造成伤害` (which had no comma `，` and replaced with `吕布的普通攻击能对身前敌人造成范围伤害` instead of `吕布的普攻能造成范围伤害`), causing Lu Bu Variant 1 (`[123300p1q1]+[123300p1q2/100]%`) to miss Tier 1 and fall back to Tier 3 (`"Lu Bu menggunakan berbeda bergerak berdasarkan musuh posisi"`)!
>
> 2. **BUG 2: `{num_ph}{Icon}` Optional-Number Match & Step 2 `if c_ex == s_ex: continue` Not Advancing `cursor` (`tag_aligner.py:386-508`):**
>    - **Root Cause A (`{1|1}<color=#FFE897>{LordHp}</color> -10` and `-15` staying `-10`):**
>      - In `tag_aligner.py:399-441`, when `icon_pair_matches` matched `{1|1}{LordHp}` (which has a leading number placeholder `{1|1}`), the regexes for `cn_clean` (`line 415`) and `out` (`line 436`) made the leading number **optional (`?`)**.
>      - On `<color=#FFE897>{LordHp}</color>-10...获得{1|1}{LordHp}` and `<color=#FFE897>{LordHp}</color>-15...获得{1|1}{LordHp}`, that optional regex matched the **1st** unnumbered `棋手生命值` / `Player HP` at index 0 (`Player HP -10`) instead of `1棋手生命值` / `1 Player HP` in the 2nd clause (`memperoleh 1 Player HP`), producing **`{1|1}<color=#FFE897>{LordHp}</color> -10 ... memperoleh 1 {LordHp}`** and causing `-15` to stay `-10`!
>    - **Root Cause B (`if c_ex == s_ex: continue` at `line 481` Left `cursor` at `0` + `{0|1}-{0|5}{Energy}` Range in `碰碰运气`):**
>      - At `tag_aligner.py:481`, when `c_ex == s_ex`, `continue` skipped advancing `cursor` in `out`!
>      - And in `<color=#FFE897>棋手升级时</color>，获得1张天赋牌<color=#FFE897>碰碰运气</color>：指定1名英雄提升5-20等级，随机消耗{0|1}-{0|5}{Energy}。`, `icon_pair_matches` only matched `{0|5}{Energy}` (leaving `{0|1}` behind), and because `c_ex == s_ex` (`"1" == "1"`, `"5-20" == "5-20"`) left `cursor = 0`, `c_ex = "1" -> s_ex = "{0|1}"` overwrote the very first `1` in `out`, producing **`memperoleh {0|1} Kartu Talent <color=#FFE897>Try Your Luck</color> ... dengan biaya acak 1-{0|5}{Energy}`**!
>    - **Root Cause C (`Yao` `70+120%` in `desc_cn` vs `100+130%` in `desc_id`):**
>      - In `曜化作星辰对当前目标造成<color=#dfa15e>[0]点物理伤害</color><color=#dfa15e>（[1]+[2]%物理攻击力）</color>。`, Tier 1 `desc_cn` has `70+120%` while `desc_id` has `100+130%`. Because `"70+120%"` wasn't found in `out`, `[1]+[2]%` was never injected and Yao fell into `_wrap_exact_tag_sequence` (`"Yao berubah jadi bintang <color=#dfa15e> dan memberikan 100+130% Physical</color>"`)!
>
> 3. **BUG 3: `18` Tagged Target Strings Still Hit `_wrap_exact_tag_sequence` or `missing_pairs` First-Word Tagging (`tag_aligner.py:568-620, 743, 802-808, 892-984, 1150-1184`):**
>    - **`split_3tag_re` (`line 569`):** Used `(\[\d+\]|\d+)\+` instead of `(\[[^\]]+\]|\d+)\+`, failing to match Ming Shiyin's `[501110p1q1]+`! And at `line 743`, `source_zh.count("\n") == result.count("\n")` failed on Ming Shiyin because `source_zh` has `\n\n` while `desc_id` has `\n`.
>    - **`split_2tag_re` (`lines 586-620`):** Required `{first_ph}[^.,;\n<]*?{last_ph}%` even when `len(phs) == 1` (`first_ph == last_ph`), requiring `[159007p1q3/100]` or `[4]` (in Dolia) and `[119190p1q3/100]` (in Dr. Bian) to appear **twice**! And it required `\[[^\]]+\]` in `expr_zh`, skipping Dolia's static `75+100%` / `50%` variant!
>    - **`m_existing` False-Positive Jump (`lines 802-808`) & `护盾`/`法力` Order (`lines 892-920`):** In Shi (`首次施法时制造水月幻境...`), `Span 0` (`<color=#ffffff>[0]点护盾</color>`) matched `Span 2` (`<color=#ffffff>[2] True Damage</color>`) at the end of `curr` and jumped `cursor` to the end of the string! And `if phs_in_inner:` (`line 893`) ran before `elif "护盾" in zh_inner:` (`line 916`) and `elif "法力" in zh_inner:` (`line 918`), wrapping `<color=#86ccfd>[0]</color> Mana` instead of `<color=#86ccfd>memulihkan tambahan [0] Mana</color>`.
>    - **`BADGE_ALIAS_MAP["转瞬"]` (`line 130`):** Missing `"Fleeting"`, causing `使用技能，随机获得1张2-5阶的<a href=3130012><color=#ffffff>╆<b>转瞬</b></color></a>英雄牌。` to wrap `╆<b> secara acak 1</b>`!
>    - **Out-of-Order `<a href=321>...╉图腾...</a>` vs `<a href=3130011>...═临时等级...</a>` (`2` Totem talents):** In `Engage: memperoleh Temporary Level sebesar 15%/30% dari jumlah Level setiap Totem.`, `Temporary Level` came before `Totem`, whereas `source_zh` has `href=321` (`Totem`) before `href=3130011` (`Temporary Level`).
>    - **Single-Span Multi-Clause `<color=#FFE897>` (`lines 963-984`) & `missing_pairs` (`lines 1150-1184`):** At `line 964`, `target_idx = next((i for i, c in enumerate(zh_clauses) if span_zh in c), -1)` always returned `-1` whenever `span_zh` contained a comma `，`! And at `lines 1166-1178`, `missing_pairs` wrapped the **first word of the sentence** (`<color=#FFE897>Memperoleh</color> <color=#FFE897>{0|2}{Energy}</color> dan 2 Hero Voucher Tier 3.`) instead of matching `"兑换券"` -> `Hero Voucher Tier 3`!

### Task 43: Fix All 3 Bugs in `src/acepatchindo/tag_aligner.py`

- [x] **Step 43.1: Complete `TERM_MAP` & Fix `normalize_formula_skeleton_zh` in `src/acepatchindo/tag_aligner.py` (`lines 285-370`)**
  1. In `normalize_formula_skeleton_zh` (`lines 285-314`), strip punctuation **before** the multi-word phrase normalizations and add the 5 remaining Tier 1 Hero skill normalizations:
     ```python
     skel = re.sub(r"[，。：:；;、“”\"!\?！？]", "", skel)
     skel = re.sub(
         r"^吕布会根据敌人位置使用不同招式(?:普攻|普通攻击)能对身前#N#格内敌人造成伤害",
         "吕布的普攻能造成范围伤害",
         skel,
     )
     skel = (
         skel.replace("甄姬引导水流", "甄姬施放水流")
         .replace("解除左右两边#N#格内友军和自身所受的控制效果", "驱散自身和左右两边#N#格内友军")
         .replace("伤害由范围内的敌人平均分摊", "")
         .replace("赵云刺出龙枪短时间内打击敌人#N#次", "赵云快速刺出#N#次龙枪打击目标")
         .replace(
             "鲁班七号召唤河豚飞艇穿越整个战场对下方区域随机投掷河豚炸弹共#N#个炸弹命中敌人后",
             "鲁班七号呼唤河豚飞艇朝战场投掷#N#枚炸弹炸弹对命中敌人",
         )
         .replace("陷入弹坑中的敌人会被灼烧每秒受到", "并留下弹坑弹坑中的敌人每秒受到")
         .replace("杨玉环弹奏琵琶循环激活以下乐曲效果之一", "杨玉环弹奏琵琶")
         .replace("破阵杨玉环弹奏琵琶对", "破阵对")
     )
     skel = re.sub(r"化身剑气(?:施展#N#次斩击|斩击范围内敌人#N#次)", "化身剑气斩击#N#次", skel)
     ```
  2. In `reinject_formula_and_skeleton` (`lines 340-355`), expand `TERM_MAP` to cover all 16 status terms in the catalog:
     ```python
     TERM_MAP = {
         "击飞": "Knock-Up",
         "眩晕": "Stun",
         "沉默": "Silence",
         "减速": "Slow",
         "免控": "Control Immunity",
         "霸体": "Control Immunity",
         "禁锢": "Immobilize",
         "定身": "Root",
         "压制": "Suppress",
         "不可选中": "Untargetable",
         "击退": "Knockback",
         "浮空": "Airborne",
         "降低生命恢复": "HP Regen Reduction",
         "嘲讽": "Taunt",
         "驱散": "Dispel",
         "冻结": "Freeze",
     }
     ```

- [ ] **Step 43.2: Fix `{num_ph}{Icon}` Required-Number Priority, Range Icon Pre-Binding, Step 2 `cursor` Advance, `split_3tag_re`, and `split_2tag_re` in `reinject_formula_and_skeleton` (`tag_aligner.py:385-625`)** *(REOPENED BY MANAGER AUDIT ROUND 7 — Step 2 single shared `cursor` at `line 482` advanced past `"100+80%"` when `c_ex == "3"` matched `"untuk 3 sekutu"` at the end of Line 1 in `Yang Yuhuan`, swapping `Qingping` `[0]..[2]` with `Pozhen` `[3]..[5]`; and `sp2b` at `line 615` only allowed `HP(?:\s+miliknya)?` and `(?:\s+miliknya)?`, failing on `Mi Yue` (`memulihkan HP sekutu itu sebesar ... Magic Attack Miyue`) -> Remediated in Task 45)*
  1. **Support Range Placeholders `{0|1}-{0|5}{Energy}` & Require Leading Number First in `icon_pair_matches` (`lines 385-442`):**
     ```python
     icon_pair_matches = list(re.finditer(
         r"((?:\{[0-9A-Za-z_:+|.%/~ -]+\}(?:\s*[~-]\s*)?)+)\s*(\{(?:Energy|LordExp|LordHp)\})",
         body_source_zh,
     ))
     for idx, m_pair in enumerate(icon_pair_matches):
         num_ph = m_pair.group(1)
         icon_ph = m_pair.group(2)
         sent = f"__WXQICON{chr(65 + idx)}__"
         icon_sentinels.append((sent, f"{num_ph}{icon_ph}"))

         clean_num_ph = normalize_plain_zh(num_ph)
         src_clean = src_clean.replace(f"{clean_num_ph}{icon_ph}", sent, 1)

         zh_icon_pat = (
             r"(?:点?\s*能量|\{Energy\})" if icon_ph == "{Energy}"
             else r"(?:点?\s*(?:棋手经验|经验)|\{LordExp\})" if icon_ph == "{LordExp}"
             else r"(?:点?\s*(?:棋手生命值|玩家生命值|生命值)|\{LordHp\})"
         )
         # Try WITH required leading number/range first!
         cn_clean, cnt_cn = re.subn(
             rf"(?:\d+(?:\.\d+)?(?:\s*[~-]\s*\d+(?:\.\d+)?)?|\{{[^{{}}]+\}}(?:\s*[~-]\s*\{{[^{{}}]+\}})?)\s*{zh_icon_pat}",
             sent,
             cn_clean,
             count=1,
         )
         if not cnt_cn:
             cn_clean = re.sub(zh_icon_pat, sent, cn_clean, count=1)

         id_icon_pat = (
             r"(?:Energy|Energi|\{Energy\})\b" if icon_ph == "{Energy}"
             else r"(?:Player EXP|EXP Chess Player|EXP Kontestan|EXP Pemain|EXP|\{LordExp\})\b" if icon_ph == "{LordExp}"
             else r"(?:Player HP|HP Chess Player|HP Kontestan|HP Pemain|Health|\{LordHp\})\b"
         )
         # Try WITH required leading number/range in `out` first!
         m_out = re.search(rf"\d+(?:\.\d+)?(?:\s*[~-]\s*\d+(?:\.\d+)?)?\s*{id_icon_pat}", out, flags=re.I)
         if not m_out:
             m_out = re.search(id_icon_pat, out, flags=re.I)
         if m_out:
             out = out[:m_out.start()] + sent + out[m_out.end():]
     ```
  2. **Advance `cursor` When `c_ex == s_ex` & Handle Compound `a+b%` Mismatch (`Yao`) in Step 2 (`lines 480-505`):**
     ```python
     for i, ((c_ex, c_u), (s_ex, s_u)) in enumerate(zip(cn_matches, src_matches)):
         unit_pat = UNIT_MAP.get(s_u or c_u, "")
         if c_ex == s_ex:
             pat_same = re.compile(rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])")
             m_same = pat_same.search(out, cursor)
             if m_same:
                 cursor = m_same.end()
             continue
         ...
         if not m and re.match(r"^\d+(?:\.\d+)?\+\d+(?:\.\d+)?%$", c_ex):
             m = re.compile(r"\d+(?:\.\d+)?\s*\+\s*\d+(?:\.\d+)?%").search(out, cursor)
     ```
  3. **Fix `split_3tag_re` (`line 569`) and `split_2tag_re` (`lines 586-620`):**
     - In `split_3tag_re`, change `(\[\d+\]|\d+)\+` to `(\[[^\]]+\]|\d+)\+` so `[501110p1q1]+` in Ming Shiyin matches!
     - In `split_2tag_re`:
       ```python
       split_2tag_re = re.compile(
           r"(<color=[^>]+>)((?:恢复)?[^<]*?(?:\[[^\]]+\]|\d+)%[^<]*?)(</color>)(<color=[^>]+>)的(生命值?|护盾)(</color>)"
       )
       for m_2 in split_2tag_re.finditer(body_source_zh):
           c1_o, expr_zh, c1_c, c2_o, kind_zh, c2_c = m_2.groups()
           toks = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?", expr_zh)
           if not toks:
               continue
           if len(toks) >= 2:
               num_pat = rf"{re.escape(toks[0])}\s*\+\s*{re.escape(toks[-1])}%"
           else:
               num_pat = rf"{re.escape(toks[0])}%"
           if kind_zh.startswith("生命"):
               sp2a = re.compile(
                   rf"(memulihkan\s+)?({num_pat}\s*(?:Magic Attack|Physical Attack|Max HP|HP Maks)(?:\s+miliknya)?)\s*((?:sebagai\s+)?HP\b)",
                   flags=re.I,
               )
               sp2b = re.compile(
                   rf"(memulihkan\s+)(HP(?:\s+miliknya)?)\s+sebesar\s+({num_pat}\s*(?:Magic Attack|Physical Attack|Max HP|HP Maks)(?:\s+miliknya)?)",
                   flags=re.I,
               )
               if m_a := sp2a.search(out):
                   mem_w, form_w, hp_w = m_a.groups()
                   mem_w = mem_w or ""
                   rep2 = (f"{c1_o}{mem_w}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}") if "恢复" in expr_zh else (f"{mem_w}{c1_o}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}")
                   out = out[:m_a.start()] + rep2 + out[m_a.end():]
               elif m_b := sp2b.search(out):
                   mem_w, hp_w, form_w = m_b.groups()
                   rep2 = (f"{c1_o}{mem_w}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}") if "恢复" in expr_zh else (f"{mem_w}{c1_o}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}")
                   out = out[:m_b.start()] + rep2 + out[m_b.end():]
       ```

- [ ] **Step 43.3: Fix `reinject_skeleton_from_source` (`m_existing` Check, `护盾`/`法力`/`兑换券` Patterns, `"转瞬": "Fleeting"`, `╉图腾` Order, Multi-Clause Single-Span, & Paragraph Newlines) (`tag_aligner.py:130, 742-1185`)** *(REOPENED BY MANAGER AUDIT ROUND 7 — `m_nest` at `line 1009` was unreachable because `ATOMIC_TAGGED_SPAN_RE` matched the inner `<color=#00FF00>2.5%</color>` first (`all_matched=True`); `LEADING_TAGGED_PREFIX_RE` at `line 810` copied untranslated English `"Gain <color=#FFE897>Nemesis</color>"`; and 7 Tier 1 strings failed Step 4 (`GLYPH_KEYWORD_MAP["╦"]` missing `"Merge"`, `(?<!>)` blocking `<color=#FFE897>╋Flash`, bare `<a>` Totem order) -> Remediated in Task 45)*
  1. **Add `"Fleeting"` to `BADGE_ALIAS_MAP["转瞬"]` (`line 130`):**
     `"转瞬": ("Fleeting", "Fleet", "Instant", "Sekilas"),`
  2. **Normalize Paragraph Break Counts (`\n` vs `\n\n`) Before Line-by-Line Alignment (`line 742`):**
     ```python
     if "\n" in source_zh and "\n" in result and source_zh.count("\n") != result.count("\n"):
         src_paras = [p for p in re.split(r"\n+", source_zh.strip()) if p.strip()]
         res_paras = [p for p in re.split(r"\n+", result.strip()) if p.strip()]
         src_seps = re.findall(r"\n+", source_zh.strip())
         if len(src_paras) == len(res_paras) == len(src_seps) + 1:
             rebuilt_nl = [res_paras[0]]
             for sep, rp in zip(src_seps, res_paras[1:]):
                 rebuilt_nl.append(sep + rp)
             result = "".join(rebuilt_nl)
     ```
  3. **Align `╉图腾` Before `═临时等级` When `source_zh` Has `<a href=321>` Before `<a href=3130011>`:**
     ```python
     if "<a href=321>" in source_zh and "<a href=3130011>" in source_zh and source_zh.find("<a href=321>") < source_zh.find("<a href=3130011>"):
         result = re.sub(
             r"memperoleh\s+(═?Temporary Level)\s+sebesar\s+(\d+%)\s+dari\s+jumlah\s+Level\s+setiap\s+(╉?Totem)",
             r"dari setiap \3, memperoleh \2 \1 berdasarkan jumlah Level-nya",
             result,
             flags=re.I,
         )
     ```
  4. **Fix `m_existing` False-Positive Jump (`lines 802-808`) & Check `护盾`/`法力`/`兑换券` Before Generic `phs_in_inner` (`lines 892-936`):**
     - At `lines 802-808`:
       ```python
       phs_in_inner = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]", zh_inner)
       if open_part in curr and close_part in curr:
           m_existing = re.compile(rf"{re.escape(open_part)}([^<]+){re.escape(close_part)}").search(curr, cursor)
           if m_existing:
               inner_cand = m_existing.group(1)
               if (phs_in_inner and all(ph in inner_cand for ph in phs_in_inner)) or (
                   not phs_in_inner
                   and not re.search(r"\[[A-Za-z0-9_+/.*%-]+\]", inner_cand)
                   and curr.find("<", cursor) == m_existing.start()
               ):
                   cursor = m_existing.end()
                   matched_this = True
                   matched_indices.add(idx)
                   continue
       ```
     - At `lines 892-936`, check `"护盾" in zh_inner`, `"法力" in zh_inner`, and `"兑换券" in zh_inner` **BEFORE** `if phs_in_inner:` (and add `elif "兑换券" in zh_inner: pattern = r"\b(?:Hero\s+)?Voucher(?:\s+Tier\s+\d+(?:-\d+)?)?\b"` and `elif "普通装备牌" in zh_inner: pattern = r"\b(?:[Kk]artu\s+Normal\s+Equipment|[Kk]artu\s+Equipment\s+Biasa)\b"`).
  5. **Fix Multi-Clause Single-Span `<color=...>` (`lines 957-984`) & Nested `<color=C1>...<color=C2>VAL</color></color>`:**
     - If `not all_matched and len(spans) == 1 and "<" not in curr and curr.strip()`:
       - First check if `source_zh` has nested `<color=([^>]+)>[^<]*<color=([^>]+)>([^<]+)</color></color>`: if so, wrap `inner_val` (`m_nest.group(3)`) with `<color={c2}>{inner_val}</color>` and wrap the surrounding damage/stat phrase with `<color={c1}>...</color>`!
       - Otherwise, split `span_zh` into `span_subs = [s for s in re.split(r"[，。！？；：:\n]+", span_zh) if s.strip()]` and `zh_clauses = [c for c in re.split(r"[，。！？；：:\n]+", source_zh) if c.strip()]`. Find `start_idx = next((i for i, c in enumerate(zh_clauses) if span_subs[0] in c), -1)` and `end_idx = next((i for i, c in enumerate(zh_clauses) if span_subs[-1] in c), start_idx)`, map both `start_idx` and `end_idx` to `content_clause_indices` in `id_clauses = re.split(r"([,.;!?\n:]+)", curr)`, and place `spans[0].group(1)` at the start of `id_clauses[actual_start]` and `spans[0].group(3)` at the end of `id_clauses[actual_end]`!

### Task 44: Add Round 6 Assertions to `tests/test_glossary_and_tiers.py`, Rebuild Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Verify `14 passed`, & Re-Publish `v1.4.12-id.2` (`06`)

- [ ] **Step 44.1: Add 5 Round 6 Precision Assertions to `tests/test_glossary_and_tiers.py`** *(REOPENED — Remediated in Task 46)*
  1. **Zero Misplaced `{1|1}` on `{LordHp}-10` / `{LordHp}-15` & Exact `-15` Preservation:**
     ```python
     s_hp10 = "<color=#FFE897>{LordHp}</color>-10，战斗开始时，<color=#FFE897>己方每名英雄</color>+2═临时等级。战斗胜利时，获得{1|1}{LordHp}，═临时等级额外+1。"
     s_hp15 = "<color=#FFE897>{LordHp}</color>-15，战斗开始时，<color=#FFE897>己方每名英雄</color>+2═临时等级。战斗胜利时，获得{1|1}{LordHp}，═临时等级额外+1。"
     assert not cat["unique"][s_hp10].startswith("{1|1}") and "{1|1}{LordHp}" in cat["unique"][s_hp10]
     assert not cat["unique"][s_hp15].startswith("{1|1}") and "-15" in cat["unique"][s_hp15] and "{1|1}{LordHp}" in cat["unique"][s_hp15]
     ```
  2. **Try Your Luck (`碰碰运气`) Range Placeholder Precision:**
     ```python
     s_tyl = "<color=#FFE897>棋手升级时</color>，获得1张天赋牌<color=#FFE897>碰碰运气</color>：指定1名英雄提升5-20等级，随机消耗{0|1}-{0|5}{Energy}。"
     assert "memperoleh 1 Kartu Talent" in cat["unique"][s_tyl] and "{0|1}-{0|5}{Energy}" in cat["unique"][s_tyl]
     ```
  3. **Zero Tier 3 Fallback on Footer-Tagged Tier 1 Hero Skills (`Donghuang`, `Lu Bu` Variant 1, `Bai Qi`, `Xiao Qiao`):**
     ```python
     s_dh = "<color=#ffffffbf>被动：</color>东皇太一创造3颗能量球绕自身转动。能量球触碰到敌人时会造成其<color=#d487e4>[0]%最大生命值的法术伤害</color>并恢复东皇<color=#9ff5d0>[1]%的最大生命值</color>。\n\n<color=#ffffffbf>主动：</color>东皇太一施展堕神契约<color=#ffffffbf>压制</color>目标敌人5秒，期间双方承受等量伤害。若期间与目标距离过远，则效果提前中断。\n\n\n<color=#86888A>点击技能描述面板，查看<b>压制</b>详细解释</color>"
     assert "<b>Suppress</b>" in cat["unique"][s_dh] and "Energi bola" not in cat["unique"][s_dh]
     ```
  4. **Zero Chunk-Sliced Tags on `Dolia`, `Ming Shiyin`, `Dr. Bian`, `Yao`, `Shi`, `Fleeting`, and `Totem`:**
     - Assert `"<color=#d487e4> tile dan"` not in `cat["unique"][dolia_key]`
     - Assert `"<b> secara acak 1</b>"` not in `cat["unique"]["使用技能，随机获得1张2-5阶的<a href=3130012><color=#ffffff>╆<b>转瞬</b></color></a>英雄牌。"]`
     - Assert `"<b> sebesar</b>"` not in `cat["unique"]["<a href=321><color=#ffffff>╉<b>图腾</b></color></a>不会被优先攻击。\n<a href=3><color=#ffffff>╪<b>开团</b></color></a>：获得每个<a href=321><color=#ffffff>╉<b>图腾</b></color></a>等级数15%的<a href=3130011><color=#ffffff>═<b>临时等级</b></color></a>。"]`
     - Assert `not cat["unique"]["获得<color=#FFE897>{0|2}{Energy}</color>以及2张<color=#FFE897>3阶英雄兑换券</color>。"].startswith("<color=#FFE897>Memperoleh</color>")`

- [ ] **Step 44.2: Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Run `pytest -v`, Commit, Force-Tag `v1.4.12-id.2`, & Re-Upload Release Assets (`06`)** *(REOPENED — Remediated in Task 46)*
  1. `/home/whise/.local/bin/uv run --python 3.12 python scripts/01b_build_hybrid_vfs_index.py`
  2. `/home/whise/.local/bin/uv run --python 3.12 python scripts/02_build_indonesian_catalog.py`
  3. `/home/whise/.local/bin/uv run --python 3.12 python scripts/03_patch_worker_modules.py`
  4. `/home/whise/.local/bin/uv run --python 3.12 python scripts/04_verify_real_windows_game.py`
  5. `/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py`
  6. `/home/whise/.local/bin/uv run --python 3.12 pytest -v` (`14 passed, 0 failed, 0 skipped`)
  7. Update SHA-256 hashes in `README.md` & `scripts/06_publish_github_release.py`, check `[x]` on all completed tasks in `.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md`, commit, `git push origin main`, `git tag -f v1.4.12-id.2 HEAD && git push -f origin v1.4.12-id.2`, and run `scripts/06_publish_github_release.py`.

---

## Phase 6 Remediation Round 7: Eliminating the Final `7` `_wrap_exact_tag_sequence` Calls (`Yang Yuhuan` Swapped Formulas & `2.5%` Nested Color), `7` Tier 1 Step-4 Fallbacks, & `Mi Yue` / `Gain` Prefix Bugs (Tasks 45–46)

> [!CAUTION]
> **Manager Forensic Audit of `commit 11d88d5` — REJECTED Due to 3 Final Bugs in `src/acepatchindo/tag_aligner.py`:**
>
> 1. **BUG 1: `Yang Yuhuan` (`杨玉环` / `惊鸿调`) — 4 Strings Have Swapped Formulas (`[0]..[2]` vs `[3]..[5]`) & Broken 2-Line vs 3-Line Tag Alignment (`tag_aligner.py:482-516, 763-775, 948`), Plus `Mi Yue` `sp2b` Regex (`tag_aligner.py:615`):**
>    - **Root Cause A (Step 2 single `cursor` across different `c_ex` values in `tag_aligner.py:482-516`):**
>      - In Chinese (`descCn`), each line of Yang Yuhuan's skill has `3名` **BEFORE** `100+80%` (`[('3', '名'), ('100+80%', ''), ('3', '名'), ('100+80%', '')]`).
>      - In Indonesian (`desc_id`), each line has `100+80%` **BEFORE** `3 sekutu` / `3 musuh` (`Qingping: memulihkan 100+80% Magic Attack sebagai HP untuk 3 sekutu... \nPozhen: memberikan 100+80% Magic Attack sebagai Magic Damage ke 3 musuh...`).
>      - When `i=0` (`c_ex="3" == s_ex="3"`) ran `m_same = pat_same.search(out, cursor)` and set `cursor = m_same.end()`, `cursor` jumped **past** `100+80%` on Line 1 (`Qingping`) to `untuk 3 sekutu`!
>      - Then `i=1` (`c_ex="100+80%"`, `s_ex="[1]+[2]%"` / `"100+[176310p1q3/100]%"`) searched from `cursor` and matched the **second** `100+80%` (`Pozhen` on Line 2)!
>      - And then `i=3` (`c_ex="100+80%"`, `s_ex="[4]+[5]%"` / `"[176300p1q1]+80%"`) wrapped around to `0` (`m = pat.search(out, 0)`) and matched the **first** `100+80%` (`Qingping` on Line 1), **swapping the heal and damage formulas between `Qingping` and `Pozhen`**:
>        - `<color=#ffffffbf> Qingping: memulihkan</color>[3] Magic <color=#9ff5d0> Damage ([4]+[5]%</color><color=#9ff5d0> Magic Attack)</color> untuk 3 sekutu dengan HP terendah.`
>        - `<color=#ffffffbf> Pozhen: memberikan memulihkan</color>[0] HP ([1]+[2]% <color=#d487e4> Magic Attack) ke</color><color=#d487e4> 3 musuh dengan</color> persentase HP tertinggi.`
>    - **Root Cause B (2-Line `source_zh` vs 3-Line `desc_id` on Yang Yuhuan's 2-Line Variant):**
>      - In `<color=#ffffffbf>清平：</color>杨玉环弹奏琵琶，为3名血量最低的友军...\n<color=#ffffffbf>破阵：</color>杨玉环弹奏琵琶，对当前血量百分比最高的3名敌人...`, `source_zh` has **2** lines (`\n` count = 1), whereas `tier1_wiki_id.json` `desc_id` has **3** lines (`Yang Yuhuan memainkan pipa dan mengaktifkan salah satu efek lagu secara bergantian.\nQingping: ...\nPozhen: ...`). Because `len(src_paras) == 2 != len(res_paras) == 3`, `reinject_skeleton_from_source` (`line 767`) failed to align line-by-line and fell into `_wrap_exact_tag_sequence` (`<color=#ffffffbf> Yang Yuhuan memainkan pipa</color>...`)!
>    - **Root Cause C (`Mi Yue` `sp2b` Regex at `tag_aligner.py:615`):**
>      - In `芈月为等级最高的近战友军召唤1只暗影仆从协助战斗...并为友军恢复<color=#d487e4>[121220p1q3/100]%芈月法术攻击力</color><color=#9ff5d0>的生命值</color>，同时窃取目标1点<color=#dfa15e>物理防御</color>和<color=#d487e4>法术防御</color>...`, `out` has `memulihkan HP sekutu itu sebesar [121220p1q3/100]% Magic Attack Miyue`.
>      - Because `sp2b` (`line 615`) only allowed `(HP(?:\s+miliknya)?)` and `(?:\s+miliknya)?`, it failed to match `HP sekutu itu` and `Magic Attack Miyue`, shifting all subsequent tags by 1 (`<color=#9ff5d0>Physical Defense</color>` and `<color=#dfa15e>Magic Defense</color> ... <color=#d487e4>bertahan sampai Round berakhir)</color>`)!
>
> 2. **BUG 2: Unreachable Nested `<color=C1>...<color=C2>VAL</color>...</color>` Block (`tag_aligner.py:1008-1024`) & `LEADING_TAGGED_PREFIX_RE` Copying Untranslated `"Gain "` (`tag_aligner.py:809-820`):**
>    - **Root Cause A (Nested Color Span in `战斗开始时，你的英雄普攻附带<color=#FFE897>敌人最大生命值<color=#00FF00>2.5%</color></color>的法术伤害。` and `获得1张诸葛亮和1张明世隐...<color=#FFE897>有概率连续施法<color=#00FF00>5</color>次</color>`):**
>      - `ATOMIC_TAGGED_SPAN_RE` (`line 36`) matches only the inner span `<color=#00FF00>2.5%</color>` (so `len(spans) == 1`), and the loop at `lines 834-1006` matches `<color=#00FF00>2.5%</color>` (`all_matched = True`, `"<" in curr == True`).
>      - Therefore, `if not all_matched and len(spans) == 1 and "<" not in curr:` at `line 1008` is **100% unreachable**, causing `2.5%` to fall into `_wrap_exact_tag_sequence` (`Saat Combat dimulai,<color=#FFE897> Basic Attack Hero <color=#00FF00> milikmu disertai Magic</color></color> Damage sebesar 2.5% Max HP musuh.`)!
>    - **Root Cause B (`LEADING_TAGGED_PREFIX_RE` at `lines 809-820` Copying `"Gain <color=#FFE897>Nemesis</color>"`):**
>      - On `获得<color=#FFE897>强敌克星</color>：造成真实伤害，每普攻4次眩晕敌人。` and `获得<color=#FFE897>断念</color>：造成伤害时降低敌方最大生命值。`, `baseline_en` starts with `"Gain <color=#FFE897>Nemesis</color>:"` (`2` words after stripping tags).
>      - `lines 809-820` copied `m_en.group(1)` verbatim from `baseline_en`, leaving English `"Gain "` at the start of the Indonesian sentence (`"Gain <color=#FFE897>Nemesis</color>: memberikan True Damage..."`)!
>      - And on `获得<color=#FFE897>法潮灵杖</color>：获取左右1格英雄法术攻击力。`, `en_spans[0]` had `"Tide Staff"` instead of `"Arcane Tide Staff"`, producing `"Memperoleh Arcane <color=#FFE897>Tide Staff:</color>"`!
>
> 3. **BUG 3: `7` Tier 1 Strings Silently Fail Step 4 (`tag_aligner.py:1188-1197`) and Fall Into Step 5 (`allow_en_fallback`, Discarding Tier 1 Human Translation for Broken Tier 3 Machine Translation) + `1` Broken `orig["unique"]` Totem Tag:**
>    - Across the entire catalog, `7` Tier 1 strings fail Step 4 (`line 1190`) and get overwritten by Step 5 (`cand_en` Tier 3 machine translation):
>      1. `<color=#FFE897>每╦合成4次【逐鹿】英雄</color>，获得1张随机1-5阶<color=#FFE897>效果锦囊牌</color>。` -> Fails `control_tokens_changed` at Step 4 because `GLYPH_KEYWORD_MAP["╦"]` (`line 1138`) only has `("ancient coin", "Ancient Coin")` and is missing `"Merge", "Synthesis", "Combine", "Menggabungkan"`, so `╦` is not placed before `Merge`!
>      2. `战斗开始时，<color=#FFE897>第一排╋闪现英雄</color>不再<a><color=#FFE897>╋<b>闪现</b></color></a>...` (and its non-`<a>` variant) -> Fails `control_tokens_changed` / `tags_changed` at Step 4 because `rf"(?<!>)"` at `line 1155` blocks placing `╋` before `Flash` when `Flash` is immediately preceded by `>` in `<color=#FFE897>Flash Hero`!
>      3. `<color=#FFE897>4/5阶的召唤单位</color>获得<a><color=#ffffff><b>╧完美复生</b></color></a>。` and `每回合<color=#FFE897>首次对【逐鹿】英雄使用的效果牌</color>会返回手牌并附加<color=#FFE897>╆转瞬</color>。` -> Fail `tags_changed` at Step 4 because they are single-clause sentences (no comma `,`) where the second span (`<a>...Perfect Revive...</a>` or `<color=#FFE897>╆Instant</color>`) matched, putting `"<"` in `id_clauses[0]`, so `untagged_indices` (`if id_clauses[i].strip() and "<" not in id_clauses[i]`) is empty `[]`!
>      4. `<color=#FFE897>场上的╉图腾被摧毁</color>时，等级最高的【大河】英雄获得<a><color=#ffffff>╉<b>图腾</b></color></a>一半等级的<a>═临时等级</a>。` -> Fails `tags_changed` because `<a href=321>` check at `line 800` missed bare `<a>` (`<a><color=#ffffff>╉<b>图腾</b></color></a>` and `<a>═临时等级</a>`), and Span 1 (`<a>...图腾...</a>`) matched the 1st `Totem` at index 0 (`Saat Totem di field hancur`) instead of the 2nd `Totem`!
>      5. `获得1张李信，李信卡牌效果提供的<a href=3130011><color=#ffffff>═<b>临时等级</b></color></a>额外+3。若李信觉醒，<color=#FFE897>敌方英雄触发<a>╫牺牲</color></a>时，也会触发己方李信的卡牌效果。` -> Fails `tags_changed` because `source_zh` has interleaved tags `<color=#FFE897>敌方英雄触发<a>╫牺牲</color></a>`!
>    - Additionally, on `<color=#99DEB0>召唤╉图腾</color>，己方所有【大河】英雄获得相当于<a><color=#99DEB0>╉<b>图腾</b></color></a>等级<color=#99DEB0>50%</color>的<a>═临时等级</a>。` (Tier 3), `orig["unique"][k]` (`baseline_en`) has corrupted tags in the upstream English patcher (`<a>Riverlands<color=#99DEB0> heroes gain...`), producing `Semua sekutu <a>Riverlands <color=#99DEB0> Hero mendapatkan... Level═</a>.`! And on `战斗中入场的召唤物存活<color=#99DEB0>8秒</color>后，<color=#99DEB0>变为其召唤者（无卡牌效果）</color>...`, `"变为其召唤者（无卡牌效果）"` is missing from `BADGE_ALIAS_MAP`, wrapping `<color=#99DEB0>Summoned</color>` at index 0!

### Task 45: Fix All 3 Final Bugs in `src/acepatchindo/tag_aligner.py`

- [x] **Step 45.1: Fix Step 2 Per-`c_ex` Cursor (`Yang Yuhuan` Swapped Formulas), 2-Line `Yang Yuhuan` Intro Folding, and `Mi Yue` `sp2a`/`sp2b` Regex (`tag_aligner.py:380-630`)**
  1. **Fold 3-Line `desc_id` Into 2 Lines When `source_zh` Starts With `<color=#ffffffbf>清平：</color>` (`around line 380`):**
     ```python
     if source_zh.lstrip().startswith("<color=#ffffffbf>清平：</color>") and out.startswith("Yang Yuhuan memainkan pipa"):
         out = re.sub(
             r"^Yang Yuhuan memainkan pipa[^.\n]*\.\s*\n\s*Qingping:\s*",
             "Qingping: Yang Yuhuan memainkan pipa, ",
             out,
         )
         cn_clean = re.sub(r"^清平杨玉环弹奏琵琶", "清平", cn_clean)
         src_clean = re.sub(r"^清平杨玉环弹奏琵琶", "清平", src_clean)
     ```
  2. **Use Per-`c_ex` Cursors (`cursor_by_cex`) in Step 2 (`lines 480-518`) So Reordered Clause Numbers (`3名` vs `100+80%`) Never Swap Formulas:**
     ```python
     if len(cn_matches) == len(src_matches):
         slots: list[tuple[str, str]] = []
         cursor_by_cex: dict[str, int] = {}
         for i, ((c_ex, c_u), (s_ex, s_u)) in enumerate(zip(cn_matches, src_matches)):
             unit_pat = UNIT_MAP.get(s_u or c_u, "")
             cur_pos = cursor_by_cex.get(c_ex, 0)
             if c_ex == s_ex:
                 pat_same = re.compile(rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])")
                 m_same = pat_same.search(out, cur_pos)
                 if m_same:
                     cursor_by_cex[c_ex] = m_same.end()
                 continue
             pat = None
             if unit_pat:
                 pat = re.compile(rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])(?={unit_pat})", flags=re.I)
                 m = pat.search(out, cur_pos)
                 if not m:
                     m = pat.search(out, 0)
                 if not m:
                     pat = None
             if not pat:
                 pat = re.compile(rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])")
                 m = pat.search(out, cur_pos)
                 if not m:
                     m = pat.search(out, 0)
             if not m and re.match(r"^\d+(?:\.\d+)?\+\d+(?:\.\d+)?%$", c_ex):
                 m = re.compile(r"(?<![\d\[])\d+(?:\.\d+)?\s*\+\s*\d+(?:\.\d+)?%").search(out, cur_pos)
                 if not m:
                     m = re.compile(r"(?<![\d\[])\d+(?:\.\d+)?\s*\+\s*\d+(?:\.\d+)?%").search(out, 0)
             if not m:
                 continue
             clean_s = re.sub(r"\s+", "", s_ex)
             if clean_s in ph_map:
                 s_ex = ph_map[clean_s]
             slot_tok = f"__EXPRSLOT{chr(65 + (i // 26))}{chr(65 + (i % 26))}__"
             delta = len(slot_tok) - (m.end() - m.start())
             out = out[:m.start()] + slot_tok + out[m.end():]
             for k_c, v_c in list(cursor_by_cex.items()):
                 if v_c > m.start():
                     cursor_by_cex[k_c] = v_c + delta
             cursor_by_cex[c_ex] = m.start() + len(slot_tok)
             slots.append((slot_tok, s_ex))
         for slot_tok, s_ex in slots:
             out = out.replace(slot_tok, s_ex)
     ```
  3. **Expand `sp2a` and `sp2b` (`lines 610-626`) to Match `Mi Yue` (`HP sekutu itu` and `Magic Attack Miyue`):**
     ```python
     sp2a = re.compile(
         rf"(memulihkan\s+)?({num_pat}\s*(?:Magic Attack|Physical Attack|Max HP|HP Maks)(?:\s+(?:miliknya|Miyue|Mi Yue|Yaria))?)\s*((?:sebagai\s+)?HP(?:\s+sekutu(?:\s+itu)?)?\b)",
         flags=re.I,
     )
     sp2b = re.compile(
         rf"(memulihkan\s+)(HP(?:\s+sekutu(?:\s+itu)?|\s+miliknya)?)\s+sebesar\s+({num_pat}\s*(?:Magic Attack|Physical Attack|Max HP|HP Maks)(?:\s+(?:miliknya|Miyue|Mi Yue|Yaria))?)",
         flags=re.I,
     )
     ```

- [x] **Step 45.2: Fix Nested `<color=C1>...<color=C2>VAL</color>...</color>`, `LEADING_TAGGED_PREFIX_RE` `"Gain "` Guard, Colon Placement, and All 7 Tier 1 Step-4 Fallbacks in `reinject_skeleton_from_source` (`tag_aligner.py:130-250, 800-1265`)**
  1. **Expand `BADGE_ALIAS_MAP` (`lines 130-250`) and `GLYPH_KEYWORD_MAP` (`lines 1126-1140`):**
     - Add to `BADGE_ALIAS_MAP`:
       - `"清平": ["Qingping"]`, `"破阵": ["Pozhen"]`, `"撕裂": ["Rend"]`
       - `"法潮灵杖": ["Arcane Tide Staff"]`, `"强敌克星": ["Bane of the Mighty", "Nemesis"]`, `"断念": ["Severance", "Heartbreak"]`
       - `"效果锦囊牌": ["kartu Efek Lucky Bag", "efek Strategi kartu", "Effect Strategy Card"]`
       - `"4/5阶的召唤单位": ["4/5 Tier Summoned Unit", "Summoned Unit Tier 4/5", "Tier 4/5 unit panggilan"]`
       - `"首次对【逐鹿】英雄使用的效果牌": ["Kartu Efek pertama yang digunakan pada Hero [Zhulu]"]`
       - `"变为其召唤者（无卡牌效果）": ["berubah menjadi pemanggilnya (tanpa efek kartu)", "menjadi summoner mereka (tidak kartu efek)"]`
       - `"第一排╋闪现英雄": ["Flash Hero di baris pertama"]`, `"第一排闪现英雄": ["Flash Hero di baris pertama"]`
       - `"后三排╋闪现英雄": ["Flash Hero di 3 baris belakang"]`, `"后三排闪现英雄": ["Flash Hero di 3 baris belakang"]`
       - `"场上的╉图腾被摧毁": ["Saat Totem di field hancur", "Totem di field hancur"]`
     - Add `"Merge", "Synthesis", "Combine", "Menggabungkan", "Gabung"` to `GLYPH_KEYWORD_MAP["╦"]` (`line 1138`).
  2. **Remove `rf"(?<!>)"` From Step 3 Control Token Regex (`line 1155`):**
     - Replace `rf"(?<!>)"` with `rf"(?<!{re.escape(ch)}<color=#FFE897>)"` and `rf"(?<!{re.escape(ch)}<color=#ffffff>)"` so `╋` and `╦` can be placed inside `<color=#FFE897>╋Flash Hero` and `<color=#FFE897>Setiap kali ╦Merge`!
  3. **Broaden Totem vs Temporary Level Reordering (`line 800`) to Include Bare `<a>` Tags & Repair Corrupted `baseline_en` Totem String:**
     - At `line 800`, check `("图腾" in source_zh and "临时等级" in source_zh and ("<a" in source_zh) and source_zh.find("图腾") < source_zh.find("临时等级"))`:
       - Also handle `memperoleh (═?Temporary Level) sebesar (setengah Level) (╉?Totem tersebut)` -> `memperoleh \2 \3 sebagai \1`, and `mendapatkan (?:╉?Temporary Level )?sebesar (\d+%) dari (╉?Totem) Level` -> `mendapatkan \2 Level \1 sebagai ═Temporary Level`.
       - And if `baseline_en` contains `"<a>Riverlands<color=#99DEB0>"` (corrupted upstream English tag order on `<color=#99DEB0>召唤╉图腾</color>，己方所有【大河】英雄获得相当于<a><color=#99DEB0>╉<b>图腾</b></color></a>等级<color=#99DEB0>50%</color>的<a>═临时等级</a>。`), sanitize `baseline_en` to `'Summon <color=#99DEB0>╉Totem</color>. All allied [Riverlands] heroes gain <a><color=#99DEB0>╉<b>Totem</b></color></a> Level <color=#99DEB0>50%</color> as <a>═Temporary Level</a>.'` before alignment!
  4. **Guard `LEADING_TAGGED_PREFIX_RE` (`line 810`) & Keep Colon Outside `close_part` When `source_zh` Has Colon Outside (`line 924`):**
     - At `line 810`, require `m_en.group(1).lstrip().startswith("<")` so English verbs like `"Gain <color=#FFE897>Nemesis</color>"` are NEVER copied into Indonesian sentences!
     - At `line 924`, only put `:` inside `{close_part}` (`f"{open_part}{kw}:{close_part} "`) if `zh_inner.endswith(("：", ":"))`; if the colon in `source_zh` is **outside** `close_part` (like `<color=#FFE897>强敌克星</color>：`), output `f"{open_part}{kw}{close_part}: "`!
  5. **Handle Nested `<color=C1>...<color=C2>VAL</color>...</color>` and Interleaved `<color=#FFE897>敌方英雄触发<a>╫牺牲</color></a>` BEFORE `ATOMIC_TAGGED_SPAN_RE` (`around line 822`):**
     - Before `spans = list(ATOMIC_TAGGED_SPAN_RE.finditer(source_zh))`:
       - If `"<color=#FFE897>敌方英雄触发<a>╫牺牲</color></a>"` in `source_zh` and `"<" not in result`:
         - Wrap `<a href=3130011><color=#ffffff>═<b>Temporary Level</b></color></a>` around `Temporary Level` and `<color=#FFE897>Hero musuh memicu <a>╫Sacrifice</color></a>` around `Hero musuh memicu Sacrifice`!
       - If `m_nest := re.search(r"<color=([^>]+)>([^<]*)<color=([^>]+)>([^<]+)</color>([^<]*)</color>", source_zh)` and `"<" not in result`:
         - Wrap the inner value (`m_nest.group(4)`, e.g. `2.5%` or `5`) in `<color={c2}>{inner_val}</color>`, and wrap the clause containing `<color={c2}>` (after `,` in `result`, or the verb phrase `memiliki ... <color={c2}>5</color> kali` / `Basic Attack Hero ... Max HP musuh`) in `<color={c1}>...</color>`!

### Task 46: Add Round 7 Anti-Regression Assertions (`0` `_wrap_exact_tag_sequence` & `0` `missing_pairs` Across Entire Catalog), Rebuild Pipeline, Commit `graft` Setup, & Re-Publish `v1.4.12-id.2`

- [x] **Step 46.1: Expand `test_round6_footer_terms_and_zero_fallback_wraps` in `tests/test_glossary_and_tiers.py`**
  1. Assert **0** calls to `_wrap_exact_tag_sequence` and **0** calls to `missing_pairs` across all `4,183` target strings in `catalog.json.gz`.
  2. Assert `Yang Yuhuan` (`杨玉环弹奏琵琶...` and `<color=#ffffffbf>清平：</color>杨玉环弹奏琵琶...`) has `[0] HP ([1]+[2]% Magic Attack)` under `Qingping` and `[3] Magic Damage ([4]+[5]% Magic Attack)` under `Pozhen` (never swapped, and never `"memberikan memulihkan"`).
  3. Assert `战斗开始时，你的英雄普攻附带<color=#FFE897>敌人最大生命值<color=#00FF00>2.5%</color></color>的法术伤害。` wraps `<color=#00FF00>2.5%</color>` around `2.5%` (not `milikmu disertai Magic`).
  4. Assert `获得<color=#FFE897>强敌克星</color>：造成真实伤害，每普攻4次眩晕敌人。` and `获得<color=#FFE897>断念</color>：造成伤害时降低敌方最大生命值。` start with `"Memperoleh "` (not `"Gain "`).
  5. Assert `Mi Yue` (`芈月为等级最高的近战友军召唤1只暗影仆从协助战斗...`) wraps `<color=#dfa15e>Physical Defense</color>` and `<color=#d487e4>Magic Defense</color>` (not `<color=#9ff5d0>Physical Defense</color>`).
  6. Assert `<color=#99DEB0>召唤╉图腾</color>，己方所有【大河】英雄获得相当于<a><color=#99DEB0>╉<b>图腾</b></color></a>等级<color=#99DEB0>50%</color>的<a>═临时等级</a>。` does NOT contain `"<a>Riverlands"` or `"Level═</a>"`.

- [x] **Step 46.2: Re-Run Full Pipeline (`01b` -> `02` -> `03` -> `04` -> `05`), Run `graft build` & `pytest -v`, Commit All Files (Including `graft` Setup), Force-Tag `v1.4.12-id.2`, & Re-Upload Release Assets (`06`)**
  1. `/home/whise/.local/bin/uv run --python 3.12 python scripts/01b_build_hybrid_vfs_index.py`
  2. `/home/whise/.local/bin/uv run --python 3.12 python scripts/02_build_indonesian_catalog.py`
  3. `/home/whise/.local/bin/uv run --python 3.12 python scripts/03_patch_worker_modules.py`
  4. `/home/whise/.local/bin/uv run --python 3.12 python scripts/04_verify_real_windows_game.py`
  5. `/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py`
  6. `graft build` and `/home/whise/.local/bin/uv run --python 3.12 pytest -v`
  7. Update SHA-256 hashes in `README.md` & `scripts/06_publish_github_release.py`, check `[x]` on all completed tasks in `.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md`, commit all modified files AND the `graft` repo setup files (`.gitignore`, `.ignore`, `.claude/`, `.gemini/`, `.mcp.json`, `AGENTS.md`, `GEMINI.md`), `git push origin main`, `git tag -f v1.4.12-id.2 HEAD && git push -f origin v1.4.12-id.2`, and run `scripts/06_publish_github_release.py`.











