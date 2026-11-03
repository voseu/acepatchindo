"""Tag-stripping normalization and tag-skeleton re-injection for HoK Ace strings."""

from __future__ import annotations

import re
from collections import Counter
from typing import Callable

from acepatchindo.validator import (
    CJK_RE,
    CONTROL_TOKEN_RE,
    PLACEHOLDER_RE,
    TAG_RE,
    sanitize_target_text,
    validate_translation,
)

# Canonical bracketed & keyword mechanic map (Chinese -> Tier 1 Indonesian/English label)
BRACKET_TERM_MAP: dict[str, str] = {
    "[光环]": "[Aura]",
    "[登场]": "[Play]",
    "[激发]": "[Trigger]",
    "[连携]": "[Combo]",
    "[变身]": "[Transform]",
    "[召唤]": "[Summon]",
    "[回手]": "[Bounce]",
    "[摧毁]": "[Destroy]",
    "[吞噬]": "[Devour]",
    "[护盾]": "[Shield]",
    "[阵营]": "[Faction]",
    "[职业]": "[Class]",
    "[物理]": "[Physical]",
    "[法术]": "[Magic]",
    "[真实]": "[True]",
    "[暴击]": "[Crit]",
    "[眩晕]": "[Stun]",
    "[冰冻]": "[Freeze]",
    "[灼烧]": "[Burn]",
    "[中毒]": "[Poison]",
    "[沉默]": "[Silence]",
    "[缴械]": "[Disarm]",
    "[免疫]": "[Immune]",
    "[被动]": "[Pasif]",
    "[主动]": "[Aktif]",
    "[天赋]": "[Talent]",
    "[效果牌]": "[Kartu Efek]",
    "[装备]": "[Equipment]",
    "[三分]": "[Three Kingdoms]",
    "【三分】": "[Three Kingdoms]",
    "[河洛]": "[Central Plains]",
    "【河洛】": "[Central Plains]",
    "[逐鹿]": "[Zhulu Plateau]",
    "【逐鹿】": "[Zhulu Plateau]",
    "[日落海]": "[Sunset Sea]",
    "【日落海】": "[Sunset Sea]",
    "[稷下]": "[Jixia]",
    "【稷下】": "[Jixia]",
    "[长城]": "[Great Wall]",
    "【长城】": "[Great Wall]",
    "[玄雍]": "[Xuanyong]",
    "【玄雍】": "[Xuanyong]",
    "[尧天]": "[Yaotian]",
    "【尧天】": "[Yaotian]",
    "[云梦泽]": "[Yunmeng]",
    "【云梦泽】": "[Yunmeng]",
    "[大河]": "[Riverlands]",
    "【大河】": "[Riverlands]",
    "[混沌裂隙]": "[Chaos Rift]",
    "【混沌裂隙】": "[Chaos Rift]",
    "牺牲": "Sacrifice",
    "筹备": "Preparation",
    "登场": "On Play",
    "光环": "Aura",
    "激发": "Inspire",
    "连携": "Synergy",
    "召唤": "Summon",
    "变身": "Transform",
    "复生": "Revive",
    "刷新": "Refresh",
    "临时等级": "Temporary Level",
    "真实等级": "True Level",
    "阿科米亚核心": "Akomia Core",
    "古币": "Ancient Coin",
    "精炼古币": "Refined Ancient Coin",
    "开团": "Engage",
    "退场": "Exit",
    "合成": "Synthesis",
    "夺取": "Steal",
    "凯旋": "Triumph",
    "唯一": "Unik",
    "先知图腾": "Seer Totem",
    "因缘图腾": "Destiny Totem",
    "往生图腾": "Afterlife Totem",
    "虚妄图腾": "Illusory Totem",
    "熊灵": "Bear Spirit",
    "始祖熊灵": "Ancestral Bear Spirit",
    "狼魂": "Wolf Soul",
    "圣殿骑士": "Templar Knight",
    "机关傀儡": "Mechanical Puppet",
    "玄雍士兵": "Xuanyong Soldier",
    "暗影仆从": "Shadow Servant",
    "影侍": "Shadow Servant",
    "常小娥": "Chang Xiao'e",
    "干将莫邪": "Gan & Mo",
}

