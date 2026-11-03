"""Tests for the 3-Tier Indonesian Glossary and Windows 108 missing strings translation."""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

from wxq_patch import translation_rules as runtime_rules

from acepatchindo.glossary import WINDOWS_108_ZH_TO_ID, ThreeTierGlossary
from acepatchindo.hybrid_classifier import HybridClassifier
from acepatchindo.validator import PLACEHOLDER_RE, TAG_RE, validate_translation
from acepatchindo.windows_108_split import WINDOWS_108_TARGET_DESC_ID

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

    assert cat.get("version") == "1.4.12-id.2"

    classifier = HybridClassifier()
    with gzip.open(
        ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "catalog" / "catalog.json.gz",
        "rt",
        encoding="utf-8",
    ) as f:
        orig_cat = json.load(f)

    # 1. Standalone names and non-targets match English baseline exactly
    test_names = [
        ("亚瑟", "Arthur"),
        ("孙尚香", "Lady Sun"),
        ("武则天", "Wu Zetian"),
        ("公孙离", "Arli"),
        ("人才储备", "Talent Reserve"),
        ("普通攻击", "Basic Attack"),
    ]
    for zh, en in test_names:
        assert cat["unique"].get(zh) in (en, orig_cat["unique"].get(zh))

    # 2. Target gameplay descriptions are translated into Indonesian with embedded proper names preserved
    target_count = 0
    target_stopword_hits = 0
    PROSE_CALQUE_RE = re.compile(
        r"\b(when|while|after|before|during|within|without|against|through|their|each|every|cannot)\b",
        re.I,
    )

    for zh_src, id_val in cat["unique"].items():
        ok, reason = runtime_rules.validate_translation(zh_src, id_val)
        assert ok, f"Runtime validation failed ({reason}) for {zh_src!r} -> {id_val!r}"
        if classifier.is_target_unique(zh_src):
            target_count += 1
            stripped = id_val
            for name in (
                "Symphony of Tides",
                "Three Kingdoms Banner",
                "Maple Leaf Dance",
                "Graceful Dance",
                "Gentle Call",
                "Indomitable Will",
                "Try Your Luck",
                "Embrace of the Sea",
            ):
                stripped = stripped.replace(name, "")
            stripped = PLACEHOLDER_RE.sub(" ", TAG_RE.sub(" ", stripped))
            if PROSE_CALQUE_RE.search(stripped):
                target_stopword_hits += 1

    assert target_count >= 4000, (
        f"Expected >= 4,000 target gameplay descriptions in unique, got {target_count}"
    )
    assert target_stopword_hits < 50, (
        f"Expected < 50 prose calque hits in target descriptions, got {target_stopword_hits}"
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
        if classifier.is_target_unique(zh_src):
            if empty_tag_re.search(id_val) and not empty_tag_re.search(zh_src):
                raise AssertionError(f"Empty tag shell in target unique: {id_val!r} for {zh_src!r}")
        else:
            orig_en = orig_cat["unique"].get(zh_src, "")
            if empty_tag_re.search(id_val) and not empty_tag_re.search(orig_en):
                raise AssertionError(f"New empty tag shell in non-target unique: {id_val!r} for {zh_src!r}")

    for r in cat["english_updates"]:
        src_val = r[4] if len(r) == 5 else r[2]
        id_val = r[3]
        if classifier.is_target_update(r[0], r[1], r[2], r[3], src_val):
            if empty_tag_re.search(id_val) and not empty_tag_re.search(src_val):
                raise AssertionError(f"Empty tag shell in target english_updates: {id_val!r} for {src_val!r}")

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

    # Phase 5 Audit Verifications:
    # 1. Card titles
    assert cat["unique"].get("人才储备") == "Talent Reserve" or (len(cat["unique"].get("人才储备", "")) <= 25 and not cat["unique"].get("人才储备", "").startswith("Saat Round dimulai"))
    assert not cat["unique"].get("海的拥抱", "").startswith("Setiap 4")
    en_map = {r[4]: r[2] for r in cat["english_updates"] if len(r) == 5}
    for zh, id_val in cat["unique"].items():
        orig_en = en_map.get(zh, "")
        if len(zh) <= 6 and orig_en and len(orig_en) <= 25:
            assert len(id_val) < 40, f"Card title '{zh}' ({orig_en}) overwritten by long description: '{id_val}'"

    # 2. Roman I protection: 0 (aku) and 0 aku. <Upper>
    assert sum(1 for v in cat["unique"].values() if re.search(r"\(\s*aku\s*\)", v)) == 0
    assert sum(1 for r in cat["english_updates"] if re.search(r"\(\s*aku\s*\)", r[3])) == 0
    assert sum(1 for v in cat["unique"].values() if re.search(r"(?:^|>|\n)\s*aku\.\s+[A-Z]", v)) == 0
    assert sum(1 for r in cat["english_updates"] if re.search(r"(?:^|>|\n)\s*aku\.\s+[A-Z]", r[3])) == 0

    # 3. Specific semantic and tag defects: zero occurrences
    phase5_forbidden = [
        "Li</color>Bai",
        "sekutu</color>terdekat",
        "Tempat suci Sage",
        "Level atas",
        "kiri dan benar",
        "Sihir ATK",
        "Fisik ATK",
        "4Chang",
        "sebuah 1",
        "adalah digunakan",
        "adalah dihancurkan",
        "adalah dimainkan",
        "adalah milikmu",
    ]
    for ft in phase5_forbidden:
        ft_low = ft.lower()
        for zh, v in cat["unique"].items():
            if classifier.is_target_unique(zh) or ft != "4Chang":
                assert ft_low not in v.lower(), f"Found forbidden Phase 5 term '{ft}' in unique: {v}"
        for r in cat["english_updates"]:
            src_val = r[4] if len(r) == 5 else r[2]
            if classifier.is_target_update(r[0], r[1], r[2], r[3], src_val) or ft != "4Chang":
                assert ft_low not in r[3].lower(), f"Found forbidden Phase 5 term '{ft}' in english_updates: {r[3]}"

    # In Phase 6 (Hybrid Gameplay Edition), target gameplay descriptions translated to ID
    # must have zero glued tag boundaries. Non-target strings keep their authentic English baseline
    # from original catalog without introducing new glued tag boundaries.
    p_glued = re.compile(r"([A-Za-z0-9%])(<(?![/])(?:color|b|i|a|size)\b[^>]*>)|(</(?:color|b|i|a|size)>)([A-Za-z0-9])")
    classifier = HybridClassifier()
    orig_path = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "catalog" / "catalog.json.gz"
    orig_unique = {}
    if orig_path.exists():
        with gzip.open(orig_path, "rt", encoding="utf-8") as f:
            orig_unique = json.load(f).get("unique", {})

    target_glued = [v for zh, v in cat["unique"].items() if classifier.is_target_unique(zh) and p_glued.search(v)]
    assert len(target_glued) == 0, f"Found glued tag boundaries in target gameplay ID: {target_glued[:3]}"

    if orig_unique:
        new_nontarget_glued = [
            v for zh, v in cat["unique"].items()
            if not classifier.is_target_unique(zh) and not p_glued.search(orig_unique.get(zh, "")) and p_glued.search(v)
        ]
        assert len(new_nontarget_glued) == 0, f"Introduced new glued tag boundaries in non-target: {new_nontarget_glued[:3]}"

    # 4. Arthur multi-tag skill semantic alignment
    arthur_src = "举起圣剑跃向敌方人群密集处，额外造成<color=#d487e4>自身15%最大生命的法术伤害</color>并禁止范围内所有敌人恢复法力值，持续3秒"
    assert arthur_src in cat["unique"], "Arthur skill missing in unique"
    assert not cat["unique"][arthur_src].startswith("<color=#d487e4>Arthur")
    assert "<color=#d487e4>Magic Damage" in cat["unique"][arthur_src]

    # Phase 6 Remediation Verifications:
    t1_data = json.loads((REFS_DIR / "tier1_wiki_id.json").read_text(encoding="utf-8"))
    ref_hero_skill_talent_lord_zh: set[str] = set()
    for h in t1_data.get("hero", []):
        if h.get("descCn"):
            ref_hero_skill_talent_lord_zh.add(h["descCn"].strip())
        if h.get("awaken", {}).get("descCn"):
            ref_hero_skill_talent_lord_zh.add(h["awaken"]["descCn"].strip())
        for sk in h.get("skills", []):
            if sk.get("descCn"):
                ref_hero_skill_talent_lord_zh.add(sk["descCn"].strip())
            for enh in sk.get("enh", []):
                if enh.get("descCn"):
                    ref_hero_skill_talent_lord_zh.add(enh["descCn"].strip())
    for t in t1_data.get("talent", []):
        if t.get("descCn"):
            ref_hero_skill_talent_lord_zh.add(t["descCn"].strip())
    for l in t1_data.get("lords", []):
        for tal in l.get("talents", []):
            if tal.get("desc"):
                ref_hero_skill_talent_lord_zh.add(tal["desc"].strip())

    # 1. Assert 0 leaked Tier 1 Equipment descriptions
    for it in t1_data.get("equip", []):
        d = (it.get("descCn") or "").strip()
        if d and d in orig_cat["unique"] and d not in ref_hero_skill_talent_lord_zh and d not in WINDOWS_108_TARGET_DESC_ID:
            assert cat["unique"][d] == orig_cat["unique"][d], f"Tier 1 equipment leaked into Indonesian: {d!r} -> {cat['unique'][d]!r}"

    # 2. Assert 0 leaked Tier 1 standalone Effect Card descriptions
    for it in t1_data.get("effect", []):
        d = (it.get("descCn") or "").strip()
        if d and d in orig_cat["unique"] and d not in ref_hero_skill_talent_lord_zh and d not in WINDOWS_108_TARGET_DESC_ID:
            assert cat["unique"][d] == orig_cat["unique"][d], f"Tier 1 effect card leaked into Indonesian: {d!r} -> {cat['unique'][d]!r}"

    # 3. Assert 0 missed Tier 1 Hero, Skill, Skill enh, or Talent descriptions
    for h in t1_data.get("hero", []):
        for sk in h.get("skills", []):
            sk_d = (sk.get("descCn") or "").strip()
            if sk_d and sk_d in orig_cat["unique"]:
                assert cat["unique"][sk_d] != orig_cat["unique"][sk_d], f"Missed skill translation: {sk_d!r}"
            for enh in sk.get("enh", []):
                enh_d = (enh.get("descCn") or "").strip()
                if enh_d and enh_d in orig_cat["unique"]:
                    assert cat["unique"][enh_d] != orig_cat["unique"][enh_d], f"Missed skill enh translation: {enh_d!r}"
    for t in t1_data.get("talent", []):
        t_d = (t.get("descCn") or "").strip()
        if t_d and t_d in orig_cat["unique"]:
            assert cat["unique"][t_d] != orig_cat["unique"][t_d], f"Missed talent translation: {t_d!r}"

    # 4. Assert 0 occurrences of mangled embedded names or leaked strings
    forbidden_leak_terms = [
        "Maple Menari",
        "Moment dari Epiphany",
        "Serigala Jiwa",
        "Kekacauan Celah",
        "Physical darah-sucking",
        "Netral{0}/{1}",
        "Memilih atas target",
        "di sana adalah",
        "Chang Xiao'Skill",
        "Milady Memanggil Lineup",
        "I. Event Aturan",
    ]
    for flt in forbidden_leak_terms:
        flt_low = flt.lower()
        for v in cat["unique"].values():
            assert flt_low not in v.lower(), f"Found leaked/mangled term {flt!r} in unique: {v}"
        for r in cat["english_updates"]:
            assert flt_low not in r[3].lower(), f"Found leaked/mangled term {flt!r} in english_updates: {r[3]}"




