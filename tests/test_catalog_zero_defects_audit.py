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
ORIG_CATALOG_PATH = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "catalog" / "catalog.json.gz"
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


def test_09_zero_contestant_and_series_mangling(catalog_data, index_data):
    """Assertion 9: Zero contestant, secret skill, and equipment/series mangling across all target strings."""
    vfs_target_zh = set(index_data.get("vfs_target_zh", []))
    target_values: list[str] = [
        val for zh, val in catalog_data["unique"].items() if zh in vfs_target_zh
    ]
    for row in catalog_data["english_updates"]:
        opt_zh = row[4] if len(row) >= 5 else ""
        if opt_zh in vfs_target_zh:
            target_values.append(row[3])

    mangling_checks = [
        # Contestant name mangling
        ("harum", re.compile(r"\bharum\b")),
        ("Ying Hukum", re.compile(r"\bYing Hukum\b")),
        ("Qin Lu", re.compile(r"\bQin Lu\b")),
        ("Putih Lagu", re.compile(r"\bPutih Lagu\b")),
        ("<b>Menyapu</b>", re.compile(r"<b>Menyapu</b>")),
        ("melalui Menyapu", re.compile(r"\bmelalui Menyapu\b")),
        ("Xiao Xiao Little Daji", re.compile(r"\bXiao Xiao Little Daji\b")),
        ("Sun Xiaobin", re.compile(r"\bSun Xiaobin\b")),
        ("Zhuang Xiaoyu", re.compile(r"\bZhuang Xiaoyu\b")),
        ("Chang Xiao'e", re.compile(r"\bChang Xiao'e\b")),
        ("Asylum Anak rusa", re.compile(r"\bAsylum Anak rusa\b")),
        ("Iblis (Dewa/HP/Max/Energi/Menerjang/pertama)", re.compile(r"\bIblis (?:Dewa|HP|Max|Energi|Menerjang|pertama)\b")),
        ("wilayah pada", re.compile(r"\bwilayah pada\b")),
        # Secret Skill duplication/drift
        ("Kartu Secret (Skill|Art) Kartu", re.compile(r"\bKartu Secret (?:Skill|Art) Kartu\b")),
        ("Kartu Secret Art", re.compile(r"\bKartu Secret Art\b")),
        # Equipment & Series mangling
        ("Terkenal Pedang Siming", re.compile(r"\bTerkenal Pedang Siming\b")),
        ("Merah Iblis", re.compile(r"\bMerah Iblis\b")),
        ("Tongkat dari Kehampaan", re.compile(r"\bTongkat dari Kehampaan\b")),
        ("Murka Savant", re.compile(r"\bMurka Savant\b")),
        ("Buku dari Dewa-Eaters", re.compile(r"\bBuku dari Dewa-Eaters\b")),
        ("Sabuk Raksasa", re.compile(r"\bSabuk Raksasa\b")),
        ("Besar Rod", re.compile(r"\bBesar Rod\b")),
        ("Berat Armor", re.compile(r"\bBerat Armor\b")),
        ("Sunset Samudra", re.compile(r"\bSunset Samudra\b")),
        ("(Totem|General|Arcomia Core) Seri", re.compile(r"\b(?:Totem|General|Arcomia Core) Seri\b")),
        ("Alam baka Totem", re.compile(r"\bAlam baka Totem\b")),
        # Tier 3 calques
        ("Kartu itu Hero", re.compile(r"\bKartu itu Hero\b")),
        ("itu adalah", re.compile(r"\bitu adalah\b")),
        ("mati-di arena", re.compile(r"\bmati-di arena\b")),
        ("mati-papan", re.compile(r"\bmati-papan\b")),
        ("ke (secara acak|Gunakan|enact)", re.compile(r"\bke (?:secara acak|Gunakan|enact)\b")),
        ("remainder dari", re.compile(r"\bremainder dari\b")),
        ("(sebuah|N) Acak", re.compile(r"\b(?:sebuah|\d+)\s+Acak\b")),
        ("(tertinggi|terendah)-Level", re.compile(r"\b(?:tertinggi|terendah)-Level\b")),
        ("rubah menembakkan", re.compile(r"\brubah menembakkan\b")),
        ("milikmu/", re.compile(r"\d+\s+milikmu/\d+")),
        ("mereka%", re.compile(r"\d+\s+mereka%")),
        ("menyerang miliknya musuh", re.compile(r"\bmenyerang miliknya musuh\b")),
        ("pada menarik/mengalahkan", re.compile(r"\bpada menarik/mengalahkan\b")),
    ]

    for label, pat in mangling_checks:
        for val in target_values:
            assert not pat.search(val), f"Target string mangling {label!r} detected in: {val!r}"


