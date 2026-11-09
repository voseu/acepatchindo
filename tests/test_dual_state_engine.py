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
        == f"{hashlib.sha256(b'initial_catalog_bytes_v1').hexdigest()}:id"
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
        == f"{hashlib.sha256(b'modified_catalog_bytes_v2').hexdigest()}:id"
    )


def test_dual_state_patch_lang_switch_id_and_en(monkeypatch) -> None:
    # Test catalog data with dual maps
    data = {
        "schema": 1,
        "version": "1.4.12",
        "baseline_occurrences": 0,
        "reviewed_updates": 0,
        "contextual": [],
        "graphics": [],
        "table_hashes": [],
        "assets": {},
        "unique": {
            "普攻": "Serangan Dasar",  # Chinese -> Indonesian
        },
        "english_updates": [],
        "en_to_id": {
            "Basic Attack": "Serangan Dasar",
        },
        "id_to_en": {
            "Serangan Dasar": "Basic Attack",
        },
        "zh_to_en_gameplay": {
            "普攻": "Basic Attack",
        },
    }

    # 1. Mode ID: translates Chinese & English to Indonesian
    monkeypatch.setenv("CELESLIB_PATCH_LANG", "id")
    cat_id = table_catalog.Catalog(data)
    assert getattr(cat_id, "patch_lang", "id") == "id"

    zh_proto = _make_wxq_table_record("skill_desc_1", "普攻")
    res_zh_id, stats_zh_id = table_catalog.translate_table(zh_proto, 0x1, cat_id)
    assert res_zh_id is not None
    assert "Serangan Dasar".encode("utf-8") in res_zh_id
    assert stats_zh_id["translated"] == 1

    en_proto = _make_wxq_table_record("skill_desc_2", "Basic Attack")
    res_en_id, stats_en_id = table_catalog.translate_table(en_proto, 0x1, cat_id)
    assert res_en_id is not None
    assert "Serangan Dasar".encode("utf-8") in res_en_id
    assert stats_en_id["translated"] == 1

    # 2. Mode EN: translates Chinese & Indonesian back to 100% English
    monkeypatch.setenv("CELESLIB_PATCH_LANG", "en")
    cat_en = table_catalog.Catalog(data)
    assert getattr(cat_en, "patch_lang", "id") == "en"

    res_zh_en, stats_zh_en = table_catalog.translate_table(zh_proto, 0x1, cat_en)
    assert res_zh_en is not None
    assert "Basic Attack".encode("utf-8") in res_zh_en
    assert stats_zh_en["translated"] == 1

    id_proto = _make_wxq_table_record("skill_desc_3", "Serangan Dasar")
    res_id_en, stats_id_en = table_catalog.translate_table(id_proto, 0x1, cat_en)
    assert res_id_en is not None
    assert "Basic Attack".encode("utf-8") in res_id_en
    assert stats_id_en["translated"] == 1

    # 3. UI Language localization
    monkeypatch.setenv("CELESLIB_UI_LANG", "en")
    monkeypatch.setenv("CELESLIB_PATCH_LANG", "id")
    rep_en_ui = adaptive._localize_report_message({
        "message": "English installed and verified. Unknown text was preserved."
    })
    assert "Indonesian Hybrid patch installed" in rep_en_ui["message"]

    monkeypatch.setenv("CELESLIB_UI_LANG", "id")
    rep_id_ui = adaptive._localize_report_message({
        "message": "English installed and verified. Unknown text was preserved."
    })
    assert "Bahasa Indonesia berhasil dipasang" in rep_id_ui["message"]


def test_numeric_template_fallback_handles_live_balance_hotfix() -> None:
    # Baseline unique has +2 in catalog
    baseline_zh = "战斗开始时，随机获得1张卡牌，本局每获胜1次，其等级额外+2。"
    baseline_id = (
        "Saat Combat dimulai, peroleh 1 kartu acak secara cuma-cuma. "
        "Setiap kali menang dalam pertandingan ini, Level-nya bertambah +2."
    )
    data = {
        "schema": 1,
        "version": "1.4.12-id.2",
        "unique": {baseline_zh: baseline_id},
        "contextual": [],
        "english_updates": [],
        "graphics": {},
        "table_hashes": {},
        "baseline_occurrences": {},
        "reviewed_updates": {},
    }
    cat = table_catalog.Catalog(data)

    # Live server hotfix changes +2 -> +3 in the Chinese source string from game protobuf
    hotfix_zh = "战斗开始时，随机获得1张卡牌，本局每获胜1次，其等级额外+3。"
    zh_proto = _make_wxq_table_record("#HOTFIX_KEY#", hotfix_zh)

    patched_bytes, stats = table_catalog.translate_table(
        zh_proto, 0x00BF2528D217FFFA, cat
    )
    assert stats["unknown"] == 0, f"Expected 0 unknown, got {stats}"
    assert stats["translated"] == 1
    expected_id = (
        "Saat Combat dimulai, peroleh 1 kartu acak secara cuma-cuma. "
        "Setiap kali menang dalam pertandingan ini, Level-nya bertambah +3."
    )
    assert expected_id.encode("utf-8") in patched_bytes


