#!/usr/bin/env python3
"""Build the Hybrid Gameplay Edition Indonesian catalog.json.gz (v1.4.12-id.2).

41,375 + 108 unique strings & 29,750 english_updates:
- Target gameplay descriptions (Hero cards, skills, talents, contestants) in Indonesian (ID)
  with all embedded entity names strictly in English (EN).
- Everything else (Names/Titles, Equipment, Standalone Effect cards, UI, Menus, Settings,
  Lobby, Shop, Tutorials, Tips, Events, Missions, Achievements, Quick-chat, Rank titles,
  Cosmetics, Mode rules) in clean English (EN).
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "extracted_source"))

from wxq_patch import table_catalog  # noqa: E402
from wxq_patch import translation_rules as runtime_rules  # noqa: E402

from acepatchindo.glossary import ThreeTierGlossary  # noqa: E402
from acepatchindo.hybrid_classifier import HybridClassifier  # noqa: E402
from acepatchindo.tag_aligner import restore_newlines_from_source  # noqa: E402
from acepatchindo.validator import CJK_RE, sanitize_target_text, validate_translation  # noqa: E402
from acepatchindo.windows_108_split import (  # noqa: E402
    WINDOWS_108_HYBRID_MAP,
    WINDOWS_108_NONTARGET_EN,
    WINDOWS_108_TARGET_DESC_ID,
)

EXTRACTED_DIR = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
SOURCE_CATALOG_GZ = EXTRACTED_DIR / "catalog" / "catalog.json.gz"
REFS_DIR = ROOT / "data" / "references"
OUT_DIR = ROOT / "data" / "catalog_checkpoints"
OUT_CATALOG_GZ = OUT_DIR / "catalog.json.gz"
OUT_EN_TO_ID_JSON = OUT_DIR / "en_to_id_map.json"


def _align_en_to_id(en_val: str, id_val: str) -> str | None:
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    classifier = HybridClassifier()
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )

    with gzip.open(SOURCE_CATALOG_GZ, "rt", encoding="utf-8") as f:
        data = json.load(f)

    tier_counts: Counter[str] = Counter()
    en_to_id_map: dict[str, str] = {}
    validation_failures = 0

    # 1. Classify all 41,375 unique Chinese -> English entries
    new_unique: dict[str, str] = {}
    for zh_src, en_base in data["unique"].items():
        if classifier.is_target_unique(zh_src, en_base):
            id_val, tier = glossary.translate_entry(zh_src, baseline_en=en_base)
            if "\n" in zh_src and "\n" not in id_val:
                id_val = restore_newlines_from_source(zh_src, id_val)
            ok_local, reason_local = validate_translation(zh_src, id_val)
            ok_runtime, reason_runtime = runtime_rules.validate_translation(zh_src, id_val)
            if not ok_local or not ok_runtime:
                validation_failures += 1
                raise ValueError(
                    f"Validation failed ({reason_local}/{reason_runtime}) for {zh_src!r} -> {id_val!r}"
                )
            new_unique[zh_src] = id_val
            tier_counts[f"{tier}_target_id"] += 1
            if en_base and en_base.strip() and id_val != en_base:
                aligned = _align_en_to_id(en_base, id_val)
                if aligned:
                    en_to_id_map[en_base] = aligned
        else:
            # Standalone names, equipment, effect cards, UI, tips, achievements stay English
            new_unique[zh_src] = en_base
            tier_counts["nontarget_en"] += 1

    # 2. Add the 108 missing Chinese strings discovered on the user's Windows game
    missing_108 = json.loads(
        (REFS_DIR / "windows_missing_108_zh.json").read_text(encoding="utf-8")
    )
    known_hashes = set(data.get("table_hashes", []))
    for item in missing_108:
        zh_src = item["source_zh"]
        for th in item.get("tables", []):
            known_hashes.add(th)
        if zh_src in WINDOWS_108_HYBRID_MAP:
            val = WINDOWS_108_HYBRID_MAP[zh_src]
            ok_local, reason_local = validate_translation(zh_src, val)
            ok_runtime, reason_runtime = runtime_rules.validate_translation(zh_src, val)
            if not ok_local or not ok_runtime:
                validation_failures += 1
                raise ValueError(
                    f"Validation failed ({reason_local}/{reason_runtime}) for missing {zh_src!r} -> {val!r}"
                )
            new_unique[zh_src] = val
            if zh_src in WINDOWS_108_TARGET_DESC_ID:
                tier_counts["missing108_target_id"] += 1
            else:
                tier_counts["missing108_nontarget_en"] += 1
        else:
            raise ValueError(f"Missing 108 string not found in WINDOWS_108_HYBRID_MAP: {zh_src!r}")

    # 3. Translate contextual entries if any ([asset_hex, key, source_zh, target_en])
    for ctx_row in data.get("contextual", []):
        if len(ctx_row) >= 4:
            zh_src, en_base = ctx_row[2], ctx_row[3]
            if classifier.is_target_unique(zh_src, en_base):
                id_val, _ = glossary.translate_entry(zh_src, baseline_en=en_base)
                ok, reason = runtime_rules.validate_translation(zh_src, id_val)
                if not ok:
                    validation_failures += 1
                    raise ValueError(f"Contextual validation failed ({reason}) for {zh_src!r}")
                ctx_row[3] = id_val
                if en_base and en_base.strip() and id_val != en_base:
                    aligned = _align_en_to_id(en_base, id_val)
                    if aligned:
                        en_to_id_map[en_base] = aligned

    # 4. Process all 29,750 english_updates entries ([asset, key, prev_en, target_en, optional_zh])
    eu_target_count = 0
    eu_nontarget_count = 0
    for row in data.get("english_updates", []):
        if not isinstance(row, list) or len(row) not in (4, 5):
            raise ValueError(f"Unexpected english_updates row format: {row!r}")
        asset = row[0]
        key = row[1]
        prev_en = row[2]
        en_target = row[3]
        val_source = row[4] if len(row) == 5 else prev_en
        opt_zh = val_source if len(row) == 5 and CJK_RE.search(val_source) else ""

        if classifier.is_target_update(asset, key, prev_en, en_target, opt_zh):
            if opt_zh:
                if opt_zh in new_unique and en_target == data["unique"].get(opt_zh):
                    id_val = new_unique[opt_zh]
                else:
                    id_val, _ = glossary.translate_entry(opt_zh, baseline_en=en_target)
            else:
                cand = sanitize_target_text(val_source, glossary.translate_en_to_id(en_target))
                id_val = cand if runtime_rules.validate_translation(val_source, cand)[0] else en_target

            if "\n" in val_source and "\n" not in id_val:
                id_val = restore_newlines_from_source(val_source, id_val)

            ok_local, reason_local = validate_translation(val_source, id_val)
            ok_runtime, reason_runtime = runtime_rules.validate_translation(val_source, id_val)
            if not ok_local or not ok_runtime:
                validation_failures += 1
                raise ValueError(
                    f"english_updates validation failed ({reason_local}/{reason_runtime}) "
                    f"for {val_source!r} -> {id_val!r}"
                )

            row[3] = id_val
            eu_target_count += 1
            if en_target and en_target.strip() and id_val != en_target:
                ok_pair, _ = runtime_rules.validate_translation(en_target, id_val)
                if ok_pair:
                    en_to_id_map[en_target] = id_val
        else:
            # Non-target stays clean English
            row[3] = en_target
            eu_nontarget_count += 1

    data["unique"] = new_unique
    data["table_hashes"] = sorted(known_hashes)
    data["version"] = "1.4.12-id.2"

    # Verify Catalog(data) instantiates cleanly with wxq_patch.table_catalog.Catalog
    _verified_cat = table_catalog.Catalog(data)
    assert len(_verified_cat.unique) == 41483

    # Write minified gzip level-9 catalog
    minified_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    compressed = gzip.compress(minified_bytes, compresslevel=9)
    OUT_CATALOG_GZ.write_bytes(compressed)

    OUT_EN_TO_ID_JSON.write_text(
        json.dumps(en_to_id_map, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    orig_size = SOURCE_CATALOG_GZ.stat().st_size
    new_size = OUT_CATALOG_GZ.stat().st_size
    target_u_tot = sum(v for k, v in tier_counts.items() if "target_id" in k)
    nontarget_u_tot = sum(v for k, v in tier_counts.items() if "nontarget_en" in k)
    print(f"Built Indonesian Hybrid catalog: {OUT_CATALOG_GZ}")
    print(f"Total unique entries: {len(new_unique)} (was 41,375)")
    print(f"Target gameplay unique translated: {target_u_tot}")
    print(f"Non-target unique kept English: {nontarget_u_tot}")
    print(f"Total english_updates: target={eu_target_count}, nontarget={eu_nontarget_count}")
    print(f"Total en_to_id reverse mappings: {len(en_to_id_map)}")
    print(f"Validation failures: {validation_failures}")
    print(f"Tier breakdown: {dict(tier_counts)}")
    print(
        f"Size comparison: {new_size:,} bytes vs original {orig_size:,} bytes "
        f"(delta: {new_size - orig_size:+,} bytes)"
    )


if __name__ == "__main__":
    main()
