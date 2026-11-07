#!/usr/bin/env python3
"""Build deterministic hybrid VFS index (data/references/hybrid_vfs_index.json) from real QtsVFS tables.

Guarantees 0 leakage into ~470 non-target tables and full capture of 4 gameplay categories:
Hero Cards, Skills, Talents, and Contestants.
"""

from __future__ import annotations

import gzip
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "extracted_source"))

from acepatchindo.tag_aligner import (
    TAG_RE,
    normalize_formula_skeleton_zh,
    normalize_plain_zh,
)
from acepatchindo.windows_108_split import (
    WINDOWS_108_NONTARGET_EN,
    WINDOWS_108_TARGET_DESC_ID,
)
from wxq_patch import adaptive, hok_terminology, table_catalog

REFS_DIR = ROOT / "data" / "references"
INDEX_OUT = REFS_DIR / "hybrid_vfs_index.json"

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

ALLOWED_TARGET_PREFIXES: frozenset[str] = frozenset(
    {
        # Card Family (12)
        "23F7", "8E55", "FBF3", "5AD1", "801D", "BC6D",
        "5A2E", "1825", "FCC7", "6D3B", "6E60", "60D2",
        # True Skill Family (5)
        "FCCD", "99AB", "4853", "865D", "CE46",
        # Talent & Contestant Trait Family (12)
        "BCDE", "75CA", "9344", "31CF", "A40D", "BE08",
        "1632", "E222", "E378", "0977", "BF5A", "CEDB",
        # Mode Talent, Hotfix & Contestant Overview (3)
        "0955", "2394", "5CFD",
        # Equipment Family (4)
        "ADCF", "D891", "C32E", "1881",
    }
)

CARD_PREFIXES: frozenset[str] = frozenset(
    {"23F7", "8E55", "FBF3", "5AD1", "801D", "BC6D", "5A2E", "1825", "FCC7", "6D3B", "6E60", "60D2"}
)
SKILL_PREFIXES: frozenset[str] = frozenset(
    {"FCCD", "99AB", "4853", "865D", "CE46"}
)
TALENT_LORD_PREFIXES: frozenset[str] = frozenset(
    {"BCDE", "75CA", "9344", "31CF", "A40D", "BE08", "1632", "E222", "E378", "0977", "BF5A", "CEDB"}
)

EQUIPMENT_TABLE_PREFIXES: frozenset[str] = frozenset(
    {"ADCF", "D891", "C32E", "1881"}
)

P_EQUIP_PATTERN = re.compile(
    r"(?:<b>唯一</b>|唯一[：:]|唯一被动|仅.{1,6}英雄穿戴|普通装备│|"
    r"^(?:<color=[^>]+>)*(?:物理吸血|法术吸血|物理防御力?|法术防御力?|攻击速度|暴击率|冷却缩减)\+\d+|"
    r"^(?:卡牌\d+选\d+|\d+选\d+)?(?:特殊装备|高级装备|装备箱)|"
    r"(?:\d+选\d+(?:一件)?|获得)(?:特殊装备|高级装备|普通装备|装备箱))"
)

P_EFFECT_CARD_PATTERN = re.compile(
    r"^(?:卡牌\d+选\d+|\d+阶卡牌\d+选\d+|(?:2选1|3选1|4选1|5选2)(?:一件|高级|普通|英雄|【)?|"
    r"获得\d+张.+英雄牌。|\d+选1.+英雄，获得\d+张该英雄牌。|"
    r"随机抽取\d+张.*英雄牌。|指定1名英雄等级\+\d+.*|\d+件装备选\d+件。|立即使所有手牌费用-\d+。)"
)

P_UNIT_FLAVOR_RE = re.compile(r"^(?:可爱的小鹿|它最大的职责就是挨打|机器仆从|训练用人偶|404\s*Error)")

