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


def test_da_qiao_deploy_tag_does_not_swallow_entire_sentence() -> None:
    source_zh = (
        "每触发2次友方<a href=1><color=#ffffff>╨<b>登场</b></color></a>效果，"
        "大乔法力上限永久减少5点，且自身等级+1。"
    )
    raw_id = (
        "Setiap 2 kali efek Deploy sekutu terpicu, batas Mana Da Qiao "
        "berkurang 5 secara permanen dan mendapat +1 Level."
    )
    aligned = reinject_skeleton_from_source(source_zh, raw_id)
    ok, reason = validate_translation(source_zh, aligned)
    assert ok, reason
    assert "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>" in aligned
    assert not aligned.endswith("</b></color></a>.")
    assert not aligned.endswith("</a>.")

    # Even with raw uncurated 'pada-entri' or missing alias, it should not swallow whole sentence
    raw_id_calque = (
        "Setiap 2 sekutu pada-entri efek terpicu, batas Mana Da Qiao "
        "berkurang 5 secara permanen dan mendapat +1 Level."
    )
    aligned_calque = reinject_skeleton_from_source(source_zh, raw_id_calque)
    ok_c, reason_c = validate_translation(source_zh, aligned_calque)
    assert ok_c, reason_c
    assert not aligned_calque.startswith("<a href=1><color=#ffffff>╨<b>Setiap 2 sekutu")



def test_gan_and_mo_bold_tag_wraps_only_equipment_name() -> None:
    source_zh = (
        "干将莫邪使用普通装备时，随机获得普通装备"
        "<color=#ffffff><b>干剑·莫邪</b></color>。"
    )
    raw_id = (
        "Saat Gan & Mo memakai Normal Equipment, memperoleh acak "
        "Normal Equipment Twin Blade · Male."
    )
    aligned = reinject_skeleton_from_source(source_zh, raw_id)
    ok, reason = validate_translation(source_zh, aligned)
    assert ok, reason
    assert "<color=#ffffff><b>Twin Blade · Male</b></color>" in aligned
    assert not aligned.startswith("<color=#ffffff><b>Saat")


def test_smart_armor_control_token_placement_and_spacing() -> None:
    source_zh = (
        "随机获得1件【日落海专属装备】。我方英雄每穿戴1件【日落海专属装备】，其"
        "<color=#FFE897>╬整备效果会额外触发1次</color>。"
    )
    raw_id = (
        "Secara acak memperoleh 1 [Equipment Eksklusif Sunset Sea]. Setiap kali "
        "Hero milikmu mengenakan 1 [Equipment Eksklusif Sunset Sea], efek Prepare-nya "
        "akan terpicu 1 kali tambahan."
    )
    aligned = reinject_skeleton_from_source(source_zh, raw_id)
    ok, reason = validate_translation(source_zh, aligned)
    assert ok, reason
    assert ",<color" not in aligned
    assert ",╬" not in aligned
    assert "╬" in aligned


def test_money_makes_might_combat_tag_does_not_swallow_first_clause() -> None:
    source_zh = (
        "战斗开始时，若金币数≥50，<color=#FFE897>全体友方英雄获得20点物理攻击力</color>。"
    )
    raw_id = (
        "Saat Combat dimulai, jika koin emas ≥50, semua Hero sekutu memperoleh "
        "20 Physical Attack."
    )
    aligned = reinject_skeleton_from_source(source_zh, raw_id)
    ok, reason = validate_translation(source_zh, aligned)
    assert ok, reason
    assert not aligned.startswith("<color=#FFE897>Saat Combat dimulai")



