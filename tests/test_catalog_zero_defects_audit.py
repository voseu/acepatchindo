"""Zero-Defect Full-Catalog Forensic Audit Test Suite."""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import pytest
from acepatchindo.validator import validate_translation

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
INDEX_PATH = ROOT / "data" / "references" / "hybrid_vfs_index.json"


@pytest.fixture(scope="module")
def catalog_data():
    if not CATALOG_PATH.exists():
        pytest.fail(f"Catalog checkpoint missing at {CATALOG_PATH}")
    with gzip.open(CATALOG_PATH, "rt", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def index_data():
    if not INDEX_PATH.exists():
        pytest.fail(f"Index missing at {INDEX_PATH}")
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def test_01_target_coverage_restored(index_data):
    """Assertion 1: stats['target_unique_count'] >= 5200."""
    stats = index_data.get("stats", {})
    target_count = stats.get("target_unique_count", 0)
    assert target_count >= 5200, f"Expected target_unique_count >= 5200, got {target_count}"


def test_02_zero_ambiguous_level_formula(catalog_data):
    """Assertion 2: Zero ambiguous Level formula calques across unique and english_updates."""
    bad_level_re = re.compile(
        r"\bLevel\s+\d+\s+(?:(?:\[[^\]]+\]|<[^>]+>|\S+)\s+)*?Hero\b[^.\n]*?\+\d+",
        re.IGNORECASE,
    )
    all_values = list(catalog_data["unique"].values()) + [
        row[3] for row in catalog_data["english_updates"]
    ]
    for val in all_values:
        assert not bad_level_re.search(val), f"Ambiguous Level formula detected: {val!r}"
        assert "sebesar Level 1 Hero" not in val, f"Pei calque detected: {val!r}"
        assert "sebesar setengah Level 1 Hero" not in val, f"Pei calque detected: {val!r}"


def test_03_zero_glossary_leaks(catalog_data):
    """Assertion 3: Zero glossary leaks across unique and english_updates."""
    all_values = list(catalog_data["unique"].values()) + [
        row[3] for row in catalog_data["english_updates"]
    ]

    for val in all_values:
        # Central Plain singular check (must be Central Plains)
        assert not re.search(r"\bCentral Plain(?![sS])\b", val), f"Found singular Central Plain: {val!r}"

        # Glitch Robot leaks
        assert "Gangguan Robot" not in val, f"Found Gangguan Robot: {val!r}"
        assert "Broken Robot" not in val, f"Found Broken Robot: {val!r}"
        assert "Glitch Bots" not in val, f"Found Glitch Bots: {val!r}"

        # Kekuatan Misterius leaks
        assert "Misterius Kekuatan" not in val, f"Found Misterius Kekuatan: {val!r}"
        assert "Misteri Kekuatan" not in val, f"Found Misteri Kekuatan: {val!r}"

        # di arena leaks
        assert "medan tempur" not in val, f"Found medan tempur: {val!r}"
        assert "di field" not in val, f"Found di field: {val!r}"

        # Zhulu Plateau leaks
        assert "[Zhuolu]" not in val, f"Found [Zhuolu]: {val!r}"
        assert "[Zhu Lu]" not in val, f"Found [Zhu Lu]: {val!r}"

        # Gan & Mo leaks
        assert "Mo Xie" not in val, f"Found Mo Xie: {val!r}"
        assert "General Moye" not in val, f"Found General Moye: {val!r}"
        assert "Ganjiang Moye" not in val, f"Found Ganjiang Moye: {val!r}"

        # Word order calques
        assert "terhubung Hero" not in val, f"Found terhubung Hero: {val!r}"
        assert "terdekat musuh" not in val, f"Found terdekat musuh: {val!r}"
        assert "asli lokasi" not in val, f"Found asli lokasi: {val!r}"

        # Bad phrasing leaks
        assert "2 Renovation" not in val, f"Found 2 Renovation: {val!r}"
        assert "Round1 {LordHp}" not in val, f"Found Round1 {{LordHp}}: {val!r}"
        assert "Round1{LordHp}" not in val, f"Found Round1{{LordHp}}: {val!r}"
        assert "Eternal Waktu Putaran" not in val, f"Found Eternal Waktu Putaran: {val!r}"
        assert "dapat rekor 12" not in val, f"Found dapat rekor 12: {val!r}"


def test_04_exact_inspection_of_previously_failed_cards(catalog_data):
    """Assertion 4: Exact inspection of previously failed cards in catalog['unique']."""
    unique = catalog_data["unique"]

    # 1. Risk Hedging
    zh_risk = "战斗失败时额外获得2次刷新，每回合开始时恢复1{LordHp}。"
    assert zh_risk in unique, f"Missing {zh_risk} in unique"
    val_risk = unique[zh_risk]
    assert "Combat fails" not in val_risk
    assert "Renovation" not in val_risk
    assert "Refresh" in val_risk
    assert "{LordHp}" in val_risk

    # 2. Power Up Module
    zh_power = "攻击蹭蹭涨每1点神秘力量提供的法术攻击力提升至8。"
    assert zh_power in unique, f"Missing {zh_power} in unique"
    val_power = unique[zh_power]
    assert "Misterius Kekuatan" not in val_power
    assert "adalah meningkat" not in val_power
    assert "Kekuatan Misterius" in val_power

    # 3. Eternal Time Loop
    zh_loop = "获得1张更强力的<color=#ffffff><b>永恒时之回环</b></color>，可以记录12张英雄牌或效果牌。"
    assert zh_loop in unique, f"Missing {zh_loop} in unique"
    val_loop = unique[zh_loop]
    assert "Eternal Time Loop" in val_loop
    assert "Eternal Waktu Putaran" not in val_loop
    assert "rekor" not in val_loop
    assert "WXQCANON" not in val_loop
    assert "sebuah lebih" not in val_loop, f"sebuah lebih detected in {val_loop!r}"
    assert "capable" not in val_loop, f"capable detected in {val_loop!r}"

    # 4. Directed Transfer
    zh_transfer = "╥阿科米亚核心的等级会优先分配给<color=#FFE897>穿戴装备最多的【日落海】英雄</color>，最多分配200级。"
    assert zh_transfer in unique, f"Missing {zh_transfer} in unique"
    val_transfer = unique[zh_transfer]
    assert not val_transfer.startswith("<color=#FFE897>Level")
    assert "<color=#FFE897>" in val_transfer

    # 5. Prepare Tooltip
    zh_prep = "卡牌的╬整备效果，会在回合开始阶段触发。刚刚上场的卡牌，其╬整备效果不会生效。"
    assert zh_prep in unique, f"Missing {zh_prep} in unique"
    val_prep = unique[zh_prep]
    assert "╬Prepare" in val_prep
    assert "A Card's" not in val_prep

    # 6. Many Friends (上阵6名【三分之地】英雄，获得1张秘技牌<b>朋友多多</b>。)
    zh_friends = "上阵6名【三分之地】英雄，获得1张秘技牌<b>朋友多多</b>。"
    assert zh_friends in unique, f"Missing {zh_friends} in unique"
    val_friends = unique[zh_friends]
    assert "<b>Many Friends</b>" in val_friends, f"Missing <b>Many Friends</b>: {val_friends!r}"
    assert "Secara acak mengambil 4" not in val_friends, f"Injected description in tag: {val_friends!r}"

    # 7. Copier linked card (指定1名1-3阶英雄，获得该英雄牌。)
    zh_copier = "指定1名1-3阶英雄，获得该英雄牌。"
    assert zh_copier in unique, f"Missing {zh_copier} in unique"
    val_copier = unique[zh_copier]
    assert "itu Kartu Hero" not in val_copier, f"Calque 'itu Kartu Hero' found in {val_copier!r}"
    assert "Kartu Hero tersebut" in val_copier or "Pilih 1 Hero" in val_copier

    # 8. Crimson Leaf Edge (枫叶舞 50% Level retention)
    zh_arli = "<color=#ffffff><b>枫叶舞</b></color>英雄离场后，其真实等级的50%会保留给下一个<color=#ffffff><b>枫叶舞</b></color>英雄，限一次。"
    assert zh_arli in unique, f"Missing {zh_arli} in unique"
    val_arli = unique[zh_arli]
    assert not val_arli.startswith("After a"), f"Untranslated English start: {val_arli!r}"
    assert "Maple Leaf Dance" in val_arli

    # 9. Support Tactics, Divine Descent, and Glory of the Past in english_updates
    upd_map = {row[1]: row[3] for row in catalog_data["english_updates"]}
    assert "#23F7828C95FCE783#" in upd_map, "Missing Support Tactics #23F7828C95FCE783# in english_updates"
    assert "#FCC75C059E4BD0DD#" in upd_map, "Missing Divine Descent #FCC75C059E4BD0DD# in english_updates"
    assert "#60D2A4FEE27099D9#" in upd_map, "Missing Glory of the Past #60D2A4FEE27099D9# in english_updates"

    val_support = upd_map["#23F7828C95FCE783#"]
    val_divine = upd_map["#FCC75C059E4BD0DD#"]
    val_glory = upd_map["#60D2A4FEE27099D9#"]

    assert "Fleeting" in val_support
    assert "Membekukan" in val_divine or "Fleeting" in val_divine
    assert "Awakened" in val_glory or "Talent" in val_glory


def test_05_100_percent_validate_translation_pass(catalog_data):
    """Assertion 5: 100% validate_translation pass with 0 failures."""
    for zh, val in catalog_data["unique"].items():
        ok, reason = validate_translation(zh, val)
        assert ok, f"Unique validation failed ({reason}): {zh!r} -> {val!r}"

    for row in catalog_data["english_updates"]:
        src = row[4] if len(row) >= 5 else row[2]
        dst = row[3]
        ok, reason = validate_translation(src, dst)
        assert ok, f"english_updates validation failed ({reason}): {src!r} -> {dst!r}"


def test_06_zero_tag_description_injections(catalog_data):
    """Assertion 6: Zero multi-sentence card descriptions injected inside <b> or <color> tags."""
    bad_tag_snippets = (
        "Secara acak mengambil 4",
        "Trap akan meledak 2 detik",
        "Dapat menempatkan 1 Electromagnetic",
        "Gunakan skill, arahkan ke 1 hero",
        "Pilih 1 Strategic Decision",
        "Ying Lü memilih 1 dari 4",
        "2 Hero dengan Level terendah",
        "Pilih 1 mekanisme di arena",
    )
    tag_content_re = re.compile(r"<(?:b|color=[^>]+)>(.*?)</(?:b|color)>", re.DOTALL)
    all_values = list(catalog_data["unique"].values()) + [
        row[3] for row in catalog_data["english_updates"]
    ]

    for val in all_values:
        for m in tag_content_re.finditer(val):
            content = m.group(1)
            for snip in bad_tag_snippets:
                assert snip not in content, f"Injected description {snip!r} inside tag in: {val!r}"


def test_07_zero_bracket_line_splits(catalog_data):
    """Assertion 7: Zero bracket line splits ([...\\n...]) across all strings."""
    bracket_split_re = re.compile(r"\[[^\]]*\n[^\]]*\]")
    all_values = list(catalog_data["unique"].values()) + [
        row[3] for row in catalog_data["english_updates"]
    ]

    for val in all_values:
        m = bracket_split_re.search(val)
        assert not m, f"Bracket split across newline detected ({m.group(0)!r}) in: {val!r}"


def test_08_zero_machine_calque_families(catalog_data):
    """Assertion 8: Zero machine-calque families across 100% of unique and english_updates."""
    calque_checks = [
        ("adalah + verb", re.compile(r"\badalah\s+(?:meningkat|berkurang|penuh|rusak|aktif|masuk|digandakan|dihapus|dibatasi)\b", re.I)),
        ("pilih X keluar dari Y", re.compile(r"\bpilih\s+\d+\s+keluar\s+dari\s+\d+\b", re.I)),
        ("terdapat tidak", re.compile(r"\bterdapat\s+tidak\b", re.I)),
        ("Melakukan tidak", re.compile(r"\bMelakukan\s+tidak\b", re.I)),
        ("pembawa dapat menjadi / kamp", re.compile(r"\bpembawa\s+dapat\s+menjadi\b|\bkamp\b", re.I)),
        ("keping dari", re.compile(r"\bkeping\s+dari\b", re.I)),
        ("inverted time/demonstrative", re.compile(r"\b(?:berikutnya|saat\s+ini)\s+(?:Round|Kartu|Efek|unit|pertandingan|Combat|slot)\b", re.I)),
        ("rahasia kartu/skill", re.compile(r"\brahasia\s+(?:kartu|teknik|skill)\b|\bRahasia\s+(?:Teknik|Skill)\s+[Kk]artu\b", re.I)),
        ("musim semi", re.compile(r"\bmusim\s+semi\b", re.I)),
        ("milikmu%", re.compile(r"\bmilikmu%", re.I)),
        ("glued ctrl token", re.compile(r"[0-9A-Za-z][\u2540-\u257f]|[\u2540-\u257f](?:diperoleh|Kartu)")),
        ("glued verb+digit", re.compile(r"\b(?:get|and|Restore|gain|deal)\d+\b", re.I)),
        ("sebuah lebih / capable dari", re.compile(r"\bsebuah\s+lebih\b|\bcapable\s+dari\b", re.I)),
        ("memindahkan menerjang / langkah pada", re.compile(r"\bmemindahkan\s+menerjang\b|\blangkah\s+pada\b", re.I)),
        ("Banyak dari Teman", re.compile(r"\bBanyak\s+dari\s+Teman\b", re.I)),
    ]

    all_values = list(catalog_data["unique"].values()) + [
        row[3] for row in catalog_data["english_updates"]
    ]

    for label, pat in calque_checks:
        for val in all_values:
            assert not pat.search(val), f"Machine calque {label!r} detected in: {val!r}"
