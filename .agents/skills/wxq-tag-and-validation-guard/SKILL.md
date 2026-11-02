---
name: wxq-tag-and-validation-guard
description: Use when formatting, injecting, or validating translated strings for catalog.json.gz or wxq_patch to prevent silent rejection by validate_translation or QtsVFS chunk capacity overflow.
---

# WXQ Tag Preservation & Validation Guard

## Overview

At runtime, `wxq_patch/table_catalog.py` calls `validate_translation(source, translated)` on every single record before encoding it into the Protobuf table. **Any string that fails `validate_translation` is silently rejected (`invalid_translation`), leaving the in-game text untranslated.**

## The 6 Mandatory Validation Invariants (`translation_rules.py`)

Every `(source, translated)` pair in `catalog.json.gz` MUST return `(True, 'ok')` from this exact function:

```python
import re
from collections import Counter

CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
TAG_RE = re.compile(r'<(?:/?[A-Za-z][^>]*|/)>')
PLACEHOLDER_RE = re.compile(
    r'\{[^{}]*\}|%(?:\d+\$)?[-+0 #]*(?:\d+|\*)?(?:\.\d+)?[diuoxXfFeEgGaAcspn%](?![A-Za-z])'
)
CONTROL_TOKEN_RE = re.compile(r'[\u2540-\u257f]')

def validate_translation(source: str, translated: object) -> tuple[bool, str]:
    if not isinstance(translated, str) or not translated.strip():
        return (False, 'empty')
    visible_translation = PLACEHOLDER_RE.sub('', TAG_RE.sub('', translated))
    if CJK_RE.search(visible_translation):
        return (False, 'still_chinese')
    source_tags = TAG_RE.findall(source)
    translated_tags = TAG_RE.findall(translated)
    angle_bracket_label = source.startswith('<{') and source.endswith('>')
    if source_tags != translated_tags and not angle_bracket_label:
        return (False, 'tags_changed')
    if Counter(PLACEHOLDER_RE.findall(source)) != Counter(PLACEHOLDER_RE.findall(translated)):
        return (False, 'placeholders_changed')
    if Counter(CONTROL_TOKEN_RE.findall(source)) != Counter(CONTROL_TOKEN_RE.findall(translated)):
        return (False, 'control_tokens_changed')
    if ';' in source and source.count(';') != translated.count(';'):
        return (False, 'semicolons_changed')
    if len(source) >= 4 and len(translated) > max(len(source) * 8, 48):
        return (False, 'extreme_expansion')
    return (True, 'ok')
```

## Tag-Preserving Alignment for Tier 1 (`hok-ace-translate-id.netlify.app`)

On `hok-ace-translate-id.netlify.app`, the `descCn` field has Unity rich-text tags and control glyphs stripped:
- **Tier 1 `descCn`:** `牺牲：苏烈的等级永久+2。`
- **Tier 1 `desc`:** `Sacrifice: Level Su Lie +2 secara permanen.`
- **Actual `catalog.json.gz` key:** `<a href=10><color=#ffffff>╫<b>牺牲</b></color></a>：苏烈的等级永久+2。`
- **Actual `catalog.json.gz` EN value:** `<a href=10><color=#ffffff>╫<b>Sacrifice</b></color></a>: Su Lie's Level permanently +2.`

### How to Align and Re-inject Tags Safely

1. **Normalize for Matching:** Strip `TAG_RE` and `CONTROL_TOKEN_RE` (`╫`) from `catalog.json.gz` Chinese keys to match against Tier 1's `descCn`.
2. **Re-inject Tag Skeleton:**
   - When the source begins with a tagged keyword prefix (e.g., `<a href=10><color=#ffffff>╫<b>牺牲</b></color></a>：`), preserve the exact tagged prefix from the English catalog value (`<a href=10><color=#ffffff>╫<b>Sacrifice</b></color></a>: `) and attach the Indonesian body (`Level Su Lie +2 secara permanen.`).
   - For inline tags (`<color=#...>...</color>`, `<b>...</b>`), map the inner text segments while keeping `TAG_RE.findall(translated) == TAG_RE.findall(source)` and `CONTROL_TOKEN_RE.findall(translated) == CONTROL_TOKEN_RE.findall(source)`.
3. **Semicolon Rule (`;`):**
   - If the Chinese source contains ASCII `;`, ensure `translated.count(';') == source.count(';')`. If a translator replaces `;` with `,` or `.`, `validate_translation` will reject the string with `semicolons_changed`!

## QtsVFS Capacity Verification Against Real Game Files

Before finalizing `catalog.json.gz`, ALWAYS run `wxq_patch.adaptive.scan` against the user's real unpatched game files at:
`/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals`

Verify that:
- `counts.get('invalid_translation', 0) == 0`
- `counts.get('capacity_skipped', 0) == 0`
- `counts.get('unknown', 0) == 0` (after adding the 108 previously-missing Chinese strings)
