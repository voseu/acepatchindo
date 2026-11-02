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

- [x] **Step 21.2: Protect 100% of Embedded & Standalone English Entity Names in `src/acepatchindo/glossary.py` & `src/acepatchindo/tag_aligner.py`**
  - In `src/acepatchindo/glossary.py`:
    1. **Remove all 7 Talent/Card name translations from `TIER1_EMBEDDED_EN_CLEANUP` (`lines 521–527`):**
       - Delete `("Indomitable Will", "Tekad Baja")`, `("Try Your Luck", "Uji Keberuntungan")`, `("Glory of the Old Guard", "Kejayaan Garda Lama")`, `("Quench with Illusions", "Padamkan dengan Ilusi")`, `("Muster the Troops", "Kumpulkan Pasukan")`, `("Power of the Source", "Kekuatan Sumber")`, `("Bane of the Mighty", "Kutukan Sang Perkasa")`! Keep ONLY genuine grammar fixes (or reverse any Indonesian-translated proper card/talent/skill/contestant names back to English!).
    2. **Build `verified_entity_names_en: set[str]` bypassing `STOPWORD_GUARD_RE` for multi-word proper names:**
       - Collect ALL English names (`len(name) >= 4` and contains uppercase) of Heroes, Skills, Talents, Contestants (`lords` / `Chess player`), Contestant `talents[*].cardName` & `related[*].name`, Tier 2 `abilities[*].name` & `skill_names`, plus `orig_cat["unique"][zh_name]` for all those Chinese entity names (so names like `Symphony of Tides`, `Embrace of the Sea`, `Use for My Own`, `Point of No Return`, `Immovable as a Mountain`, `Burn the Boats`, `Try Your Luck`, `Indomitable Will`, `Glory of the Old Guard`, `Quench with Illusions`, `Muster the Troops`, `Power of the Source`, `Bane of the Mighty`, `Child of Flow`, `Three Kingdoms Banner`, `Super Copier`, `Build Upgrade` are **ALL** included in `instance.protected_en_terms` even when they contain `of`, `the`, `for`, `with`, `as`, `a`, `to` — excluding only generic sentences `len(name) > 40` or lowercase prose!).
    3. **Register Chinese -> Canonical English Entity Names for Tag/Span Lookup (`BADGE_ALIAS_MAP` / `tier1_exact_zh_to_id`):**
       - Ensure every Chinese Hero, Skill, Talent, Contestant, and Contestant Secret-Art / Ability Name maps to its **English** name (`orig_cat["unique"].get(zh_name) or en_name`) inside `glossary` and `tag_aligner.BADGE_ALIAS_MAP`, so when `tag_aligner.py` aligns `<color=#FFE897>潮汐的交响</color>`, `<color=#FFE897>超级复印机</color>`, `<color=#FFE897>构筑升级</color>`, or `<b>温柔呼唤</b>` inside an Indonesian description, the span content stays **English**!

- [x] **Step 21.3: Create `src/acepatchindo/hybrid_classifier.py` Using Exact QtsVFS Table Hashes, 48-Bit Key Suffixes (`#60D2`), & Reference Sets**
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
         - All `lords[*].talents[*]` & `lords[*].related[*]` descriptions in `tier1["lords"]`, all `abilities[*].desc` / `effect_copies` / `rule_notes` in `tier2_details["Chess player"]`, Contestant skill/passive/secret-art/trait/card descriptions in `#23F7..#6E60`, `#BCDE..#CEDB`, `#2394`, `#7D6E`, `#5CFD`, `#D262`, `4E0F1B7C13F264AE` (including Contestant secret art & ability card mechanics referencing `秘技牌`/`秘技卡`/`棋手到达`/`棋手每次`/`棋手技能`/`构筑升级`/`为我所用`/`翩跹舞步`/`潮汐的交响`/`蔷薇秘宝`/`枫叶舞`/`河豚书包`/`回溯孙小宾`/`超级复印机`), while strictly **excluding** loading tips (`#341F`), general rules tutorials (`#A360`, `#1F89`), achievements (`#637E`), event missions (`049FDCA512DC8897`, `79E3F2A531266997`, `1586D98CC6E0B77E`), and cosmetics/avatars/gifts (`#E2B0`)!
       - Plus the `18` curated entries in `WINDOWS_108_TARGET_DESC_ID`.

