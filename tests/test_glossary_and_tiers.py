"""Tests for the 3-Tier Indonesian Glossary and Windows 108 missing strings translation."""

from __future__ import annotations

import json
from pathlib import Path

from wxq_patch import translation_rules as runtime_rules

from acepatchindo.glossary import WINDOWS_108_ZH_TO_ID, ThreeTierGlossary
from acepatchindo.validator import validate_translation

ROOT = Path(__file__).resolve().parents[1]
REFS_DIR = ROOT / "data" / "references"


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