BADGE_ALIAS_MAP: dict[str, list[str]] = {
    "闪现": ["Flash.", "Flash"],
    "整备": ["Preparation:", "Preparation", "Prepare"],
    "筹备": ["Preparation:", "Preparation", "Prepare"],
    "登场": ["Deploy:", "Deploy", "On Play"],
    "开团": ["Engage:", "Engage", "Initiate"],
    "牺牲": ["Sacrifice:", "Sacrifice"],
    "复生": ["Revive:", "Revive"],
    "完美复生": ["Perfect Revive:", "Perfect Revive", "Perfect Resurrection"],
    "临时等级": ["Temporary Level", "Level Sementara"],
    "真实等级": ["True Level", "Level Nyata"],
    "阿科米亚核心": ["Akomia Core", "Arcomia Core", "Core Akomia"],
    "古币": ["Ancient Coin", "Koin Kuno"],
    "精炼古币": ["Refined Ancient Coin", "Koin Kuno Murni"],
    "光环": ["Aura"],
    "激发": ["Inspire", "Trigger"],
    "连携": ["Synergy", "Combo"],
    "变身": ["Transform"],
    "召唤": ["Summon"],
    "回手": ["Bounce"],
    "摧毁": ["Destroy"],
    "吞噬": ["Devour"],
    "护盾": ["Shield"],
    "刷新": ["Refresh"],
    "退场": ["Exit:", "Exit"],
    "合成": ["Synthesis", "Merge"],
    "转瞬": ["Fleet", "Instant"],
    "图腾系列": ["Totem Series", "Seri Totem"],
    "图腾": ["Totem"],
    "夺取": ["Steal"],
    "凯旋": ["Triumph"],
    "开局": ["Game Start", "Start"],
    "唯一": ["Unique", "Unik"],
    "主动": ["Aktif:", "Aktif", "Active"],
    "被动": ["Pasif:", "Pasif", "Passive"],
    "主动技能变为融合技": [
        "Skill Aktif menjadi sebuah Skill Gabungan",
        "Skill Aktif menjadi Skill Gabungan",
    ],
    "击退": ["Knockback", "knockback"],
    "眩晕": ["Stun", "stun"],
    "击飞": ["Knock-up", "Knock up", "knock-up"],
    "河洛": ["Central Plains", "Central Plain"],
    "逐鹿": ["Zhulu Plateau", "Zhulu", "Conquest"],
    "三分": ["Three Kingdoms"],
    "日落海": ["Sunset Sea", "Sunset"],
    "稷下": ["Jixia"],
    "长城": ["Great Wall"],
    "玄雍": ["Xuanyong"],
    "尧天": ["Yaotian"],
    "云梦泽": ["Yunmeng", "Cloudream"],
    "大河": ["Riverlands", "Great River"],
    "混沌裂隙": ["Chaos Rift"],
    "先知图腾": ["Seer Totem", "Prophet Totem"],
    "因缘图腾": ["Destiny Totem"],
    "往生图腾": ["Afterlife Totem"],
    "虚妄图腾": ["Illusory Totem", "Illusion Totem"],
    "熊灵": ["Bear Spirit", "Spirit Bear"],
    "始祖熊灵": ["Ancestral Bear Spirit", "Ancestor Bear Spirit"],
    "狼魂": ["Wolf Soul"],
    "圣殿骑士": ["Templar Knight"],
    "机关傀儡": ["Mechanical Puppet", "mechanism puppet"],
    "玄雍士兵": ["Xuanyong Soldier"],
    "暗影仆从": ["Shadow Servant"],
    "影侍": ["Shadow Servant"],
    "常小娥": ["Chang Xiao'e"],
    "干将莫邪": ["Gan & Mo"],
    "【逐鹿】英雄牌": ["Kartu Hero [Zhulu]", "Kartu Hero Zhulu", "[Zhulu]"],
    "【河洛】英雄牌": ["Kartu Hero [Central Plain]", "Kartu Hero Central Plain", "[Central Plain]"],
    "【日落海】英雄牌": [
        "Kartu Hero [Sunset Sea]",
        "Kartu Hero [Sunset]",
        "Kartu Hero Sunset",
        "[Sunset Sea]",
        "[Sunset]",
    ],
    "【三分】英雄牌": ["Kartu Hero [Three Kingdoms]", "[Three Kingdoms]"],
    "【稷下】英雄牌": ["Kartu Hero [Jixia]", "[Jixia]"],
    "【长城】英雄牌": ["Kartu Hero [Great Wall]", "[Great Wall]"],
    "【玄雍】英雄牌": ["Kartu Hero [Xuanyong]", "[Xuanyong]"],
    "【尧天】英雄牌": ["Kartu Hero [Yaotian]", "[Yaotian]"],
    "【云梦泽】英雄牌": ["Kartu Hero [Cloudream]", "[Cloudream]"],
}

LEADING_TAGGED_PREFIX_RE = re.compile(
    r"^(\s*(?:<(?:/?[A-Za-z][^>]*|/)>|[\u2540-\u257f]|[^：:\n<])+?(?:</[A-Za-z][^>]*>)+)\s*[：:]\s*"
)

FORMULA_TOKEN_RE = re.compile(
    r"\[[A-Za-z0-9_+/.*%-]+\]|\{[^{}]*\d[^{}]*\}|\d+(?:\.\d+)?"
)

COMPOUND_EXPR_RE = re.compile(
    r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\{[^{}]*\d[^{}]*\}|\d+(?:\.\d+)?%?)"
    r"(?:\s*[+~-]\s*(?:\[[A-Za-z0-9_+/.*%-]+\]|\{[^{}]*\d[^{}]*\}|\d+(?:\.\d+)?%?))*%?"
)

ATOMIC_TAGGED_SPAN_RE = re.compile(
    r"((?:<(?![/])[A-Za-z][^>]*>|[\u2540-\u257f])+)([^<>]+?)((?:</[A-Za-z][^>]*>)+)"
)


def normalize_plain_zh(text: str) -> str:
    """Strip Unity tags, control tokens, and whitespace so text matches Tier 1 descCn."""
    cleaned = TAG_RE.sub("", text)
    cleaned = CONTROL_TOKEN_RE.sub("", cleaned)
    return re.sub(r"\s+", "", cleaned).strip()


