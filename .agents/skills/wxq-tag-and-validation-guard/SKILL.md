---
name: wxq-tag-and-validation-guard
description: Use when formatting, injecting, or validating translated strings for catalog.json.gz or wxq_patch to prevent silent rejection by validate_translation or QtsVFS chunk capacity overflow.
---

# WXQ Tag Preservation, Validation Guard & Layout Invariants

## Overview

At build time (`src/acepatchindo/validator.py`) and runtime (`wxq_patch/translation_rules.py`), every `(source, translated)` pair is validated by `validate_translation(source, translated)`. **Any string that fails `validate_translation` is rejected (`invalid_translation`).**

## The 7 Mandatory Validation Invariants (`src/acepatchindo/validator.py`)

Every `(source, translated)` pair in `catalog.json.gz` MUST return `(True, 'ok')` from `validate_translation`:

```python
import re
from collections import Counter

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
TAG_RE = re.compile(r"<(?:/?[A-Za-z][^>]*|/)>")
PLACEHOLDER_RE = re.compile(
    r"\{[^{}]*\}|%(?:\d+\$)?[-+0 #]*(?:\d+|\*)?(?:\.\d+)?[diuoxXfFeEgGaAcspn%](?![A-Za-z])"
)
CONTROL_TOKEN_RE = re.compile(r"[\u2540-\u257f]")
RUNTIME_BRACKET_TOKEN_RE = re.compile(r"\[(?:\d+|\d+[A-Za-z0-9_+/.*%-]+)\]")

def validate_translation(source: str, translated: object) -> tuple[bool, str]:
    if not isinstance(translated, str) or not translated.strip():
        return (False, "empty")
    visible_translation = PLACEHOLDER_RE.sub("", TAG_RE.sub("", translated))
    if CJK_RE.search(visible_translation):
        return (False, "still_chinese")
    source_tags = TAG_RE.findall(source)
    translated_tags = TAG_RE.findall(translated)
    angle_bracket_label = source.startswith("<{") and source.endswith(">")
    if source_tags != translated_tags and not angle_bracket_label:
        return (False, "tags_changed")
    if Counter(PLACEHOLDER_RE.findall(source)) != Counter(PLACEHOLDER_RE.findall(translated)):
        return (False, "placeholders_changed")
    if Counter(RUNTIME_BRACKET_TOKEN_RE.findall(source)) != Counter(
        RUNTIME_BRACKET_TOKEN_RE.findall(translated)
    ):
        return (False, "bracket_tokens_changed")
    if Counter(CONTROL_TOKEN_RE.findall(source)) != Counter(CONTROL_TOKEN_RE.findall(translated)):
        return (False, "control_tokens_changed")
    if ";" in source and source.count(";") != translated.count(";"):
        return (False, "semicolons_changed")
    if len(source) >= 4 and len(translated) > max(len(source) * 8, 48):
        return (False, "extreme_expansion")
    return (True, "ok")
```

## Critical Alignment & Layout Invariants (`tag_aligner.py` & `card_wrapper.py`)

1. **Zero Fullwidth CJK Punctuation Outside Braces:**
   - Never leave `。，：；（）` outside `{...}` placeholders in translated strings (`ThreeTierGlossary._finalize_output` strips/normalizes them while protecting `{...}` placeholders).
2. **Atomic `{N|val}{Icon}` Binding (`adapt_tier1_placeholders_to_source`):**
   - Always bind dynamic placeholder ranges (`{N|v1}-{M|v2}`) and `{N|val}{Icon}` pairs (`{3|1}{LordExp}`, `{0|1}{Energy}`, `{0|3}{Energy}`, `{1|10}{LordHp}`) atomically BEFORE generic number replacement so `{3|1}` never replaces a proper noun number like `Tier 3`.
3. **Tracker Placeholder Isolation (`reinject_formula_and_skeleton`):**
   - Identify trailing tracker clauses (`NORM_ZH_TRACKER_RE`, e.g. `（总复生次数：{ResCardInfoDataBin_1541_15412_0: 1}）`, `（已击败：{killcount:0}）`, `（当前：{XYTokenAValue:75}）`) and exclude their placeholders (`tracker_phs`) from generic Step 2c numeric replacement so they never overwrite card counts in the main sentence.
4. **Snug Box-Drawing Control Glyphs (`[\u2540-\u257f]`):**
   - Control tokens (`╪ ╨ ╫ ╬ ═ ╆ ╇ ╈ ╉ ╊ ╧`) must ALWAYS have a space or opening tag before them and ZERO space/newline immediately after them (e.g., `╧<b>Revive</b>` or `<a href=11><color=#99DEB0>╬Prepare</color></a>`).
5. **CJK-Safe Word Wrapping (`wrap_card_description`):**
   - For any card description without `;`, every line's visible length (`_visible_length(line)`) must be `<= 34` characters (unless a single unbroken token exceeds 34 chars), with zero mid-word splits, zero split `[...]`/`{...}`/`<...>` tokens across newlines, and zero standalone `+` or `-` at the end of a line.

## QtsVFS Capacity Verification Against Real Game Files

Always run `.venv/bin/pytest tests/ -v` (including `tests/test_real_game_vfs.py` and `tests/test_catalog_zero_defects_audit.py`) to verify against the untouched Chinese game packages in `/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`:
- `counts.get('invalid_translation', 0) == 0`
- `counts.get('capacity_skipped', 0) == 0`
- `counts.get('unknown', 0) == 0`