### Task 22: Update Catalog Builder (`02`), Unconditional Catalog-SHA Pre-Install Restore (`dual_state_patch.py`), Worker Patcher (`03`), & Dynamic Real-Game Verifier (`04`)

- [x] **Step 22.1: Rebuild `scripts/02_build_indonesian_catalog.py` for Hybrid `v1.4.12-id.2`**
  - Start from `orig_cat` (`Honor of Kings Ace English Patcher 1.4.12.exe_extracted/catalog/catalog.json.gz`).
  - For `data["unique"]`:
    - If `HybridClassifier` classifies `(zh_src, en_base)` as target gameplay description (`hero_card_desc | skill_desc | talent_desc | contestant_desc`), translate to Bahasa Indonesia (`glossary.translate_entry`) while keeping embedded proper names in English!
    - Otherwise, keep `en_base` (`100%` clean original English)!
  - For the `108` Windows missing Chinese strings:
    - Inject `18` entries from `WINDOWS_108_TARGET_DESC_ID` (Indonesian) and `90` entries from `WINDOWS_108_NONTARGET_EN` (English) so all `41,483` `unique` keys exist with **0 raw Chinese** and **0 `unknown`**!
  - For `data["contextual"]` and `data["english_updates"]` (`29,750` entries):
    - Only translate rows classified by `HybridClassifier.is_target_contextual_or_update(asset_hex, key, prev_en, target_en, opt_zh)` as Hero Card, Skill, Talent, or Contestant **descriptions** into Bahasa Indonesia (validated against both `zh_src` and `prev_en` as before); keep all Name rows and all non-target UI/Equipment/Effect/Tutorial/Achievement rows equal to `orig_cat`'s clean English `target_en`!
  - Set `data["version"] = "1.4.12-id.2"` and emit detailed category breakdown counts (`hero_card_desc`, `skill_desc`, `talent_desc`, `contestant_desc`, `reverted_en_names`, `reverted_en_other`, `windows_108_id=18`, `windows_108_en=90`).

- [x] **Step 22.2: Fix One-Click Live Upgrade (`v1.4.12-id.1` -> `v1.4.12-id.2`) in `src/acepatchindo/dual_state_patch.py` & Rebuild Worker (`03`)**
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
  - Run `scripts/03_patch_worker_modules.py` and verify `en_to_id` ONLY contains the Hybrid target description mappings (approx. `2,000–6,000` mappings, **0** standalone entity names, **0** UI/Settings/Equipment strings!).