def normalize_formula_skeleton_zh(text: str) -> str:
    """Normalize Chinese text by replacing dynamic formula tokens, icon placeholders, and numbers with #N#."""
    p = normalize_plain_zh(text)
    p = re.sub(r"点击技能描述面板.*$", "", p)
    p = re.sub(r"(?:主动|被动|觉醒|天赋|效果|秘技|清平|长恨)[：:]", "", p)
    p = p.replace("（", "(").replace("）", ")").replace("【", "[").replace("】", "]")
    p = (
        p.replace("{Energy}", "能量")
        .replace("{LordExp}", "棋手经验")
        .replace("{LordHp}", "棋手生命值")
    )
    p = re.sub(r"\[\d+\]点?(物理|法术|真实)伤害\(([^)]+)\)", r"\2的\1伤害", p)
    p = re.sub(r"\[\d+\]点?(护盾|生命值?)\(([^)]+)\)", r"\2的\1", p)
    p = re.sub(
        r"[一二两三四五六七八九十]+(?=周|次|秒|格|层|名|个|张|点|回合|件|把|枚|颗|只|条|道)",
        "#N#",
        p,
    )
    skel = FORMULA_TOKEN_RE.sub("#N#", p)
    skel = skel.replace("#N#-#N#", "#N#").replace("#N#点", "#N#")
    while "#N#+#N#" in skel or "#N##N#" in skel:
        skel = skel.replace("#N#+#N#", "#N#").replace("#N##N#", "#N#")
    skel = re.sub(r"最大生命值的?生命值?", "最大生命值", skel)
    skel = (
        skel.replace("释放", "施放")
        .replace("基础物理攻击", "物理攻击")
        .replace("基础法术攻击", "法术攻击")
        .replace("目标敌人", "目标")
        .replace("若期间与目标距离过远", "若期间目标距离过远")
        .replace("普通攻击能对身前敌人造成范围伤害", "普攻能造成范围伤害")
        .replace("普通攻击能造成范围伤害", "普攻能造成范围伤害")
        .replace("普攻能对身前敌人造成范围伤害", "普攻能造成范围伤害")
    )
    skel = re.sub(r"恢复东皇(?:#N#%|#N#)+的最大生命值", "恢复东皇#N#%最大生命值", skel)
    skel = re.sub(r"恢复东皇(?:#N#%|#N#)+生命值", "恢复东皇#N#%最大生命值", skel)
    skel = re.sub(r"^吕布会根据敌人位置使用不同招式普攻能对身前#N#格内敌人造成伤害", "吕布的普攻能造成范围伤害", skel)
    skel = re.sub(r"[，。：:；;、“”\"!\?！？]", "", skel)
    return skel


