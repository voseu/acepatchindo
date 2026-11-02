#!/usr/bin/env python3
"""Upgrade wxq_patch Python 3.12 worker modules for Indonesian + Dual-State (ZH->ID & EN->ID) support."""

from __future__ import annotations

import gzip
import json
import marshal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "extracted_source"))

from wxq_patch import translation_rules as runtime_rules  # noqa: E402

from acepatchindo.dual_state_patch import (  # noqa: E402
    render_adaptive_source,
    render_table_catalog_source,
)

WXQ_DIR = ROOT / "extracted_source" / "wxq_patch"
ORIG_CATALOG_GZ = (
    ROOT
    / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
    / "catalog"
    / "catalog.json.gz"
)
ID_CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
EN_TO_ID_JSON = ROOT / "data" / "catalog_checkpoints" / "en_to_id_map.json"


def _align_en_to_id_pair(en_val: str, id_val: str) -> str | None:
    """Ensure (en_val -> id_val) passes runtime validate_translation(en_val, id_val)."""
    ok, reason = runtime_rules.validate_translation(en_val, id_val)
    if ok:
        return id_val
    if reason == "semicolons_changed" and ";" in en_val:
        needed = en_val.count(";") - id_val.count(";")
        repaired = id_val
        while needed > 0 and ", " in repaired:
            repaired = repaired.replace(", ", "; ", 1)
            needed -= 1
        if runtime_rules.validate_translation(en_val, repaired)[0]:
            return repaired
    return None


def build_en_to_id_dict() -> dict[str, str]:
    with gzip.open(ORIG_CATALOG_GZ, "rt", encoding="utf-8") as f:
        orig_cat = json.load(f)
    with gzip.open(ID_CATALOG_GZ, "rt", encoding="utf-8") as f:
        id_cat = json.load(f)

    id_targets: set[str] = set(id_cat["unique"].values())
    for row in id_cat.get("contextual", []):
        if len(row) >= 4:
            id_targets.add(row[3])
    for row in id_cat.get("english_updates", []):
        if len(row) >= 4:
            id_targets.add(row[3])

    en_to_id: dict[str, str] = {}
    for zh, en_val in orig_cat["unique"].items():
        id_val = id_cat["unique"].get(zh)
        if en_val and id_val and en_val != id_val and en_val not in id_targets:
            aligned = _align_en_to_id_pair(en_val, id_val)
            if aligned:
                en_to_id[en_val] = aligned

    # Only map current 1.4.12 English targets (orig_row[3]), never stale cross-key orig_row[2]
    for orig_row, id_row in zip(
        orig_cat.get("english_updates", []), id_cat.get("english_updates", [])
    ):
        en_curr = orig_row[3]
        id_val = id_row[3]
        if en_curr and id_val and en_curr != id_val and en_curr not in id_targets:
            aligned = _align_en_to_id_pair(en_curr, id_val)
            if aligned:
                en_to_id[en_curr] = aligned

    return en_to_id


def patch_table_catalog_pyc() -> None:
    tc_pyc = WXQ_DIR / "table_catalog.pyc"
    orig_backup = WXQ_DIR / "_orig_table_catalog.pyc"
    if not orig_backup.exists():
        orig_backup.write_bytes(tc_pyc.read_bytes())

    en_to_id = build_en_to_id_dict()
    EN_TO_ID_JSON.write_text(
        json.dumps(en_to_id, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    orig_raw = orig_backup.read_bytes()
    header, orig_marshal = orig_raw[:16], orig_raw[16:]
    src = render_table_catalog_source(orig_marshal)
    code_obj = compile(src, "wxq_patch/table_catalog.py", "exec", optimize=0)
    tc_pyc.write_bytes(header + marshal.dumps(code_obj))
    print(
        f"Patched {tc_pyc} with self-contained Dual-State engine "
        f"(en_to_id={len(en_to_id):,} validated mappings)."
    )


def patch_adaptive_pyc() -> None:
    ad_pyc = WXQ_DIR / "adaptive.pyc"
    orig_backup = WXQ_DIR / "_orig_adaptive.pyc"
    if not orig_backup.exists():
        orig_backup.write_bytes(ad_pyc.read_bytes())

    orig_raw = orig_backup.read_bytes()
    header, orig_marshal = orig_raw[:16], orig_raw[16:]
    src = render_adaptive_source(orig_marshal)
    code_obj = compile(src, "wxq_patch/adaptive.py", "exec", optimize=0)
    ad_pyc.write_bytes(header + marshal.dumps(code_obj))
    print(f"Patched {ad_pyc} with Automatic Pre-Install Chinese Originals Restore.")


if __name__ == "__main__":
    patch_table_catalog_pyc()
    patch_adaptive_pyc()
