#!/usr/bin/env python3
"""Extract Tier 1 (ID), Tier 2 (EN), and the 108 missing Chinese strings from the Windows game."""

from __future__ import annotations

import html
import json
import re
import struct
import sys
from pathlib import Path

import httpx
from lz4.block import LZ4BlockError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extracted_source"))

from wxq_patch import adaptive, table_catalog  # noqa: E402
from wxq_patch.translation_rules import CJK_RE  # noqa: E402

REFS_DIR = ROOT / "data" / "references"
EXTRACTED_DIR = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
CATALOG_DIR = EXTRACTED_DIR / "catalog"
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

    marker = "const entries = "
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Failed to locate const entries on Tier 2 site")

    entries, _ = json.JSONDecoder().raw_decode(text, idx + len(marker))
    for item in entries:
        for k, v in list(item.items()):
            if isinstance(v, str):
                item[k] = html.unescape(v)
    return entries


def _parse_table_records(raw: bytes) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for tag, nested, _encoded in table_catalog.fields(raw):
        if tag != 10:
            raise table_catalog.ProtobufError("Unexpected top-level field")
        parts = list(table_catalog.fields(nested))
        if len(parts) != 2 or sorted(p[0] for p in parts) != [10, 18]:
            raise table_catalog.ProtobufError(
                "Missing, duplicate, or unknown record fields"
            )
        key = next(p[1].decode("utf-8") for p in parts if p[0] == 10)
        source = next(p[1].decode("utf-8") for p in parts if p[0] == 18)
        records.append((key, source))
    if not records:
        raise table_catalog.ProtobufError("Empty table")
    return records


def extract_windows_missing_strings() -> list[dict]:
    if not WINDOWS_ORIGINALS.exists():
        raise FileNotFoundError(
            f"Windows originals path not mounted: {WINDOWS_ORIGINALS}\n"
            "Mount with: udisksctl mount -b /dev/nvme0n1p3 -o ro"
        )

    cat = adaptive.load_catalog(CATALOG_DIR)
    if cat is None:
        raise RuntimeError(f"Failed to load baseline catalog from {CATALOG_DIR}")

    pkgs, _ = adaptive.discover(WINDOWS_ORIGINALS, cat)
    missing_by_zh: dict[str, dict] = {}

    for pkg in pkgs:
        slots = pkg.build_slot_map()
        index_data = pkg.index_path.read_bytes()
        scan_tables = pkg.package_id == "1" or not cat.known.isdisjoint(pkg.entries)

        for h in sorted(pkg.entries):
            if not scan_tables and h not in cat.graphics:
                continue
            if h in cat.graphics:
                continue

            chunk_map = slots.get(h, {})
            if not chunk_map or sorted(chunk_map) != list(range(len(chunk_map))):
                continue

            try:
                raw = pkg.extract(h, slots)
                expected_size = struct.unpack_from(
                    "<I", index_data, pkg.entries[h].entry_offset + 44
                )[0]
                if len(raw) != expected_size:
                    continue
                records = _parse_table_records(raw)
            except (
                ValueError,
                OSError,
                KeyError,
                LZ4BlockError,
                table_catalog.ProtobufError,
                UnicodeDecodeError,
            ):
                continue

            asset_hex = f"{h:016X}"
            for key, source in records:
                identity = (asset_hex, key, source)
                if identity in cat.english_updates:
                    continue
                if source in cat.targets:
                    continue
                if not CJK_RE.search(source):
                    continue
                if cat.lookup(h, key, source) is None:
                    slot = missing_by_zh.setdefault(
                        source,
                        {"source_zh": source, "count": 0, "tables": []},
                    )
                    slot["count"] += 1
                    if asset_hex not in slot["tables"]:
                        slot["tables"].append(asset_hex)

    return sorted(missing_by_zh.values(), key=lambda x: (-x["count"], x["source_zh"]))


def main() -> None:
    if not EXTRACTED_DIR.exists() or not (ROOT / "extracted_source" / "wxq_patch").exists():
        raise FileNotFoundError(
            "Baseline extracted directories are missing in workspace."
        )

    REFS_DIR.mkdir(parents=True, exist_ok=True)

    tier1 = fetch_tier1_netlify()
    tier1_path = REFS_DIR / "tier1_wiki_id.json"
    tier1_path.write_text(
        json.dumps(tier1, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"[Tier 1] Saved {tier1_path} (lords={len(tier1['lords'])}, talent={len(tier1['talent'])})"
    )

    tier2 = fetch_tier2_hokace_wiki()
    tier2_path = REFS_DIR / "tier2_wiki_en.json"
    tier2_path.write_text(
        json.dumps(tier2, ensure_ascii=False, indent=2), encoding="utf-8"
    )
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

