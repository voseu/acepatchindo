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
sys.path.insert(0, str(ROOT / "extracted_source"))

from wxq_patch import table_catalog  # noqa: E402
from wxq_patch import translation_rules as runtime_rules  # noqa: E402

from acepatchindo.glossary import ThreeTierGlossary  # noqa: E402
from acepatchindo.validator import CJK_RE, sanitize_target_text, validate_translation  # noqa: E402

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
    validation_failures = 0

    # 1. Translate all 41,375 unique Chinese -> English entries into Indonesian
    new_unique: dict[str, str] = {}
    for zh_src, en_base in data["unique"].items():
        id_val, tier = glossary.translate_entry(zh_src, baseline_en=en_base)
        ok_local, reason_local = validate_translation(zh_src, id_val)
        ok_runtime, reason_runtime = runtime_rules.validate_translation(zh_src, id_val)
        if not ok_local or not ok_runtime:
            validation_failures += 1
            raise ValueError(
                f"Validation failed ({reason_local}/{reason_runtime}) for {zh_src!r} -> {id_val!r}"
            )
        new_unique[zh_src] = id_val
        tier_counts[tier] += 1
        if en_base and en_base.strip() and id_val != en_base:
            en_to_id_map[en_base] = id_val

    # 2. Add the 108 missing Chinese strings discovered on the user's Windows game
    missing_108 = json.loads(
        (REFS_DIR / "windows_missing_108_zh.json").read_text(encoding="utf-8")
    )
    known_hashes = set(data.get("table_hashes", []))
    for item in missing_108:
        zh_src = item["source_zh"]
        for th in item.get("tables", []):
            known_hashes.add(th)
        if zh_src not in new_unique:
            id_val, tier = glossary.translate_entry(zh_src, baseline_en=None)
            ok_local, reason_local = validate_translation(zh_src, id_val)
            ok_runtime, reason_runtime = runtime_rules.validate_translation(
                zh_src, id_val
            )
            if not ok_local or not ok_runtime:
                validation_failures += 1
                raise ValueError(
                    f"Validation failed ({reason_local}/{reason_runtime}) for missing {zh_src!r} -> {id_val!r}"
                )
            new_unique[zh_src] = id_val
            tier_counts[f"{tier}_missing108"] += 1

    # 3. Translate contextual entries if any ([asset_hex, key, source_zh, target_en])
    for ctx_row in data.get("contextual", []):
        if len(ctx_row) >= 4:
            zh_src, en_base = ctx_row[2], ctx_row[3]
            id_val, _ = glossary.translate_entry(zh_src, baseline_en=en_base)
            ok, reason = runtime_rules.validate_translation(zh_src, id_val)
            if not ok:
                validation_failures += 1
                raise ValueError(f"Contextual validation failed ({reason}) for {zh_src!r}")
            ctx_row[3] = id_val
            if en_base and en_base.strip() and id_val != en_base:
                en_to_id_map[en_base] = id_val

    # 4. Translate all 29,750 english_updates entries ([asset, key, prev_en, target_en, optional_zh])
    eu_count = 0
    for row in data.get("english_updates", []):
        if not isinstance(row, list) or len(row) not in (4, 5):
            raise ValueError(f"Unexpected english_updates row format: {row!r}")
        prev_en = row[2]
        en_target = row[3]
        val_source = row[4] if len(row) == 5 else prev_en

        if len(row) == 5 and CJK_RE.search(val_source):
            if val_source in new_unique and en_target == data["unique"].get(val_source):
                id_val = new_unique[val_source]
            else:
                id_val, _ = glossary.translate_entry(val_source, baseline_en=en_target)
        else:
            cand = sanitize_target_text(val_source, glossary.translate_en_to_id(en_target))
            id_val = cand if runtime_rules.validate_translation(val_source, cand)[0] else en_target

        ok_local, reason_local = validate_translation(val_source, id_val)
        ok_runtime, reason_runtime = runtime_rules.validate_translation(val_source, id_val)
        if not ok_local or not ok_runtime:
            validation_failures += 1
            raise ValueError(
                f"english_updates validation failed ({reason_local}/{reason_runtime}) "
                f"for {val_source!r} -> {id_val!r}"
            )

        row[3] = id_val
        eu_count += 1
        if en_target and en_target.strip() and id_val != en_target:
            en_to_id_map[en_target] = id_val
        if prev_en and prev_en.strip() and id_val != prev_en:
            en_to_id_map.setdefault(prev_en, id_val)

    data["unique"] = new_unique
    data["table_hashes"] = sorted(known_hashes)
    data["version"] = "1.4.12-id.1"

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
    print(f"Built Indonesian catalog: {OUT_CATALOG_GZ}")
    print(f"Total unique entries: {len(new_unique)} (was 41,375)")
    print(f"Total english_updates translated: {eu_count}")
    print(f"Total en_to_id reverse mappings: {len(en_to_id_map)}")
    print(f"Validation failures: {validation_failures}")
    print(f"Tier breakdown: {dict(tier_counts)}")
    print(
        f"Size comparison: {new_size:,} bytes vs original {orig_size:,} bytes "
        f"(delta: {new_size - orig_size:+,} bytes)"
    )


if __name__ == "__main__":
    main()