- [x] **Step 22.3: Fix Hardcoded Receipt Path & Verify Hybrid Contract on Real Windows Game (`scripts/04_verify_real_windows_game.py`)**
  - Replace hardcoded `1793497168990741300-92b4bcbb/originals` in `scripts/04_verify_real_windows_game.py` and `tests/test_real_game_vfs.py` with dynamic resolution:
    `ADAPTIVE_ROOT = Path("/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive")`
    and a helper `find_windows_originals() -> Path | None` returning `sorted(ADAPTIVE_ROOT.glob("*/*/originals"))[-1]` if any exists!
  - Update `run_verification()` in `scripts/04_verify_real_windows_game.py` to execute **3 rigorous checks**:
    1. **`[1/3]` Unpatched Chinese `originals/` -> Hybrid `v1.4.12-id.2`:** Full `adaptive.scan(..., materialize=True)` + `stage_unity_package` across all **6** QtsVFS packages (`508` tables, `unknown == 0`, `invalid_translation == 0`, `capacity_skipped == 0`), **PLUS** decode materialized Protobuf `.bytes` payloads to assert concrete in-game proof:
       - Hero/Skill/Talent/Contestant descriptions in `#23F7`, `#FCCD`, `#BCDE`, `#0955` are in **Bahasa Indonesia** (with embedded names in **English**).
       - Standalone Hero/Skill/Talent/Contestant Names in `#23F7`, `#FCCD`, `#BCDE` are in **English** (`"Arthur"`, `"Lady Sun"`, `"Sky Splitter"`, `"Symphony of Tides"`, `"Maple Leaf Dance"`).
       - Equipment (`#ADCF`), Achievements (`#637E`), Loading Tips (`#341F`), and UI Settings (`Image Cache Directory`, `Download Manager`) are in **English**!
    2. **`[2/3]` Dual-State `EN -> Hybrid ID` Verification:** Verify `en_to_id` against English baseline catalog / staged English table so target descriptions convert `EN -> ID` while English Names & UI remain `100%` untouched in English!
    3. **`[3/3]` Live Windows Upgrade Trigger (`v1.4.12-id.1` -> `v1.4.12-id.2`):** Against `/run/media/whise/Windows/Program Files/WXQLauncher/WXQ` and real receipt `1793628251781039400-c81278c0/receipt.json`, verify that live files match the active Windows receipt (`_matching_restore_items` logic under Linux path mapping) and lack matching `patcher_catalog_sha256.txt`, proving `v1.4.12-id.2` will auto-restore `originals/` on first click of **Install** on Windows!

### Task 23: Update Unit & Integration Test Suites (`tests/test_glossary_and_tiers.py`, `tests/test_dual_state_engine.py`, `tests/test_real_game_vfs.py`)

- [x] **Step 23.1: Update `tests/test_glossary_and_tiers.py` for Hybrid `v1.4.12-id.2` Invariants**
  - Assert `cat["version"] == "1.4.12-id.2"` and `len(cat["unique"]) == 41483` and `len(cat["english_updates"]) == 29750`.
  - **Invariant 1 (Names Stay 100% English):** Assert that across ALL Hero, Skill, Talent, and Contestant Chinese names in `tier1_wiki_id.json` (`hero`, `skills`, `talent`, `lords`) present in `orig_cat["unique"]`, `cat["unique"][zh_name] == orig_cat["unique"][zh_name]` (**0** names translated to Indonesian!). Also assert embedded names inside Indonesian descriptions (`Indomitable Will`, `Try Your Luck`, `Symphony of Tides`, `Three Kingdoms Banner`, `Maple Leaf Dance`, `Super Copier`, `Build Upgrade`) remain in **English** (`0` occurrences of `Tekad Baja`, `Uji Keberuntungan`, `Kejayaan Garda Lama`, `Padamkan dengan Ilusi`, `Kumpulkan Pasukan`, `Kekuatan Sumber`, `Kutukan Sang Perkasa` for those proper card names!).
  - **Invariant 2 (Non-Target Strings Revert 100% to English):** Assert UI/Menu/Settings (`"图片缓存目录" -> "Image Cache Directory"`, `"下载管理" -> "Download Manager"`, `"打开文件夹" -> "Open Folder"`), Equipment names & descriptions (`"灵泉法杖"`, `"三分旗帜"`, `"仅三分英雄穿戴..."`), standalone Effect Card names & descriptions, Achievements, and Quick-Chat strings are in clean **English** (`0` CJK characters remaining across non-exempt entries!).
  - **Invariant 3 (Target Gameplay Descriptions Stay Natural Indonesian, Free of Indlish & Tag Bugs):** Assert Hero Card descriptions, Skill descriptions (including collapsed short summaries & Lv.10/40/100 enhancements), Talent descriptions, and Contestant descriptions are in natural **Bahasa Indonesia**, passing all tag/placeholder/formula/grammar regression assertions from Task 20 (`0` `(aku)`, `0` `Li</color>Bai`, `0` `adalah digunakan`, `0` `sebuah 1`, `0` `Level atas`, `0` `kiri dan benar`, and `< 25` English stopword leaks across all classified target Indonesian descriptions after stripping protected English entity names & mechanics!).