def test_10_zero_opus_mt_control_token_and_wrap_regressions():
    """Verify that no active target string carries Opus-MT hallucinations, leaked tokens, or line length regressions."""
    from acepatchindo.hybrid_classifier import get_hybrid_classifier
    from acepatchindo.card_wrapper import _visible_length

    with gzip.open(CATALOG_PATH, "rt", encoding="utf-8") as f:
        catalog = json.load(f)

    with gzip.open(ORIG_CATALOG_PATH, "rt", encoding="utf-8") as f:
        orig_cat = json.load(f)

    classifier = get_hybrid_classifier()
    unique = catalog["unique"]
    orig_unique = orig_cat["unique"]

    active_targets = []
    for zh, val in unique.items():
        en = orig_unique.get(zh, "")
        if classifier.is_target_unique(zh, en):
            active_targets.append((zh, val))

    assert len(active_targets) >= 5_000, f"Expected >= 5000 active targets, got {len(active_targets)}"

    opus_mt_patterns = [
        ("musical_note_d", re.compile(r"♪")),
        ("musical_note_2d", re.compile(r"♫")),
        ("synchronis", re.compile(r"\bSynchronis", re.I)),
        ("teks", re.compile(r"\(Teks\)", re.I)),
        ("riot_rasio", re.compile(r"\bRiot\s+rasio\b", re.I)),
        ("forensic", re.compile(r"\bForensic\b", re.I)),
        ("zhang", re.compile(r"\b\d+\s*Zhang\b", re.I)),
        ("chang", re.compile(r"\b\d+\s*Chang\b", re.I)),
        ("dunia_kecil", re.compile(r"sangat\s+kecil\s+bagian\s+dari\s+dunia", re.I)),
        ("hell_menjadi", re.compile(r"He'll\s+menjadi", re.I)),
    ]

    control_token_leaks = [
        ("almia_core", re.compile(r"\bAlmia\s+Core\b", re.I)),
        ("accomia_core", re.compile(r"\bAccomia\s+Core\b", re.I)),
        ("acomia_core", re.compile(r"\bAcomia\s+Core\b", re.I)),
        ("initiate_bentrokan", re.compile(r"╪\s*Bentrokan")),
        ("initiate_memulai", re.compile(r"╪\s*Memulai")),
        ("prepare_siap", re.compile(r"╬\s*Siap")),
        ("revive_sempurna", re.compile(r"╧\s*Sempurna")),
        ("fleeting_instant", re.compile(r"╆\s*Instant")),
        ("retire_exit", re.compile(r"╈\s*Exit")),
        ("retire_keluar", re.compile(r"╈\s*Keluar")),
        ("combine_menggabungkan", re.compile(r"╦\s*Menggabungkan")),
        ("combine_merge", re.compile(r"╦\s*Merge")),
        ("soul_snatch_jiwa_merebut", re.compile(r"╊\s*Jiwa\s+Merebut")),
        ("steal_merebut", re.compile(r"╊\s*Merebut")),
        ("steal_capture", re.compile(r"╊\s*Capture")),
        ("steal_plunder", re.compile(r"╊\s*Plunder")),
        ("steal_seizure", re.compile(r"╊\s*Seizure")),
        ("bond_totem_pernikahan", re.compile(r"╉\s*Pernikahan\s+Totem")),
        ("afterlife_totem_rebirth", re.compile(r"╉\s*Rebirth\s+Totem")),
        ("seer_totem_prophet", re.compile(r"╉\s*Prophet\s+Totem")),
    ]

    phrase_leaks = [
        ("medan_milikmu_tempur", re.compile(r"medan\s+\w+\s+tempur", re.I)),
        ("sebuah_di_luar_arena", re.compile(r"sebuah\s+di\s+luar\s+arena", re.I)),
        ("cermin_kartu", re.compile(r"<b>cermin</b>\s*kartu", re.I)),
        ("yao_rusa_level", re.compile(r"rusa\s+Level\s+adalah\s+\+30", re.I)),
    ]

    for zh, val in active_targets:
        # 1. Opus-MT hallucinations
        for label, pat in opus_mt_patterns:
            assert not pat.search(val), f"Opus-MT hallucination {label!r} in {val!r} (ZH: {zh!r})"

        # 2. Inappropriate Strum
        if "扫拂" not in zh and "轮指" not in zh:
            assert "Strum" not in val, f"Invalid Strum without 扫拂/轮指 in {val!r} (ZH: {zh!r})"

        # 3. Control token leaks
        for label, pat in control_token_leaks:
            assert not pat.search(val), f"Control token leak {label!r} in {val!r} (ZH: {zh!r})"

        # 4. Leaked Series title (should be Series, not Seri)
        if "系列" in zh:
            assert not re.search(
                r"\b(Totem|Steal|Flash|Temporary Level|Arcomia Core|Deploy|Initiate|Sacrifice|Prepare|Low-Tier|Starting Lineup|Ancient Coin|Summon|Combine|Multi-Faction|Contract|Tactics Card|Shield|Effect Card|Factionless|Grassroots|General)\s+Seri\b",
                val,
                re.I,
            ), f"Leaked 'Seri' title in {val!r} (ZH: {zh!r})"

        # 5. Word wrap check: if no ';' in zh, each line visible length <= 34 (unless single unbroken token > 34)
        if ";" not in zh:
            for line in val.split("\n"):
                vis_len = _visible_length(line)
                if vis_len > 34:
                    line_masked = re.sub(r"\[[^\]]+\]", lambda m: m.group(0).replace(" ", "_"), line)
                    words = [w for w in line_masked.split(" ") if w]
                    has_long_word = any(_visible_length(w) > 34 for w in words)
                    assert has_long_word, f"Line exceeds 34 visible chars ({vis_len}): {line!r} in {val!r} (ZH: {zh!r})"

        # 6. Phrase leaks
        for label, pat in phrase_leaks:
            assert not pat.search(val), f"Phrase leak {label!r} in {val!r} (ZH: {zh!r})"


