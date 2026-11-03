"""Tests for the 3-Tier Indonesian Glossary and Windows 108 missing strings translation."""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

from wxq_patch import translation_rules as runtime_rules

from acepatchindo.glossary import WINDOWS_108_ZH_TO_ID, ThreeTierGlossary
from acepatchindo.hybrid_classifier import ALLOWED_TARGET_PREFIXES, HybridClassifier
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

    assert 4000 <= target_count <= 5200, (
        f"Expected between 4,000 and 5,200 target gameplay descriptions in unique, got {target_count}"
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
        "Luban Tidak",
        "Tidak. 7",
        "Mementalkan Atas",
        "Hebat Dinding",
        "Damage Atas",
        "Decay Bawah",
        "Batas Atas",
        "Mechanical Minion sebuah1",
        "pada Skill Menggunakan",
        "Three Kingdoms Pejuang",
        "Sunset Pejuang",
        "orbit di sekitarnya",
        "dasar Lu Bu serangan",
        "dasar Augran serangan",
        "melompat menjadi padat",
        "sebuah padat",
        "itu orbit",
        "itu mengelilinginya",
        "Merah tua Bayangan",
        "Hati Menjaga",
        "putri duyung wujud dalam air",
        "Basic Attack Basic Attack",
        "ke Menyerang",
        "ke Memberikan",
        "ke Memulihkan",
        "ke Memicu",
    ]
    for flt in forbidden_leak_terms:
        flt_low = flt.lower()
        for v in cat["unique"].values():
            assert flt_low not in v.lower(), f"Found leaked/mangled term {flt!r} in unique: {v}"
        for r in cat["english_updates"]:
            assert flt_low not in r[3].lower(), f"Found leaked/mangled term {flt!r} in english_updates: {r[3]}"

    # Phase 6 Round 2 Remediation Verifications:
    # 1. 0 Voice lines / quotes leaked into Indonesian
    voice_quotes = [
        "女人，是水做的。",
        "你已经被盯上了。",
        "清理工作才刚刚开始。",
        "生存，还是毁灭，这是个问题。",
    ]
    for vq in voice_quotes:
        if vq in cat["unique"] and vq in orig_cat["unique"]:
            assert cat["unique"][vq] == orig_cat["unique"][vq], f"Voice line translated to ID: {vq!r} -> {cat['unique'][vq]!r}"

    # 2. Check hybrid VFS index invariants
    vfs_index_path = REFS_DIR / "hybrid_vfs_index.json"
    if vfs_index_path.exists():
        vfs_data = json.loads(vfs_index_path.read_text(encoding="utf-8"))
        assert len(vfs_data.get("vfs_target_keys", [])) >= 24000
        # 0 conflicting sfx between target and veto
        tgt_sfx = {k[5:17] for k in vfs_data.get("vfs_target_keys", [])}
        veto_sfx = set(vfs_data.get("vfs_veto_sfx", []))
        conflicts = tgt_sfx & veto_sfx
        assert len(conflicts) == 0, f"Found conflicting sfx in VFS index: {conflicts}"
        # 0 non-CJK in target zh
        cjk_re = re.compile(r"[\u4e00-\u9fff]")
        non_cjk = [z for z in vfs_data.get("vfs_target_zh", []) if not cjk_re.search(z)]
        assert len(non_cjk) == 0, f"Found non-CJK strings in vfs_target_zh: {non_cjk[:5]}"
        # 0 #60D2 tag leaks (e.g. '三分之地   战士')
        assert all("三分之地   战士" not in z for z in vfs_data.get("vfs_target_zh", []))
        assert all("三分之地\t" not in z for z in vfs_data.get("vfs_target_zh", []))

    # Phase 6 Round 3 Remediation Verifications:
    # 1. Assert specific unique strings translated to Indonesian
    round3_target_uniques = [
        "<color=#FFE897>4/5阶的召唤单位</color>获得╧完美复生。",
        "光辉伤害提升至[0]%法术攻击力",
        "子弹伤害提升至40+25%物理攻击力",
        "导弹伤害提升至30+80%物理攻击力",
    ]
    for tu in round3_target_uniques:
        if tu in cat["unique"] and tu in orig_cat["unique"]:
            assert cat["unique"][tu] != orig_cat["unique"][tu], f"Target unique not translated to ID: {tu!r}"
    cirrus_found = False
    for k, v in cat["unique"].items():
        if "云中君展翅舞蹈向周围1格射出羽箭" in k:
            cirrus_found = True
            assert v != orig_cat["unique"].get(k), f"Cirrus skill not translated to ID: {k!r}"
    assert cirrus_found, "Cirrus skill string not found in unique catalog!"

    # 2. Assert specific english_updates translated to Indonesian
    round3_upd_keys = {
        "#BCDEF24440F2D6B7#",
        "#BCDEEB1EA4FBE926#",
        "#BCDE84EBBBE3F468#",
        "#23F7F8529D5D33D5#",
    }
    orig_upd_map = {r[1]: r for r in orig_cat.get("english_updates", [])}
    for r in cat.get("english_updates", []):
        if r[1] in round3_upd_keys:
            orig_r = orig_upd_map.get(r[1])
            assert orig_r is not None, f"Key {r[1]} not found in original catalog english_updates"
            assert r[3] != orig_r[3], f"Row {r[1]} in english_updates was not translated to ID!"

    # 3. Assert 0 mismatches between cat["unique"] and cat["english_updates"]
    for r in cat.get("english_updates", []):
        k = r[1]
        opt_zh = r[4] if len(r) > 4 else ""
        tag = k[1:5] if k.startswith("#") and len(k) >= 5 else ""
        if opt_zh and opt_zh in cat["unique"] and tag in ALLOWED_TARGET_PREFIXES - {"60D2"}:
            if cat["unique"][opt_zh] != orig_cat["unique"].get(opt_zh):
                orig_r = orig_upd_map.get(k)
                if orig_r:
                    assert r[3] != orig_r[3], f"Row {k} in english_updates not translated even though unique was: {opt_zh!r}"

    # Phase 6 Round 4 Remediation Verifications:
    diff_u = {k: v for k, v in cat["unique"].items() if v != orig_cat["unique"].get(k)}

    # 1. Zero lost \n newlines
    lost_nl = [k for k, v in diff_u.items() if "\n" in k and "\n" not in v]
    assert len(lost_nl) == 0, f"Found strings that lost \\n newlines ({len(lost_nl)}): {lost_nl[:3]}"

    # 2. Zero misplaced control glyphs at index 0
    CTRL = set("╥╆╪╬╉═╧╊╅╈╦╇╋")
    misplaced_ctrl = []
    for k, v in diff_u.items():
        v_clean = TAG_RE.sub("", v).strip()
        k_clean = TAG_RE.sub("", k).strip()
        if v_clean and v_clean[0] in CTRL:
            if not any(c in k_clean[:6] for c in CTRL):
                misplaced_ctrl.append((k, v))
    assert len(misplaced_ctrl) == 0, f"Found misplaced control glyphs at index 0 ({len(misplaced_ctrl)}): {misplaced_ctrl[:3]}"

    if "<color=#FFE897>4/5阶的召唤单位</color>获得╧完美复生。" in cat["unique"]:
        val_pr = cat["unique"]["<color=#FFE897>4/5阶的召唤单位</color>获得╧完美复生。"]
        assert not val_pr.startswith("╧"), f"Perfect Revive glyph misplaced at start: {val_pr!r}"
        assert "╧Perfect Revive" in val_pr, f"Missing ╧Perfect Revive in: {val_pr!r}"

    if "战斗开始时，╉先知图腾将两侧的友军变为╉先知图腾分身，复制本体70%的属性。" in cat["unique"]:
        val_pt = cat["unique"]["战斗开始时，╉先知图腾将两侧的友军变为╉先知图腾分身，复制本体70%的属性。"]
        assert not val_pt.startswith("╉"), f"Prophet Totem glyph misplaced at start: {val_pt!r}"

    # 3. Zero deleted numbers / scrambled placeholders
    bad_ph_patterns = [
        "Memperoleh ,",
        "Memperoleh .",
        " -. ",
        "-20 {Energy}",
        "Skill </color> kali",
        "setiap kamu kalah</color> kali",
        "Tier {0|",
    ]
    for bp in bad_ph_patterns:
        hits = [v for v in diff_u.values() if bp in v]
        assert len(hits) == 0, f"Found scrambled placeholder / deleted number pattern {bp!r} in {hits[:2]}"

    # 4. Zero _wrap_exact_tag_sequence mid-clause chunk slicing on multi-color skills
    bad_chunk_slices = [
        "<color=#ffffffbf> Pasif: Basic Attack",
        "<color=#ffffffbf> di depannya",
        "<color=#ffffffbf> pipa dan mengaktifkan",
        "<color=#d487e4> bola energi yang",
        "<color=#d487e4> Saat bola",
    ]
    for bc in bad_chunk_slices:
        hits = [v for v in diff_u.values() if bc in v]
        assert len(hits) == 0, f"Found mid-clause chunk slice {bc!r} in {hits[:2]}"

    # 5. Zero leaked choice/draw effect cards, equipment-choice cards, or training dummy strings
    unauthorized_leaks = [
        "3选1一件特殊装备。",
        "3选1一件高级装备。",
        "5选2【三分之地】4-5阶英雄，各获得2张其英雄牌。",
        "404 Error，出厂设置故障，无法攻击敌人。",
        "训练用人偶4号，结实耐用可靠！",
    ]
    for z in unauthorized_leaks:
        if z in cat["unique"] and z in orig_cat["unique"]:
            assert cat["unique"][z] == orig_cat["unique"][z], f"Unauthorized string leaked into ID: {z!r} -> {cat['unique'][z]!r}"

    # 6. Bai Ge's Burst of Inspiration accuracy
    bai_ge_src = "释放3道剑气，斩击手牌中随机3张非觉醒英雄牌，将每张牌斩为2张╆转瞬版复制。"
    if bai_ge_src in cat["unique"]:
        bg_val = cat["unique"][bai_ge_src]
        assert "pedang" in bg_val, f"Expected 'pedang' in Bai Ge Burst of Inspiration: {bg_val!r}"
        assert "menyalin 1 Hero" not in bg_val, f"Found incorrect Improvised Creation in Bai Ge Burst of Inspiration: {bg_val!r}"

    # Phase 6 Round 5 Remediation Verifications (Task 42):
    # 7. Zero unexpanded sentinel/slot tokens across entire catalog
    for sec in ("unique", "english_updates"):
        items = cat[sec].items() if isinstance(cat[sec], dict) else enumerate(cat[sec])
        for k, v in items:
            if isinstance(v, list):
                for row in v:
                    assert "__EXPR" not in str(row) and "__WXQ" not in str(row) and "__SLOT" not in str(row), f"Unexpanded sentinel in {sec}: {row}"
            else:
                assert "__EXPR" not in str(v) and "__WXQ" not in str(v) and "__SLOT" not in str(v), f"Unexpanded sentinel in {sec}: {k} -> {v}"

    # 8. Zero <color=#ffffffbf> header bleed into body words
    header_bleed = [
        (k, v) for k, v in diff_u.items()
        if re.search(r"<color=#ffffffbf>\s*(?:Pasif|Aktif)\s*:\s+\S+", v)
    ]
    assert len(header_bleed) == 0, f"Header bleed into body words ({len(header_bleed)}): {header_bleed[:5]}"

    # 9. Zero overwritten duration/distance numbers
    assert not any("selama [6] detik" in v or "selama [159004p2q2] detik" in v or "dalam [2] tile" in v for v in diff_u.values()), "Found overwritten duration/distance numbers in diff_u"

    # 10. Parenthetical 2-tag Hero skills preserve exact tags (Lu Bu)
    lubu_target_keys = [
        k for k in cat["unique"]
        if "吕布" in k and "[0]点物理伤害" in k and ("（[1]+[2]%物理攻击力）" in k or "([1]+[2]%物理攻击力)" in k)
    ]
    assert len(lubu_target_keys) > 0, "Missing Lu Bu parenthetical skill string in cat['unique']"
    for lk in lubu_target_keys:
        lubu_val = cat["unique"][lk]
        assert "<color=#ffffffbf>Aktif:</color>" in lubu_val, f"Missing clean '<color=#ffffffbf>Aktif:</color>' in: {lubu_val!r}"
        assert "<color=#dfa15e>[0] Physical Damage</color><color=#dfa15e> ([1]+[2]% Physical Attack)</color>" in lubu_val, f"Missing parenthetical formula tags in: {lubu_val!r}"

    exemplar_lubu = (
        "<color=#ffffffbf>被动：</color>吕布会根据敌人位置使用不同招式，普攻能对身前2格内敌人造成伤害。\n"
        "<color=#ffffffbf>主动：</color>吕布跳向指定位置，落地后挥斩，对大范围的敌人造成<color=#dfa15e>[0]点物理伤害</color><color=#dfa15e>（[1]+[2]%物理攻击力）</color>并击飞[3]秒。\n"
        "<color=#86888A>点击技能描述面板，查看<b>击飞</b>详细解释</color>"
    )
    if exemplar_lubu in cat["unique"]:
        ex_val = cat["unique"][exemplar_lubu]
        assert "<color=#ffffffbf>Aktif:</color>" in ex_val
        assert "<color=#dfa15e>[0] Physical Damage</color><color=#dfa15e> ([1]+[2]% Physical Attack)</color>" in ex_val


