"""Tests for Dual-State (ZH->ID and EN->ID) table_catalog & adaptive auto-restore."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from wxq_patch import adaptive, table_catalog

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


def _make_wxq_table_record(key: str, text: str) -> bytes:
    """Build authentic WXQ localization Protobuf record: field 1 -> {field 1: key, field 2: text}."""
    key_b = key.encode("utf-8")
    txt_b = text.encode("utf-8")
    nested = (
        b"\x0a"
        + _encode_varint(len(key_b))
        + key_b
        + b"\x12"
        + _encode_varint(len(txt_b))
        + txt_b
    )
    return b"\x0a" + _encode_varint(len(nested)) + nested


def test_dual_state_translates_chinese_english_and_is_idempotent(tmp_path: Path) -> None:
    cat_path = tmp_path / "catalog.json.gz"
    cat_path.write_bytes(ID_CATALOG_GZ.read_bytes())

    en_to_id_data = json.loads(EN_TO_ID_JSON.read_text(encoding="utf-8"))
    with gzip.open(tmp_path / "en_to_id.json.gz", "wt", encoding="utf-8") as f:
        json.dump(en_to_id_data, f, ensure_ascii=False)

    cat = table_catalog.load_catalog(cat_path)
    sample_en, sample_id = next(iter(en_to_id_data.items()))
    sample_zh, sample_zh_id = next(
        (k, v) for k, v in cat.unique.items() if k != v
    )

    # 1. Clean Chinese Protobuf record -> Indonesian
    zh_proto = _make_wxq_table_record("#TEST_ZH#", sample_zh)
    patched_zh, stats_zh = table_catalog.translate_table(
        zh_proto, 0x00BF2528D217FFFA, cat
    )
    assert patched_zh is not None
    assert stats_zh["records"] == 1
    assert stats_zh["translated"] == 1
    assert stats_zh["unknown"] == 0
    assert sample_zh_id.encode("utf-8") in patched_zh

    # 2. Already-English Protobuf record -> Indonesian
    en_proto = _make_wxq_table_record("#TEST_EN#", sample_en)
    patched_en, stats_en = table_catalog.translate_table(
        en_proto, 0x00BF2528D217FFFA, cat
    )
    assert patched_en is not None
    assert stats_en["records"] == 1
    assert stats_en["translated"] == 1
    assert sample_id.encode("utf-8") in patched_en

    # 3. Idempotency: Already-Indonesian Protobuf record -> already_english == 1, translated == 0
    _, stats_id = table_catalog.translate_table(
        patched_en, 0x00BF2528D217FFFA, cat
    )
    assert stats_id["translated"] == 0
    assert stats_id["already_english"] == 1


def test_adaptive_auto_restores_chinese_originals_before_install(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[str] = []

    def fake_matching_restore_items(game: Path) -> list[tuple[Path, dict]]:
        return [(tmp_path / "receipt.json", {"relative": "WXQ_Data/Package/builtin/4/4.db"})]

    def fake_scan(game: Path, assets: Path, work: Path, *, materialize: bool = True):
        return (["non_empty_plan"], {}, {"translated": 10}, [])

    def fake_orig_run(action: str, game: Path, assets: Path, work: Path) -> dict:
        calls.append(action)
        return {
            "state": "current",
            "action": action,
            "message": "English installed and verified. Unknown text was preserved.",
        }

    monkeypatch.setattr(adaptive, "_matching_restore_items", fake_matching_restore_items)
    monkeypatch.setattr(adaptive, "scan", fake_scan)
    monkeypatch.setattr(adaptive, "_orig_run", fake_orig_run)

    res = adaptive._run("install", tmp_path / "game", tmp_path / "assets", tmp_path / "work")
    assert calls == ["restore", "install"]
    assert res["action"] == "install"
    assert (
        res["message"]
        == "Bahasa Indonesia berhasil dipasang dan diverifikasi. Teks tidak dikenal dipertahankan."
    )


def test_adaptive_unconditionally_restores_v1_full_id_when_catalog_sha_differs(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[str] = []

    game_dir = tmp_path / "game"
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    cat_path = assets_dir / "catalog.json.gz"
    cat_path.write_bytes(b"initial_catalog_bytes_v1")
    work_dir = tmp_path / "work"

    rcp_dir = tmp_path / "rcp1"
    rcp_dir.mkdir(parents=True, exist_ok=True)
    rcp_file = rcp_dir / "receipt.json"
    rcp_file.write_text("{}", encoding="utf-8")

    def fake_matching_restore_items(game: Path) -> list[tuple[Path, dict]]:
        return [(rcp_file, {})]

    def fake_receipt_root(game: Path) -> Path:
        return tmp_path

    def fake_scan(game: Path, assets: Path, work: Path, *, materialize: bool = True):
        # Empty plans simulating already-patched files on disk (v1.4.12-id.1 state)
        return ([], {}, {"translated": 0}, [])

    def fake_orig_run(action: str, game: Path, assets: Path, work: Path) -> dict:
        calls.append(action)
        return {
            "state": "current",
            "action": action,
            "message": "English installed and verified. Unknown text was preserved.",
        }

    monkeypatch.setattr(adaptive, "_matching_restore_items", fake_matching_restore_items)
    monkeypatch.setattr(adaptive, "receipt_root", fake_receipt_root)
    monkeypatch.setattr(adaptive, "scan", fake_scan)
    monkeypatch.setattr(adaptive, "_orig_run", fake_orig_run)

    # 1. First run: missing patcher_catalog_sha256.txt triggers restore then install
    calls.clear()
    res1 = adaptive._run("install", game_dir, assets_dir, work_dir)
    assert calls == ["restore", "install"]
    assert res1["action"] == "install"
    sha_file = rcp_dir / "patcher_catalog_sha256.txt"
    assert sha_file.exists()
    assert (
        sha_file.read_text(encoding="utf-8").strip()
        == hashlib.sha256(b"initial_catalog_bytes_v1").hexdigest()
    )

    # 2. Second run: matching catalog SHA is idempotent (no redundant restore)
    calls.clear()
    res2 = adaptive._run("install", game_dir, assets_dir, work_dir)
    assert calls == ["install"]
    assert res2["action"] == "install"

    # 3. Third run: modified catalog SHA triggers restore then install again
    cat_path.write_bytes(b"modified_catalog_bytes_v2")
    calls.clear()
    res3 = adaptive._run("install", game_dir, assets_dir, work_dir)
    assert calls == ["restore", "install"]
    assert res3["action"] == "install"
    assert (
        sha_file.read_text(encoding="utf-8").strip()
        == hashlib.sha256(b"modified_catalog_bytes_v2").hexdigest()
    )


