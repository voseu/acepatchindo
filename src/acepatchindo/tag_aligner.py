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
    "复生": ["Revive:", "Revive", "di-revive", "revived", "revive", "Bangkit", "di-Revive"],
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
    "因缘图腾": ["Bond Totem", "Destiny Totem", "Totem Ikatan"],
    "先知图腾": ["Prophet Totem", "Totem Nabi"],
    "转生图腾": ["Rebirth Totem", "Totem Kelahiran Kembali"],
    "夺取": ["Steal"],
    "凯旋": ["Triumph"],
    "开局": ["Game Start", "Start"],
    "唯一": ["Unique", "Unik"],
    "主动": ["Aktif:", "Aktif", "Active"],
    "被动": ["Pasif:", "Pasif", "Passive"],
    "清平": ["Qingping", "Serenity"],
    "破阵": ["Pozhen", "Discord", "Conquest"],
    "长恨": ["Changhen", "Sorrow"],
    "压制": ["mensuppress", "suppress", "Suppress", "Supresi", "men-suppress"],
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
    "先知图腾": ["Seer Totem", "Prophet Totem", "Totem Nabi"],
    "因缘图腾": ["Bond Totem", "Destiny Totem", "Totem Ikatan", "Totem Takdir"],
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
        r"[一二两三四五六七八九十]+(?=周|次|秒|格|层|名|个|张|点|回合|件|把|枚|颗|只|条|道|束|片|朵|发|支|波)",
        "#N#",
        p,
    )
    skel = FORMULA_TOKEN_RE.sub("#N#", p)
    skel = skel.replace("#N#-#N#", "#N#").replace("#N#点", "#N#")
    while "#N#+#N#" in skel or "#N##N#" in skel:
        skel = skel.replace("#N#+#N#", "#N#").replace("#N##N#", "#N#")
    skel = re.sub(r"最大生命值?的?生命值?", "最大生命值", skel)
    skel = (
        skel.replace("释放", "施放")
        .replace("基础物理攻击", "物理攻击")
        .replace("基础法术攻击", "法术攻击")
        .replace("的物理攻击力", "物理攻击力")
        .replace("的基础攻击力", "物理攻击力")
        .replace("基础攻击力", "物理攻击力")
        .replace("目标敌人", "目标")
        .replace("霸体", "免控")
        .replace("项羽最大生命值", "最大生命值")
        .replace("机关魔手", "机关魔爪")
        .replace("铠召唤魔铠", "铠使用魔铠")
        .replace("附近", "周围")
        .replace("若期间与目标距离过远", "若期间目标距离过远")
        .replace("普通攻击能对身前敌人造成范围伤害", "普攻能造成范围伤害")
        .replace("普通攻击能造成范围伤害", "普攻能造成范围伤害")
        .replace("普攻能对身前敌人造成范围伤害", "普攻能造成范围伤害")
    )
    skel = re.sub(r"恢复东皇(?:#N#%|#N#)+的最大生命值", "恢复东皇#N#%最大生命值", skel)
    skel = re.sub(r"恢复东皇(?:#N#%|#N#)+生命值", "恢复东皇#N#%最大生命值", skel)
    skel = re.sub(r"(?<!李元芳)丢出飞镖", "李元芳丢出飞镖", skel)
    skel = re.sub(
        r"^吕布会根据敌人位置使用不同招式(?:普攻|普通攻击)能对身前#N#格内敌人造成伤害",
        "吕布的普通攻击能对身前敌人造成范围伤害",
        skel,
    )
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

    # Step 0: Trailing UI hint separation before body alignment
    m_footer = re.search(
        r"(\n*)((?:<color=[^>]+>)*点击技能描述面板[，,]查看(.+?)详细解释(?:</color>)*)\s*$",
        source_zh,
    )
    footer_id = ""
    body_source_zh = source_zh
    if m_footer:
        body_source_zh = source_zh[: m_footer.start()]
        leading_nl = m_footer.group(1) or "\n\n"
        full_footer_zh = m_footer.group(2)
        term_zh = m_footer.group(3)
        TERM_MAP = {
            "击飞": "Knock-Up",
            "眩晕": "Stun",
            "沉默": "Silence",
            "减速": "Slow",
            "免控": "Control Immunity",
            "霸体": "Control Immunity",
            "禁锢": "Immobilize",
            "定身": "Root",
        }
        term_id = term_zh
        for zh_t, id_t in TERM_MAP.items():
            term_id = term_id.replace(zh_t, id_t)
        term_id = term_id.replace("，", ", ")
        color_m = re.search(r"<color=([^>]+)>", full_footer_zh)
        c_val = color_m.group(1) if color_m else "#86888A"
        has_b = "<b>" in term_zh

        # Strip any existing footer from out
        out = re.sub(
            r"(\n*)?(?:<color=[^>]+>)?(?:Klik|Ketuk|Tap).*?panel deskripsi.*?(?:</color>)?\s*$",
            "",
            out,
            flags=re.I,
        ).rstrip()

        if has_b:
            footer_id = f"{leading_nl}<color={c_val}>Ketuk panel deskripsi Skill untuk melihat penjelasan detail {term_id}</color>"
        else:
            footer_id = f"{leading_nl}<color={c_val}>Ketuk panel deskripsi Skill untuk melihat penjelasan detail <b>{term_id}</b></color>"

    # Step 1: Parenthetical formula grafting and 3-part split recovery spans
    if re.search(r"\[\d+\]", body_source_zh) and baseline_en:
        en_tagged_dmg = re.findall(
            r"(?:<color=[^>]+>)?\[\d+\][^<]*(?:</color>)?\s*(?:<color=[^>]+>)?\s*\(\[\d+\][^)]*\)(?:</color>)?",
            baseline_en,
        )
        id_dmg_spans = list(
            re.finditer(
                r"(?:memberikan\s+|menyebabkan\s+|memulihkan\s+|mendapatkan\s+)?(?:\d+(?:\.\d+)?%?|[A-Za-z ]+?Damage|Shield|HP|Max HP)\s+sebesar\s+\d+(?:\.\d+)?%?(?:\s*\+\s*\d+(?:\.\d+)?%?)?\s*(?:Physical Attack|Magic Attack|Max HP|HP Maks|HP Maksimum|Attack|HP)(?:\s+miliknya|\s+[A-Za-z']+)?(?:\s+sebagai\s+(?:Physical|Magic|True)\s+Damage|\s+HP)?",
                out,
                flags=re.IGNORECASE,
            )
        )
        if en_tagged_dmg and len(en_tagged_dmg) == len(id_dmg_spans):
            for m_span, repl_str in reversed(list(zip(id_dmg_spans, en_tagged_dmg))):
                clean_repl = repl_str.replace("magical attack", "Magic Attack").replace(
                    "Magical Damage", "Magic Damage"
                )
                out = out[: m_span.start()] + clean_repl + out[m_span.end() :]

    # Handle 2-tag/3-tag split recovery in body_source_zh (e.g. <color=#d487e4>...</color><color=#9ff5d0>的生命值</color>)
    m_split_rec = re.search(
        r"(<color=([^>]+)>)(?:恢复)?([^<]+)(</color>)\s*(<color=([^>]+)>)的?生命值?(</color>)",
        body_source_zh,
    )
    if m_split_rec:
        rec_col = m_split_rec.group(2)
        hp_col = m_split_rec.group(6)
        m_id_rec = re.search(
            r"\b(memulihkan\s+)(.+?)\s+(Max HP|HP|Health)\b",
            out,
            flags=re.I,
        )
        if m_id_rec and "<color=" not in m_id_rec.group(0):
            p1, form_text, hp_word = m_id_rec.group(1), m_id_rec.group(2), m_id_rec.group(3)
            repl_rec = f"{p1}<color={rec_col}>{form_text}</color> <color={hp_col}>{hp_word}</color>"
            out = out[: m_id_rec.start()] + repl_rec + out[m_id_rec.end() :]

    # Step 2: COMPOUND_EXPR_RE 1-to-1 numeric/formula substitution BEFORE icon placeholders!
    zh_num_counter_re = re.compile(
        r"[一二两三四五六七八九十]+(?=周|次|秒|格|层|名|个|张|点|回合|件|把|枚|颗|只|条|道|束|片|朵|发|支|波)"
    )
    cn_clean = zh_num_counter_re.sub(
        "1", normalize_plain_zh(desc_cn).replace("（", "(").replace("）", ")")
    )
    src_clean = zh_num_counter_re.sub(
        "1", normalize_plain_zh(body_source_zh).replace("（", "(").replace("）", ")")
    )
    # Strip icon placeholders from src_clean so only numeric/formula expressions are compared
    src_clean = (
        src_clean.replace("{Energy}", "")
        .replace("{LordExp}", "")
        .replace("{LordHp}", "")
    )
    cn_clean = (
        cn_clean.replace("能量", "")
        .replace("棋手经验", "")
        .replace("棋手生命值", "")
    )
    src_clean = re.sub(r"\[\d+\]点?(物理|法术|真实)伤害\(([^)]+)\)", r"\2的\1伤害", src_clean)
    src_clean = re.sub(r"\[\d+\]点?(护盾|生命值?)\(([^)]+)\)", r"\2的\1", src_clean)

    ph_map = {
        re.sub(r"\s+", "", ph): ph
        for ph in PLACEHOLDER_RE.findall(body_source_zh)
        if not re.match(r"^\{(Energy|LordExp|LordHp)\}$", ph)
    }
    cn_exprs = COMPOUND_EXPR_RE.findall(cn_clean)
    src_exprs = COMPOUND_EXPR_RE.findall(src_clean)
    if len(cn_exprs) == len(src_exprs):
        slots: list[tuple[str, str]] = []
        for i, (c_ex, s_ex) in enumerate(zip(cn_exprs, src_exprs)):
            if c_ex != s_ex:
                clean_s = re.sub(r"\s+", "", s_ex)
                if clean_s in ph_map:
                    s_ex = ph_map[clean_s]
                slot_tok = f"__EXPR_SLOT_{i}__"
                subbed, cnt = re.subn(
                    rf"(?<![\d\[{{|A-Za-z]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z])",
                    slot_tok,
                    out,
                    count=1,
                )
                if cnt:
                    out = subbed
                    slots.append((slot_tok, s_ex))
        for slot_tok, s_ex in slots:
            out = out.replace(slot_tok, s_ex)

    # Any remaining unmatched numeric/formula placeholders from body_source_zh
    needed_numeric_phs = Counter(
        ph for ph in PLACEHOLDER_RE.findall(body_source_zh)
        if not re.match(r"^\{(Energy|LordExp|LordHp)\}$", ph)
    )
    curr_numeric_phs = Counter(
        ph for ph in PLACEHOLDER_RE.findall(out)
        if not re.match(r"^\{(Energy|LordExp|LordHp)\}$", ph)
    )
    if curr_numeric_phs != needed_numeric_phs:
        missing_phs: list[str] = []
        for ph, count in needed_numeric_phs.items():
            diff = count - curr_numeric_phs.get(ph, 0)
            if diff > 0:
                missing_phs.extend([ph] * diff)
        for ph in missing_phs:
            m_num = re.search(r"(?<![\d\[{|A-Za-z])\d+(?:\.\d+)?%?(?![\d\]}|A-Za-z])", out)
            if m_num:
                out = out[: m_num.start()] + ph + out[m_num.end() :]

    # Step 3: Attach {Energy}, {LordExp}, {LordHp} icon placeholders AFTER Step 2!
    for m in re.finditer(
        r"(\{[0-9A-Za-z_:+|.%/~-]+\})\{(Energy|LordExp|LordHp)\}", body_source_zh
    ):
        num_ph, icon_name = m.group(1), m.group(2)
        full_ph = f"{num_ph}{{{icon_name}}}"
        icon_kw_pattern = (
            r"(?:Energy|Energi)\b" if icon_name == "Energy"
            else r"(?:Player EXP|EXP Chess Player|EXP Kontestan|EXP Pemain|EXP)\b" if icon_name == "LordExp"
            else r"(?:Player HP|HP Chess Player|HP Kontestan|HP Pemain|Health)\b"
        )
        subbed, cnt = re.subn(
            rf"{re.escape(num_ph)}\s*{icon_kw_pattern}",
            full_ph,
            out,
            count=1,
        )
        if cnt:
            out = subbed

    all_needed_phs = Counter(PLACEHOLDER_RE.findall(body_source_zh))
    all_curr_phs = Counter(PLACEHOLDER_RE.findall(out))
    for icon_name in ("Energy", "LordExp", "LordHp"):
        needed_cnt = all_needed_phs.get(f"{{{icon_name}}}", 0)
        curr_cnt = all_curr_phs.get(f"{{{icon_name}}}", 0)
        diff = needed_cnt - curr_cnt
        if diff > 0:
            icon_kw_pattern = (
                r"(?<!\{)\b(?:Energy|Energi)\b(?!\})" if icon_name == "Energy"
                else r"(?<!\{)\b(?:Player EXP|EXP Chess Player|EXP Kontestan|EXP Pemain)\b(?!\})" if icon_name == "LordExp"
                else r"(?<!\{)\b(?:Player HP|HP Chess Player|HP Kontestan|HP Pemain)\b(?!\})"
            )
            while diff > 0:
                subbed, cnt = re.subn(icon_kw_pattern, f"{{{icon_name}}}", out, count=1)
                if cnt:
                    out = subbed
                    diff -= 1
                else:
                    break

    res_body = reinject_skeleton_from_source(
        body_source_zh,
        out,
        inner_translator=inner_translator,
        baseline_en=baseline_en,
        en_translator=en_translator,
        allow_en_fallback=False,
    )
    if footer_id:
        res_body = res_body.rstrip() + footer_id
    return res_body


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

    # 0. Multiline line-by-line alignment if both have newlines
    if "\n" in source_zh and "\n" in result and source_zh.count("\n") == result.count("\n"):
        src_lines = source_zh.split("\n")
        res_lines = result.split("\n")
        aligned_lines: list[str] = []
        for s_l, r_l in zip(src_lines, res_lines):
            if not s_l.strip() and not r_l.strip():
                aligned_lines.append("")
                continue
            l_aligned = reinject_skeleton_from_source(
                s_l,
                r_l,
                inner_translator=inner_translator,
                baseline_en=None,
                en_translator=en_translator,
                allow_en_fallback=False,
            )
            aligned_lines.append(l_aligned)
        cand_multiline = "\n".join(aligned_lines)
        if (
            TAG_RE.findall(cand_multiline) == tags_in_src
            and Counter(PLACEHOLDER_RE.findall(cand_multiline)) == Counter(phs_in_src)
            and Counter(CONTROL_TOKEN_RE.findall(cand_multiline)) == Counter(ctrls_in_src)
        ):
            ok, _ = validate_translation(source_zh, cand_multiline)
            if ok:
                return normalize_tag_boundary_spacing(source_zh, cand_multiline)

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
    if spans and TAG_RE.findall(result) != tags_in_src:
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

            # Check if this exact tag is already present in curr
            if f"{open_part}" in curr and f"{close_part}" in curr:
                # Could already be wrapped
                pass

            aliases: list[str] = []
            has_brackets = (zh_inner.startswith("[") and zh_inner.endswith("]")) or (
                zh_inner.startswith("【") and zh_inner.endswith("】")
            )
            bracket_clean = zh_inner.strip("[]【】")
            colon_clean = bracket_clean.rstrip("：: ")

            # Priority 1: Exact bracketed term check FIRST
            if zh_inner in BRACKET_TERM_MAP:
                aliases.append(BRACKET_TERM_MAP[zh_inner])
            if bracket_clean in BRACKET_TERM_MAP:
                term = BRACKET_TERM_MAP[bracket_clean]
                if has_brackets:
                    aliases.append(f"[{term}]")
                    aliases.append(f"【{term}】")
                aliases.append(term)
            if colon_clean in BRACKET_TERM_MAP:
                term = BRACKET_TERM_MAP[colon_clean]
                aliases.extend([f"{term}:", f"{term}.", term])
            if zh_inner in BADGE_ALIAS_MAP:
                aliases.extend(BADGE_ALIAS_MAP[zh_inner])
            if bracket_clean in BADGE_ALIAS_MAP:
                for b_alias in BADGE_ALIAS_MAP[bracket_clean]:
                    if has_brackets:
                        aliases.append(f"[{b_alias}]")
                        aliases.append(f"【{b_alias}】")
                    aliases.append(b_alias)
            if colon_clean in BADGE_ALIAS_MAP:
                for b_alias in BADGE_ALIAS_MAP[colon_clean]:
                    aliases.extend([f"{b_alias}:", f"{b_alias}.", b_alias])
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
                if f_idx == -1 and alias.strip():
                    m_ci = re.search(rf"\b{re.escape(alias.strip())}\b", curr[cursor:], flags=re.I)
                    if m_ci:
                        cand_idx = cursor + m_ci.start()
                        before = curr[:cand_idx]
                        if before.rfind("<") <= before.rfind(">"):
                            f_idx = cand_idx
                            alias = m_ci.group(0)
                if f_idx != -1:
                    # Ensure not already inside a tag
                    before = curr[:f_idx]
                    if before.rfind("<") > before.rfind(">"):
                        continue
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
                phs_in_inner = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]", zh_inner)
                if phs_in_inner:
                    ph_anchor = re.escape(phs_in_inner[-1])
                    pattern = rf"(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?{ph_anchor}(?:%|\s*persen)?\s*(?:Physical Attack|Magic Attack|Max HP|HP|Physical Defense|Magic Defense|Physical Lifesteal|Magic Lifesteal|Attack Speed|Movement Speed)?(?:\s+sebagai\s+(?:Physical|Magic|True)\s+Damage)?"
                elif zh_inner.endswith(("：", ":")) or any(k in zh_inner for k in ("被动", "主动", "清平", "长恨", "Pasif", "Aktif")):
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
                    pattern = r"(?:(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Physical Attack|Magic Attack)?\s*(?:sebagai\s+)?(?:Physical Damage|Damage))"
                elif "物理防御" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Physical Defense"
                elif "法术伤害" in zh_inner or "法术攻击力" in zh_inner:
                    pattern = r"(?:(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Magic Attack)?\s*(?:sebagai\s+)?(?:Magic Damage|Damage))"
                elif "法术防御" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Magic Defense"
                elif "吸血" in zh_inner or "Lifesteal" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*(?:Physical Lifesteal|Magic Lifesteal|Lifesteal)"
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

        if TAG_RE.findall(curr) == tags_in_src or len(TAG_RE.findall(curr)) > len(TAG_RE.findall(result)):
            result = curr

    # 3. Restore untagged control tokens (e.g. ═ before Temporary Level or ╫ between stats)
    GLYPH_KEYWORD_MAP: dict[str, tuple[str, ...]] = {
        "═": ("Temporary Level", "Level Sementara", "Temp Level"),
        "╧": ("Perfect Revive", "Kebangkitan Sempurna", "Revive", "Bangkit"),
        "╥": ("Akomia Core", "Inti Akomia"),
        "╉": ("Prophet Totem", "Bond Totem", "Rebirth Totem", "Totem"),
        "╬": ("Preparation", "Persiapan"),
        "╆": ("Fleeting", "Instant", "Sekilas"),
        "╋": ("Flash",),
        "╪": ("Engage", "Inisiasi"),
        "╫": ("On Play", "Deploy", "Saat Diterjunkan", "Sacrifice", "Pengorbanan"),
        "╨": ("Sacrifice", "Pengorbanan", "Deploy", "Saat Diterjunkan"),
        "╈": ("Awaken", "Bangkit"),
        "╦": ("ancient coin", "Ancient Coin"),
    }

    if ctrls_in_src and Counter(CONTROL_TOKEN_RE.findall(result)) != Counter(ctrls_in_src):
        src_ctrl_counts = Counter(ctrls_in_src)
        cur_ctrl_counts = Counter(CONTROL_TOKEN_RE.findall(result))
        for ch, target_cnt in src_ctrl_counts.items():
            needed = target_cnt - cur_ctrl_counts[ch]
            if needed > 0:
                kws = GLYPH_KEYWORD_MAP.get(ch, ())
                for kw in kws:
                    while needed > 0:
                        subbed, cnt = re.subn(
                            rf"(?<!{re.escape(ch)})"
                            rf"(?<!{re.escape(ch)} )"
                            rf"(?<!{re.escape(ch)}<b>)"
                            rf"(?<!{re.escape(ch)}<b> )"
                            rf"(?<!>)"
                            rf"\b({re.escape(kw)})\b",
                            rf"{ch}\1",
                            result,
                            count=1,
                        )
                        if cnt:
                            result = subbed
                            needed -= 1
                        else:
                            break
                if ch == "╫" and needed > 0:
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
                if needed > 0:
                    clean_src = TAG_RE.sub("", source_zh).strip()
                    if clean_src.startswith(ch):
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
    if "\n" in source_zh and "\n" in stripped_id and source_zh.count("\n") == stripped_id.count("\n"):
        src_lines = source_zh.split("\n")
        id_lines = stripped_id.split("\n")
        res_lines: list[str] = []
        for s_line, i_line in zip(src_lines, id_lines):
            res_lines.append(_wrap_exact_tag_sequence(s_line, i_line, inner_translator))
        return "\n".join(res_lines)

    tokens = TAG_RE.split(source_zh)
    tags = TAG_RE.findall(source_zh)
    if not tags:
        return stripped_id

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
        m_lead = re.match(r"^\n+", tok)
        lead_nl = m_lead.group(0) if m_lead else ""
        m_trail = re.search(r"\n+$", tok)
        trail_nl = m_trail.group(0) if m_trail else ""

        if idx in chunk_map:
            content = f"{lead_nl}{tok_ctrls}{chunk_map[idx]}{trail_nl}"
            if out_parts and out_parts[-1].endswith(">") and content and content[0].isalnum():
                out_parts.append(" ")
            out_parts.append(content)
        else:
            all_nl = "".join(c for c in tok if c == "\n")
            out_parts.append(f"{all_nl}{tok_ctrls}")

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
                rebuilt = (ch * (cnt - cur_ctrl[ch])) + rebuilt

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