def test_round6_footer_terms_and_zero_fallback_wraps() -> None:
    catalog_path = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
    with gzip.open(catalog_path, "rt", encoding="utf-8") as f:
        cat = json.load(f)

    # 1. Zero Misplaced {1|1} on {LordHp}-10 / {LordHp}-15 & Exact -15 Preservation
    s_hp10 = "<color=#FFE897>{LordHp}</color>-10，战斗开始时，<color=#FFE897>己方每名英雄</color>+2═临时等级。战斗胜利时，获得{1|1}{LordHp}，═临时等级额外+1。"
    s_hp15 = "<color=#FFE897>{LordHp}</color>-15，战斗开始时，<color=#FFE897>己方每名英雄</color>+2═临时等级。战斗胜利时，获得{1|1}{LordHp}，═临时等级额外+1。"
    if s_hp10 in cat["unique"]:
        assert not cat["unique"][s_hp10].startswith("{1|1}") and "{1|1}{LordHp}" in cat["unique"][s_hp10]
    if s_hp15 in cat["unique"]:
        assert not cat["unique"][s_hp15].startswith("{1|1}") and "-15" in cat["unique"][s_hp15] and "{1|1}{LordHp}" in cat["unique"][s_hp15]

    # 2. Try Your Luck (碰碰运气) Range Placeholder Precision
    s_tyl = "<color=#FFE897>棋手升级时</color>，获得1张天赋牌<color=#FFE897>碰碰运气</color>：指定1名英雄提升5-20等级，随机消耗{0|1}-{0|5}{Energy}。"
    if s_tyl in cat["unique"]:
        assert "memperoleh 1 Kartu Talent" in cat["unique"][s_tyl] and "{0|1}-{0|5}{Energy}" in cat["unique"][s_tyl]

    # 3. Zero Tier 3 Fallback on Footer-Tagged Tier 1 Hero Skills (Donghuang, Lu Bu Variant 1, Bai Qi, Xiao Qiao)
    s_dh = "<color=#ffffffbf>被动：</color>东皇太一创造3颗能量球绕自身转动。能量球触碰到敌人时会造成其<color=#d487e4>[0]%最大生命值的法术伤害</color>并恢复东皇<color=#9ff5d0>[1]%的最大生命值</color>。\n\n<color=#ffffffbf>主动：</color>东皇太一施展堕神契约<color=#ffffffbf>压制</color>目标敌人5秒，期间双方承受等量伤害。若期间与目标距离过远，则效果提前中断。\n\n\n<color=#86888A>点击技能描述面板，查看<b>压制</b>详细解释</color>"
    if s_dh in cat["unique"]:
        assert "<b>Suppress</b>" in cat["unique"][s_dh] and "Energi bola" not in cat["unique"][s_dh]

    # 4. Zero Chunk-Sliced Tags on Dolia, Ming Shiyin, Dr. Bian, Yao, Shi, Fleeting, and Totem
    dolia_k = "<color=#ffffffbf>被动：</color>朵莉亚在自身创建的水域内会化身人鱼形态。普通攻击会额外恢复5点法力值，对目标附带<color=#d487e4>50%法术攻击力的法术伤害</color>，在水域内再次施放技能，原水域消失形成新水域。\n<color=#ffffffbf>主动：</color>跃向3格内友军密集处创造一片水域，水域持续10秒，朵莉亚在水域中化身人鱼形态，落地立即恢复范围内友军<color=#d487e4>75+100%法术攻击力</color><color=#9ff5d0>的生命值</color>，10点法力值（法力值恢复不对朵莉亚生效），水域每秒恢复范围内友军<color=#d487e4>50%法术攻击力</color><color=#9ff5d0>的生命值</color>，朵莉亚离开水域时水域消失并且恢复人形态。"
    if dolia_k in cat["unique"]:
        assert "<color=#d487e4> tile dan" not in cat["unique"][dolia_k]

    fleet_k = "使用技能，随机获得1张2-5阶的<a href=3130012><color=#ffffff>╆<b>转瞬</b></color></a>英雄牌。"
    if fleet_k in cat["unique"]:
        assert "<b> secara acak 1</b>" not in cat["unique"][fleet_k]

    totem_k = "<a href=321><color=#ffffff>╉<b>图腾</b></color></a>不会被优先攻击。\n<a href=3><color=#ffffff>╪<b>开团</b></color></a>：获得每个<a href=321><color=#ffffff>╉<b>图腾</b></color></a>等级数15%的<a href=3130011><color=#ffffff>═<b>临时等级</b></color></a>。"
    if totem_k in cat["unique"]:
        assert "<b> sebesar</b>" not in cat["unique"][totem_k]

    voucher_k = "获得<color=#FFE897>{0|2}{Energy}</color>以及2张<color=#FFE897>3阶英雄兑换券</color>。"
    if voucher_k in cat["unique"]:
        assert not cat["unique"][voucher_k].startswith("<color=#FFE897>Memperoleh</color>")







