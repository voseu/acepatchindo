"""Tests for the 3-Tier Indonesian Glossary and Windows 108 missing strings translation."""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

from wxq_patch import translation_rules as runtime_rules

from acepatchindo.glossary import WINDOWS_108_ZH_TO_ID, ThreeTierGlossary
from acepatchindo.validator import PLACEHOLDER_RE, TAG_RE, validate_translation

ROOT = Path(__file__).resolve().parents[1]
REFS_DIR = ROOT / "data" / "references"
CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"

STOPWORD_RE = re.compile(
    r"\b(the|and|with|from|into|when|while|after|before|during|within|without|"
    r"between|against|through|for|you|your|their|his|her|its|this|that|these|those|"
    r"each|every|deals|dealing|restores|restoring|gains|gaining|grants|granting|"
    r"increases|increasing|reduces|reducing|summons|summoning|triggers|triggering|"
    r"enemies|allies|cannot|will|have|has|had|are|was|were|been)\b",
    re.I,
)


def test_three_tier_glossary_loads_and_prioritizes_tier1() -> None:
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )
    assert len(glossary.tier1_exact_zh_to_id) > 1000
    assert len(glossary.tier2_zh_to_en) > 500

    # Test Tier 1 tagged prefix alignment (Su Lie Sacrifice from Tier 1)
    tagged_cn = "<a href=10><color=#ffffff>╫<b>牺牲</b></color></a>：苏烈的等级永久+2。"
    baseline_en = "<a href=10><color=#ffffff>╫<b>Sacrifice</b></color></a>: Su Lie's Level permanently +2."
    translated, tier = glossary.translate_entry(tagged_cn, baseline_en=baseline_en)
    assert tier == "tier1"
    assert "secara permanen" in translated
    assert validate_translation(tagged_cn, translated) == (True, "ok")
    assert runtime_rules.validate_translation(tagged_cn, translated) == (True, "ok")


def test_tier2_fallback_and_proper_noun_protection() -> None:
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )
    # AI bot avatar & Proper Noun preservation in EN -> ID
    assert glossary.translate_en_to_id("AI impersonates avatar 4337") == "Avatar Bot AI 4337"
    en_skill = (
        "<color=#ffffff><b>Unique</b></color>. Attack Speed +30%. "
        "Every 3 basic attacks against a target summons a Cirrus spirit, "
        "dealing 4% of the target's Max HP as Physical Damage."
    )
    id_skill = glossary.translate_en_to_id(en_skill)
    assert "Attack Speed" in id_skill
    assert "Physical Damage" in id_skill
    assert "Max HP" in id_skill
    assert "Cirrus" in id_skill
    assert "Setiap 3 Basic Attack" in id_skill


def test_all_108_missing_windows_strings_have_authentic_translations_and_validate() -> None:
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )
    missing_items = json.loads(
        (REFS_DIR / "windows_missing_108_zh.json").read_text(encoding="utf-8")
    )
    assert len(missing_items) == 108

    for item in missing_items:
        zh = item["source_zh"]
        assert zh in WINDOWS_108_ZH_TO_ID, f"Missing curated translation for {zh!r}"
        translated, _ = glossary.translate_entry(zh, baseline_en=None)
        ok, reason = validate_translation(zh, translated)
        assert ok, f"Failed validation ({reason}) for {zh!r} -> {translated!r}"
        assert runtime_rules.validate_translation(zh, translated) == (True, "ok")


