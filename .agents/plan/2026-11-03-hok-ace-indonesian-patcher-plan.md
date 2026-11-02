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