def reinject_formula_and_skeleton(
    source_zh: str,
    desc_cn: str,
    desc_id: str,
    inner_translator: Callable[[str], str] | None = None,
    baseline_en: str | None = None,
    en_translator: Callable[[str], str] | None = None,
) -> str:
    """Substitute dynamic formula placeholders from source_zh/baseline_en into Tier 1 desc_id, then reinject tags."""
    out = desc_id

    # 1. Protect pipe-delimited numeric + icon placeholders and standalone icons with sentinels
    sentinels_icon: list[tuple[str, str]] = []
    for m in re.finditer(
        r"(\{[0-9A-Za-z_:+|.%/~-]+\})\{(Energy|LordExp|LordHp)\}", source_zh
    ):
        num_ph, icon_name = m.group(1), m.group(2)
        full_ph = f"{num_ph}{{{icon_name}}}"
        tok = f"__WXQICONPH{len(sentinels_icon)}__"
        if icon_name == "Energy":
            subbed, count = re.subn(r"\b\d+\s*(?:Energy|Energi)\b", tok, out, count=1)
            if count > 0:
                out = subbed
                sentinels_icon.append((tok, full_ph))
        elif icon_name == "LordExp":
            subbed, count = re.subn(
                r"\b\d+\s*(?:Player EXP|EXP Chess Player|EXP Pemain|EXP)\b",
                tok,
                out,
                count=1,
            )
            if count > 0:
                out = subbed
                sentinels_icon.append((tok, full_ph))
        elif icon_name == "LordHp":
            subbed, count = re.subn(
                r"\b\d+\s*(?:Player HP|HP Chess Player|HP Pemain|Health)\b",
                tok,
                out,
                count=1,
            )
            if count > 0:
                out = subbed
                sentinels_icon.append((tok, full_ph))

    # Also handle standalone {Energy}, {LordExp}, {LordHp} in source_zh when not preceded by {num_ph}
    standalone_icons = re.findall(
        r"(?<!\})(?:\{(Energy|LordExp|LordHp)\})", source_zh
    )
    for icon_name in standalone_icons:
        tok = f"__WXQICONPH{len(sentinels_icon)}__"
        full_ph = f"{{{icon_name}}}"
        if icon_name == "Energy":
            subbed, count = re.subn(r"\b(?:Energy|Energi)\b", tok, out, count=1)
            if count > 0:
                out = subbed
                sentinels_icon.append((tok, full_ph))
        elif icon_name == "LordExp":
            subbed, count = re.subn(
                r"\b(?:Player EXP|EXP Chess Player|EXP Pemain)\b",
                tok,
                out,
                count=1,
            )
            if count > 0:
                out = subbed
                sentinels_icon.append((tok, full_ph))
        elif icon_name == "LordHp":
            subbed, count = re.subn(
                r"\b(?:Player HP|HP Chess Player|HP Pemain)\b",
                tok,
                out,
                count=1,
            )
            if count > 0:
                out = subbed
                sentinels_icon.append((tok, full_ph))

    # 2. If source_zh uses parenthetical [\d+]点...（[\d+]+[\d+]%...）, graft the exact formula span or align after normalization
    if re.search(r"\[\d+\]", source_zh) and baseline_en:
        en_tagged_dmg = re.findall(
            r"(?:<color=[^>]+>)?\[\d+\][^<]*(?:</color>)?\s*(?:<color=[^>]+>)?\s*\(\[\d+\][^)]*\)(?:</color>)?",
            baseline_en,
        )
        id_dmg_spans = list(
            re.finditer(
                r"(?:(?:\d+(?:\.\d+)?\+)?\d+(?:\.\d+)?%\s*(?:Physical Attack|Magic Attack|Max HP|HP Maksimum|[A-Za-z ]+?)\s+sebagai\s+(?:Physical Damage|Magic Damage|True Damage|Shield|HP)|(?:Physical Damage|Magic Damage|True Damage|Shield|HP)\s+sebesar\s+(?:\d+(?:\.\d+)?\+)?\d+(?:\.\d+)?%\s*(?:Physical Attack|Magic Attack|Max HP|HP Maksimum|[A-Za-z ]+?)|mendapatkan Shield sebesar\s+[^.,\n]+|Memulihkan\s+[^.,\n]+\s+HP)",
                out,
            )
        )
        if en_tagged_dmg and len(en_tagged_dmg) == len(id_dmg_spans):
            for m_span, repl_str in reversed(list(zip(id_dmg_spans, en_tagged_dmg))):
                clean_repl = repl_str.replace("magical attack", "Magic Attack").replace(
                    "Magical Damage", "Magic Damage"
                )
                out = out[: m_span.start()] + clean_repl + out[m_span.end() :]

    # 3. Align compound expressions between desc_cn and source_zh (both share exact Chinese word order)
    zh_num_counter_re = re.compile(
        r"[一二两三四五六七八九十]+(?=周|次|秒|格|层|名|个|张|点|回合|件|把|枚|颗|只|条|道)"
    )
    cn_clean = zh_num_counter_re.sub(
        "1", normalize_plain_zh(desc_cn).replace("（", "(").replace("）", ")")
    )
    src_clean = zh_num_counter_re.sub(
        "1", normalize_plain_zh(source_zh).replace("（", "(").replace("）", ")")
    )
    src_clean = (
        src_clean.replace("{Energy}", "能量")
        .replace("{LordExp}", "棋手经验")
        .replace("{LordHp}", "棋手生命值")
    )
    src_clean = re.sub(r"\[\d+\]点?(物理|法术|真实)伤害\(([^)]+)\)", r"\2的\1伤害", src_clean)
    src_clean = re.sub(r"\[\d+\]点?(护盾|生命值?)\(([^)]+)\)", r"\2的\1", src_clean)

    ph_map = {re.sub(r"\s+", "", ph): ph for ph in PLACEHOLDER_RE.findall(source_zh)}
    cn_exprs = COMPOUND_EXPR_RE.findall(cn_clean)
    src_exprs = COMPOUND_EXPR_RE.findall(src_clean)
    if len(cn_exprs) == len(src_exprs):
        for c_ex, s_ex in zip(cn_exprs, src_exprs):
            if c_ex != s_ex:
                clean_s = re.sub(r"\s+", "", s_ex)
                if clean_s in ph_map:
                    s_ex = ph_map[clean_s]
                out = re.sub(
                    rf"(?<![\d\[{{|A-Za-z]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z])",
                    s_ex,
                    out,
                    count=1,
                )

    needed_phs = Counter(PLACEHOLDER_RE.findall(source_zh))
    curr_phs = Counter(PLACEHOLDER_RE.findall(out))
    if curr_phs != needed_phs:
        missing_phs: list[str] = []
        for ph, count in needed_phs.items():
            diff = count - curr_phs.get(ph, 0)
            if diff > 0:
                missing_phs.extend([ph] * diff)
        for ph in missing_phs:
            m_num = re.search(r"(?<![\d\[{|A-Za-z])\d+(?:\.\d+)?%?(?![\d\]}|A-Za-z])", out)
            if m_num:
                out = out[: m_num.start()] + ph + out[m_num.end() :]

    # 4. Handle trailing UI inspection hint if present in source_zh
    ui_hint_m = re.search(
        r"(\n*(?:<color=[^>]+>)*点击技能描述面板[，,].*?(?:</color>)?)$", source_zh
    )
    if ui_hint_m and not re.search(r"(?:Klik|Ketuk|Tap).*?panel deskripsi", out, flags=re.I):
        hint_raw = ui_hint_m.group(1)
        color_m = re.search(r"<color=([^>]+)>", hint_raw)
        c_val = color_m.group(1) if color_m else "#7288a7"
        out = out.rstrip() + f"\n<color={c_val}>Ketuk panel deskripsi Skill untuk melihat penjelasan detail</color>"

    # Wrap formula and stat spans if source_zh had them inside <color=...>...</color>
    # e.g. <color=#dfa15e>80+[194010p1q2/100]%物理攻击力的物理伤害</color> and <color=#dfa15e>[194011p1q2]点物理防御</color>
    color_spans = re.findall(r"(<color=[^>]+>)([^<]+)(</color>)", source_zh)
    if color_spans:
        for open_tag, zh_content, close_tag in color_spans:
            pattern = None
            if zh_content.endswith(("：", ":")) or any(k in zh_content for k in ("被动", "主动", "清平", "Pasif", "Aktif")):
                label_zh = zh_content.rstrip("：: ")
                label_trans = (
                    "Pasif" if "被动" in label_zh
                    else "Aktif" if "主动" in label_zh
                    else (inner_translator(label_zh) if inner_translator else label_zh)
                )
                pattern = rf"\b(?:Pasif|Aktif|{re.escape(label_trans)})\s*[:：]"
            elif "自身" in zh_content or ("生命" in zh_content and ("法术伤害" in zh_content or "物理伤害" in zh_content)):
                pattern = r"(?:Magic Damage|Physical Damage|Shield|perisai)?\s*(?:sebesar\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)%?\s*(?:base\s+|dasar\s+)?(?:Physical Attack|Magic Attack|Max HP)(?:\s+[A-Za-z]+)?(?:\s+sebagai\s+(?:Magic Damage|Physical Damage|True Damage))?"
            elif "物理伤害" in zh_content or "物理攻击力" in zh_content:
                pattern = r"(?:(?:\d+(?:\.\d+)?\+)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Physical Attack|Magic Attack)?\s*(?:sebagai\s+)?(?:Physical Damage|Damage))"
            elif "物理防御" in zh_content:
                pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Physical Defense"
            elif "法术伤害" in zh_content or "法术攻击力" in zh_content:
                pattern = r"(?:(?:\d+(?:\.\d+)?\+)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Magic Attack)?\s*(?:sebagai\s+)?(?:Magic Damage|Damage))"
            elif "法术防御" in zh_content:
                pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Magic Defense"
            elif "生命" in zh_content or "HP" in zh_content:
                pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*(?:Max HP|HP|Health)(?:\s*(?:diri|sekutu|miliknya))?(?:\s*sebagai\s*(?:Magic Damage|Physical Damage|True Damage))?"
            elif "移动速度" in zh_content:
                pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Movement Speed"
            elif "攻击速度" in zh_content:
                pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Attack Speed"
            elif "法术穿透" in zh_content:
                pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Magic Penetration"
            elif "物理穿透" in zh_content:
                pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Physical Penetration"

            if pattern:
                for m in re.finditer(pattern, out):
                    span_text = m.group(0).strip()
                    if not span_text:
                        continue
                    before = out[: m.start()]
                    if before.rfind("<color=") > before.rfind("</color>"):
                        continue
                    s_idx = m.start() + m.group(0).find(span_text)
                    e_idx = s_idx + len(span_text)
                    out = out[:s_idx] + f"{open_tag}{span_text}{close_tag}" + out[e_idx:]
                    break

    if TAG_RE.findall(out) != TAG_RE.findall(source_zh):
        out = TAG_RE.sub("", out)

    # Restore sentinels
    for tok, full_ph in sentinels_icon:
        out = out.replace(tok, full_ph, 1)

    return reinject_skeleton_from_source(
        source_zh,
        out,
        inner_translator=inner_translator,
        baseline_en=baseline_en,
        en_translator=en_translator,
        allow_en_fallback=False,
    )