def test_catalog_has_no_indlish_or_untranslated_english_prose() -> None:
    assert CATALOG_GZ.exists(), f"Missing {CATALOG_GZ}"
    with gzip.open(CATALOG_GZ, "rt", encoding="utf-8") as f:
        cat = json.load(f)

    assert len(cat["unique"]) == 41483
    assert len(cat["english_updates"]) == 29750

    unique_stopword_hits = 0
    for zh_src, id_val in cat["unique"].items():
        ok, reason = runtime_rules.validate_translation(zh_src, id_val)
        assert ok, f"Runtime validation failed ({reason}) for {zh_src!r} -> {id_val!r}"
        stripped = PLACEHOLDER_RE.sub(" ", TAG_RE.sub(" ", id_val))
        if STOPWORD_RE.search(stripped):
            unique_stopword_hits += 1

    eu_stopword_hits = 0
    for row in cat["english_updates"]:
        val_source = row[4] if len(row) == 5 else row[2]
        id_val = row[3]
        ok, reason = runtime_rules.validate_translation(val_source, id_val)
        assert ok, f"Runtime validation failed ({reason}) for {val_source!r} -> {id_val!r}"
        stripped = PLACEHOLDER_RE.sub(" ", TAG_RE.sub(" ", id_val))
        if STOPWORD_RE.search(stripped):
            eu_stopword_hits += 1

    assert unique_stopword_hits < 100, (
        f"Expected < 100 stopword hits in unique, got {unique_stopword_hits}"
    )
    assert eu_stopword_hits < 100, (
        f"Expected < 100 stopword hits in english_updates, got {eu_stopword_hits}"
    )

    # Verify formula-parameterized Tier 1 Hero skills use Tier 1 Indonesian translations
    biron_zh = (
        "狂铁挥舞2次武器，每次挥击对身前的敌人造成<color=#dfa15e>"
        "50+[503310p1q2/100]%物理攻击力的物理伤害</color>。"
    )
    assert "mengayunkan senjatanya 2 kali" in cat["unique"][biron_zh]
    assert "50+[503310p1q2/100]%" in cat["unique"][biron_zh]

    sulie_zh = (
        "苏烈旋转一周，对周围敌人造成<color=#dfa15e>80+[194010p1q2/100]%物理攻击力的物理伤害"
        "</color>，并降低其<color=#dfa15e>[194011p1q2]点物理防御</color>，持续5秒。"
    )
    sulie_val = cat["unique"][sulie_zh]
    assert "Su Lie berputar satu putaran" in sulie_val
    assert "80+[194010p1q2/100]%" in sulie_val
    assert "<color=#dfa15e>[194011p1q2] Physical Defense</color>" in sulie_val
    assert "<color=#dfa15e></color>" not in sulie_val

    # Phase 3 Audit Verifications: zero nested placeholders, zero empty tags, zero glued words
    nested_re = re.compile(r"\{[^{}]*\{|\}[^{}]*\}")
    assert sum(1 for v in cat["unique"].values() if nested_re.search(v)) == 0
    assert sum(1 for r in cat["english_updates"] if nested_re.search(r[3])) == 0

    empty_tag_re = re.compile(r"<(color=[^>]+|b|i|a[^>]*|size=[^>]+)>\s*</(?:color|b|i|a|size)>")
    for zh_src, id_val in cat["unique"].items():
        if empty_tag_re.search(id_val) and not empty_tag_re.search(zh_src):
            raise AssertionError(f"Empty tag shell in unique: {id_val!r} for {zh_src!r}")
    for r in cat["english_updates"]:
        src_val = r[4] if len(r) == 5 else r[2]
        id_val = r[3]
        if empty_tag_re.search(id_val) and not empty_tag_re.search(src_val):
            raise AssertionError(f"Empty tag shell in english_updates: {id_val!r} for {src_val!r}")

    glued_words = ["untuksetiap", "secaraacak", "sebelumnyaLevel", "KartuAncientCoin", "SetiapkaliHero"]
    for gw in glued_words:
        for v in cat["unique"].values():
            assert gw not in v, f"Found glued word {gw} in unique: {v}"
        for r in cat["english_updates"]:
            assert gw not in r[3], f"Found glued word {gw} in english_updates: {r[3]}"

    # Phase 4 Audit Verifications: zero occurrences of corrupted canonical terms and broken tokens
    forbidden_terms = [
        "Kuno Koin",
        "Sementara Level",
        "Nyata Level",
        "Sihir Menyerang",
        "Sihir Damage",
        "Sihir Defense",
        "Mantra Penetrasi",
        "Cepat Growth",
        "di ketertiban",
        "jumlah sebagai",
        "Sempurna Kebangkitan",
        "Api Thief",
        "Kartu Effect",
        "Talent Kartu",
        "Equipment Kartu",
        "Hero Kupon",
        "<b>═",
        "╫,",
    ]
    for ft in forbidden_terms:
        ft_low = ft.lower()
        for v in cat["unique"].values():
            assert ft_low not in v.lower(), f"Found forbidden term '{ft}' in unique: {v}"
        for r in cat["english_updates"]:
            assert ft_low not in r[3].lower(), f"Found forbidden term '{ft}' in english_updates: {r[3]}"
    glossary = ThreeTierGlossary.from_reference_files(
        REFS_DIR / "tier1_wiki_id.json",
        REFS_DIR / "tier2_wiki_en.json",
    )
    assert "kali" not in glossary.translate_en_to_id(
        "the new sounds of the times flow in the heart"
    )
    assert "momen terbaik sepanjang karier" in glossary.translate_en_to_id("Career-defining moment")
    assert "(Opsional) Aku berusia di atas {0} tahun" in glossary.translate_en_to_id("(Optional) I am over {0} years old")
    assert "(Sampai jumpa lagi), aku pasti akan memberimu gacha besar!" in glossary.translate_en_to_id("(See you next time), I will definitely give you a big gacha!")
    assert "Sudah memakai colekan kustom ini" in glossary.translate_en_to_id("Already wearing this personalized poke")
    assert "Pengenalan suara gagal" in glossary.translate_en_to_id("#? (Voice recognition failed)")
    assert "mobil" not in glossary.translate_en_to_id("caring for allies")
    assert "lebih beruang" not in glossary.translate_en_to_id("the bearer of the flame")
    assert (
        glossary.translate_en_to_id("%s challenged your Championship Lineup and won.")
        == "%s menantang Formasi Kejuaraan milikmu dan menang."
    )