def test_clean_work_staging_removes_hardlinked_staged_files_before_install(
    tmp_path: Path, monkeypatch
) -> None:
    import os

    game = tmp_path / "WXQ"
    pkg4_dir = game / "WXQ_Data" / "Package" / "builtin" / "4"
    pkg4_dir.mkdir(parents=True)
    live_db = pkg4_dir / "4.db"
    live_db.write_bytes(b"LIVE_PACKAGE_4_BYTES")

    work = tmp_path / "work"
    staged_dir = work / "staged" / "4" / "4"
    staged_dir.mkdir(parents=True)
    staged_db = staged_dir / "4.db"
    # Simulate hardlink created by previous commit() via os.link
    os.link(live_db, staged_db)
    assert live_db.stat().st_ino == staged_db.stat().st_ino

    repl_dir = work / "replacements" / "4"
    repl_dir.mkdir(parents=True)
    (repl_dir / "OLD.assets").write_bytes(b"STALE")

    seen_staged_exists: list[bool] = []

    def fake_orig_run(action: str, g: Path, a: Path, w: Path) -> dict:
        seen_staged_exists.append((w / "staged").exists() or (w / "replacements").exists())
        return {"state": "current", "message": "English installed and verified."}

    monkeypatch.setattr(adaptive, "_orig_run", fake_orig_run)
    monkeypatch.setattr(adaptive, "_needs_pre_install_restore", lambda g, s: False)

    adaptive._run("install", game, tmp_path / "assets", work)
    assert seen_staged_exists == [False]
    assert not staged_db.exists()
    # Live file in game directory must remain completely intact!
    assert live_db.exists()
    assert live_db.read_bytes() == b"LIVE_PACKAGE_4_BYTES"


def test_partial_game_update_preserves_receipt_and_restores_remaining_packages(
    tmp_path: Path, monkeypatch
) -> None:
    import hashlib
    import json

    game = tmp_path / "WXQ"
    p1 = game / "WXQ_Data" / "Package" / "builtin" / "1" / "1.db"
    p4 = game / "WXQ_Data" / "Package" / "builtin" / "4" / "4.db"
    p1.parent.mkdir(parents=True)
    p4.parent.mkdir(parents=True)

    # Simulate partial game update: 1.db was updated by launcher, 4.db is still patched
    p1.write_bytes(b"UPDATED_BY_LAUNCHER_1_DB")
    patched_p4_bytes = b"PATCHED_4_DB_STILL_LIVE"
    p4.write_bytes(patched_p4_bytes)
    p4_after_sha = hashlib.sha256(patched_p4_bytes).hexdigest()

    r_root = tmp_path / "receipts"
    r_dir = r_root / "1793497168990741300-92b4bcbb"
    r_dir.mkdir(parents=True)
    receipt_data = {
        "state": "complete",
        "action": "install",
        "files": [
            {
                "relative": "WXQ_Data/Package/builtin/1/1.db",
                "before": "00" * 32,
                "after": "11" * 32,  # No longer matches live p1
            },
            {
                "relative": "WXQ_Data/Package/builtin/4/4.db",
                "before": "22" * 32,
                "after": p4_after_sha,  # Still matches live p4!
            },
        ],
    }
    (r_dir / "receipt.json").write_text(json.dumps(receipt_data), encoding="utf-8")
    monkeypatch.setattr(adaptive, "receipt_root", lambda g: r_root)

    # 1. Receipt must STILL match live so prune_stale_state does NOT delete it
    assert adaptive._receipt_matches_live(game, receipt_data) is True
    assert adaptive.find_restore(game) is not None

    # 2. _matching_restore_items must return 4.db and skip updated 1.db
    items = adaptive._matching_restore_items(game)
    assert len(items) == 1
    assert items[0][1]["relative"] == "WXQ_Data/Package/builtin/4/4.db"


def test_lock_and_process_errors_are_localized_in_id(
    tmp_path: Path, monkeypatch
) -> None:
    import json
    import sys

    monkeypatch.setenv("CELESLIB_UI_LANG", "id")
    rep_lock = adaptive._localize_report_message(
        {"message": "Another patch operation is using this installation"}
    )
    assert "Operasi patch lain sedang menggunakan instalasi ini" in rep_lock["message"]

    rep_game = adaptive._localize_report_message(
        {"message": "Close the game before patching: wxq.exe"}
    )
    assert "Tutup game terlebih dahulu sebelum memasang patch: wxq.exe" in rep_game["message"]

    # Verify zero-arg adaptive.main() (as invoked by PyInstaller adaptive_worker)
    res_file = tmp_path / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ace-worker.exe",
            "discover",
            "--work",
            str(tmp_path / "work"),
            "--result",
            str(res_file),
        ],
    )
    code = adaptive.main()
    assert code in (0, 1)
    assert res_file.is_file()
    payload = json.loads(res_file.read_text(encoding="utf-8"))
    assert isinstance(payload.get("message"), str)






