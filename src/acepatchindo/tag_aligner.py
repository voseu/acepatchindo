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
    "筹备": "Prepare",
    "登场": "Deploy",
    "光环": "Aura",
    "激发": "Inspire",
    "连携": "Synergy",
    "召唤": "Summon",
    "变身": "Transform",
    "复生": "Revive",
    "刷新": "Refresh",
    "临时等级": "Temporary Level",
    "真实等级": "True Level",
    "阿科米亚核心": "Arcomia Core",
    "古币": "Ancient Coin",
    "精炼古币": "Refined Ancient Coin",
    "开团": "Initiate",
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
    "干剑·莫邪": "Twin Blade · Male",
}

BADGE_ALIAS_MAP: dict[str, list[str]] = {
    "闪现": ["Flash.", "Flash"],
    "整备": ["Prepare:", "Prepare", "Preparation:", "Preparation"],
    "筹备": ["Prepare:", "Prepare", "Preparation:", "Preparation"],
    "登场": ["Deploy:", "Deploy", "pada-entri efek", "pada-entri", "Deployment", "On Play"],
    "开团": ["Initiate:", "Initiate", "Engage:", "Engage", "Inisiasi"],
    "牺牲": ["Sacrifice:", "Sacrifice"],
    "复生": ["Revive:", "Revive", "di-revive", "revived", "revive", "Bangkit", "di-Revive", "Resurrect"],
    "完美复生": ["Perfect Revive:", "Perfect Revive", "Perfect Resurrection", "Perfect Resurrect"],
    "临时等级": ["Temporary Level", "Level Sementara"],
    "真实等级": ["True Level", "Level Nyata"],
    "阿科米亚核心": ["Arcomia Core", "Akomia Core", "Core Akomia"],
    "干剑·莫邪": ["Twin Blade · Male", "Twin Blade · Female", "Twin Blades", "Twin Blade"],
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
    "转瞬": ["Fleeting", "Fleet", "Instant", "Sekilas"],
    "图腾系列": ["Totem Series", "Seri Totem"],
    "图腾": ["Totem"],
    "因缘图腾": ["Bond Totem", "Destiny Totem", "Totem Ikatan"],
    "先知图腾": ["Prophet Totem", "Totem Nabi"],
    "转生图腾": ["Rebirth Totem", "Totem Kelahiran Kembali"],
    "往生图腾": ["Afterlife Totem", "Rebirth Totem", "Totem Kehidupan Kembali"],
    "夺取": ["Steal"],
    "凯旋": ["Triumph"],
    "开局": ["Game Start", "Start"],
    "唯一": ["Unique", "Unik"],
    "主动": ["Aktif:", "Aktif", "Active"],
    "被动": ["Pasif:", "Pasif", "Passive"],
    "普通攻击：": ["Basic Attack:", "Basic Attack"],
    "普通攻击": ["Basic Attack"],
    "强化普攻：": ["Enhanced Basic Attack:", "Basic Attack Diperkuat:"],
    "强化普攻": ["Enhanced Basic Attack", "Basic Attack Diperkuat"],
    "1技能：": ["Skill 1:", "Skill 1"],
    "2技能：": ["Skill 2:", "Skill 2"],
    "3技能：": ["Skill 3:", "Skill 3"],
    "连招：": ["Combo:", "Kombo:", "Combo", "Kombo"],
    "小提示：": ["Tips:", "Tip:", "Tips", "Tip"],
    "人形态：": ["Bentuk Manusia:", "Human Form:", "Bentuk Manusia", "Human Form"],
    "人形态": ["Bentuk Manusia", "Human Form", "wujud manusia"],
    "人鱼形态：": ["Bentuk Putri Duyung:", "Mermaid Form:", "Bentuk Putri Duyung", "Mermaid Form"],
    "人鱼形态": ["Bentuk Putri Duyung", "Mermaid Form", "wujud duyung"],
    "清平：": ["Qingping:", "Qingping"],
    "长恨：": ["Changhen:", "Changhen"],
    "2层：": ["2 Stack:", "2 stack:", "2 Stack", "2 stack"],
    "3层：": ["3 Stack:", "3 stack:", "3 Stack", "3 stack"],
    "法球返回时：": ["Saat bola kembali:", "Saat bola kembali"],
    "短剑会留存在原地：": ["Belati tetap berada di tempat:", "Belati tetap berada di tempat"],
    "伤害减免": ["Damage Reduction"],
    "移动速度": ["Movement Speed"],
    "移速": ["Movement Speed"],
    "攻击速度": ["Attack Speed"],
    "攻速": ["Attack Speed"],
    "物理攻击": ["Physical Attack", "Attack dasarnya", "Attack"],
    "物理防御": ["Physical Defense"],
    "法术防御": ["Magic Defense"],
    "浮空": ["melayang", "Levitate", "Airborne"],
    "嘲讽": ["memberi taunt", "taunt", "Taunt"],
    "冰冻": ["Freeze", "freeze", "membekukan", "beku"],
    "减速": ["Slow", "slow", "memperlambat"],
    "沉默": ["Silence", "silence", "membungkam"],
    "退场": ["Retreat", "Exit", "mundur"],
    "镜像": ["Mirror", "cermin", "bayangan"],
    "万镜": ["Myriad Mirrors"],
    "人才搜寻": ["Talent Search"],
    "碰碰运气": ["Try Your Luck"],
    "英雄兑换券": ["Hero Voucher"],
    "兑换券": ["Voucher"],
    "普通装备牌": ["Kartu Normal Equipment", "kartu Normal Equipment", "Kartu Equipment Biasa"],
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
    "往生图腾": ["Afterlife Totem", "Rebirth Totem", "Totem Kehidupan Kembali"],
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
    "清平": ["Qingping", "Serenity"],
    "破阵": ["Pozhen", "Discord", "Conquest"],
    "撕裂": ["Rend", "sobekan", "Sobekan"],
    "法潮灵杖": ["Arcane Tide Staff", "Tide Staff", "Tongkat Pasang Surut"],
    "强敌克星": ["Bane of the Mighty", "Nemesis", "Penakluk Musuh Kuat"],
    "断念": ["Severance", "Heartbreak", "Pemutus Harapan"],
    "效果锦囊牌": [
        "kartu Efek Lucky Bag",
        "efek Strategi kartu",
        "Effect Strategy Card",
        "Kartu Strategi Efek",
        "kartu strategi efek",
    ],
    "4/5阶的召唤单位": [
        "4/5 Tier Summoned Unit",
        "Summoned Unit Tier 4/5",
        "Tier 4/5 unit panggilan",
        "Unit Panggilan Tier 4/5",
        "unit summon Tier 4/5",
    ],
    "首次对【逐鹿】英雄使用的效果牌": [
        "Kartu Efek pertama yang digunakan pada Hero [Zhulu]",
        "pertama Kartu Efek digunakan pada sebuah [Zhulu Plateau] Hero",
        "Kartu Efek pertama yang dipakai pada Hero [Zhulu]",
    ],
    "变为其召唤者（无卡牌效果）": [
        "berubah menjadi pemanggilnya (tanpa efek kartu)",
        "menjadi summoner mereka (tidak kartu efek)",
        "berubah menjadi summoner mereka (tanpa efek kartu)",
    ],
    "第一排╋闪现英雄": [
        "╋Flash Hero di baris pertama",
        "Flash Hero di baris pertama",
        "depan-baris╋ Flash Hero",
        "Hero Flash di baris pertama",
    ],
    "第一排闪现英雄": [
        "Flash Hero di baris pertama",
        "depan-baris Flash Hero",
        "Hero Flash di baris pertama",
    ],
    "后三排╋闪现英雄": [
        "╋Flash Hero di 3 baris belakang",
        "Flash Hero di 3 baris belakang",
        "kembali 3 baris dari╋ Flash Hero",
        "kembali 3-baris╋ Flash Hero",
        "Hero Flash di 3 baris belakang",
    ],
    "后三排闪现英雄": [
        "Flash Hero di 3 baris belakang",
        "kembali 3 baris dari Flash Hero",
        "Hero Flash di 3 baris belakang",
    ],
    "场上的╉图腾被摧毁": [
        "Saat Totem di field hancur",
        "Saat ╉Totem di field hancur",
        "Totem di field hancur",
        "╉Totem di papan dihancurkan",
        "Totem di arena hancur",
    ],
}

ATOMIC_KEYWORD_ALIASES: dict[str, tuple[str, ...]] = {
    "登场": ("Deploy", "pada-entri efek", "pada-entri", "Deployment", "On Play"),
    "开团": ("Initiate", "Engage", "Inisiasi", "Awal Combat", "Combat start", "Combat Start"),
    "整备": ("Prepare", "Preparation", "Persiapan"),
    "筹备": ("Prepare", "Preparation", "Persiapan"),
    "复生": ("Revive", "Resurrect", "Bangkit"),
    "完美复生": ("Perfect Revive", "Perfect Resurrect", "Perfect Resurrection"),
    "阿科米亚核心": ("Arcomia Core", "Akomia Core", "Acomia Core"),
    "干剑·莫邪": ("Twin Blade · Male", "Twin Blade · Female", "Twin Blades", "Twin Blade"),
    "图腾": ("Totem",),
    "转瞬": ("Instant", "Fleeting", "Sekilas"),
    "闪现": ("Flash.", "Flash"),
    "唯一": ("Unique", "Satu-satunya"),
    "无法拆卸": (
        "tidak dapat dilepas",
        "tidak dapat dibongkar",
        "tidak bisa dibongkar",
        "Cannot be dismantled",
        "Indismantlable",
        "Non-dismantlable",
    ),
    "日落海专属装备": (
        "Sunset Exclusive Equipment",
        "[Sunset] Exclusive Equipment",
        "[Sunset Sea] Exclusive Equipment",
        "Sunset Sea Exclusive Equipment",
        "Eksklusif Equipment",
        "Exclusive Equipment",
    ),
    "灵异探测大改装": (
        "Supranatural Detector Perombakan Besar",
        "Supranatural Detector",
        "Spiritual Detection Major Modification",
    ),
    "空山人语": ("Words of Empty Mountain", "Empty Mountain Words"),
    "水穷云起": ("Rising Clouds from Water End", "Water End Cloud Rise"),
    "玄微之种": ("Xuanwei Seed", "Seed of Xuanwei"),
}

