import re
from acepatchindo.card_wrapper import (
    ensure_placeholder_spacing,
    normalize_brackets,
    wrap_card_description,
)
from acepatchindo.validator import validate_translation


def test_ensure_placeholder_spacing_fixes_glued_tokens():
    raw = "Memperoleh {0|1}{Energy}, memulihkan 1{LordHp} dan 4{LordExp}."
    fixed = ensure_placeholder_spacing(raw)
    assert fixed == "Memperoleh {0|1} {Energy}, memulihkan 1 {LordHp} dan 4 {LordExp}."


def test_ensure_placeholder_spacing_fixes_digit_glued_to_words():
    raw = "gagal, +2Renovation dan 4Chess player experience."
    fixed = ensure_placeholder_spacing(raw)
    assert "+2 Renovation" in fixed
    assert "4 Chess player experience" in fixed


def test_normalize_brackets_converts_fullwidth():
    raw = "Dapat dipasang ke Hero 【Central Plains】 atau 【Sunset Sea】."
    assert normalize_brackets(raw) == "Dapat dipasang ke Hero [Central Plains] atau [Sunset Sea]."


def test_wrap_card_description_prevents_mid_word_split_and_preserves_tags():
    source_zh = "<a href=1><color=#ffffff>╨<b>登场</b></color></a>：己方穿戴装备最多的1名英雄等级+2。"
    translated = (
        "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>: "
        "1 Hero sekutu dengan Equipment terbanyak mendapat +2 Level."
    )
    wrapped = wrap_card_description(translated, max_width=26)
    assert "\n" in wrapped
    for line in wrapped.split("\n"):
        visible = re.sub(r"<[^>]+>", "", line)
        assert len(visible) <= 28
        assert not line.endswith("+")
        assert not line.endswith("-")
    ok, reason = validate_translation(source_zh, wrapped)
    assert ok, f"Validation failed: {reason}"


def test_wrap_card_description_never_wraps_semicolons():
    raw = "Bagian 1; Bagian 2; Bagian 3 yang sangat panjang melebihi batas karakter lebar card."
    assert wrap_card_description(raw, max_width=26) == raw


def test_fixes_tier1_level_n_hero_ambiguity():
    # Allain
    zh_allain = "<a href=1><color=#ffffff>╨<b>登场</b></color></a>：己方穿戴装备最多的1名英雄等级+2。"
    raw_allain = "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>: Level 1 Hero milikmu yang memakai Equipment terbanyak +2."
    from acepatchindo.card_rewriter import polish_indonesian_card_text
    fixed = polish_indonesian_card_text(zh_allain, raw_allain)
    assert "Level 1 Hero" not in fixed
    assert "1 Hero sekutu yang memakai Equipment terbanyak mendapat +2 Level" in fixed or "1 Hero" in fixed
    assert "mendapat +2 Level" in fixed

    # Dolia
    zh_dolia = "<a href=1><color=#ffffff>╨<b>登场</b></color></a>：随机3名英雄及<a href=11><color=#ffffff>🌀<b>阿科米亚核心</b></color></a>等级+1。"
    raw_dolia = "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>: Level 3 Hero acak dan <a href=11><color=#ffffff>🌀<b>Akomia Core</b></color></a> +1."
    fixed_dolia = polish_indonesian_card_text(zh_dolia, raw_dolia)
    assert "Level 3 Hero" not in fixed_dolia
    assert "3 Hero acak" in fixed_dolia
    assert "Arcomia Core" in fixed_dolia
    assert "+1 Level" in fixed_dolia


def test_unifies_glossary_and_entity_names():
    from acepatchindo.card_rewriter import polish_indonesian_card_text
    raw = (
        "<a href=3><color=#ffffff>╪<b>Engage</b></color></a>: Saat Ganjiang Moye, "
        "Baili Shouyue, Zhuge Liang, Yang Yuhuan, atau Jiang Ziya berada di field "
        "atau di medan tempur, efek Preparation memberikan Kartu Tactic dan Akomia Core."
    )
    fixed = polish_indonesian_card_text("", raw)
    assert "Initiate" in fixed
    assert "Engage" not in fixed
    assert "Gan & Mo" in fixed
    assert "Ganjiang Moye" not in fixed
    assert "Shouyue" in fixed
    assert "Baili Shouyue" not in fixed
    assert "Kongming" in fixed
    assert "Zhuge Liang" not in fixed
    assert "Yuhuan" in fixed
    assert "Yang Yuhuan" not in fixed
    assert "Ziya" in fixed
    assert "Jiang Ziya" not in fixed
    assert "di arena" in fixed
    assert "di field" not in fixed
    assert "di medan tempur" not in fixed
    assert "Prepare" in fixed
    assert "Preparation" not in fixed
    assert "Kartu Efek" in fixed
    assert "Kartu Tactic" not in fixed
    assert "Arcomia Core" in fixed
    assert "Akomia Core" not in fixed


def test_syncs_parent_card_references_to_related_card_titles():
    from acepatchindo.card_rewriter import rewrite_en_card_to_id
    en_celestial = "Gain 3 Melodious Notes."
    id_celestial = rewrite_en_card_to_id("获得3张绕梁之音。", en_celestial)
    assert "Melody" in id_celestial
    assert "Melodious Notes" not in id_celestial

    en_glimmer = "Restore 1{LordHp}. Gain 2 Famous Blade • Life-Stealer."
    id_glimmer = rewrite_en_card_to_id("恢复1{LordHp}，获得2张名刀·司命。", en_glimmer)
    assert "Destiny" in id_glimmer
    assert "Famous Blade" not in id_glimmer

    en_voucher = "Gain 1 Tier 5 Hero Exchange Vouchers."
    id_voucher = rewrite_en_card_to_id("获得1张五阶英雄兑换券。", en_voucher)
    assert "Tier 5 Hero Voucher" in id_voucher


def test_rewrites_broken_calques_in_en_card():
    from acepatchindo.card_rewriter import rewrite_en_card_to_id
    en_rec = "After use, Record all non-Awakened cards. From now on, these Cards gain +1 next Round."
    id_rec = rewrite_en_card_to_id("", en_rec)
    assert "Rekor" not in id_rec
    assert "Mencatat" in id_rec
    assert "dari Sekarang pada" not in id_rec
    assert "mulai sekarang" in id_rec.lower()
    assert "ini Kartu" not in id_rec
    assert "Kartu ini" in id_rec
    assert "berikutnya Round" not in id_rec
    assert "Round berikutnya" in id_rec

    en_loc = "creates a clone at original location of nearest enemy"
    id_loc = rewrite_en_card_to_id("", en_loc)
    assert "asli lokasi" not in id_loc
    assert "lokasi awal" in id_loc
    assert "terdekat musuh" not in id_loc
    assert "musuh terdekat" in id_loc