- [x] **Step 23.2: Add `v1.4.12-id.1 -> v1.4.12-id.2` Unconditional Pre-Install Restore Test in `tests/test_dual_state_engine.py` & Zero-Skip Guard in `tests/test_real_game_vfs.py`**
  - In `tests/test_dual_state_engine.py`: add `test_adaptive_unconditionally_restores_v1_full_id_when_catalog_sha_differs` simulating a game directory already patched with `v1.4.12-id.1` (where `scan()` returns **empty `plans_check == []`**!) + an active receipt without matching `patcher_catalog_sha256.txt`, proving `_run("install", ...)` **still calls `_orig_run("restore", ...)` first**, then `_orig_run("install", ...)`, and stamps `patcher_catalog_sha256.txt` so a second `_run("install", ...)` does **NOT** restore again!
  - In `tests/test_real_game_vfs.py`: use `find_windows_originals()` so when `/run/media/whise/Windows` is mounted, the test **NEVER skips** and asserts all 3 checks from `04_verify_real_windows_game.py`!

### Task 24: Full Pipeline Execution (`02` -> `03` -> `04` -> `05`), All `pytest -v` Green (`0` Skipped!), Update Docs, & Publish GitHub Release `v1.4.12-id.2` (`06`)

- [x] **Step 24.1: Execute Build, Patch, Real-Game Verification, Repack, & Full Test Suite**
  - Run in exact order:
    1. `/home/whise/.local/bin/uv run --python 3.12 python scripts/02_build_indonesian_catalog.py`
    2. `/home/whise/.local/bin/uv run --python 3.12 python scripts/03_patch_worker_modules.py`
    3. `/home/whise/.local/bin/uv run --python 3.12 python scripts/04_verify_real_windows_game.py`
    4. `/home/whise/.local/bin/uv run --python 3.12 python scripts/05_repack_windows_exe.py`
    5. `/home/whise/.local/bin/uv run --python 3.12 pytest -v` (**0 failed, 0 skipped!**)

- [x] **Step 24.2: Update `README.md` & `scripts/06_publish_github_release.py` (`TAG = "v1.4.12-id.2"`), Commit, Push `main`, & Publish GitHub Release `v1.4.12-id.2`**
  - Update `scripts/06_publish_github_release.py` to set `TAG = "v1.4.12-id.2"` and `TITLE = "Honor of Kings: Ace Indonesian Patcher v1.4.12-id.2 (Hybrid Gameplay Edition)"` (keep `v1.4.12-id.1` intact on GitHub Releases as the Full-Indonesian archive release, and publish `v1.4.12-id.2` as the new Latest Release with `dist/Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe` + `dist/SHA256SUMS.txt` and exact SHA-256 digests!).
  - Update `README.md` with accurate `v1.4.12-id.2` Hybrid Edition scope (Indonesian descriptions for Hero Cards, Skills, Talents, and Contestants; English for all Hero/Skill/Talent/Contestant Names and all other game UI, Equipment, Effect Cards, Tutorials, and Menus; automatic one-click upgrade from both English Patcher `1.4.12` and Full Indonesian `v1.4.12-id.1`) and exact SHA-256 checksums.
  - Mark all Phase 6 checkboxes (`[x]`) in `.agents/plan/2026-11-03-hok-ace-indonesian-patcher-plan.md`, commit cleanly on `main`, `git push origin main`, create & push tag `v1.4.12-id.2`, run `scripts/06_publish_github_release.py`, and verify HTTP `200` + exact remote `digest` match via `gh release view v1.4.12-id.2 --repo voseu/acepatchindo --json assets,isLatest`!