def normalize_tag_boundary_spacing(source: str, text: str) -> str:
    """Ensure natural single space between words/numbers and rich-text tags without breaking validation."""
    if not text or "<" not in text:
        return text

    # Space between alphanumeric/%/] and opening tag: Mendapatkan<color=... -> Mendapatkan <color=...
    spaced = re.sub(
        r"([A-Za-z0-9%\]])(<(?![/])(?:color|b|i|a|size)\b[^>]*>)",
        r"\1 \2",
        text,
    )
    # Space between closing tag and alphanumeric: ...</color>dari -> ...</color> dari
    spaced = re.sub(
        r"(</(?:color|b|i|a|size)>)([A-Za-z0-9])",
        r"\1 \2",
        spaced,
    )
    # Collapse any accidental double spaces created
    spaced = re.sub(r"[ ]{2,}", " ", spaced)

    ok, _ = validate_translation(source, spaced)
    return spaced if ok else text


def reinject_skeleton_from_source(
    source_zh: str,
    plain_id: str,
    inner_translator: Callable[[str], str] | None = None,
    baseline_en: str | None = None,
    en_translator: Callable[[str], str] | None = None,
    allow_en_fallback: bool = True,
) -> str:
    """Re-inject exact tags, placeholders, and control tokens from source_zh into plain_id."""
    tags_in_src = TAG_RE.findall(source_zh)
    ctrls_in_src = CONTROL_TOKEN_RE.findall(source_zh)
    phs_in_src = PLACEHOLDER_RE.findall(source_zh)

    result = plain_id

    # 1. If baseline_en has valid matching tags & a short leading tagged keyword prefix
    if baseline_en and TAG_RE.findall(baseline_en) == tags_in_src and tags_in_src:
        m_en = LEADING_TAGGED_PREFIX_RE.match(baseline_en)
        m_id = re.match(r"^([^:\n]{1,40}):\s*(.+)$", result, re.S)
        if (
            m_en
            and m_id
            and TAG_RE.findall(m_en.group(1)) == tags_in_src
            and len(TAG_RE.sub("", m_en.group(1)).strip().split()) <= 2
        ):
            cand = sanitize_target_text(source_zh, f"{m_en.group(1)}: {m_id.group(2)}")
            if validate_translation(source_zh, cand)[0]:
                return cand

    # 2. Match all atomic tagged spans in source_zh and wrap corresponding terms in result
    spans = list(ATOMIC_TAGGED_SPAN_RE.finditer(source_zh))
    if spans and "<" not in result:
        en_spans = (
            list(ATOMIC_TAGGED_SPAN_RE.finditer(baseline_en))
            if baseline_en and len(TAG_RE.findall(baseline_en)) == len(tags_in_src)
            else []
        )
        curr = result
        cursor = 0
        all_matched = True
        for idx, m_span in enumerate(spans):
            open_part = m_span.group(1)
            zh_inner = m_span.group(2).strip()
            close_part = m_span.group(3)

            aliases: list[str] = []
            has_brackets = (zh_inner.startswith("[") and zh_inner.endswith("]")) or (
                zh_inner.startswith("【") and zh_inner.endswith("】")
            )
            bracket_clean = zh_inner.strip("[]【】")

            # Priority 1: Exact bracketed term check FIRST
            if zh_inner in BRACKET_TERM_MAP:
                aliases.append(BRACKET_TERM_MAP[zh_inner])
            if bracket_clean in BRACKET_TERM_MAP:
                term = BRACKET_TERM_MAP[bracket_clean]
                if has_brackets:
                    aliases.append(f"[{term}]")
                    aliases.append(f"【{term}】")
                aliases.append(term)
            if zh_inner in BADGE_ALIAS_MAP:
                aliases.extend(BADGE_ALIAS_MAP[zh_inner])
            if bracket_clean in BADGE_ALIAS_MAP:
                for b_alias in BADGE_ALIAS_MAP[bracket_clean]:
                    if has_brackets:
                        aliases.append(f"[{b_alias}]")
                        aliases.append(f"【{b_alias}】")
                    aliases.append(b_alias)
            if idx < len(en_spans):
                en_inner = en_spans[idx].group(2).strip()
                if en_inner and en_inner not in aliases:
                    if has_brackets and not (
                        en_inner.startswith("[") and en_inner.endswith("]")
                    ):
                        aliases.append(f"[{en_inner}]")
                    aliases.extend([f"{en_inner}:", f"{en_inner}.", en_inner])
            if inner_translator:
                t_inner = inner_translator(zh_inner)
                if t_inner and t_inner not in aliases:
                    if has_brackets and not (
                        t_inner.startswith("[") and t_inner.endswith("]")
                    ):
                        aliases.append(f"[{t_inner}]")
                    aliases.extend([f"{t_inner}:", f"{t_inner}.", t_inner])
            if zh_inner not in aliases:
                aliases.append(zh_inner)

            matched_this = False
            for alias in aliases:
                f_idx = curr.find(alias, cursor)
                if f_idx != -1:
                    if alias.endswith((".", ":", "\n")):
                        kw = alias[:-1]
                        punct = alias[-1]
                        tagged = f"{open_part}{kw}{close_part}{punct}"
                    else:
                        tagged = f"{open_part}{alias}{close_part}"
                    curr = curr[:f_idx] + tagged + curr[f_idx + len(alias) :]
                    cursor = f_idx + len(tagged)
                    matched_this = True
                    break
            if not matched_this:
                # Check formula / stat pattern for color spans
                pattern = None
                if zh_inner.endswith(("：", ":")) or any(k in zh_inner for k in ("被动", "主动", "清平", "Pasif", "Aktif")):
                    label_zh = zh_inner.rstrip("：: ")
                    label_trans = (
                        "Pasif" if "被动" in label_zh
                        else "Aktif" if "主动" in label_zh
                        else (inner_translator(label_zh) if inner_translator else label_zh)
                    )
                    pattern = rf"\b(?:Pasif|Aktif|{re.escape(label_trans)})\s*[:：]"
                elif "自身" in zh_inner or ("生命" in zh_inner and ("法术伤害" in zh_inner or "物理伤害" in zh_inner)):
                    pattern = r"(?:Magic Damage|Physical Damage|Shield|perisai)?\s*(?:sebesar\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)%?\s*(?:base\s+|dasar\s+)?(?:Physical Attack|Magic Attack|Max HP)(?:\s+[A-Za-z]+)?(?:\s+sebagai\s+(?:Magic Damage|Physical Damage|True Damage))?"
                elif "物理伤害" in zh_inner or "物理攻击力" in zh_inner:
                    pattern = r"(?:(?:\d+(?:\.\d+)?\+)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Physical Attack|Magic Attack)?\s*(?:sebagai\s+)?(?:Physical Damage|Damage))"
                elif "物理防御" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Physical Defense"
                elif "法术伤害" in zh_inner or "法术攻击力" in zh_inner:
                    pattern = r"(?:(?:\d+(?:\.\d+)?\+)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Magic Attack)?\s*(?:sebagai\s+)?(?:Magic Damage|Damage))"
                elif "法术防御" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Magic Defense"
                elif "生命" in zh_inner or "HP" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*(?:Max HP|HP|Health)(?:\s*(?:diri|sekutu|miliknya))?(?:\s*sebagai\s*(?:Magic Damage|Physical Damage|True Damage))?"
                elif "移动速度" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Movement Speed"
                elif "攻击速度" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Attack Speed"
                elif "法术穿透" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Magic Penetration"
                elif "物理穿透" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Physical Penetration"

                if pattern:
                    for m in re.finditer(pattern, curr):
                        span_text = m.group(0).strip()
                        if not span_text or m.start() < cursor:
                            continue
                        before = curr[: m.start()]
                        if before.rfind("<color=") > before.rfind("</color>"):
                            continue
                        s_idx = m.start() + m.group(0).find(span_text)
                        e_idx = s_idx + len(span_text)
                        tagged = f"{open_part}{span_text}{close_part}"
                        curr = curr[:s_idx] + tagged + curr[e_idx:]
                        cursor = s_idx + len(tagged)
                        matched_this = True
                        break

            if not matched_this:
                all_matched = False

        if not all_matched and len(spans) == 1 and "<" not in curr and curr.strip():
            span_zh = spans[0].group(2)
            if len(normalize_plain_zh(span_zh)) >= 0.75 * len(normalize_plain_zh(source_zh)):
                curr = f"{spans[0].group(1)}{curr}{spans[0].group(3)}"
                all_matched = True
            else:
                zh_clauses = [c for c in re.split(r"[，。！？；\n]+", source_zh) if c.strip()]
                target_idx = next((i for i, c in enumerate(zh_clauses) if span_zh in c), -1)
                id_clauses = re.split(r"([,.;!?\n]+)", curr)
                content_clause_indices = [
                    i for i in range(0, len(id_clauses), 2) if id_clauses[i].strip()
                ]
                if target_idx != -1 and content_clause_indices:
                    mapped_idx = int(
                        round(
                            target_idx
                            / max(1, len(zh_clauses) - 1)
                            * (len(content_clause_indices) - 1)
                        )
                    )
                    actual_idx = content_clause_indices[
                        min(mapped_idx, len(content_clause_indices) - 1)
                    ]
                    id_clauses[actual_idx] = (
                        f"{spans[0].group(1)}{id_clauses[actual_idx].strip()}{spans[0].group(3)}"
                    )
                    curr = "".join(id_clauses)
                    all_matched = True
        elif not all_matched and len(spans) > 1:
            unmatched_spans = [s for s in spans if s.group(0) not in curr]
            if len(unmatched_spans) == 1:
                u_span = unmatched_spans[0]
                u_zh = u_span.group(2)
                zh_clauses = [c for c in re.split(r"[，。！？；\n]+", source_zh) if c.strip()]
                target_idx = next((i for i, c in enumerate(zh_clauses) if u_zh in c), len(zh_clauses) - 1)
                id_clauses = re.split(r"([,.;!?\n]+)", curr)
                untagged_indices = [
                    i
                    for i in range(0, len(id_clauses), 2)
                    if id_clauses[i].strip() and "<" not in id_clauses[i]
                ]
                if untagged_indices:
                    mapped_idx = int(
                        round(
                            target_idx
                            / max(1, len(zh_clauses) - 1)
                            * (len(untagged_indices) - 1)
                        )
                    )
                    actual_idx = untagged_indices[
                        min(mapped_idx, len(untagged_indices) - 1)
                    ]
                    id_clauses[actual_idx] = (
                        f"{u_span.group(1)}{id_clauses[actual_idx].strip()}{u_span.group(3)}"
                    )
                    curr = "".join(id_clauses)
                    all_matched = True

        if all_matched:
            result = curr

    # 3. Restore untagged control tokens (e.g. ═ before Temporary Level or ╫ between stats)
    # NEVER replace spaces or commas with control tokens!
    if ctrls_in_src and Counter(CONTROL_TOKEN_RE.findall(result)) != Counter(ctrls_in_src):
        src_ctrl_counts = Counter(ctrls_in_src)
        cur_ctrl_counts = Counter(CONTROL_TOKEN_RE.findall(result))
        for ch, target_cnt in src_ctrl_counts.items():
            needed = target_cnt - cur_ctrl_counts[ch]
            if needed > 0:
                if ch == "═":
                    for kw in ("Temporary Level", "Level Sementara"):
                        while needed > 0 and kw in result and f"═{kw}" not in result:
                            subbed, cnt = re.subn(
                                rf"(?<![═>])\b{re.escape(kw)}\b",
                                f"═{kw}",
                                result,
                                count=1,
                            )
                            if cnt:
                                result = subbed
                                needed -= 1
                            else:
                                break
                elif ch == "╫":
                    sep_maps = (
                        (", +", "╫+"),
                        (", -", "╫-"),
                        (" / ", "╫"),
                        (", ", "╫"),
                        (" dan ", "╫"),
                    )
                    for src_sep, dst_sep in sep_maps:
                        while needed > 0 and src_sep in result:
                            result = result.replace(src_sep, dst_sep, 1)
                            needed -= 1
                if needed > 0 and (ch not in result or result.count(ch) < target_cnt):
                    result = (ch * needed) + result

    # 4. Check if candidate already passes all rules
    cand = sanitize_target_text(source_zh, result)
    if (
        TAG_RE.findall(cand) == tags_in_src
        and Counter(PLACEHOLDER_RE.findall(cand)) == Counter(phs_in_src)
        and Counter(CONTROL_TOKEN_RE.findall(cand)) == Counter(ctrls_in_src)
        and not CJK_RE.search(PLACEHOLDER_RE.sub("", TAG_RE.sub("", cand)))
    ):
        ok, _ = validate_translation(source_zh, cand)
        if ok:
            return normalize_tag_boundary_spacing(source_zh, cand)

    # 5. Deterministic fallback: NEVER emit empty tags
    if baseline_en and allow_en_fallback:
        b_tags = TAG_RE.findall(baseline_en)
        if b_tags == tags_in_src or len(b_tags) == len(tags_in_src):
            repaired_en = baseline_en
            repaired_en = re.sub(
                r"(<color=[^>]+>)\s*(</color>)\s*([A-Za-z0-9+%-]+)",
                r"\1\3\2",
                repaired_en,
            )
            repaired_en = re.sub(
                r"([A-Za-z0-9+%-]+)\s*(<color=[^>]+>)\s*(</color>)",
                r"\2\1\3",
                repaired_en,
            )
            if len(TAG_RE.findall(repaired_en)) == len(tags_in_src):
                parts = TAG_RE.split(repaired_en)
                rebuilt_en: list[str] = []
                for p_i, p_text in enumerate(parts):
                    rebuilt_en.append(p_text)
                    if p_i < len(tags_in_src):
                        rebuilt_en.append(tags_in_src[p_i])
                repaired_en = "".join(rebuilt_en)

            from acepatchindo.lexicon_id import translate_segment_en_to_id
            cand_en = translate_preserving_skeleton(
                repaired_en,
                en_translator or translate_segment_en_to_id,
            )
            cand_en = sanitize_target_text(source_zh, cand_en)
            cand_en = normalize_tag_boundary_spacing(source_zh, cand_en)
            ok, _ = validate_translation(source_zh, cand_en)
            if ok:
                return cand_en

    stripped_result = CONTROL_TOKEN_RE.sub("", TAG_RE.sub("", result)).strip()
    wrapped = _wrap_exact_tag_sequence(source_zh, stripped_result, inner_translator)
    final_cand = sanitize_target_text(source_zh, wrapped)
    return normalize_tag_boundary_spacing(source_zh, final_cand)