def test_11_universal_structural_invariants():
    """Verify universal structural invariants across all active target gameplay entries:
    1. Zero detached control tokens or mangled keywords.
    2. Zero reversed pronoun word orders (Verb + milikmu).
    3. Zero whole-clause tag swallowing when source tags are short (<= 5 chars).
    4. Zero equipment header defects ('<b>hanya</b>', 'disassembled', 'Harta kartu', hanging signs).
    """
    from acepatchindo.hybrid_classifier import get_hybrid_classifier
    from acepatchindo.validator import TAG_RE

    with gzip.open(CATALOG_PATH, "rt", encoding="utf-8") as f:
        catalog = json.load(f)

    with gzip.open(ORIG_CATALOG_PATH, "rt", encoding="utf-8") as f:
        orig_cat = json.load(f)

    classifier = get_hybrid_classifier()
    unique = catalog["unique"]
    orig_unique = orig_cat["unique"]

    active_targets = []
    for zh, val in unique.items():
        en = orig_unique.get(zh, "")
        if classifier.is_target_unique(zh, en):
            active_targets.append((zh, val))

    assert len(active_targets) >= 5_000

    detached_pat = re.compile(r"[\u2540-\u257f]\s*(?:$|[\.,;!\?\)])")
    forbidden_after_ctrl = re.compile(
        r"[\u2540-\u257f]\s*(?:<[^>]+>\s*)*(?:sebuah\s+(?:tim|grup)|Roh\s+Extraction|capturing\s+entri|sacrificed\s+Hero|Ikatan\s+Totem|Destiny\s+Totem|Melahap)\b",
        re.I,
    )
    verb_milikmu = re.compile(r"\b(?:memicu|mendapatkan|menggunakan|memperoleh|melepaskan|menyerang|memanggil)\s+milikmu\b", re.I)

    for zh, val in active_targets:
        plain_val = TAG_RE.sub("", val)

        # 1. Zero detached control tokens
        assert not detached_pat.search(plain_val), f"Detached control token in {val!r} (ZH: {zh!r})"
        assert not forbidden_after_ctrl.search(val), f"Forbidden phrase after control token in {val!r} (ZH: {zh!r})"

        # 2. Zero reversed pronoun word order
        assert not verb_milikmu.search(val), f"Reversed 'Verb + milikmu' in {val!r} (ZH: {zh!r})"

        # 3. Tag-swallowing check
        inner_zhs = re.findall(r"<[^>]+>([^<]+)</[^>]+>", zh)
        if inner_zhs and all(len(z.strip()) <= 5 for z in inner_zhs):
            inner_ids = re.findall(r"<[^>]+>([^<]+)</[^>]+>", val)
            for i_id in inner_ids:
                assert len(i_id.strip()) < 45, f"Tag swallowed >= 45 chars ({len(i_id.strip())}) in {val!r} (ZH: {zh!r})"

        # 4. Equipment & Treasure
        if "唯一" in zh:
            assert not re.search(r"<b>\s*hanya\s*</b>", val, re.I), f"Found '<b>hanya</b>' in {val!r} (ZH: {zh!r})"
        assert not re.search(r"\bdisassembled\b", val, re.I), f"Found 'disassembled' in {val!r} (ZH: {zh!r})"
        assert not re.search(r"\bHarta\s+kartu\b", val, re.I), f"Found 'Harta kartu' in {val!r} (ZH: {zh!r})"

        # 5. Hanging signs on non-formula lines
        if not zh.strip().endswith("+") and not zh.strip().endswith("-"):
            for line in val.split("\n"):
                line_s = line.strip()
                if not re.search(r"\[[0-9a-zA-Z_./*+%-]+\]", line_s):
                    assert not line_s.endswith("+"), f"Hanging '+' at line end in {val!r} (ZH: {zh!r})"
                    assert not (line_s.endswith("-") and not line_s.endswith(" -")), f"Hanging '-' at line end in {val!r} (ZH: {zh!r})"


