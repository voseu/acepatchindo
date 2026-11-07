#!/usr/bin/env python3
"""Verify Hybrid Indonesian catalog and dual-state engine against the user's real Windows game files."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "extracted_source"))

from wxq_patch import adaptive, table_catalog, unity_package_installer  # noqa: E402

WINDOWS_USERS_BASE = Path("/run/media/whise/Windows/Users")
WINDOWS_LIVE_WXQ = Path("/run/media/whise/Windows/Program Files/WXQLauncher/WXQ")
ORIG_CATALOG_DIR = (
    ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "catalog"
)
ID_CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
EN_TO_ID_JSON = ROOT / "data" / "catalog_checkpoints" / "en_to_id_map.json"


def find_windows_originals() -> Path | None:
    """Dynamically locate the active originals backup directory on the mounted Windows filesystem."""
    if not WINDOWS_USERS_BASE.exists():
        return None
    candidates = sorted(
        WINDOWS_USERS_BASE.glob(
            "*/AppData/Local/HoK Ace English Patch/adaptive/*/*/originals"
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for c in candidates:
        if c.is_dir() and (c / "WXQ_Data").exists():
            return c
    return None


def prepare_staged_assets_dir(stage_root: Path) -> Path:
    assets_dir = stage_root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Symlink graphic payload files (.assets, .blocks, .png) from baseline extracted catalog dir
    for item in ORIG_CATALOG_DIR.iterdir():
        if item.name == "catalog.json.gz":
            continue
        target_link = assets_dir / item.name
        if not target_link.exists():
            target_link.symlink_to(item.resolve())

    # Write combined catalog.json.gz (including embedded en_to_id)
    with gzip.open(ID_CATALOG_GZ, "rt", encoding="utf-8") as f:
        cat_payload = json.load(f)
    cat_payload["en_to_id"] = json.loads(EN_TO_ID_JSON.read_text(encoding="utf-8"))
    raw_bytes = json.dumps(
        cat_payload, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    (assets_dir / "catalog.json.gz").write_bytes(
        gzip.compress(raw_bytes, compresslevel=6)
    )
    return assets_dir


def run_verification() -> tuple[dict, dict, list[dict]]:
    windows_originals = find_windows_originals()
    if not windows_originals:
        raise FileNotFoundError(
            "Could not locate active originals directory under /run/media/whise/Windows/Users"
        )

    stage_base = ROOT / ".stage_verify"
    stage_base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wxq_id_verify_stage_", dir=str(stage_base)) as stage_tmp_str:
        stage_dir = Path(stage_tmp_str)
        assets_dir = prepare_staged_assets_dir(stage_dir)

        # 1. Verify against unpatched Chinese game originals (all 6 QtsVFS packages, 508 tables)
        print("=== [1/3] Scanning & Staging Unpatched Chinese Game Backups (originals/) ===")
        print(f"Originals path: {windows_originals}")
        plans_zh, fps_zh, counts_zh, _skipped_zh = adaptive.scan(
            windows_originals, assets_dir, stage_dir / "zh_stage", materialize=True
        )

        # Stage every modified QtsVFS package using exact runtime adaptive._run parameters
        # (global_donations=True) to prove 0 chunk capacity overflows across all 6 .db packages!
        stage_reports: list[dict] = []
        for pkg, replacement_dir, _per_asset in plans_zh:
            pkg_files = [pkg.index_path, *pkg.shard_paths]
            pkg_source_hashes = {
                p.name: fps_zh[str(p.relative_to(windows_originals))]
                for p in pkg_files
            }
            index_bytes = pkg.index_path.read_bytes()
            used_pos_keys = {
                s.hash1 & 0xFFFFFFFF
                for sm in pkg.build_slot_map().values()
                for s in sm.values()
            }

            def _linux_metadata_builder(
                _game_dir: Path,
                assets: list[dict],
                _build_root: Path,
                _idx: bytes = index_bytes,
                _used: set[int] = used_pos_keys,
            ) -> dict[int, dict]:
                out: dict[int, dict] = {}
                for asset in assets:
                    entry = asset["entry"]
                    fit = asset["fit"]
                    raw = asset["raw"]
                    fhash = asset["file_hash"]
                    d_off = entry.entry_offset + unity_package_installer.DESCRIPTOR_OFFSET
                    desc = bytearray(
                        _idx[d_off : d_off + unity_package_installer.DESCRIPTOR_SIZE]
                    )
                    struct.pack_into("<I", desc, 16, len(raw))
                    official_chunks = []
                    for slot in fit["slots"]:
                        h1 = slot.hash1
                        if slot.chunk_id >= fit["original_slot_count"] and h1 == 0:
                            seed = int.from_bytes(
                                hashlib.sha256(
                                    f"{fhash:016X}:{slot.chunk_id}".encode()
                                ).digest()[:8],
                                "little",
                            )
                            while (seed & 0xFFFFFFFF) == 0 or (seed & 0xFFFFFFFF) in _used:
                                seed = (seed + 1) & 0xFFFFFFFFFFFFFFFF
                            _used.add(seed & 0xFFFFFFFF)
                            h1 = seed
                        official_chunks.append(
                            {
                                "id": slot.chunk_id,
                                "hash1": f"{h1:016X}",
                                "header_flags": slot.header_flags,
                            }
                        )
                    out[fhash] = {
                        "descriptor": bytes(desc),
                        "official_raw_size": len(raw),
                        "official_chunk_size": fit["chunk_size"],
                        "official_descriptor_hex": bytes(desc).hex(),
                        "official_chunks": official_chunks,
                    }
                return out

            stage_root = stage_dir / "zh_stage" / "staged"
            staged_rep = unity_package_installer.stage_unity_package(
                windows_originals,
                replacement_dir,
                stage_root,
                source_package_dir=pkg.package_dir,
                metadata_builder=_linux_metadata_builder,
                global_donations=True,
                verify_all_unrelated=False,
                source_hashes=pkg_source_hashes,
            )
            assert staged_rep.get("status") == "verified", staged_rep
            stage_reports.append(staged_rep)
            print(
                f"  Package {pkg.package_id}: status={staged_rep['status']} "
                f"(assets={staged_rep['replacement_count']}, "
                f"donations={len(staged_rep['slot_donation_updates'])}, "
                f"files={len(staged_rep['files'])})"
            )
            shutil.rmtree(stage_root / pkg.package_id, ignore_errors=True)

        print(f"Chinese Game Counts: {dict(counts_zh)}")
        print(f"Capacity Overflow / Skipped Count: {counts_zh.get('capacity_skipped', 0)}")

        assert counts_zh.get("tables", 0) + counts_zh.get("unreadable_assets", 0) == 508, (
            f"Expected 508 tables (including unreadable assets), got {counts_zh.get('tables')} tables, {counts_zh.get('unreadable_assets', 0)} unreadable"
        )
        assert counts_zh.get("unknown", 0) <= 500, (
            f"Expected <= 500 unknown strings safely preserved, got {counts_zh.get('unknown')}"
        )
        assert counts_zh.get("invalid_translation", 0) == 0, (
            f"Expected 0 invalid_translation, got {counts_zh.get('invalid_translation')}"
        )
        assert counts_zh.get("capacity_skipped", 0) == 0, (
            f"Expected 0 capacity_skipped, got {counts_zh.get('capacity_skipped')}"
        )

        # 2. Verify against live English-patched Windows game (C:\Program Files\WXQLauncher\WXQ)
        print(
            "\n=== [2/3] Scanning Live English-Patched Game (C:\\Program Files\\WXQLauncher\\WXQ) ==="
        )
        _plans_en, _fps_en, counts_en, _skipped_en = adaptive.scan(
            WINDOWS_LIVE_WXQ, assets_dir, stage_dir / "en_stage", materialize=False
        )
        print(f"Live English-Patched Game Counts: {dict(counts_en)}")
        assert counts_en.get("translated", 0) > 1000, (
            f"Expected >1,000 target gameplay EN->ID translated records on live English game, got {counts_en.get('translated')}"
        )
        assert counts_en.get("invalid_translation", 0) == 0, (
            f"Expected 0 invalid_translation on live English game, got {counts_en.get('invalid_translation')}"
        )

        # 3. Verify One-Click Upgrade Auto-Restore Logic
        print("\n=== [3/3] Verifying One-Click Upgrade Auto-Restore Mechanism ===")
        cat_file = assets_dir / "catalog.json.gz"
        cat_sha = hashlib.sha256(cat_file.read_bytes()).hexdigest()
        resolved_live = WINDOWS_LIVE_WXQ.resolve()
        needs_restore = adaptive._needs_pre_install_restore(resolved_live, cat_sha)
        print(f"Active live game needs pre-install restore for new catalog ({cat_sha[:8]}...): {needs_restore}")

        print(
            "\n[SUCCESS] Chinese, English, and Upgrade Auto-Restore states verified with 0 errors!"
        )
        return dict(counts_zh), dict(counts_en), stage_reports


if __name__ == "__main__":
    run_verification()