def _wrap_exact_tag_sequence(
    source_zh: str,
    stripped_id: str,
    inner_translator: Callable[[str], str] | None = None,
) -> str:
    """Guarantee TAG_RE, PLACEHOLDER_RE, and CONTROL_TOKEN_RE match source_zh while NEVER emitting empty tags."""
    tokens = TAG_RE.split(source_zh)
    tags = TAG_RE.findall(source_zh)

    vis_indices = [
        idx for idx, t in enumerate(tokens)
        if CONTROL_TOKEN_RE.sub("", t).strip()
    ]
    if not vis_indices:
        vis_indices = [0]

    words = stripped_id.split()
    if not words:
        words = ["."]

    k = len(vis_indices)
    chunks: list[str] = []
    if k == 1:
        chunks = [" ".join(words)]
    else:
        n = len(words)
        chunk_size = max(1, n // k)
        for i in range(k):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < k - 1 else n
            if start < n:
                chunks.append(" ".join(words[start:end]) if start < end else words[-1])
            else:
                chunks.append(words[-1])

    out_parts: list[str] = []
    chunk_map = {idx: chunks[c_i] for c_i, idx in enumerate(vis_indices)}

    for idx, tok in enumerate(tokens):
        tok_ctrls = "".join(CONTROL_TOKEN_RE.findall(tok))
        if idx in chunk_map:
            content = f"{tok_ctrls}{chunk_map[idx]}"
            if out_parts and out_parts[-1].endswith(">") and content and content[0].isalnum():
                out_parts.append(" ")
            out_parts.append(content)
        else:
            out_parts.append(tok_ctrls)

        if idx < len(tags):
            cur_tag = tags[idx]
            if out_parts and out_parts[-1] and out_parts[-1][-1].isalnum() and not cur_tag.startswith("</"):
                out_parts.append(" ")
            out_parts.append(cur_tag)

    rebuilt = "".join(out_parts)
    rebuilt = normalize_tag_boundary_spacing(source_zh, rebuilt)

    # Reconcile placeholders exactly
    src_ph = Counter(PLACEHOLDER_RE.findall(source_zh))
    cur_ph = Counter(PLACEHOLDER_RE.findall(rebuilt))
    if cur_ph != src_ph:
        for ph, cnt in list(cur_ph.items()):
            while cnt > src_ph[ph]:
                rebuilt = rebuilt.replace(ph, "", 1)
                cnt -= 1
        cur_ph = Counter(PLACEHOLDER_RE.findall(rebuilt))
        for ph, cnt in src_ph.items():
            if cur_ph[ph] < cnt:
                rebuilt += ph * (cnt - cur_ph[ph])

    # Reconcile control tokens exactly
    src_ctrl = Counter(CONTROL_TOKEN_RE.findall(source_zh))
    cur_ctrl = Counter(CONTROL_TOKEN_RE.findall(rebuilt))
    if cur_ctrl != src_ctrl:
        for ch, cnt in list(cur_ctrl.items()):
            while cnt > src_ctrl[ch]:
                rebuilt = rebuilt.replace(ch, "", 1)
                cnt -= 1
        cur_ctrl = Counter(CONTROL_TOKEN_RE.findall(rebuilt))
        for ch, cnt in src_ctrl.items():
            if cur_ctrl[ch] < cnt:
                rebuilt += ch * (cnt - cur_ctrl[ch])

    return rebuilt


def translate_preserving_skeleton(
    source: str,
    segment_translator: Callable[[str], str],
) -> str:
    """Translate text segments while keeping every tag, placeholder, control token, and ';' intact."""
    if ";" in source:
        parts = source.split(";")
        translated_parts = [
            _translate_single_skeleton(p, segment_translator) for p in parts
        ]
        candidate = ";".join(translated_parts)
        cand = sanitize_target_text(source, candidate)
        return normalize_tag_boundary_spacing(source, cand)
    cand = sanitize_target_text(
        source, _translate_single_skeleton(source, segment_translator)
    )
    return normalize_tag_boundary_spacing(source, cand)


def _translate_single_skeleton(
    source: str,
    segment_translator: Callable[[str], str],
) -> str:
    tags = TAG_RE.findall(source)
    segments = TAG_RE.split(source)
    out: list[str] = []
    for idx, seg in enumerate(segments):
        if seg:
            ctrls = CONTROL_TOKEN_RE.findall(seg)
            if ctrls:
                sub_segs = CONTROL_TOKEN_RE.split(seg)
                rejoined: list[str] = []
                for c_idx, s in enumerate(sub_segs):
                    rejoined.append(_translate_preserving_placeholders(s, segment_translator))
                    if c_idx < len(ctrls):
                        rejoined.append(ctrls[c_idx])
                out.append("".join(rejoined))
            else:
                out.append(_translate_preserving_placeholders(seg, segment_translator))
        if idx < len(tags):
            out.append(tags[idx])
    return "".join(out)


def _translate_preserving_placeholders(
    seg: str,
    segment_translator: Callable[[str], str],
) -> str:
    if not seg or not seg.strip():
        return seg
    stripped = seg.strip()
    if stripped in BRACKET_TERM_MAP:
        return seg.replace(stripped, BRACKET_TERM_MAP[stripped], 1)

    # Protect placeholders with temporary ASCII sentinels that regex translators won't touch
    phs = PLACEHOLDER_RE.findall(seg)
    if not phs:
        return segment_translator(seg)

    protected = seg
    sentinels: list[tuple[str, str]] = []
    for i, ph in enumerate(phs):
        tok = f"__WXQPH{i}__"
        protected = protected.replace(ph, tok, 1)
        sentinels.append((tok, ph))

    translated = segment_translator(protected)
    for tok, ph in sentinels:
        translated = translated.replace(tok, ph, 1)
    return translated