def test_12_forensic_cleanliness_and_zero_regressions():
    """Verify forensic cleanliness and zero regressions across all active target gameplay entries:
    1. All 58 raw entries in WINDOWS_108_TARGET_DESC_ID pass validator & runtime_rules.
    2. Zero detached box-drawing glyphs followed by space/newline + letters.
    3. Zero 'Seri' when '平局' not in source_zh.
    4. Zero 'Kartu Efek Series' (must be 'Effect Card Series').
    5. Zero leaks: Chess Player, di papan, sebuah tambahan/Combat, bebas Refresh, kalah HP,
       saat bermain, tempat di atas, Mimpi Shop, Trait Kemampuan, Lainnya [Faction],
       <Name> kartu, Kartu Li Xin Efek, milikmu Skill/Control/Temporary/permanen, memicu Retreat.
    """
    from acepatchindo.hybrid_classifier import get_hybrid_classifier
    from acepatchindo.validator import validate_translation, RUNTIME_BRACKET_TOKEN_RE
    from acepatchindo.card_wrapper import _visible_length
    from acepatchindo.windows_108_split import WINDOWS_108_TARGET_DESC_ID
    from collections import Counter
    import wxq_patch.translation_rules as runtime_rules

    # 1. All 58 raw entries pass validation
    for zh, id_t in WINDOWS_108_TARGET_DESC_ID.items():
        ok1, r1 = validate_translation(zh, id_t)
        ok2, r2 = runtime_rules.validate_translation(zh, id_t)
        assert ok1 and ok2, f"WINDOWS_108 raw failed ({r1}/{r2}): {zh!r} -> {id_t!r}"

    with gzip.open(CATALOG_PATH, "rt", encoding="utf-8") as f:
        catalog = json.load(f)

    with gzip.open(ORIG_CATALOG_PATH, "rt", encoding="utf-8") as f:
        orig_cat = json.load(f)

    classifier = get_hybrid_classifier()
    unique = catalog["unique"]
    orig_unique = orig_cat["unique"]

    active_targets = []
    for zh, val in unique.items():
        en = orig_unique.get(zh, "")
        if classifier.is_target_unique(zh, en):
            active_targets.append((zh, val))

    assert len(active_targets) >= 5_000

    space_after_ctrl = re.compile(r"[\u2500-\u257f]\s+(?:<[^>]+>)*[A-Za-z]")
    chess_player_pat = re.compile(r"\bChess\s+Player\b", re.I)
    di_papan_pat = re.compile(r"\bdi\s+papan\b", re.I)
    sebuah_pat = re.compile(r"\bsebuah\s+(?:tambahan|Ekstra|Combat)\b", re.I)
    bebas_refresh_pat = re.compile(r"\bbebas\s+Refresh\b", re.I)
    kalah_hp_pat = re.compile(r"\bkalah\s+\d+%?\s*(?:dari\s+)?(?:Max\s+)?HP\b", re.I)
    saat_bermain_pat = re.compile(r"\bsaat\s+bermain\b", re.I)
    tempat_di_atas_pat = re.compile(r"\btempat\s+di\s+atas\b", re.I)
    mimpi_shop_pat = re.compile(r"\bMimpi\s+Shop\b", re.I)
    trait_kemampuan_pat = re.compile(r"\bTrait\s+[Kk]emampuan\b")
    lainnya_faction_pat = re.compile(r"\bLainnya\s+\[")
    name_kartu_pat = re.compile(r"\b(?:Marco|Shouyue|Consort Yu|Arli|Ascension|Master Artisan)\s+kartu\b", re.I)
    lixin_kartu_pat = re.compile(r"\bKartu\s+Li\s+Xin\s+Efek\b", re.I)
    milikmu_leak_pat = re.compile(r"\bmilikmu\s+(?:Skill|Control|Temporary|permanen)\b", re.I)
    retreat_leak_pat = re.compile(r"memicu\s+(?:efek\s+)?Retreat\b", re.I)
    sendiri_hp_pat = re.compile(r"\bsendiri\s+(?:Max\s+)?(?:HP|Level)\b", re.I)

    for zh, val in active_targets:
        # 2. Zero detached box-drawing glyphs followed by space/newline + letters
        assert not space_after_ctrl.search(val), f"Space after box-drawing in {val!r} (ZH: {zh!r})"

        # 3. Zero \bSeri\b when 平局 not in zh
        if "平局" not in zh:
            assert not re.search(r"\bSeri\b", val), f"Unexpected 'Seri' in {val!r} (ZH: {zh!r})"

        # 4. Zero Kartu Efek Series
        assert "<color=#99DEB0>Kartu Efek Series</color>" not in val, f"Kartu Efek Series leak in {val!r}"

        # 5. Zero specific leaks
        assert not chess_player_pat.search(val), f"Chess Player in {val!r}"
        assert not di_papan_pat.search(val), f"di papan in {val!r}"
        assert not sebuah_pat.search(val), f"sebuah tambahan/Combat in {val!r}"
        assert not bebas_refresh_pat.search(val), f"bebas Refresh in {val!r}"
        assert not kalah_hp_pat.search(val), f"kalah HP in {val!r}"
        assert not saat_bermain_pat.search(val), f"saat bermain in {val!r}"
        assert not tempat_di_atas_pat.search(val), f"tempat di atas in {val!r}"
        assert not mimpi_shop_pat.search(val), f"Mimpi Shop in {val!r}"
        assert not trait_kemampuan_pat.search(val), f"Trait Kemampuan in {val!r}"
        assert not lainnya_faction_pat.search(val), f"Lainnya [Faction] in {val!r}"
        assert not name_kartu_pat.search(val), f"<Name> kartu in {val!r}"
        assert not lixin_kartu_pat.search(val), f"Kartu Li Xin Efek in {val!r}"
        assert not milikmu_leak_pat.search(val), f"milikmu injection in {val!r}"
        assert not retreat_leak_pat.search(val), f"memicu Retreat in {val!r}"
        assert not sendiri_hp_pat.search(val), f"sendiri HP/Level in {val!r}"

    # 6. Universal structural invariant checks (15 forensic categories)
    FACTION_PAT = r"\[(?:Central Plains|Riverlands|Three Kingdoms|Sunset Sea|Zhulu Plateau|High Heaven|First Lands|Factionless|Great Wall|Jixia|Divinity)\]"
    UNBRACKETED_FACTION = r"\b(?:Central Plains|Riverlands|Three Kingdoms|Sunset Sea|Zhulu Plateau|High Heaven|First Lands|Factionless|Great Wall|Jixia)\s+(?:Hero|Kartu)\b"
    strict_checks = [
        ("Keberangkatan", re.compile(r"\bKeberangkatan\b", re.I)),
        ("Ultimate Treasure adalah", re.compile(r"Ultimate\s+Treasure\s+adalah", re.I)),
        ("pamungkas acak harta", re.compile(r"pamungkas\s+acak\s+harta", re.I)),
        ("Faction Hero/Kartu/Token", re.compile(rf"{FACTION_PAT}\s+(?:Hero|Kartu|Token)\b")),
        ("[Keilahian] / [Suci]", re.compile(r"\[(?:Keilahian|Suci)\]", re.I)),
        ("Skill menggunakan", re.compile(r"\bSkill\s+menggunakan\b", re.I)),
        ("sebuah milikmu / Awaken milikmu Kartu", re.compile(r"\bsebuah\s+milikmu\b|\bAwaken(?:ed)?\s+milikmu\s+Kartu\b", re.I)),
        ("Khusus Tamu", re.compile(r"\bKhusus\s+Tamu\b", re.I)),
        ("tag kartu anti-evasion", re.compile(r">[A-Za-z][A-Za-z0-9 '·•\-:&]*(?:</b>)?(?:</color>)?(?:</a>)?\s+[Kk]artu\b(?!\s+(?:Hero|Efek|Equipment|Talent|Strategi|Mekanisme|Taktik|Biru|Pilihan))")),
        ("Baili Shouyue", re.compile(r"\bBaili\s+Shouyue\b", re.I)),
        ("Baili Xuance", re.compile(r"\bBaili\s+Xuance\b", re.I)),
        ("Blade of Fate / terkenal pedang", re.compile(r"\b(?:Blade of Fate|terkenal pedang)\b", re.I)),
        ("Tim Buff / Semua anggota meningkatkan", re.compile(r"\bTim\s+Buff\b|Semua\s+anggota\s+meningkatkan", re.I)),
        ("0-yuan / 0 Yuan", re.compile(r"\b0-(?:yuan|Yuan)\b|\b0\s+Yuan\b", re.I)),
        ("double colon", re.compile(r"::")),
        ("nested brackets", re.compile(r"\[[^\]]*\[|\][^\[]*\]")),
        ("split decimal / range", re.compile(r"\d+\s*(?:miliknya|mereka)\s*[\.\-~]\s*\d+|\d+\s*[\.\-~]\s*(?:miliknya|mereka)\s*\d+")),
        ("masuk field / mimpi menyimpan / peluang ke", re.compile(r"\bmasuk\s+field\b|\bmimpi\s+menyimpan\b|\bpeluang\s+ke\b", re.I)),
        ("Opus/grammar corruption", re.compile(r"Tidak\.|adalah\s+di\s+atas|\bSaat\s+tipe\b|mantra\s+sucks|scarcestone|Deploy\s+horizontally|Hero\.Hero|memicu\.|itu\.\.\.|<color=[^>]+>11\.</color>|\bAmbil\s+Summon\b", re.I)),
        ("Modifier kartu inverted", re.compile(r"\b(?:Shared Fortune|Mysterious Hero|Lanjutan Mekanisme|Tier tinggi|No Faction|Lelang|Umum)\s+[Kk]artu\b")),
        ("chess", re.compile(r"\bchess\b", re.I)),
        ("papan", re.compile(r"\bpapan\b", re.I)),
        ("Unbracketed Faction", re.compile(UNBRACKETED_FACTION)),
        ("keluar dari", re.compile(r"\d+\s+keluar\s+dari\s+\d+", re.I)),
        ("bebas Refresh/Shop/penguatan / di menyimpan", re.compile(r"\bbebas\s+(?:Refresh|Shop|penguatan)\b|\bdi\s+menyimpan\b", re.I)),
        ("Tidak kalah Level / ke kalah digit", re.compile(r"\bTidak\s+kalah\s+Level\b|\bke\s+kalah\s+\d", re.I)),
        ("kamu bermain / bermain Kartu / undian kartu", re.compile(r"\bkamu\s+bermain\b|\bbermain\s+(?:sebuah\s+|sama\s+)?(?:Awakened\s+)?Kartu\b|\bundian\s+kartu\b", re.I)),
        ("sendiri Hero / kamu sendiri sebuah / pemain Level", re.compile(r"\bsendiri\s+Hero\b|\bkamu\s+sendiri\s+sebuah\b|\bpemain\s+Level\b", re.I)),
        ("evolves / fictitious / seized unit / Luar biasa Suara", re.compile(r"\bevolves\b|\bfictitious\b|\bseized\s+unit\b|\bLuar\s+biasa\s+Suara\b", re.I)),
        ("Sub-card anomalies & top 3", re.compile(r"╆Fleeting\s+Kartu\s+Hero\b|di\s+atas\s+3\b|1\s+kali\s+Menyerap|Bintang-Poin|Langka\s+Peti|Bintang\s+Cat\s+Harta|Mawar\s+Hadiah|Cahaya\s+bintang\s+Shimmer|Lebih\s+awal\s+game\s+Surge|Mistis\s+Suara|Melodious\s+Suara", re.I)),
    ]
    cjk_outside_braces = re.compile(r"[。，：；（）]")
    detached_icon_pat = re.compile(r"\{\d+\|[^{}]+\}\s+(?:Hero|Voucher|Kartu)\b|\bKonversi\s+\{(?:Energy|LordExp|LordHp)\}")

    for zh, val in active_targets:
        for label, rx in strict_checks:
            assert not rx.search(val), f"Forensic violation '{label}' in {val!r} (ZH: {zh!r})"
        if "棋手" in zh:
            assert not re.search(r"\bPeserta\b", val, re.I), f"Peserta leak in {val!r}"
        if "第二" in zh and "秒" not in zh:
            assert not re.search(r"\bdetik\b", val, re.I), f"detik leak in {val!r}"
        if "平局" in zh:
            assert not re.search(r"\bMenarik\b", val, re.I), f"Menarik leak for 平局 in {val!r}"
        if "获得1张{ResCardInfoDataBin_1981" in zh:
            assert re.search(r"Tier\s*\{ResCardInfoDataBin_1981", val), f"Voucher Tier placeholder not aligned in {val!r}"
        if "{killcount:0}" in zh:
            assert not re.search(r"memperoleh\s*\{killcount:0\}", val, re.I), f"killcount placeholder swapped into stat slot in {val!r}"

        # CJK fullwidth punctuation outside {...} must be zero
        val_no_braces = re.sub(r"\{[^{}]*\}", "", val)
        assert not cjk_outside_braces.search(val_no_braces), f"Fullwidth CJK punctuation outside braces in {val!r} (ZH: {zh!r})"

        # Runtime bracket formula token multiset equality
        assert Counter(RUNTIME_BRACKET_TOKEN_RE.findall(zh)) == Counter(RUNTIME_BRACKET_TOKEN_RE.findall(val)), (
            f"Runtime bracket tokens mismatch in {val!r} (ZH: {zh!r})"
        )

        # Detached {N|val}{Icon} checks
        assert not detached_icon_pat.search(val), f"Detached placeholder/icon in {val!r} (ZH: {zh!r})"

        # Verify 4张古币牌 retains 4 Kartu and tracker placeholder
        if "本回合每使用4张古币牌" in zh:
            assert "4 Kartu" in val, f"Missing '4 Kartu' in {val!r}"
            assert re.search(r"\(total\s+Revive:\s*\{ResCardInfoDataBin_1541_15412_0:\s*1\}\)", val), f"Missing tracker in {val!r}"

        # Word wrap check: if no ';' in zh, each line visible length <= 34 (unless single unbroken token > 34)
        if ";" not in zh:
            for line in val.split("\n"):
                vis_len = _visible_length(line)
                if vis_len > 34:
                    line_masked = re.sub(r"\[[^\]]+\]", lambda m: m.group(0).replace(" ", "_"), line)
                    words = [w for w in line_masked.split(" ") if w]
                    has_long_word = any(_visible_length(w) > 34 for w in words)
                    assert has_long_word, f"Line exceeds 34 visible chars ({vis_len}): {line!r} in {val!r} (ZH: {zh!r})"