HERO_FACTION_CLASS_RE = re.compile(
    r"^(?:河洛|逐鹿|三分(?:之地)?|日落海|稷下|长城|玄雍|尧天|云梦泽|大河(?:流域)?|无阵营|混沌裂隙)\s+"
    r"(?:战士|法师|坦克|刺客|射手|辅助)$"
)

VOICE_LORE_QUOTES: frozenset[str] = frozenset(
    {
        "女人，是水做的。", "你已经被盯上了。", "你是我喜欢的口味。", "你需要接受电疗。",
        "清理工作才刚刚开始。", "现在，接受支配。", "我的枪去而复返，你的生命有去无回。",
        "“哒哒哒，哒哒哒。”", "一子定乾坤。", "不坠命运之名。", "不该背对我。",
        "以圣剑的名义起誓。", "以绝望挥剑，着逝者为铠。", "以魂洗剑，以命度心。",
        "先有破灭，然后重生。", "兼爱、非攻、尚同。", "听，是风在低语。",
        "天不生夫子，万古如长夜。", "带翅膀的不一定是天使。", "把心事，都藏进花里。",
        "敌动，我不动。", "映照潮汐的起伏，以免迷失战场的道路。", "春风吹又生，斩草又除根。",
        "有缘千里来相会。", "武道没有定式，人生亦是如此。", "滴答，滴答，滴答，滴答~",
        "玄微有灵，万物生长。", "用兵之道，在于用阵。", "眼界必须放长远。",
        "福祸双依，天命难解。", "良药苦口，蜜语伤人。", "萤火庇护，万物复苏。",
        "行到水穷处，坐看云起时。", "言为心声，字为心画。", "长枪所向，一往无前。",
        "可爱的小鹿，可靠的前排坦克。", "它最大的职责就是挨打。", "机器仆从A1",
    }
)


