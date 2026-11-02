"""Tests for runtime validation rules and Unity rich-text tag skeleton re-injection."""

from __future__ import annotations

from wxq_patch import translation_rules as runtime_rules

from acepatchindo.tag_aligner import (
    normalize_plain_zh,
    reinject_skeleton_from_source,
    translate_preserving_skeleton,
)
from acepatchindo.validator import sanitize_target_text, validate_translation


def test_validate_translation_enforces_all_seven_rules() -> None:
    # 1. Empty string rejected
    assert validate_translation("攻击", "") == (False, "empty")
    assert validate_translation("攻击", "   ") == (False, "empty")

    # Valid with exact tags, placeholders, control tokens, semicolons
    src = "<a href=2><color=#708090ff><b>[阵营]</b></color></a>：获得+{0}攻击╫+{1}生命;全队生效"
    good = "<a href=2><color=#708090ff><b>[Faction]</b></color></a>: Dapat +{0} ATK╫+{1} HP; aktif untuk tim"
    assert validate_translation(src, good) == (True, "ok")
    assert runtime_rules.validate_translation(src, good) == (True, "ok")

    # 2. Rejects remaining CJK
    bad_cjk = "<a href=2><color=#708090ff><b>[阵营]</b></color></a>: Dapat +{0} ATK╫+{1} HP; aktif untuk tim"
    assert validate_translation(src, bad_cjk) == (False, "still_chinese")
    assert runtime_rules.validate_translation(src, bad_cjk) == (False, "still_chinese")

    # 3. Rejects stripped or reordered tags (unless angle_bracket_label <{...}>)
    bad_tags = "[Faction]: Dapat +{0} ATK╫+{1} HP; aktif untuk tim"
    assert validate_translation(src, bad_tags) == (False, "tags_changed")
    assert runtime_rules.validate_translation(src, bad_tags) == (False, "tags_changed")

    angle_src = "<{0}>"
    assert validate_translation(angle_src, "{0}") == (True, "ok")
    assert runtime_rules.validate_translation(angle_src, "{0}") == (True, "ok")

    # 4. Rejects missing or altered placeholders
    bad_ph = "<a href=2><color=#708090ff><b>[Faction]</b></color></a>: Dapat +{0} ATK╫+10 HP; aktif untuk tim"
    assert validate_translation(src, bad_ph) == (False, "placeholders_changed")
    assert runtime_rules.validate_translation(src, bad_ph) == (False, "placeholders_changed")

    # 5. Rejects missing control token ╫
    bad_ctrl = "<a href=2><color=#708090ff><b>[Faction]</b></color></a>: Dapat +{0} ATK +{1} HP; aktif untuk tim"
    assert validate_translation(src, bad_ctrl) == (False, "control_tokens_changed")
    assert runtime_rules.validate_translation(src, bad_ctrl) == (False, "control_tokens_changed")

    # 6. Rejects ASCII semicolon mismatch when ';' is in source
    src_semi = "第一阶段;第二阶段"
    assert validate_translation(src_semi, "Tahap 1, Tahap 2") == (
        False,
        "semicolons_changed",
    )
    assert validate_translation(src_semi, "Tahap 1; Tahap 2") == (True, "ok")
    assert sanitize_target_text("第一阶段，第二阶段", "Tahap 1; Tahap 2") == "Tahap 1, Tahap 2"

    # 7. Rejects extreme expansion when len(source) >= 4
    src_short4 = "物理伤害"
    too_long = "A" * 49
    assert validate_translation(src_short4, too_long) == (False, "extreme_expansion")
    assert runtime_rules.validate_translation(src_short4, too_long) == (
        False,
        "extreme_expansion",
    )


def test_normalize_plain_zh_strips_unity_tags_and_control_tokens() -> None:
    raw = "<b><color=#f2a900>登场</color></b>：若<a href=2><color=#708090ff><b>[光环]</b></color></a>激活╫获得1张牌"
    assert normalize_plain_zh(raw) == "登场：若[光环]激活获得1张牌"


def test_reinject_skeleton_preserves_tags_placeholders_and_tokens() -> None:
    source_zh = (
        "<a href=2><color=#708090ff><b>[光环]</b></color></a>："
        "全体友方英雄获得+{0}攻击╫+{1}最大生命"
    )
    plain_id = "[Aura]: Semua Hero sekutu mendapatkan +{0} ATK, +{1} Max HP"
    reconstructed = reinject_skeleton_from_source(source_zh, plain_id)
    ok, reason = validate_translation(source_zh, reconstructed)
    assert ok, f"Failed validation ({reason}): {reconstructed}"
    assert runtime_rules.validate_translation(source_zh, reconstructed) == (True, "ok")
    assert "<a href=2><color=#708090ff><b>[Aura]</b></color></a>" in reconstructed
    assert "╫" in reconstructed


def test_reinject_skeleton_with_english_prefix_preserves_href_keyword() -> None:
    source_zh = "<a href=10><color=#ffffff>╫<b>牺牲</b></color></a>：苏烈的等级永久+2。"
    baseline_en = "<a href=10><color=#ffffff>╫<b>Sacrifice</b></color></a>: Su Lie's Level permanently +2."
    plain_id = "Sacrifice: Level Su Lie +2 secara permanen."
    reconstructed = reinject_skeleton_from_source(
        source_zh, plain_id, baseline_en=baseline_en
    )
    assert validate_translation(source_zh, reconstructed) == (True, "ok")
    assert runtime_rules.validate_translation(source_zh, reconstructed) == (True, "ok")
    assert "<a href=10><color=#ffffff>╫<b>Sacrifice</b></color></a>" in reconstructed


def test_translate_preserving_skeleton_handles_semicolon_segments() -> None:
    source_zh = "伤害提升{0}%;减伤提升{1}%"
    segment_translator = lambda seg: (
        seg.replace("伤害提升", "DMG meningkat ").replace(
            "减伤提升", "Reduksi DMG meningkat "
        )
    )
    result = translate_preserving_skeleton(source_zh, segment_translator)
    assert result == "DMG meningkat {0}%;Reduksi DMG meningkat {1}%"
    assert validate_translation(source_zh, sanitize_target_text(source_zh, result)) == (
        True,
        "ok",
    )