def restore_newlines_from_source(source_zh: str, target_id: str) -> str:
    """Guarantee that if source_zh contains newlines, target_id retains them without breaking validation."""
    if "\n" not in source_zh or "\n" in target_id:
        return target_id

    res = target_id

    # 1. Leading newlines
    m_lead = re.match(r"^\n+", source_zh)
    if m_lead and not res.startswith("\n"):
        res = m_lead.group(0) + res

    # 2. Trailing newlines
    m_trail = re.search(r"\n+$", source_zh)
    if m_trail and not res.endswith("\n"):
        res = res + m_trail.group(0)

    # 3. If still no internal newline, look for paragraph anchors
    if "\n" not in res.strip():
        anchors = [
            r"(\n*\s*(?:<[^>]+>\s*)*(?:Aktif|Active|主动)\s*[:：—\-])",
            r"(\n*\s*(?:<[^>]+>\s*)*(?:Rend|Tear|Koyak|撕裂)\s*[:：])",
            r"(\n*\s*(?:<[^>]+>\s*)*(?:Klik|Ketuk|Tap)\s+panel)",
            r"(\n*\s*(?:<[^>]+>\s*)*(?:Berat Pedang|Heavy Sword)\s*[:：])",
            r"(\n*\s*(?:<[^>]+>\s*)*(?:Magical Deer|Rusa Ajaib|神奇小鹿)\s*[:：])",
            r"(\n*\s*(?:<[^>]+>\s*)*(?:Pelayan|Minion)\s+(?:setiap|memberikan))",
            r"(\n*\s*(?:<[^>]+>\s*)*Jika\s+sudah\s+dalam\s+wujud\s+harimau)",
            r"(\n*\s*(?:<[^>]+>\s*)*Basic Attack\s+Memulihkan)",
            r"(\n*\s*(?:<[^>]+>\s*)*10\s+stack\s+Evolusi)",
            r"(\n*\s*(?:<[^>]+>\s*)*20\s+stack\s+Evolusi)",
            r"(\n*\s*<color=#86888A>)",
        ]
        for anc in anchors:
            m = re.search(anc, res[1:], flags=re.I)
            if m:
                idx = m.start() + 1
                nl_to_insert = "\n\n" if "\n\n" in source_zh else "\n"
                cand_res = res[:idx].rstrip() + nl_to_insert + res[idx:].lstrip()
                if validate_translation(source_zh, cand_res)[0]:
                    res = cand_res
                    break

    # 4. Specific content-based line restoration
    if "\n" not in res:
        if "消耗3点神秘力量强化" in source_zh:
            cand_res = res.replace(": <color", ":\n<color").replace(", <color", "\n<color")
            if validate_translation(source_zh, cand_res)[0]:
                res = cand_res
        elif "释放花朵" in source_zh:
            cand_res = res.replace("memberikan <color", "memberikan\n<color").replace("mengurangi Musuh", "mengurangi\nMusuh")
            if validate_translation(source_zh, cand_res)[0]:
                res = cand_res
        elif "大乔唤出一道波浪前行" in source_zh:
            cand_res = res.replace("Damage.", "Damage.\n\n")
            if validate_translation(source_zh, cand_res)[0]:
                res = cand_res
        elif source_zh.count("\n") == 1 and ". " in res:
            cand_res = res.replace(". ", ".\n", 1)
            if validate_translation(source_zh, cand_res)[0]:
                res = cand_res
        elif "\n\n" in source_zh and ". " in res:
            cand_res = res.replace(". ", ".\n\n", 1)
            if validate_translation(source_zh, cand_res)[0]:
                res = cand_res

    ok, _ = validate_translation(source_zh, res)
    return res if ok else target_id