GLYPH_KEYWORD_MAP: dict[str, tuple[str, ...]] = {
    "═": ("Temporary Level", "Level Sementara", "Temp Level"),
    "╧": ("Perfect Revive", "Revive", "Resurrect", "Kebangkitan Sempurna", "Bangkit"),
    "╥": ("Arcomia Core", "Akomia Core", "Inti Akomia"),
    "╉": ("Prophet Totem", "Bond Totem", "Rebirth Totem", "Totem"),
    "╬": ("Prepare", "Preparation", "Persiapan"),
    "╆": ("Fleeting", "Instant", "Sekilas"),
    "╋": ("Flash",),
    "╪": ("Initiate", "Engage", "Inisiasi"),
    "╫": ("Deploy", "On Play", "Saat Diterjunkan", "Sacrifice", "Pengorbanan"),
    "╨": ("Deploy", "Sacrifice", "Pengorbanan", "Saat Diterjunkan", "pada-entri"),
    "╈": ("Awaken", "Bangkit"),
    "╦": ("ancient coin", "Ancient Coin", "Merge", "Synthesis", "Combine", "Menggabungkan", "Gabung"),
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


NORM_ZH_LIFE_RE = re.compile(r"棋手生命(?!值)")
NORM_ZH_UNWRAP_NUM_RE = re.compile(r"\{[0-9]+\|([^{}]+)\}")
NORM_ZH_UNWRAP_NAME_RE = re.compile(r"\{[^{}:]+:\s*([^{}]+)\}")
NORM_ZH_TRACKER_RE = re.compile(
    r"[（\(][^）\)]*(?:当前|已击败|击败次数|复生次数|还剩|胜利次数|幸运数字|剩余使用次数|还可获得)[^）\)]*[）\)]"
)
NORM_ZH_STRIP_PH_RE = re.compile(r"\{[^{}]*\}")
NORM_ZH_SPACES_RE = re.compile(r"\s+")


def normalize_plain_zh(text: str) -> str:
    """Strip Unity tags, control tokens, dynamic placeholders, and whitespace so text matches Tier 1 descCn."""
    s = TAG_RE.sub("", text)
    s = CONTROL_TOKEN_RE.sub("", s)
    # 1. Replace game token placeholders with their Chinese wiki equivalents
    s = s.replace("{Energy}", "能量").replace("{LordExp}", "棋手经验").replace("{LordHp}", "棋手生命值")
    s = NORM_ZH_LIFE_RE.sub("棋手生命值", s)
    # 2. Unwrap default values from dynamic placeholders instead of deleting them
    s = NORM_ZH_UNWRAP_NUM_RE.sub(r"\1", s)
    s = NORM_ZH_UNWRAP_NAME_RE.sub(r"\1", s)
    # 3. Strip runtime tracker suffixes and brackets/quotes
    s = NORM_ZH_TRACKER_RE.sub("", s)
    s = s.replace("【", "[").replace("】", "]").replace("“", "").replace("”", "").replace('"', "")
    s = NORM_ZH_STRIP_PH_RE.sub("", s)
    return NORM_ZH_SPACES_RE.sub("", s).strip()


def adapt_tier1_placeholders_to_source(source_zh: str, t1_id: str) -> str:
    """Preserve game runtime placeholders ({Energy}, {LordExp}, {LordHp}, dynamic templates, and tracker suffixes)."""
    out = t1_id

    # Identify trailing tracker clauses and their internal placeholders
    tracker_clauses = [m.group(0) for m in NORM_ZH_TRACKER_RE.finditer(source_zh)]
    tracker_phs: set[str] = set()
    for tc in tracker_clauses:
        tracker_phs.update(PLACEHOLDER_RE.findall(tc))

    # 0a. Dynamic placeholder ranges: {N|v1}-{M|v2}
    # Must run BEFORE atomic icon pairs so ranges like {0|1}-{0|5}{Energy} are not broken into 1-{0|5}
    for m in re.finditer(r"(\{(\d+)\|([^{}]+)\}\s*-\s*\{(\d+)\|([^{}]+)\})", source_zh):
        full_range = m.group(1)
        v1 = m.group(3)
        v2 = m.group(5)
        range_pattern = rf"(?<![A-Za-z0-9_{{|]){re.escape(v1)}\s*-\s*{re.escape(v2)}(?![A-Za-z0-9_{{|])"
        out = re.sub(range_pattern, full_range, out, count=1)

    # 0b. Atomic binding for {N|val}{Icon} pairs (e.g. {3|1}{LordExp}, {0|1}{Energy}, {0|3}{Energy})
    # Must run BEFORE independent icon and number passes to prevent swapping numbers or replacing proper nouns
    for m in re.finditer(r"(\{([^{}|:]+)[:|]([^{}]+)\})\s*(\{(?:Energy|LordExp|LordHp)\})", source_zh):
        full_pair = f"{m.group(1)}{m.group(4)}"
        if out.count(full_pair) >= source_zh.count(full_pair):
            continue
        num_ph = m.group(1)
        val = m.group(3).strip()
        icon_ph = m.group(4)
        if icon_ph == "{LordExp}":
            icon_pat = r"(?:(?:(?:Contestant|Chess Player|Player|Pemain|Lord)\s+)?(?:EXP|Pengalaman|Experience|\{LordExp\})(?:\s+(?:Contestant|Chess Player|Player|Pemain|Lord))?)"
        elif icon_ph == "{LordHp}":
            icon_pat = r"(?:(?:(?:Contestant|Chess Player|Player|Pemain|Lord)\s+)?(?:HP|Darah|Health|\{LordHp\})(?:\s+(?:Contestant|Chess Player|Player|Pemain|Lord))?)"
        else:
            icon_pat = r"(?:Energi|Energy|\{Energy\})\b"
        pair_pat = re.compile(rf"(?<![A-Za-z0-9_{{|:]){re.escape(val)}\s*{icon_pat}", re.I)
        out = pair_pat.sub(f"{num_ph}{icon_ph}", out, count=1)

    # 1. Map icon placeholders if in source_zh
    if "{LordExp}" in source_zh and out.count("{LordExp}") < source_zh.count("{LordExp}"):
        pattern_exp = (
            r"(?<!\{)\b(?:(?:Contestant|Chess Player|Player|Pemain|Lord)\s+)?(?:EXP|Pengalaman|Experience)\b(?!\})"
            r"|(?<!\{)\b(?:EXP|Pengalaman|Experience)(?:\s+(?:Contestant|Chess Player|Player|Pemain|Lord))?\b(?!\})"
        )
        needed = source_zh.count("{LordExp}") - out.count("{LordExp}")
        out = re.sub(pattern_exp, "{LordExp}", out, count=needed, flags=re.I)
    if "{LordHp}" in source_zh and out.count("{LordHp}") < source_zh.count("{LordHp}"):
        pattern_hp = (
            r"(?<!\{)\b(?:(?:Contestant|Chess Player|Player|Pemain|Lord)\s+)?(?:HP|Darah|Health)\b(?!\})"
            r"|(?<!\{)\b(?:HP|Darah|Health)(?:\s+(?:Contestant|Chess Player|Player|Pemain|Lord))?\b(?!\})"
        )
        needed = source_zh.count("{LordHp}") - out.count("{LordHp}")
        out = re.sub(pattern_hp, "{LordHp}", out, count=needed, flags=re.I)
    if "{Energy}" in source_zh and out.count("{Energy}") < source_zh.count("{Energy}"):
        needed = source_zh.count("{Energy}") - out.count("{Energy}")
        out = re.sub(r"(?<!\{)\b(?:Energi|Energy)\b(?!\})", "{Energy}", out, count=needed, flags=re.I)

    # 2b. Dynamic placeholders with defaults: {N|val}
    for m in re.finditer(r"\{(\d+)\|([^{}]+)\}", source_zh):
        full_ph = m.group(0)
        if full_ph in out:
            continue
        if full_ph in tracker_phs:
            continue
        val = m.group(2)
        pattern = r"(?<![A-Za-z0-9_{|])" + re.escape(val) + r"(?![A-Za-z0-9_{|])"
        out = re.sub(pattern, full_ph, out, count=1)

    # 2c. Named or token dynamic placeholders with defaults: {Name: val}
    for m in re.finditer(r"\{([A-Za-z0-9_]+)\s*:\s*([^{}]+)\}", source_zh):
        full_ph = m.group(0)
        if full_ph in out:
            continue
        # Skip tracker placeholders so they never replace leading stat numbers in main body!
        if full_ph in tracker_phs:
            continue
        val = m.group(2).strip()

        # If it's a Tier Voucher placeholder, strictly attach to Tier number!
        if "阶英雄兑换券" in source_zh and ("Hero Voucher" in out or "Tier" in out):
            pattern_tier = r"(?<=\bTier\s)" + re.escape(val) + r"(?![A-Za-z0-9_{|])"
            if re.search(pattern_tier, out):
                out = re.sub(pattern_tier, full_ph, out, count=1)
                continue

        pattern = r"(?<![A-Za-z0-9_{|:])" + re.escape(val) + r"(?![A-Za-z0-9_{|])"
        out = re.sub(pattern, full_ph, out, count=1)

    # 3. Trailing tracker suffixes in source_zh
    for tc in tracker_clauses:
        inner_phs = PLACEHOLDER_RE.findall(tc)
        if not inner_phs:
            continue
        ph = inner_phs[0]
        if "已击败" in tc or "killcount" in tc:
            if re.search(r"Sudah\s+mengalahkan:\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"(Sudah\s+mengalahkan:\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
            elif re.search(r"Dikalahkan:\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"(Dikalahkan:\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
            elif ph not in out:
                out = out.rstrip(". ") + f" (Sudah mengalahkan: {ph})."
        elif "复生次数" in tc or "ResCardInfoDataBin_1541" in tc:
            if re.search(r"total\s+Revive:\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"(total\s+Revive:\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
            elif ph not in out:
                out = out.rstrip(". ") + f" (total Revive: {ph})."
        elif "XYTokenAValue" in tc:
            if re.search(r"(?:saat\s+ini|Current):\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"((?:saat\s+ini|Current):\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
        elif "当前" in tc and ph not in out:
            if "{Dynamic:" in tc:
                dyn_m = re.search(r"\{Dynamic:\d+\}", tc)
                dyn_ph = dyn_m.group(0) if dyn_m else "{Dynamic:0}"
                out = out.rstrip(". ") + f" (Saat ini: {dyn_ph})."
            elif "层" in tc:
                out = out.rstrip(". ") + f" (Saat ini: {ph} Lapis)."
            elif "胜" in tc:
                out = out.rstrip(". ") + f" (Saat ini: {ph} Kemenangan)."
            elif "张" in tc:
                out = out.rstrip(". ") + f" (Saat ini: {ph} Kartu)."
            elif "件" in tc:
                out = out.rstrip(". ") + f" (Saat ini: {ph} item)."
            else:
                out = out.rstrip(". ") + f" (Saat ini: {ph})."

    return out


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
    skel = re.sub(r"[，。：:；;、“”\"!\?！？]", "", skel)
    skel = re.sub(
        r"^吕布会根据敌人位置使用不同招式(?:普攻|普通攻击)能对身前#N#格内敌人造成伤害",
        "吕布的普攻能造成范围伤害",
        skel,
    )
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
        .replace("甄姬引导水流", "甄姬施放水流")
        .replace("解除左右两边#N#格内友军和自身所受的控制效果", "驱散自身和左右两边#N#格内友军")
        .replace("伤害由范围内的敌人平均分摊", "")
        .replace("赵云刺出龙枪短时间内打击敌人#N#次", "赵云快速刺出#N#次龙枪打击目标")
        .replace(
            "鲁班七号召唤河豚飞艇穿越整个战场对下方区域随机投掷河豚炸弹共#N#个炸弹命中敌人后",
            "鲁班七号呼唤河豚飞艇朝战场投掷#N#枚炸弹炸弹对命中敌人",
        )
        .replace("陷入弹坑中的敌人会被灼烧每秒受到", "并留下弹坑弹坑中的敌人每秒受到")
        .replace("杨玉环弹奏琵琶循环激活以下乐曲效果之一", "杨玉环弹奏琵琶")
        .replace("破阵杨玉环弹奏琵琶对", "破阵对")
    )
    skel = re.sub(r"恢复东皇(?:#N#%|#N#)+的最大生命值", "恢复东皇#N#%最大生命值", skel)
    skel = re.sub(r"恢复东皇(?:#N#%|#N#)+生命值", "恢复东皇#N#%最大生命值", skel)
    skel = re.sub(r"(?<!李元芳)丢出飞镖", "李元芳丢出飞镖", skel)
    skel = re.sub(r"化身剑气(?:施展#N#次斩击|斩击范围内敌人#N#次)", "化身剑气斩击#N#次", skel)
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
            "压制": "Suppress",
            "不可选中": "Untargetable",
            "击退": "Knockback",
            "浮空": "Airborne",
            "降低生命恢复": "HP Regen Reduction",
            "嘲讽": "Taunt",
            "驱散": "Dispel",
            "冻结": "Freeze",
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

    # Strip excess control tokens from desc_id that are not present in body_source_zh
    zh_ctrls = Counter(CONTROL_TOKEN_RE.findall(body_source_zh))
    out_ctrls = Counter(CONTROL_TOKEN_RE.findall(out))
    for ch, count in out_ctrls.items():
        excess = count - zh_ctrls.get(ch, 0)
        if excess > 0:
            out = out.replace(ch, "", excess)

    # Fold 3-line desc_id to 2 lines when source_zh is 2-line Yang Yuhuan variant
    if (
        source_zh.lstrip().startswith(("<color=#ffffffbf>清平：</color>", "清平："))
        and out.strip().startswith("Yang Yuhuan memainkan pipa")
    ):
        out = re.sub(
            r"^Yang Yuhuan memainkan pipa[^.\n]*\.\s*\n\s*Qingping:\s*",
            "Qingping: Yang Yuhuan memainkan pipa, ",
            out,
        )
        desc_cn = re.sub(r"^杨玉环弹奏琵琶[^，,\n]*[，,\n]\s*(?:循环激活以下乐曲效果之一[：:]\s*)?", "", desc_cn)

    # Step 1: Pre-bind Chinese numerals to digits (1..10)
    ZH_DIGIT_MAP = {
        "一": "1", "二": "2", "两": "2", "三": "3", "四": "4",
        "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
    }
    zh_num_counter_re = re.compile(
        r"([一二两三四五六七八九十])(周|次|秒|格|层|名|个|张|点|回合|件|把|枚|颗|只|条|道|束|片|朵|发|支|波|阶)"
    )
    cn_clean = normalize_plain_zh(desc_cn).replace("（", "(").replace("）", ")")
    src_clean = normalize_plain_zh(body_source_zh).replace("（", "(").replace("）", ")")
    src_clean = zh_num_counter_re.sub(lambda m: f"{ZH_DIGIT_MAP.get(m.group(1), m.group(1))}{m.group(2)}", src_clean)
    cn_clean = zh_num_counter_re.sub(lambda m: f"{ZH_DIGIT_MAP.get(m.group(1), m.group(1))}{m.group(2)}", cn_clean)

    # Pre-align custom/translated placeholders in `out` (e.g. {Advanced Simulation Tactic:-10} -> {推演高级战术:-20})
    src_named_phs = [
        ph for ph in PLACEHOLDER_RE.findall(body_source_zh)
        if not re.match(r"^\{(?:Energy|LordExp|LordHp)\}$", ph)
    ]
    out_named_phs = [
        ph for ph in PLACEHOLDER_RE.findall(out)
        if not re.match(r"^\{(?:Energy|LordExp|LordHp)\}$", ph)
    ]
    if len(src_named_phs) == len(out_named_phs):
        for ph_out, ph_src in zip(out_named_phs, src_named_phs):
            if ph_out != ph_src:
                out = out.replace(ph_out, ph_src)

    # Pre-bind {num_ph}{Energy|LordExp|LordHp} using letter-only sentinels BEFORE COMPOUND_EXPR_RE
    icon_sentinels: list[tuple[str, str]] = []
    icon_pair_matches = list(re.finditer(
        r"((?:\{[0-9A-Za-z_:+|.%/~ -]+\}(?:\s*[~-]\s*)?)+)\s*(\{(?:Energy|LordExp|LordHp)\})",
        body_source_zh,
    ))
    for idx, m_pair in enumerate(icon_pair_matches):
        num_ph = m_pair.group(1)
        icon_ph = m_pair.group(2)
        sent = f"__WXQICON{chr(65 + idx)}__"
        icon_sentinels.append((sent, f"{num_ph}{icon_ph}"))

        zh_icon_pat = (
            r"(?:点?\s*能量|\{Energy\})" if icon_ph == "{Energy}"
            else r"(?:点?\s*(?:棋手经验|经验)|\{LordExp\})" if icon_ph == "{LordExp}"
            else r"(?:点?\s*(?:棋手生命值|玩家生命值|生命值)|\{LordHp\})"
        )
        src_clean, cnt_src = re.subn(
            rf"(?:\d+(?:\.\d+)?(?:\s*[~-]\s*\d+(?:\.\d+)?)?|\{{[^{{}}]+\}}(?:\s*[~-]\s*\{{[^{{}}]+\}})?)\s*{zh_icon_pat}",
            sent,
            src_clean,
            count=1,
        )
        if not cnt_src:
            src_clean = re.sub(zh_icon_pat, sent, src_clean, count=1)

        # Try WITH required leading number/range first!
        cn_clean, cnt_cn = re.subn(
            rf"(?:\d+(?:\.\d+)?(?:\s*[~-]\s*\d+(?:\.\d+)?)?|\{{[^{{}}]+\}}(?:\s*[~-]\s*\{{[^{{}}]+\}})?)\s*{zh_icon_pat}",
            sent,
            cn_clean,
            count=1,
        )
        if not cnt_cn:
            cn_clean = re.sub(zh_icon_pat, sent, cn_clean, count=1)

        id_icon_pat = (
            r"(?:Energy|Energi|\{Energy\})\b" if icon_ph == "{Energy}"
            else r"(?:Player EXP|EXP Chess Player|EXP Kontestan|EXP Pemain|EXP|\{LordExp\})\b" if icon_ph == "{LordExp}"
            else r"(?:Player HP|HP Chess Player|HP Kontestan|HP Pemain|Health|\{LordHp\})\b"
        )
        # Try WITH required leading number/range in `out` first!
        m_out = re.search(rf"\d+(?:\.\d+)?(?:\s*[~-]\s*\d+(?:\.\d+)?)?\s*{id_icon_pat}", out, flags=re.I)
        if not m_out:
            m_out = re.search(id_icon_pat, out, flags=re.I)
        if m_out:
            out = out[:m_out.start()] + sent + out[m_out.end():]

    # Strip remaining standalone icon placeholders from src_clean/cn_clean
    for icon_term in (
        "能量", "棋手经验", "经验", "棋手生命值", "玩家生命值",
        "{Energy}", "{LordExp}", "{LordHp}",
    ):
        src_clean = src_clean.replace(icon_term, "")
        cn_clean = cn_clean.replace(icon_term, "")
    src_clean = re.sub(r"\[\d+\]点?(物理|法术|真实)伤害\(([^)]+)\)", r"\2的\1伤害", src_clean)
    src_clean = re.sub(r"\[\d+\]点?(护盾|生命值?)\(([^)]+)\)", r"\2的\1", src_clean)

    # Step 2: COMPOUND_EXPR_RE substitution using cursor and letter-only __EXPRSLOTAA__ tokens
    ph_map = {
        re.sub(r"\s+", "", ph): ph
        for ph in PLACEHOLDER_RE.findall(body_source_zh)
        if not re.match(r"^\{(Energy|LordExp|LordHp)\}$", ph)
    }
    expr_with_unit_re = re.compile(
        r"((?:\[[A-Za-z0-9_+/.*%-]+\]|\{[^{}]*\d[^{}]*\}|\d+(?:\.\d+)?%?)"
        r"(?:\s*[+~-]\s*(?:\[[A-Za-z0-9_+/.*%-]+\]|\{[^{}]*\d[^{}]*\}|\d+(?:\.\d+)?%?))*%?)"
        r"([秒格层名个张回合件次把枚颗只条道束片朵发支波阶])?"
    )
    UNIT_MAP = {
        "秒": r"\s*detik\b",
        "格": r"\s*(?:tile|petak)\b",
        "层": r"\s*(?:stack|lapisan)\b",
        "次": r"\s*kali\b",
        "回合": r"\s*(?:Round|putaran)\b",
    }
    cn_matches = expr_with_unit_re.findall(cn_clean)
    src_matches = expr_with_unit_re.findall(src_clean)
    if len(cn_matches) == len(src_matches):
        slots: list[tuple[str, str]] = []
        cursor_by_cex: dict[str, int] = {}
        for i, ((c_ex, c_u), (s_ex, s_u)) in enumerate(zip(cn_matches, src_matches)):
            unit_pat = UNIT_MAP.get(s_u or c_u, "")
            cur_pos = cursor_by_cex.get(c_ex, 0)
            if c_ex == s_ex:
                pat_same = re.compile(rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])")
                m_same = pat_same.search(out, cur_pos)
                if m_same:
                    cursor_by_cex[c_ex] = m_same.end()
                continue
            pat = None
            if unit_pat:
                pat = re.compile(rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])(?={unit_pat})", flags=re.I)
                m = pat.search(out, cur_pos)
                if not m:
                    m = pat.search(out, 0)
                if not m:
                    pat = None
            if not pat:
                pat = re.compile(rf"(?<![\d\[{{|A-Za-z_]){re.escape(c_ex)}(?![\d%\]}}|A-Za-z_])")
                m = pat.search(out, cur_pos)
                if not m:
                    m = pat.search(out, 0)
            if not m and re.match(r"^\d+(?:\.\d+)?\+\d+(?:\.\d+)?%$", c_ex):
                m = re.compile(r"(?<![\d\[])\d+(?:\.\d+)?\s*\+\s*\d+(?:\.\d+)?%").search(out, cur_pos)
                if not m:
                    m = re.compile(r"(?<![\d\[])\d+(?:\.\d+)?\s*\+\s*\d+(?:\.\d+)?%").search(out, 0)
            if not m:
                continue
            clean_s = re.sub(r"\s+", "", s_ex)
            if clean_s in ph_map:
                s_ex = ph_map[clean_s]
            slot_tok = f"__EXPRSLOT{chr(65 + (i // 26))}{chr(65 + (i % 26))}__"
            delta = len(slot_tok) - (m.end() - m.start())
            out = out[:m.start()] + slot_tok + out[m.end():]
            for k_c, v_c in list(cursor_by_cex.items()):
                if v_c > m.start():
                    cursor_by_cex[k_c] = v_c + delta
            cursor_by_cex[c_ex] = m.start() + len(slot_tok)
            slots.append((slot_tok, s_ex))
        for slot_tok, s_ex in slots:
            out = out.replace(slot_tok, s_ex)

    # Restore icon sentinels right after Step 2
    for sent, val in icon_sentinels:
        out = out.replace(sent, val)

    # Step 2b: Graft parenthetical 2-tag formulas, split 3-tag recovery, and split 2-tag formulas
    stat_label = r"(?:Physical Attack|Magic Attack|Max HP|HP Maks|HP Maksimum|Attack|HP)"

    def _get_formula_span_re(first_ph: str, last_ph: str) -> re.Pattern:
        return re.compile(
            rf"(?:(?:Physical|Magic|True)\s+Damage\s+(?:sebesar\s+)?|Damage\s+(?:sebesar\s+)?|Shield\s+(?:sebesar\s+)?|HP\s+(?:sebesar\s+)?)?"
            rf"(?:\d+(?:\.\d+)?%?\s*\+\s*)?{re.escape(first_ph)}"
            + (rf"(?:[^.,;\n<)]*?{re.escape(last_ph)})?" if first_ph != last_ph else "")
            + rf"[^.,;\n<)]*?{stat_label}(?:\s+(?:miliknya|dasarnya|dasar|tambahan))?"
            rf"(?:\s+sebagai\s+(?:(?:Physical|Magic|True)\s+Damage|HP))?",
            flags=re.I,
        )

    # Case 1: 2-Tag Parenthetical formulas
    paren_2tag_re = re.compile(
        r"(<color=[^>]+>)([^<\[\d]*?)(\[\d+\])点?(物理伤害|法术伤害|真实伤害|护盾|生命值?)(</color>)\s*(<color=[^>]+>)[（(]([^）)]+)[）)](</color>)"
    )
    for m_p in paren_2tag_re.finditer(body_source_zh):
        open1, pre_zh, idx_a, kind_zh, close1, open2, inner_zh, close2 = m_p.groups()
        if f"{open1}{idx_a}" in out:
            continue
        inner_phs = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]", inner_zh)
        if not inner_phs:
            continue
        kind_id = {
            "物理伤害": "Physical Damage",
            "法术伤害": "Magic Damage",
            "真实伤害": "True Damage",
            "护盾": "Shield",
            "生命": "HP",
            "生命值": "HP",
        }.get(kind_zh, "Damage")
        first_ph = inner_phs[0]
        last_ph = inner_phs[-1]
        span_re = _get_formula_span_re(first_ph, last_ph)
        m_sp = span_re.search(out)
        inner_clean = ""
        if not m_sp and first_ph not in out:
            alt_re = re.compile(
                rf"(?:(?:Physical|Magic|True)\s+Damage\s+(?:sebesar\s+)?|Damage\s+(?:sebesar\s+)?|Shield\s+(?:sebesar\s+)?|HP\s+(?:sebesar\s+)?|memulihkan\s+(?:tambahan\s+)?)?"
                rf"(?:\d+(?:\.\d+)?%?\s*\+\s*\d+(?:\.\d+)?%|\d+(?:\.\d+)?%?)"
                rf"\s*{stat_label}(?:\s+(?:miliknya|dasarnya|dasar|tambahan))?"
                rf"(?:\s+sebagai\s+{kind_id})?",
                flags=re.I,
            )
            m_sp = alt_re.search(out)
            if m_sp:
                matched_inner = inner_zh
                for zh_s, id_s in (
                    ("法术攻击力", "Magic Attack"),
                    ("物理攻击力", "Physical Attack"),
                    ("最大生命值", "Max HP"),
                    ("生命值", "HP"),
                    ("生命", "HP"),
                ):
                    matched_inner = matched_inner.replace(zh_s, id_s)
                inner_clean = matched_inner
        if m_sp:
            matched_formula = m_sp.group(0).strip()
            if not inner_clean:
                inner_clean = re.sub(
                    r"^(?:(?:Physical|Magic|True)\s+Damage|Damage|Shield|HP)\s+(?:sebesar\s+)?",
                    "",
                    matched_formula,
                    flags=re.I,
                )
                inner_clean = re.sub(
                    r"\s+sebagai\s+(?:(?:Physical|Magic|True)\s+Damage|HP)$",
                    "",
                    inner_clean,
                    flags=re.I,
                )
            prefix_id = "memulihkan " if "恢复" in pre_zh and not re.search(r"memulihkan\s+$", out[:m_sp.start()], flags=re.I) else ""
            rep = f"{open1}{prefix_id}{idx_a} {kind_id}{close1}{open2} ({inner_clean}){close2}"
            out = out[:m_sp.start()] + rep + out[m_sp.end():]

    # Case 2: 3-Tag Split Recovery (<color=C1>...+</color><color=C2>...%</color><color=C3>的生命值</color>)
    split_3tag_re = re.compile(
        r"(<color=[^>]+>)(?:恢复)?(\[[^\]]+\]|\d+)\+(</color>)(<color=[^>]+>)(\[[^\]]+\]|\d+)%([^<]+)(</color>)(<color=[^>]+>)的生命值?(</color>)"
    )
    for m_3 in split_3tag_re.finditer(body_source_zh):
        c1_o, p1, c1_c, c2_o, p2, stat_zh, c2_c, c3_o, c3_c = m_3.groups()
        sp3_re = re.compile(
            rf"(memulihkan\s+)?({re.escape(p1)}\s*\+\s*)({re.escape(p2)}%\s*(?:Magic Attack|Physical Attack|Max HP|HP Maks)(?:\s+miliknya)?)(?:\s+sebagai)?\s+(HP\b)",
            flags=re.I,
        )
        m_s3 = sp3_re.search(out)
        if m_s3:
            mem_p = m_s3.group(1) or ""
            part1 = f"{mem_p}{m_s3.group(2)}" if "恢复" in m_3.group(0) else m_s3.group(2)
            prefix_outside = "" if "恢复" in m_3.group(0) else mem_p
            rep3 = f"{prefix_outside}{c1_o}{part1.strip()}{c1_c}{c2_o}{m_s3.group(3).strip()}{c2_c} {c3_o}{m_s3.group(4)}{c3_c}"
            out = out[:m_s3.start()] + rep3 + out[m_s3.end():]

    # Case 3: 2-Tag Split Recovery/Shield (<color=C1>...%</color><color=C2>的(生命值|护盾)</color>)
    split_2tag_re = re.compile(
        r"(<color=[^>]+>)((?:恢复)?[^<]*?(?:\[[^\]]+\]|\d+)%[^<]*?)(</color>)(<color=[^>]+>)的(生命值?|护盾)(</color>)"
    )
    for m_2 in split_2tag_re.finditer(body_source_zh):
        c1_o, expr_zh, c1_c, c2_o, kind_zh, c2_c = m_2.groups()
        toks = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?", expr_zh)
        if not toks:
            continue
        if len(toks) >= 2:
            num_pat = rf"{re.escape(toks[0])}\s*\+\s*{re.escape(toks[-1])}%"
        else:
            num_pat = rf"{re.escape(toks[0])}%"
        if kind_zh.startswith("生命"):
            sp2a = re.compile(
                rf"(memulihkan\s+)?({num_pat}\s*(?:Magic Attack|Physical Attack|Max HP|HP Maks)(?:\s+(?:miliknya|Miyue|Mi Yue|Yaria))?)\s*((?:sebagai\s+)?HP(?:\s+sekutu(?:\s+itu)?)?\b)",
                flags=re.I,
            )
            sp2b = re.compile(
                rf"(memulihkan\s+)(HP(?:\s+sekutu(?:\s+itu)?|\s+miliknya)?)\s+sebesar\s+({num_pat}\s*(?:Magic Attack|Physical Attack|Max HP|HP Maks)(?:\s+(?:miliknya|Miyue|Mi Yue|Yaria))?)",
                flags=re.I,
            )
            if m_a := sp2a.search(out):
                mem_w, form_w, hp_w = m_a.groups()
                mem_w = mem_w or ""
                rep2 = (f"{c1_o}{mem_w}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}") if "恢复" in expr_zh else (f"{mem_w}{c1_o}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}")
                out = out[:m_a.start()] + rep2 + out[m_a.end():]
            elif m_b := sp2b.search(out):
                mem_w, hp_w, form_w = m_b.groups()
                rep2 = (f"{c1_o}{mem_w}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}") if "恢复" in expr_zh else (f"{mem_w}{c1_o}{form_w}{c1_c} {c2_o}{hp_w}{c2_c}")
                out = out[:m_b.start()] + rep2 + out[m_b.end():]
        elif kind_zh == "护盾":
            sp2s = re.compile(
                rf"(?:(Shield|perisai)\s+(?:sebesar\s+)?({num_pat}\s*(?:Max HP|Magic Attack|Physical Attack|HP Maks)(?:\s+[A-Za-z']+)?)|({num_pat}\s*(?:Max HP|Magic Attack|Physical Attack|HP Maks)(?:\s+[A-Za-z']+)?)\s*(Shield|perisai))",
                flags=re.I,
            )
            if m_s := sp2s.search(out):
                if m_s.group(1):
                    sh_w, form_w = m_s.group(1), m_s.group(2)
                    rep2 = f"{c1_o}{form_w}{c1_c} {c2_o}{sh_w}{c2_c}"
                    out = out[:m_s.start()] + rep2 + out[m_s.end():]
                else:
                    form_w, sh_w = m_s.group(3), m_s.group(4)
                    rep2 = f"{c1_o}{form_w}{c1_c} {c2_o}{sh_w}{c2_c}"
                    out = out[:m_s.start()] + rep2 + out[m_s.end():]

    # Identify trailing tracker clauses and their internal placeholders
    tracker_clauses = [m.group(0) for m in NORM_ZH_TRACKER_RE.finditer(body_source_zh)]
    tracker_phs: set[str] = set()
    for tc in tracker_clauses:
        tracker_phs.update(PLACEHOLDER_RE.findall(tc))

    # Inject tracker suffixes into their matching clauses in out
    for tc in tracker_clauses:
        inner_phs = PLACEHOLDER_RE.findall(tc)
        if not inner_phs:
            continue
        ph = inner_phs[0]
        if "已击败" in tc or "killcount" in tc:
            if re.search(r"Sudah\s+mengalahkan:\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"(Sudah\s+mengalahkan:\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
            elif re.search(r"Dikalahkan:\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"(Dikalahkan:\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
            elif ph not in out:
                out = out.rstrip(". ") + f" (Sudah mengalahkan: {ph})."
        elif "复生次数" in tc or "ResCardInfoDataBin_1541" in tc:
            if re.search(r"total\s+Revive:\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"(total\s+Revive:\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
            elif ph not in out:
                out = out.rstrip(". ") + f" (total Revive: {ph})."
        elif "XYTokenAValue" in tc:
            if re.search(r"(?:saat\s+ini|Current):\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"((?:saat\s+ini|Current):\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
        elif "当前" in tc:
            if re.search(r"(?:saat\s+ini|Current):\s*(?:\d+|\{[^{}]+\})", out, re.I):
                out = re.sub(r"((?:saat\s+ini|Current):\s*)(?:\d+|\{[^{}]+\})", rf"\g<1>{ph}", out, flags=re.I)
            elif ph not in out:
                if "{Dynamic:" in tc:
                    dyn_m = re.search(r"\{Dynamic:\d+\}", tc)
                    dyn_ph = dyn_m.group(0) if dyn_m else "{Dynamic:0}"
                    out = out.rstrip(". ") + f" (Saat ini: {dyn_ph})."
                elif "层" in tc:
                    out = out.rstrip(". ") + f" (Saat ini: {ph} Lapis)."
                elif "胜" in tc:
                    out = out.rstrip(". ") + f" (Saat ini: {ph} Kemenangan)."
                elif "张" in tc:
                    out = out.rstrip(". ") + f" (Saat ini: {ph} Kartu)."
                elif "件" in tc:
                    out = out.rstrip(". ") + f" (Saat ini: {ph} item)."
                else:
                    out = out.rstrip(". ") + f" (Saat ini: {ph})."

    # Step 2c: Any remaining unmatched numeric/formula placeholders from body_source_zh (excluding tracker placeholders!)
    needed_numeric_phs = Counter(
        ph for ph in PLACEHOLDER_RE.findall(body_source_zh)
        if not re.match(r"^\{(Energy|LordExp|LordHp)\}$", ph) and ph not in tracker_phs
    )
    curr_numeric_phs = Counter(
        ph for ph in PLACEHOLDER_RE.findall(out)
        if not re.match(r"^\{(Energy|LordExp|LordHp)\}$", ph) and ph not in tracker_phs
    )
    if curr_numeric_phs != needed_numeric_phs:
        missing_phs: list[str] = []
        for ph, count in needed_numeric_phs.items():
            diff = count - curr_numeric_phs.get(ph, 0)
            if diff > 0:
                missing_phs.extend([ph] * diff)
        for ph in missing_phs:
            m_num = re.search(r"(?<![\d\[{|A-Za-z_])\d+(?:\.\d+)?%?(?![\d\]}|A-Za-z_])", out)
            if m_num:
                out = out[: m_num.start()] + ph + out[m_num.end() :]

    # Step 3: Attach any standalone {Energy}, {LordExp}, {LordHp} icon placeholders
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

    # Clean header tags to guarantee exact header tags and zero header bleed
    HEADER_PATTERNS = [
        (r"<color=([^>]+)>(?:被动|Pasif)[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Pasif\s*:\s*(?:</color>)?", "Pasif:"),
        (r"<color=([^>]+)>(?:主动|Aktif)[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Aktif\s*:\s*(?:</color>)?", "Aktif:"),
        (r"<color=([^>]+)>普通攻击[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Basic Attack\s*:\s*(?:</color>)?", "Basic Attack:"),
        (r"<color=([^>]+)>强化普攻[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*(?:Enhanced Basic Attack|Basic Attack Diperkuat)\s*:\s*(?:</color>)?", "Enhanced Basic Attack:"),
        (r"<color=([^>]+)>1技能[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Skill 1\s*:\s*(?:</color>)?", "Skill 1:"),
        (r"<color=([^>]+)>2技能[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Skill 2\s*:\s*(?:</color>)?", "Skill 2:"),
        (r"<color=([^>]+)>3技能[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Skill 3\s*:\s*(?:</color>)?", "Skill 3:"),
        (r"<color=([^>]+)>连招[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*(?:Combo|Kombo)\s*:\s*(?:</color>)?", "Combo:"),
        (r"<color=([^>]+)>小提示[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*(?:Tips|Tip)\s*:\s*(?:</color>)?", "Tips:"),
        (r"<color=([^>]+)>人形态[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*(?:Bentuk Manusia|Human Form)\s*:\s*(?:</color>)?", "Bentuk Manusia:"),
        (r"<color=([^>]+)>人鱼形态[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*(?:Bentuk Putri Duyung|Mermaid Form)\s*:\s*(?:</color>)?", "Bentuk Putri Duyung:"),
        (r"<color=([^>]+)>清平[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Qingping\s*:\s*(?:</color>)?", "Qingping:"),
        (r"<color=([^>]+)>长恨[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*Changhen\s*:\s*(?:</color>)?", "Changhen:"),
        (r"<color=([^>]+)>2层[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*2 Stack\s*:\s*(?:</color>)?", "2 Stack:"),
        (r"<color=([^>]+)>3层[:：]?</color>", r"(?:<color=[^>]+>)?[^\S\r\n]*3 Stack\s*:\s*(?:</color>)?", "3 Stack:"),
    ]
    for zh_pat, id_pat, canonical_id in HEADER_PATTERNS:
        m_h = re.search(zh_pat, body_source_zh)
        if m_h:
            c_col = m_h.group(1)
            if f"<color={c_col}>{canonical_id}</color>" not in out:
                out = re.sub(id_pat, f"<color={c_col}>{canonical_id}</color> ", out, count=1)

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

    # Eliminate space before closing tag for colons: Aktif: </color> -> Aktif:</color> 
    text = re.sub(r":\s+</color>\s*", r":</color> ", text)
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
    # Ensure space after period before opening tag: Unik.<color=... -> Unik. <color=...
    spaced = re.sub(r"\.[ \t]*(?=<(?:color=|a\b|b\b|size=))", ". ", spaced)
    # Clean rogue spaces right after opening tags: <color=#d487e4> Magic -> <color=#d487e4>Magic
    spaced = re.sub(r"(<(?:color=[^>]+|b|i|a\b[^>]*|size=[^>]+)>)[ \t]+", r"\1", spaced)
    # Clean space after comma if followed by tag or control token
    spaced = re.sub(r",(?=[<[\u2540-\u257f]])", ", ", spaced)
    # Collapse any accidental double spaces created
    spaced = re.sub(r"[ ]{2,}", " ", spaced)

    ok, _ = validate_translation(source, spaced)
    return spaced if ok else text


HIGHLIGHT_TAG_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "你的召唤单位": ("Unit Summon milikmu", "Summoned Unit milikmu", "unit Summon milikmu", "Unit panggilan", "Unit Summon"),
    "棋手": ("Kontestan", "Player", "Pemain"),
    "棋手升级时": ("Saat Player naik Level", "Saat Kontestan naik Level", "Ketika Player naik Level", "Player naik Level"),
    "碰碰运气": ("Try Your Luck", "Cobalah Keberuntunganmu"),
    "镜像": ("Mirror", "cermin"),
    "万镜": ("All Mirrors", "cermin"),
    "英雄总等级": ("total Level Hero", "Total Level Hero"),
    "等价交换": ("Equal Exchange", "Pertukaran Setara"),
    "无限释放技能": ("menggunakan Skill tanpa batas", "Skill tanpa batas"),
    "20%攻速": ("20% Attack Speed", "20% Kecepatan Serangan"),
    "至少穿戴2件装备": ("mengenakan minimal 2 Equipment", "memakai minimal 2 Equipment", "minimal 2 Equipment"),
    "模型缩小": ("model Hero mengecil", "model mengecil"),
    "回满法力值": ("Mana langsung penuh", "memulihkan penuh Mana"),
    "攻速上限改为5.0": (
        "Batas Attack Speed diubah jadi 5.0",
        "Attack Speed limit 5.0",
        "Attack Speed cap changed to 5.0",
        "Batas Attack Speed diubah menjadi 5.0",
    ),
    "法术攻击力+20": ("Magic Attack +20",),
    "法术攻击力+30": ("Magic Attack +30",),
    "物理攻击力+10": ("Physical Attack +10",),
    "双剑·雄": ("Twin Blades: Male", "Twin Blade · Male", "Dual Swords: Male", "Twin Blade: Male"),
    "双剑·雌": ("Twin Blades: Female", "Twin Blade · Female", "Dual Swords: Female", "Twin Blade: Female"),
    "险中求富": ("Seeking wealth in danger", "Seeking Wealth in Danger", "Mencari Keberuntungan di Bahaya"),
    "站这别动": ("Stay Put", "Stay Right There", "Berdiri di Sini Jangan Bergerak"),
    "怒莲之刺": ("Thorn of the Angry Lotus", "Wrathlotus Thorn"),
    "4张": ("4", "4 Kartu"),
    "商店购买": ("Pembelian di Shop", "Membeli di Shop"),
    "出售英雄牌": ("menjual Kartu Hero", "Menjual Kartu Hero", "menjual Kartu"),
    "已觉醒英雄": ("Hero milikmu yang sudah Awaken", "Hero yang sudah Awaken", "Hero milikmu yang sudah Awakening", "Hero yang sudah Awakening"),
    "3阶英雄牌": ("Kartu Hero Tier 3", "Hero Tier 3"),
    "法力值清空": ("menguras habis Mana", "Mana dikosongkan", "mengosongkan Mana"),
    "受到的伤害": ("menerima Damage", "Damage yang diterima"),
}


def _wrap_keyword_or_entity(u_open: str, u_close: str, u_zh: str, text_segment: str) -> str:
    """Safely wrap only the keyword/proper noun entity inside text_segment rather than swallowing the whole clause."""
    raw = text_segment.strip()
    if not raw:
        return text_segment

    # Check candidates for u_zh
    candidates: list[str] = []
    if u_zh in BADGE_ALIAS_MAP:
        candidates.extend([a.rstrip(":") for a in BADGE_ALIAS_MAP[u_zh]])
    if u_zh in ATOMIC_KEYWORD_ALIASES:
        candidates.extend(ATOMIC_KEYWORD_ALIASES[u_zh])
    if u_zh in BRACKET_TERM_MAP:
        candidates.append(BRACKET_TERM_MAP[u_zh])
    if u_zh in HIGHLIGHT_TAG_ALIAS_MAP:
        candidates.extend(HIGHLIGHT_TAG_ALIAS_MAP[u_zh])
    for ch in re.findall(r"[\u2540-\u257f]", u_open + u_zh):
        if ch in GLYPH_KEYWORD_MAP:
            candidates.extend(GLYPH_KEYWORD_MAP[ch])

    # Search for known candidate
    candidates.sort(key=len, reverse=True)
    for cand in candidates:
        if not cand.strip():
            continue
        m = re.search(rf"\b{re.escape(cand.strip())}\b", text_segment, flags=re.I)
        if m:
            before = text_segment[: m.start()]
            if before.rfind("<") <= before.rfind(">"):
                return text_segment[: m.start()] + f"{u_open}{m.group(0)}{u_close}" + text_segment[m.end() :]

    # Special single-span mechanic target phrase wrapping (Directed Transfer & Level gain)
    if "穿戴装备最多" in u_zh:
        m_equip = re.search(
            r"(?:(?:1\s+)?Hero\s+\[[^\]]+\](?:\s+milikmu|\s+sekutu)?\s+(?:yang\s+memakai|yang\s+mengenakan|dengan)\s+Equipment\s+terbanyak|"
            r"Hero\s+\[[^\]]+\](?:\s+milikmu|\s+sekutu)?\s+dengan\s+Equipment\s+terbanyak)",
            text_segment,
            flags=re.I,
        )
        if m_equip:
            before = text_segment[: m_equip.start()]
            if before.rfind("<") <= before.rfind(">"):
                return text_segment[: m_equip.start()] + f"{u_open}{m_equip.group(0)}{u_close}" + text_segment[m_equip.end() :]

    if re.search(r"等级\+(?:\d+|\{[^}]+\})", u_zh):
        m_lvl = re.search(r"(?:mendapat\s+)?\+\s*(?:\d+|\{[^}]+\})\s*Level", text_segment, flags=re.I)
        if m_lvl:
            before = text_segment[: m_lvl.start()]
            if before.rfind("<") <= before.rfind(">"):
                return text_segment[: m_lvl.start()] + f"{u_open}{m_lvl.group(0)}{u_close}" + text_segment[m_lvl.end() :]

    # If proper noun entity tag (<color=...><b> or <b>)
    if "<b>" in u_open:
        # Match English proper noun at the end of the clause
        m_end = re.search(r"([A-Z][A-Za-z0-9'·•\- ]+[A-Za-z0-9])(?=[\.,;!\?]?\s*$)", text_segment)
        if m_end:
            before = text_segment[: m_end.start(1)]
            if before.rfind("<") <= before.rfind(">"):
                return text_segment[: m_end.start(1)] + f"{u_open}{m_end.group(1)}{u_close}" + text_segment[m_end.end(1) :]
        # Or any capitalized title/entity phrase in clause
        m_cap = re.search(r"\b([A-Z][a-z0-9]+(?:\s+[·•\-\w]+)*)\b", text_segment)
        if m_cap:
            before = text_segment[: m_cap.start(1)]
            if before.rfind("<") <= before.rfind(">"):
                return text_segment[: m_cap.start(1)] + f"{u_open}{m_cap.group(1)}{u_close}" + text_segment[m_cap.end(1) :]

    # If control token or mechanic link (<a href=...>)
    CTRL = set("╥╆╪╬╉═╧╊╅╈╦╇╋")
    if any(c in u_open for c in CTRL) or "<a href=" in u_open:
        m_mech = re.search(
            r"\b(Deploy|Initiate|Prepare|Revive|Perfect Revive|Flash|Totem|Temporary Level|Sacrifice|Steal|Arcomia Core|pada-entri)\b",
            text_segment,
            flags=re.I,
        )
        if m_mech:
            before = text_segment[: m_mech.start(1)]
            if before.rfind("<") <= before.rfind(">"):
                return text_segment[: m_mech.start(1)] + f"{u_open}{m_mech.group(1)}{u_close}" + text_segment[m_mech.end(1) :]
        canonical = "Deploy"
        if u_zh in BADGE_ALIAS_MAP and BADGE_ALIAS_MAP[u_zh]:
            canonical = BADGE_ALIAS_MAP[u_zh][0].rstrip(":")
        elif u_zh in ATOMIC_KEYWORD_ALIASES and ATOMIC_KEYWORD_ALIASES[u_zh]:
            canonical = ATOMIC_KEYWORD_ALIASES[u_zh][0]
        if "efek" in text_segment.lower():
            m_efek = re.search(r"\b(efek)\b", text_segment, flags=re.I)
            if m_efek:
                return text_segment[: m_efek.start(1)] + f"{u_open}{canonical}{u_close} " + text_segment[m_efek.start(1) :]

    # If clause starts with "Saat Combat dimulai" and tag is NOT for combat start
    if text_segment.strip().startswith("Saat Combat dimulai") and "战斗开始" not in u_zh:
        m_sc = re.search(r"^(Saat Combat dimulai,?\s*)", text_segment)
        if m_sc:
            rem = text_segment[m_sc.end():]
            if rem.strip():
                return m_sc.group(1) + f"{u_open}{rem.strip()}{u_close}"

    # Fallback: if not control token and not <a href=>
    if not any(c in u_open for c in CTRL) and "<a href=" not in u_open:
        if len(u_zh.strip()) <= 6 and len(raw) >= 45:
            m_first = re.search(r"\b([A-Z][A-Za-z0-9'·•\-]+|\d+%?)\b", raw)
            if m_first:
                return raw[: m_first.start()] + f"{u_open}{m_first.group(0)}{u_close}" + raw[m_first.end() :]
        return f"{u_open}{text_segment.strip()}{u_close}"

    # Last resort for control tokens: wrap the first word or token, NEVER insert raw Chinese u_zh
    words = text_segment.strip().split()
    if words:
        first_word = words[0]
        rem = text_segment.strip()[len(first_word):]
        return f"{u_open}{first_word}{u_close}{rem}"

    return f"{u_open}{u_close} {text_segment}"


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

    # Fold 3-line result to 2 lines when source_zh is 2-line Yang Yuhuan variant
    if (
        source_zh.lstrip().startswith(("<color=#ffffffbf>清平：</color>", "清平："))
        and result.strip().startswith("Yang Yuhuan memainkan pipa")
    ):
        result = re.sub(
            r"^Yang Yuhuan memainkan pipa[^.\n]*\.\s*\n\s*Qingping:\s*",
            "Qingping: Yang Yuhuan memainkan pipa, ",
            result,
        )

    # Sanitize corrupted upstream English patcher baseline_en
    if baseline_en and "<a>Riverlands<color=#99DEB0>" in baseline_en:
        baseline_en = "Summon <color=#99DEB0>╉Totem</color>. All allied [Riverlands] heroes gain <a><color=#99DEB0>╉<b>Totem</b></color></a> Level <color=#99DEB0>50%</color> as <a>═Temporary Level</a>."

    # 0. Multiline line-by-line alignment if both have newlines
    if "\n" in source_zh and "\n" in result and source_zh.count("\n") != result.count("\n"):
        src_paras = [p for p in re.split(r"\n+", source_zh.strip()) if p.strip()]
        res_paras = [p for p in re.split(r"\n+", result.strip()) if p.strip()]
        src_seps = re.findall(r"\n+", source_zh.strip())
        if len(src_paras) == len(res_paras) and len(src_seps) == len(src_paras) - 1:
            rebuilt_nl = [res_paras[0]]
            for sep, rp in zip(src_seps, res_paras[1:]):
                rebuilt_nl.append(sep + rp)
            result = "".join(rebuilt_nl)

    if "\n" in source_zh and "\n" in result and source_zh.count("\n") == result.count("\n"):
        src_lines = source_zh.split("\n")
        res_lines = result.split("\n")
        b_lines = (
            baseline_en.split("\n")
            if (baseline_en and baseline_en.count("\n") == source_zh.count("\n"))
            else []
        )
        aligned_lines: list[str] = []
        for idx, (s_l, r_l) in enumerate(zip(src_lines, res_lines)):
            if not s_l.strip() and not r_l.strip():
                aligned_lines.append("")
                continue
            b_l = b_lines[idx] if idx < len(b_lines) else None
            l_aligned = reinject_skeleton_from_source(
                s_l,
                r_l,
                inner_translator=inner_translator,
                baseline_en=b_l,
                en_translator=en_translator,
                allow_en_fallback=allow_en_fallback,
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

    if "图腾" in source_zh and "临时等级" in source_zh and ("<a" in source_zh) and source_zh.find("图腾") < source_zh.find("临时等级"):
        result = re.sub(
            r"memperoleh\s+(═?Temporary Level)\s+sebesar\s+(\d+%)\s+dari\s+jumlah\s+Level\s+setiap\s+(╉?Totem)",
            r"dari setiap \3, memperoleh \2 \1 berdasarkan jumlah Level-nya",
            result,
            flags=re.I,
        )
        result = re.sub(
            r"memperoleh\s+(═?Temporary Level)\s+sebesar\s+(setengah\s+Level)\s+(╉?Totem\s+tersebut)",
            r"memperoleh \2 \3 sebagai \1",
            result,
            flags=re.I,
        )
        result = re.sub(
            r"mendapatkan\s+(?:╉?Temporary\s+Level\s+)?sebesar\s+(\d+%)\s+dari\s+(╉?Totem)\s+Level",
            r"mendapatkan \2 Level \1 sebagai ═Temporary Level",
            result,
            flags=re.I,
        )

    # 1. If baseline_en has valid matching tags & a short leading tagged keyword prefix
    if baseline_en and TAG_RE.findall(baseline_en) == tags_in_src and tags_in_src:
        m_en = LEADING_TAGGED_PREFIX_RE.match(baseline_en)
        m_id = re.match(r"^([^:\n]{1,40}):\s*(.+)$", result, re.S)
        if (
            m_en
            and m_id
            and m_en.group(1).lstrip().startswith("<")
            and TAG_RE.findall(m_en.group(1)) == tags_in_src
            and len(TAG_RE.sub("", m_en.group(1)).strip().split()) <= 2
        ):
            cand = sanitize_target_text(source_zh, f"{m_en.group(1)}: {m_id.group(2)}")
            if validate_translation(source_zh, cand)[0]:
                return cand

    # Special: Handle interleaved <color=#FFE897>敌方英雄触发<a>╫牺牲</color></a>
    if "<color=#FFE897>敌方英雄触发<a>╫牺牲</color></a>" in source_zh and "<" not in result:
        cand_il = result
        cand_il = re.sub(r"\b(═?Temporary Level)\b", r"<a href=3130011><color=#ffffff>═<b>\1</b></color></a>", cand_il)
        cand_il = re.sub(r"(Hero musuh\s+(?:Memicu|memicu)\s+)(?:<a>)?(?:╫)?(?:Sacrifice|Pengorbanan)(?:</a>)?", r"<color=#FFE897>\1<a>╫Sacrifice</color></a>", cand_il, flags=re.I)
        if validate_translation(source_zh, cand_il)[0]:
            return cand_il

    # Special: Handle nested <color=C1>...<color=C2>VAL</color>...</color>
    m_nest = re.search(r"<color=([^>]+)>([^<]*)<color=([^>]+)>([^<]+)</color>([^<]*)</color>", source_zh)
    if m_nest and "<" not in result:
        c1 = m_nest.group(1)
        c2 = m_nest.group(3)
        inner_val = m_nest.group(4)
        if inner_val in result:
            cand_nest = result.replace(inner_val, f"<color={c2}>{inner_val}</color>", 1)
            m_phrase = re.search(rf"(?:sebesar\s+)?<color={re.escape(c2)}>{re.escape(inner_val)}</color>(?:\s+Max HP\s+musuh|\s+kali)?", cand_nest, flags=re.I)
            if m_phrase:
                phrase_span = m_phrase.group(0)
                cand_nest = cand_nest[:m_phrase.start()] + f"<color={c1}>{phrase_span}</color>" + cand_nest[m_phrase.end():]
                if validate_translation(source_zh, cand_nest)[0]:
                    return cand_nest

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
        matched_indices: set[int] = set()
        for idx, m_span in enumerate(spans):
            open_part = m_span.group(1)
            zh_inner = m_span.group(2).strip()
            close_part = m_span.group(3)

            # Check if this exact span is ALREADY wrapped in curr at or after cursor
            phs_in_inner = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]", zh_inner)
            if open_part in curr and close_part in curr:
                m_existing = re.compile(rf"{re.escape(open_part)}([^<]+){re.escape(close_part)}").search(curr, cursor)
                if m_existing:
                    inner_cand = m_existing.group(1)
                    if (phs_in_inner and all(ph in inner_cand for ph in phs_in_inner)) or (
                        not phs_in_inner
                        and not re.search(r"\[[A-Za-z0-9_+/.*%-]+\]", inner_cand)
                        and curr.find("<", cursor) == m_existing.start()
                    ):
                        cursor = m_existing.end()
                        matched_this = True
                        matched_indices.add(idx)
                        continue

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
            if zh_inner in ATOMIC_KEYWORD_ALIASES:
                aliases.extend(ATOMIC_KEYWORD_ALIASES[zh_inner])
            if bracket_clean in ATOMIC_KEYWORD_ALIASES:
                for a_alias in ATOMIC_KEYWORD_ALIASES[bracket_clean]:
                    if has_brackets:
                        aliases.append(f"[{a_alias}]")
                        aliases.append(f"【{a_alias}】")
                    aliases.append(a_alias)
            if colon_clean in ATOMIC_KEYWORD_ALIASES:
                for a_alias in ATOMIC_KEYWORD_ALIASES[colon_clean]:
                    aliases.extend([f"{a_alias}:", f"{a_alias}.", a_alias])
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
                    CTRL = set("╥╆╪╬╉═╧╊╅╈╦╇╋")
                    before_adj = before
                    for ch in CTRL:
                        if ch in open_part and re.search(rf"{re.escape(ch)}\s*$", before):
                            before_adj = re.sub(rf"{re.escape(ch)}\s*$", "", before)
                            break
                        if ch in open_part and alias.startswith(ch):
                            alias = alias[len(ch):].lstrip()
                    if alias.endswith((".", ":", "\n")):
                        kw = alias[:-1]
                        punct = alias[-1]
                        if punct in (":", "：") and zh_inner.endswith(("：", ":")):
                            tagged = f"{open_part}{kw}:{close_part} "
                        elif punct in (":", "："):
                            tagged = f"{open_part}{kw}{close_part}: "
                        else:
                            tagged = f"{open_part}{kw}{close_part}{punct}"
                    else:
                        tagged = f"{open_part}{alias}{close_part}"
                    curr = before_adj + tagged + curr[f_idx + len(alias) :]
                    cursor = len(before_adj) + len(tagged)
                    matched_this = True
                    matched_indices.add(idx)
                    break
            if not matched_this:
                # Check formula / stat pattern for color spans
                pattern = None
                phs_in_inner = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]", zh_inner)
                if zh_inner.startswith(("（", "(")) and zh_inner.endswith(("）", ")")):
                    pattern = r"\([^\)]*?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)[^\)]*?\)"
                elif "护盾" in zh_inner:
                    pattern = r"(?:(?:Shield|perisai)\s+(?:sebesar\s+)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:\s*[xX]\s*(?:jumlah\s+Round|Round))?%?(?:\s*\+\s*(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)%?\s*(?:Physical Attack|Magic Attack|Max HP)(?:\s+miliknya)?)?|(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)%?\s+(?:Shield|perisai)))"
                elif "法力" in zh_inner:
                    pattern = r"(?:(?:memulihkan\s+(?:tambahan\s+)?)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Mana\b|(?:Mana\s+(?:sebesar\s+)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)))"
                elif "兑换券" in zh_inner:
                    pattern = r"\b(?:Hero\s+)?Voucher(?:\s+Tier\s+\d+(?:-\d+)?)?\b"
                elif "普通装备牌" in zh_inner:
                    pattern = r"\b(?:[Kk]artu\s+Normal\s+Equipment|[Kk]artu\s+Equipment\s+Biasa|Normal\s+Equipment)\b"
                elif zh_inner.endswith(("：", ":")) or any(k in zh_inner for k in ("被动", "主动", "清平", "长恨", "Pasif", "Aktif")):
                    label_zh = zh_inner.rstrip("：: ")
                    label_trans = (
                        "Pasif" if "被动" in label_zh
                        else "Aktif" if "主动" in label_zh
                        else (inner_translator(label_zh) if inner_translator else label_zh)
                    )
                    pattern = rf"\b(?:Pasif|Aktif|{re.escape(label_trans)})\s*[:：]"
                elif phs_in_inner:
                    ph_anchor = re.escape(phs_in_inner[-1])
                    pattern = rf"(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?{ph_anchor}(?:%|\s*persen)?\s*(?:Physical Attack|Magic Attack|Max HP|HP|Physical Defense|Magic Defense|Physical Lifesteal|Magic Lifesteal|Attack Speed|Movement Speed)?(?:\s+sebagai\s+(?:Physical|Magic|True)\s+Damage)?"
                elif "自身" in zh_inner or ("生命" in zh_inner and ("法术伤害" in zh_inner or "物理伤害" in zh_inner)):
                    pattern = r"(?:Magic Damage|Physical Damage|Shield|perisai)?\s*(?:sebesar\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)%?\s*(?:base\s+|dasar\s+)?(?:Physical Attack|Magic Attack|Max HP)(?:\s+[A-Za-z]+)?(?:\s+sebagai\s+(?:Magic Damage|Physical Damage|True Damage))?"
                elif "物理伤害" in zh_inner or "物理攻击" in zh_inner:
                    pattern = r"(?:(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Physical Attack)(?:\s*(?:sebagai\s+)?(?:Physical Damage|Damage))?|(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:sebagai\s+)?(?:Physical Damage|Damage))"
                elif "物理防御" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Physical Defense"
                elif "法术伤害" in zh_inner or "法术攻击" in zh_inner:
                    pattern = r"(?:(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:Magic Attack)(?:\s*(?:sebagai\s+)?(?:Magic Damage|Damage))?|(?:(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*\+\s*)?(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)(?:%|\s*persen)?\s*(?:sebagai\s+)?(?:Magic Damage|Damage))"
                elif "法术防御" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*Magic Defense"
                elif "吸血" in zh_inner or "Lifesteal" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*(?:Physical Lifesteal|Magic Lifesteal|Lifesteal)"
                elif "生命" in zh_inner or "HP" in zh_inner:
                    pattern = r"(?:(?:sebagai\s+)?(?:Max HP|HP|Health)(?:\s*(?:diri|sekutu|miliknya))?|(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*(?:Max HP|HP|Health)(?:\s*(?:diri|sekutu|miliknya))?(?:\s*sebagai\s*(?:Magic Damage|Physical Damage|True Damage))?)"
                elif "伤害减免" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)%?\s*Damage Reduction"
                elif "移动速度" in zh_inner or "移速" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Movement Speed"
                elif "攻击速度" in zh_inner or "攻速" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Attack Speed"
                elif "法术穿透" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Magic Penetration"
                elif "物理穿透" in zh_inner:
                    pattern = r"(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?%?)\s*Physical Penetration"
                elif "眩晕" in zh_inner:
                    pattern = r"\b(?:stun(?:\s+selama)?(?:\s+(?:\[[A-Za-z0-9_+/.*%-]+\]|\d+(?:\.\d+)?)\s*detik)?)\b"
                elif "击飞" in zh_inner:
                    pattern = r"\b(?:Knock-up|knock-up|Knockback|knockback|menghempaskan(?:\s+musuh)?(?:\s+ke\s+udara)?|terhempas(?:\s+ke\s+udara)?)\b"

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
                        matched_indices.add(idx)
                        break

            if not matched_this:
                all_matched = False

        if not all_matched and len(spans) == 1 and "<" not in curr and curr.strip():
            m_nest = re.search(
                r"<color=([^>]+)>([^<]*)<color=([^>]+)>([^<]+)</color>([^<]*)</color>",
                source_zh,
            )
            if m_nest:
                c1_col, p1, c2_col, inner_val, p2 = m_nest.groups()
                inner_trans = inner_translator(inner_val) if inner_translator else inner_val
                m_inner = re.search(rf"\b{re.escape(inner_trans)}\b", curr, flags=re.I) or re.search(
                    rf"\b{re.escape(inner_val)}\b", curr, flags=re.I
                )
                if m_inner:
                    tagged_inner = f"<color={c2_col}>{m_inner.group(0)}</color>"
                    curr = curr[: m_inner.start()] + tagged_inner + curr[m_inner.end() :]
                    curr = f"<color={c1_col}>{curr}</color>"
                    all_matched = True
            elif len(normalize_plain_zh(spans[0].group(2))) >= 0.75 * len(normalize_plain_zh(source_zh)):
                curr = f"{spans[0].group(1)}{curr}{spans[0].group(3)}"
                all_matched = True
            else:
                span_zh = spans[0].group(2)
                span_subs = [s for s in re.split(r"[，。！？；：:\n]+", span_zh) if s.strip()]
                zh_clauses = [c for c in re.split(r"[，。！？；：:\n]+", source_zh) if c.strip()]
                id_clauses = re.split(r"([,.;!?\n:]+)", curr)
                content_clause_indices = [
                    i for i in range(0, len(id_clauses), 2) if id_clauses[i].strip()
                ]
                if span_subs and zh_clauses and content_clause_indices:
                    start_idx = next(
                        (i for i, c in enumerate(zh_clauses) if span_subs[0] in c), -1
                    )
                    end_idx = next(
                        (i for i, c in enumerate(zh_clauses) if span_subs[-1] in c), start_idx
                    )
                    if start_idx != -1:
                        if end_idx == -1 or end_idx < start_idx:
                            end_idx = start_idx
                        mapped_start = int(
                            round(
                                start_idx
                                / max(1, len(zh_clauses) - 1)
                                * (len(content_clause_indices) - 1)
                            )
                        )
                        mapped_end = int(
                            round(
                                end_idx
                                / max(1, len(zh_clauses) - 1)
                                * (len(content_clause_indices) - 1)
                            )
                        )
                        actual_start = content_clause_indices[
                            min(mapped_start, len(content_clause_indices) - 1)
                        ]
                        actual_end = content_clause_indices[
                            min(mapped_end, len(content_clause_indices) - 1)
                        ]
                        CTRL = set("╥╆╪╬╉═╧╊╅╈╦╇╋")
                        if (
                            len(span_zh) <= 8
                            or any(c in spans[0].group(1) for c in CTRL)
                            or "<a href=" in spans[0].group(1)
                            or actual_start == actual_end
                            or "穿戴装备最多" in span_zh
                            or "等级+" in span_zh
                        ):
                            id_clauses[actual_start] = _wrap_keyword_or_entity(
                                spans[0].group(1), spans[0].group(3), span_zh, id_clauses[actual_start]
                            )
                        else:
                            id_clauses[actual_start] = (
                                f"{spans[0].group(1)}{id_clauses[actual_start].lstrip()}"
                            )
                            id_clauses[actual_end] = (
                                f"{id_clauses[actual_end].rstrip()}{spans[0].group(3)}"
                            )
                        curr = "".join(id_clauses)
                        all_matched = True
        elif not all_matched:
            unmatched_indices = [i for i in range(len(spans)) if i not in matched_indices]
            for u_idx in unmatched_indices:
                u_span = spans[u_idx]
                u_open = u_span.group(1)
                u_zh = u_span.group(2).strip()
                u_close = u_span.group(3)
                phs = re.findall(r"\[[A-Za-z0-9_+/.*%-]+\]", u_zh)
                placed = False
                if phs:
                    for ph in phs:
                        for m_ph in re.finditer(rf"\b{re.escape(ph)}\b", curr):
                            before = curr[: m_ph.start()]
                            if before.rfind("<") <= before.rfind(">"):
                                tagged = f"{u_open}{m_ph.group(0)}{u_close}"
                                curr = curr[: m_ph.start()] + tagged + curr[m_ph.end() :]
                                placed = True
                                break
                        if placed:
                            break
                if not placed:
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
                        CTRL = set("╥╆╪╬╉═╧╊╅╈╦╇╋")
                        if any(c in u_open for c in CTRL) and actual_idx == 0 and not any(c in source_zh[:6] for c in CTRL):
                            if len(untagged_indices) > 1:
                                actual_idx = untagged_indices[1]
                        id_clauses[actual_idx] = _wrap_keyword_or_entity(
                            u_open, u_close, u_zh, id_clauses[actual_idx]
                        )
                        curr = "".join(id_clauses)

        if TAG_RE.findall(curr) == tags_in_src or len(TAG_RE.findall(curr)) > len(TAG_RE.findall(result)):
            result = curr

    # 3. Restore untagged control tokens (e.g. ═ before Temporary Level or ╫ between stats)
    GLYPH_KEYWORD_MAP: dict[str, tuple[str, ...]] = {
        "═": ("Temporary Level", "Level Sementara", "Temp Level"),
        "╧": ("Perfect Revive", "Revive", "Resurrect", "Kebangkitan Sempurna", "Bangkit"),
        "╥": ("Arcomia Core", "Akomia Core", "Inti Akomia"),
        "╉": ("Prophet Totem", "Bond Totem", "Rebirth Totem", "Totem"),
        "╬": ("Prepare", "Preparation", "Persiapan"),
        "╆": ("Fleeting", "Instant", "Sekilas"),
        "╋": ("Flash",),
        "╪": ("Initiate", "Engage", "Inisiasi"),
        "╫": ("Deploy", "On Play", "Saat Diterjunkan", "Sacrifice", "Pengorbanan"),
        "╨": ("Deploy", "Sacrifice", "Pengorbanan", "Saat Diterjunkan", "pada-entri"),
        "╈": ("Awaken", "Bangkit"),
        "╦": ("ancient coin", "Ancient Coin", "Merge", "Synthesis", "Combine", "Menggabungkan", "Gabung"),
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
                            rf"(?<!{re.escape(ch)}<color=#FFE897>)"
                            rf"(?<!{re.escape(ch)}<color=#ffffff>)"
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
                    if f"{ch}<b>" in source_zh and f"{ch}<b>" not in result:
                        if "<b>" in result:
                            result = result.replace("<b>", f"{ch}<b>", needed)
                            needed -= min(needed, result.count(f"{ch}<b>"))
                    if needed > 0 and clean_src.startswith(ch):
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

    # CRITICAL: If result already has valid tags, check if it passes validation before stripping
    curr_tags = TAG_RE.findall(result)
    if curr_tags and len(curr_tags) == len(tags_in_src):
        cand = sanitize_target_text(source_zh, result)
        ok, _ = validate_translation(source_zh, cand)
        if ok:
            return normalize_tag_boundary_spacing(source_zh, cand)

    if (
        curr_tags
        and len(curr_tags) < len(tags_in_src)
        and len(curr_tags) % 2 == 0
        and len(tags_in_src) % 2 == 0
    ):
        src_pairs = [(tags_in_src[i], tags_in_src[i + 1]) for i in range(0, len(tags_in_src) - 1, 2)]
        cur_pairs = [(curr_tags[i], curr_tags[i + 1]) for i in range(0, len(curr_tags) - 1, 2)]
        missing_pairs: list[tuple[str, str]] = []
        cur_copy = list(cur_pairs)
        for sp in src_pairs:
            if sp in cur_copy:
                cur_copy.remove(sp)
            else:
                missing_pairs.append(sp)

        STOPWORDS = {
            "memperoleh", "mendapatkan", "dan", "serta", "atau", "saat", "ketika",
            "jika", "pada", "untuk", "dengan", "dari", "ke", "di", "ini", "itu",
            "akan", "dapat", "bisa", "selama", "setiap", "adalah", "sebagai"
        }
        patched_res = result
        for m_open, m_close in missing_pairs:
            m_words = list(re.finditer(r"\b([A-Za-z0-9+%-]+)\b", patched_res))
            for mw in m_words:
                before = patched_res[: mw.start()]
                if before.rfind("<") <= before.rfind(">"):
                    w = mw.group(1)
                    if w.lower() in STOPWORDS:
                        continue
                    patched_res = (
                        patched_res[: mw.start()]
                        + f"{m_open}{w}{m_close}"
                        + patched_res[mw.end() :]
                    )
                    break
        if len(TAG_RE.findall(patched_res)) == len(tags_in_src):
            cand = sanitize_target_text(source_zh, patched_res)
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return normalize_tag_boundary_spacing(source_zh, cand)

    if not tags_in_src:
        cand = sanitize_target_text(source_zh, TAG_RE.sub("", result))
        return normalize_tag_boundary_spacing(source_zh, cand)

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
        first_vis_tok = tokens[vis_indices[0]].strip()
        starts_header = words[0].lower().rstrip(":").rstrip("：") in ("pasif", "aktif", "active", "passive")
        is_header_tok = first_vis_tok.rstrip(":").rstrip("：") in ("被动", "主动", "Pasif", "Aktif")
        if starts_header and is_header_tok and k > 1:
            chunks.append(words[0])
            rem_words = words[1:]
            rem_k = k - 1
            if rem_words:
                n = len(rem_words)
                chunk_size = max(1, n // rem_k)
                for i in range(rem_k):
                    start = i * chunk_size
                    end = (i + 1) * chunk_size if i < rem_k - 1 else n
                    if start < n:
                        chunks.append(" ".join(rem_words[start:end]) if start < end else rem_words[-1])
                    else:
                        chunks.append(rem_words[-1])
            else:
                for _ in range(rem_k):
                    chunks.append(".")
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

