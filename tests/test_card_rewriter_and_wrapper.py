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