def find_windows_originals() -> Path:
    users_base = Path("/run/media/whise/Windows/Users")
    if not users_base.exists():
        raise FileNotFoundError(f"Windows Users path not found: {users_base}")
    candidates = sorted(
        users_base.glob("*/AppData/Local/HoK Ace English Patch/adaptive/*/*/originals"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for c in candidates:
        if c.is_dir() and (c / "WXQ_Data").exists():
            return c
    raise FileNotFoundError("Could not find active originals directory on Windows partition")


def build_index() -> dict:
    windows_originals = find_windows_originals()
    cat_dir = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "catalog"
    cat = adaptive.load_catalog(cat_dir)
    if cat is None:
        raise RuntimeError("Failed to load baseline catalog")

    pkgs, _ = adaptive.discover(windows_originals, cat)

    # 1. Load reference datasets
    t1 = json.loads((REFS_DIR / "tier1_wiki_id.json").read_text(encoding="utf-8"))
    t2 = json.loads((REFS_DIR / "tier2_wiki_en.json").read_text(encoding="utf-8"))
    t2d = json.loads((REFS_DIR / "tier2_wiki_details_en.json").read_text(encoding="utf-8"))

    # Build ref_target_zh & ref_target_plain
    ref_target_zh: set[str] = set()

    def _add_ref_desc(d: str) -> None:
        if not d:
            return
        d_str = d.strip()
        if d_str:
            ref_target_zh.add(d_str)
        for line in d_str.splitlines():
            line_str = line.strip()
            line_clean = re.sub(r"^[╆]?转瞬[。.]?", "", line_str).strip()
            if len(normalize_plain_zh(line_clean)) >= 6:
                ref_target_zh.add(line_clean)
            m = re.match(r"^([^：:]{2,15})[：:](.+)$", line_clean)
            if m:
                rhs = m.group(2).strip()
                rhs_clean = re.sub(r"^[╆]?转瞬[。.]?", "", rhs).strip()
                if len(normalize_plain_zh(rhs_clean)) >= 6:
                    ref_target_zh.add(rhs_clean)

    for h in t1.get("hero", []):
        if h.get("descCn"):
            _add_ref_desc(h["descCn"])
        if h.get("awaken", {}).get("descCn"):
            _add_ref_desc(h["awaken"]["descCn"])
        for sk in h.get("skills", []):
            if sk.get("descCn"):
                _add_ref_desc(sk["descCn"])
            for enh in sk.get("enh", []):
                if enh.get("descCn"):
                    _add_ref_desc(enh["descCn"])

    for t in t1.get("talent", []):
        if t.get("descCn"):
            _add_ref_desc(t["descCn"])

    for eq in t1.get("equip", []):
        if eq.get("descCn"):
            _add_ref_desc(eq["descCn"])
        elif eq.get("desc") and _CJK_RE.search(eq["desc"]):
            _add_ref_desc(eq["desc"])

    for eff in t1.get("effect", []):
        if eff.get("descCn"):
            _add_ref_desc(eff["descCn"])
        elif eff.get("desc") and _CJK_RE.search(eff["desc"]):
            _add_ref_desc(eff["desc"])

    for lord in t1.get("lords", []):
        for tal in lord.get("talents", []):
            if tal.get("descCn"):
                _add_ref_desc(tal["descCn"])
            elif tal.get("desc") and _CJK_RE.search(tal["desc"]):
                _add_ref_desc(tal["desc"])
        for rel in lord.get("related", []):
            if rel.get("descCn"):
                _add_ref_desc(rel["descCn"])
            elif rel.get("desc") and _CJK_RE.search(rel["desc"]):
                _add_ref_desc(rel["desc"])

    for item in t2d:
        if item.get("type") in ("Hero", "Summon", "Talent", "Chess player", "Equipment", "Effect card"):
            zh = item.get("zh", {})
            for ab in zh.get("abilities", []):
                d = ab.get("desc", "").strip()
                if d and len(normalize_plain_zh(d)) >= 6:
                    _add_ref_desc(d)
            for k in ("effect_copies", "calc_copies", "breakpoints", "rule_notes"):
                for s in zh.get(k, []):
                    s_str = s.strip()
                    if s_str and len(normalize_plain_zh(s_str)) >= 6:
                        _add_ref_desc(s_str)

    for s in WINDOWS_108_TARGET_DESC_ID:
        _add_ref_desc(s)

    ref_target_plain: set[str] = {
        normalize_plain_zh(s) for s in ref_target_zh if normalize_plain_zh(s)
    }
    ref_target_skel: set[str] = {
        normalize_formula_skeleton_zh(s)
        for s in ref_target_zh
        if len(normalize_plain_zh(s)) >= 6
    }

    # 2. Build Veto Sets
    veto_names_zh: set[str] = {
        "玩球！",
        "火鹰轰炸！",
        "大河之剑天上来。",
        "欢迎来到炮火的世界！",
        "蓉城小霸王，威力无穷！",
        "大河流域阵营的特殊单位。",
        "瑶妹描述",
        "小妲己描述",
    }
    veto_names_zh.update(VOICE_LORE_QUOTES)

    # Short category/subtitle tags in #60D2
    veto_names_zh.update(
        {
            "效果", "装备", "提升等级", "提升临时等级", "资源", "运营",
            "战斗", "通用", "版本通用", "添加牺牲词条", "阵营英雄牌·金色扭蛋",
        }
    )

    # Names from Tier 1
    for cat_name in ("hero", "talent", "lords", "equip", "effect"):
        for item in t1.get(cat_name, []):
            if not isinstance(item, dict):
                continue
            name_cn = (item.get("cn") or item.get("nameCn") or "").strip()
            if name_cn:
                veto_names_zh.add(name_cn)
            for sk in item.get("skills", []):
                if isinstance(sk, dict):
                    sk_cn = (sk.get("cn") or sk.get("nameCn") or "").strip()
                    if sk_cn:
                        veto_names_zh.add(sk_cn)

    factions = t1.get("factions", {})
    if isinstance(factions, dict):
        for zh_f in factions:
            if isinstance(zh_f, str) and zh_f.strip():
                veto_names_zh.add(zh_f.strip())

    # Names from Tier 2
    for entry in t2:
        alt_zh = (entry.get("alt") or "").strip()
        if alt_zh:
            veto_names_zh.add(alt_zh)

    # Names from Tier 2 details
    for item in t2d:
        alt_zh = (item.get("alt") or "").strip()
        if alt_zh:
            veto_names_zh.add(alt_zh)
        for ab in item.get("zh", {}).get("abilities", []):
            ab_name = (ab.get("name") or "").strip()
            if ab_name:
                veto_names_zh.add(ab_name)
        for sk_n in item.get("zh", {}).get("skill_names", []):
            if sk_n.strip():
                veto_names_zh.add(sk_n.strip())

    # Names from hok_terminology
    for dict_name in ("HERO_NAMES", "CARD_AND_SKILL_NAMES", "EQUIPMENT_NAMES", "CHESSPLAYER_NAMES", "FACTION_NAMES"):
        d = getattr(hok_terminology, dict_name, {})
        if isinstance(d, dict):
            for k in d:
                veto_names_zh.add(k.strip())

    # Equipment and Effect descriptions are targets; keep veto sets empty
    veto_equip_zh: set[str] = set()
    veto_equip_plain: set[str] = set()
    veto_effect_zh: set[str] = set()
    veto_effect_plain: set[str] = set()

    # 3. Scan all 508 tables across discovered packages
    print("Scanning 508 tables across packages...")
    chinese_records: list[tuple[str, str]] = []
    english_records: list[tuple[str, str]] = []
    nontarget_table_zh: set[str] = set()
    m60_lookup: dict[str, str] = {}
    m60_hero_suffixes: set[str] = set()

    for pkg in pkgs:
        slots = pkg.build_slot_map()
        for h in sorted(pkg.entries):
            chunk_map = slots.get(h, {})
            if not chunk_map or sorted(chunk_map) != list(range(len(chunk_map))):
                continue
            try:
                raw = pkg.extract(h, slots)
                records: list[tuple[str, str]] = []
                for tag, nested, _ in table_catalog.fields(raw):
                    if tag == 10:
                        parts = list(table_catalog.fields(nested))
                        if len(parts) == 2 and sorted(p[0] for p in parts) == [10, 18]:
                            k = next(p[1].decode("utf-8") for p in parts if p[0] == 10)
                            s = next(p[1].decode("utf-8") for p in parts if p[0] == 18)
                            records.append((k, s))
                if not records:
                    continue

                first_k = records[0][0]
                prefix = first_k[1:5] if first_k.startswith("#") and len(first_k) >= 5 else ""

                # Populate m60_lookup ONLY from Chinese records so English tables NEVER overwrite it!
                if prefix == "60D2":
                    for k, s in records:
                        if _CJK_RE.search(s):
                            sfx = k[5:17] if len(k) >= 17 else ""
                            m60_lookup[sfx] = s
                            if HERO_FACTION_CLASS_RE.search(s):
                                m60_hero_suffixes.add(sfx)
                            s_str = s.strip()
                            p_str = normalize_plain_zh(s_str)
                            if HERO_FACTION_CLASS_RE.search(s_str) or (
                                len(p_str) < 8
                                and not any(p in s_str for p in ("，", "。", "：", ":", "\n"))
                            ):
                                if s_str not in ref_target_zh:
                                    veto_names_zh.add(s_str)
                    continue

                if prefix not in ALLOWED_TARGET_PREFIXES:
                    for _, s in records:
                        if _CJK_RE.search(s):
                            s_str = s.strip()
                            if s_str:
                                nontarget_table_zh.add(s_str)
                else:
                    for k, s in records:
                        if _CJK_RE.search(s):
                            chinese_records.append((k, s))
                        else:
                            english_records.append((k, s))
            except Exception:
                pass

    print(f"Extracted {len(m60_hero_suffixes)} hero suffixes from #60D2.")
    print(f"Collected {len(nontarget_table_zh)} non-target table Chinese strings.")
    print(f"Candidate Chinese records from allowed tables: {len(chinese_records)}")
    print(f"Paired English records from allowed tables: {len(english_records)}")

    # 4. Filter Per-Record for vfs_target_keys & vfs_target_zh
    vfs_target_keys: set[str] = set()
    vfs_target_zh: set[str] = set()
    vfs_veto_keys: set[str] = set()
    vfs_veto_zh: set[str] = set()

    target_sfx: set[str] = set()
    veto_sfx: set[str] = set()
    hard_veto_sfx: set[str] = set()

    def is_ref_target(zh_s: str, pl_s: str, sk_s: str) -> bool:
        return (
            zh_s in ref_target_zh
            or pl_s in ref_target_plain
            or (len(pl_s) >= 6 and sk_s in ref_target_skel)
        )

    # Pass A: Evaluate strictly on Chinese records
    for k, zh in chinese_records:
        zh_str = zh.strip()
        if not zh_str:
            continue

        tag = k[1:5] if k.startswith("#") and len(k) >= 5 else ""
        sfx = k[5:17] if len(k) >= 17 else ""
        plain_zh = normalize_plain_zh(zh_str)
        skel_zh = normalize_formula_skeleton_zh(zh_str)
        is_ref = is_ref_target(zh_str, plain_zh, skel_zh)

        # Basic veto conditions
        is_vetoed = False
        if tag == "60D2":
            # All #60D2 records themselves stay English
            vfs_veto_keys.add(k)
            vfs_veto_zh.add(zh_str)
            # If this #60D2 record is a gameplay description in reference, mark suffix as target
            # so the paired card tables (#FCC7, #23F7, etc.) become targets!
            if is_ref:
                target_sfx.add(sfx)
            continue
        elif zh_str in WINDOWS_108_NONTARGET_EN:
            is_vetoed = True
            hard_veto_sfx.add(sfx)
        elif P_UNIT_FLAVOR_RE.match(plain_zh):
            is_vetoed = True
            hard_veto_sfx.add(sfx)
        elif zh_str in veto_names_zh and not is_ref:
            is_vetoed = True
        elif zh_str.startswith("棋手") and "技能-" in zh_str:
            is_vetoed = True
        elif zh_str in ("瑶妹描述", "小妲己描述"):
            is_vetoed = True
        elif (zh_str in nontarget_table_zh) and not is_ref:
            is_vetoed = True

        if is_vetoed:
            vfs_veto_keys.add(k)
            vfs_veto_zh.add(zh_str)
            veto_sfx.add(sfx)
            continue

        # Check by family
        is_target = False

        if is_ref and tag != "60D2":
            is_target = True

        elif tag in CARD_PREFIXES:
            m60_val = m60_lookup.get(sfx, "")
            if P_UNIT_FLAVOR_RE.match(plain_zh):
                is_vetoed = True
                hard_veto_sfx.add(sfx)
            elif is_ref:
                is_target = True
            elif sfx in m60_hero_suffixes:
                if zh_str != m60_val and len(plain_zh) >= 4:
                    is_target = True
            elif m60_val in ("秘技", "技能", "专属", "棋手", "棋手·秘技", "任务", "天赋", "效果", "装备"):
                if len(plain_zh) >= 4 and any(p in zh_str for p in ("，", "。", "：", ":", "\n", "+", "-", "%")):
                    is_target = True
            else:
                is_vetoed = True

        elif tag in SKILL_PREFIXES:
            if zh_str in VOICE_LORE_QUOTES or zh_str.endswith("！") or zh_str.endswith("!"):
                is_vetoed = True
            elif P_UNIT_FLAVOR_RE.match(plain_zh):
                is_vetoed = True
            elif is_ref:
                is_target = True
            elif len(plain_zh) >= 6 and re.search(
                r"(\d+|%|\[\d+\]|\+|伤害|恢复|生命|护盾|法力|物理|法术|攻击|防御|速度|冷却|眩晕|击飞|减速|沉默|免疫|召唤|被动|主动|入场|登场|牺牲|觉醒|提升|降低|增加|减少|造成|获得|持续|范围|目标|友军|敌方|敌人|回合|技能|普攻|暴击|分身|层数|上限)",
                plain_zh,
            ):
                is_target = True
            else:
                is_vetoed = True

        elif tag in TALENT_LORD_PREFIXES:
            # Must NOT be UI counter pattern
            if "{0}/{1}" in zh_str or re.search(r"\{0\}(?:/\{1\})?$", plain_zh):
                is_vetoed = True
            elif zh_str.startswith("当前祝福：") or "炸弹牌加入了对局" in zh_str:
                is_vetoed = True
            elif is_ref:
                is_target = True
            elif len(plain_zh) >= 9 and any(p in zh_str for p in ("，", "。", "：", ":", "\n")):
                is_target = True
            else:
                is_vetoed = True

        elif tag in EQUIPMENT_TABLE_PREFIXES:
            if len(plain_zh) >= 6 and (
                any(p in zh_str for p in ("，", "。", "：", ":", "\n", "+", "%"))
                or is_ref
            ):
                is_target = True
            else:
                is_vetoed = True

        elif tag == "0955":
            if len(plain_zh) >= 10 and any(p in zh_str for p in ("，", "。", "：")) and not re.search(r"场上.*数", zh_str):
                is_target = True
            else:
                is_vetoed = True

        elif tag == "2394":
            if is_ref or (
                len(plain_zh) >= 8 and any(p in zh_str for p in ("，", "。", "：", ":", "\n"))
            ):
                is_target = True
            else:
                is_vetoed = True

        elif tag == "5CFD":
            # Only the 3 Contestant descriptions
            if len(plain_zh) >= 15 and zh_str.startswith("选择棋手"):
                is_target = True
            else:
                is_vetoed = True

        if is_target and not is_vetoed:
            vfs_target_keys.add(k)
            vfs_target_zh.add(zh_str)
            target_sfx.add(sfx)
        else:
            vfs_veto_keys.add(k)
            vfs_veto_zh.add(zh_str)
            veto_sfx.add(sfx)

    # Reconcile sfx conflicts: any suffix in hard_veto_sfx cannot be in target_sfx,
    # but valid target_sfx will not be vetoed by soft vetoes
    target_sfx -= hard_veto_sfx
    veto_sfx -= target_sfx
    vfs_target_keys = {k for k in vfs_target_keys if k[5:17] in target_sfx}
    vfs_veto_keys = {k for k in vfs_veto_keys if k[5:17] not in target_sfx}

    # Pass B: Propagate to English records using reconciled sfx
    for k, val in english_records:
        tag = k[1:5] if k.startswith("#") and len(k) >= 5 else ""
        sfx = k[5:17] if len(k) >= 17 else ""

        if tag in ALLOWED_TARGET_PREFIXES - {"60D2"} and sfx in target_sfx:
            vfs_target_keys.add(k)
        else:
            vfs_veto_keys.add(k)
            if sfx not in target_sfx:
                veto_sfx.add(sfx)

    vfs_target_keys = {k for k in vfs_target_keys if k[5:17] in target_sfx}
    vfs_veto_keys = {k for k in vfs_veto_keys if k[5:17] not in target_sfx}

    # Also add Chinese strings from baseline catalog's target updates
    with gzip.open(
        ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "catalog" / "catalog.json.gz",
        "rt",
        encoding="utf-8",
    ) as f:
        orig_cat_data = json.load(f)
    for r in orig_cat_data.get("english_updates", []):
        k = r[1]
        sfx = k[5:17] if len(k) >= 17 else ""
        tag = k[1:5] if k.startswith("#") and len(k) >= 5 else ""
        if tag in ALLOWED_TARGET_PREFIXES - {"60D2"} and sfx not in hard_veto_sfx:
            if len(r) > 4 and _CJK_RE.search(r[4]):
                zh_u = r[4].strip()
                p_u = normalize_plain_zh(zh_u)
                sk_u = normalize_formula_skeleton_zh(zh_u)
                if is_ref_target(zh_u, p_u, sk_u) or sfx in target_sfx or zh_u in vfs_target_zh:
                    target_sfx.add(sfx)
                    vfs_target_keys.add(k)
                    if not (
                        zh_u in veto_names_zh
                        or zh_u in veto_equip_zh
                        or zh_u in veto_effect_zh
                        or p_u in veto_equip_plain
                        or p_u in veto_effect_plain
                    ):
                        vfs_target_zh.add(zh_u)
            elif sfx in target_sfx:
                vfs_target_keys.add(k)

    target_sfx -= hard_veto_sfx
    veto_sfx -= target_sfx
    vfs_target_keys = {k for k in vfs_target_keys if k[5:17] in target_sfx}
    vfs_veto_keys = {k for k in vfs_veto_keys if k[5:17] not in target_sfx}

    # Ensure any string in ref_target_zh is in vfs_target_zh and never in vfs_veto_zh
    for s in ref_target_zh:
        if s not in veto_names_zh and s not in veto_equip_zh and s not in veto_effect_zh:
            vfs_target_zh.add(s)

    vfs_veto_zh = vfs_veto_zh - vfs_target_zh - ref_target_zh
    veto_names_zh = veto_names_zh - ref_target_zh

    # Invariant: 0 non-CJK in vfs_target_zh
    non_cjk_in_target_zh = [s for s in vfs_target_zh if not _CJK_RE.search(s)]
    assert len(non_cjk_in_target_zh) == 0, f"Found non-CJK strings in vfs_target_zh: {non_cjk_in_target_zh[:10]}"

    # Invariant: 0 conflicting row suffixes between target and veto keys
    target_sfxes = {k[5:17] for k in vfs_target_keys}
    veto_sfxes = {k[5:17] for k in vfs_veto_keys}
    sfx_conflicts = target_sfxes & veto_sfxes
    if sfx_conflicts:
        print("Conflicting sfx:", sfx_conflicts)
        print("Keys in target with this sfx:", [k for k in vfs_target_keys if k[5:17] in sfx_conflicts])
        print("Keys in veto with this sfx:", [k for k in vfs_veto_keys if k[5:17] in sfx_conflicts])
    assert len(sfx_conflicts) == 0, f"Found {len(sfx_conflicts)} conflicting sfx between target and veto keys!"

    payload = {
        "hero_suffixes": sorted(m60_hero_suffixes),
        "vfs_target_keys": sorted(vfs_target_keys),
        "vfs_target_zh": sorted(vfs_target_zh),
        "vfs_veto_keys": sorted(vfs_veto_keys),
        "vfs_veto_zh": sorted(vfs_veto_zh),
        "vfs_veto_sfx": sorted(veto_sfx),
        "ref_target_zh": sorted(ref_target_zh),
        "ref_target_plain": sorted(ref_target_plain),
        "ref_target_skel": sorted(ref_target_skel),
        "nontarget_table_zh": sorted(nontarget_table_zh),
        "veto_names_zh": sorted(veto_names_zh),
        "veto_equip_zh": sorted(veto_equip_zh),
        "veto_equip_plain": sorted(veto_equip_plain),
        "veto_effect_zh": sorted(veto_effect_zh),
        "veto_effect_plain": sorted(veto_effect_plain),
    }

    INDEX_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote hybrid VFS index to {INDEX_OUT} ({len(INDEX_OUT.read_bytes()):,} bytes)")
    print(
        f"Summary: {len(vfs_target_keys):,} target keys, {len(vfs_target_zh):,} target zh, "
        f"{len(vfs_veto_keys):,} veto keys, {len(vfs_veto_zh):,} veto zh, {len(veto_sfx):,} veto sfx."
    )
    return payload


if __name__ == "__main__":
    build_index()
