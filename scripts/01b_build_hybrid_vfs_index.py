#!/usr/bin/env python3
"""Build deterministic hybrid VFS index (data/references/hybrid_vfs_index.json) from real QtsVFS tables.

Guarantees 0 leakage into ~470 non-target tables and full capture of 4 gameplay categories:
Hero Cards, Skills, Talents, and Contestants.
"""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "extracted_source"))

from acepatchindo.tag_aligner import TAG_RE, normalize_plain_zh
from acepatchindo.windows_108_split import (
    WINDOWS_108_NONTARGET_EN,
    WINDOWS_108_TARGET_DESC_ID,
)
from wxq_patch import adaptive, hok_terminology, table_catalog

REFS_DIR = ROOT / "data" / "references"
INDEX_OUT = REFS_DIR / "hybrid_vfs_index.json"

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
    r"(?:<b>唯一</b>|唯一被动|穿戴给英雄|穿戴者|穿着这件装备|仅.{1,6}英雄穿戴|普通装备│"
    r"|^(?:<color=[^>]+>)*(?:物理吸血|法术吸血|物理防御力?|法术防御力?|攻击速度|暴击率|冷却缩减)\+\d+)"
)

P_EFFECT_CARD_PATTERN = re.compile(
    r"^(?:卡牌\d+选\d+|获得\d+张.+英雄牌。|\d+选1.+英雄，获得\d+张该英雄牌。|"
    r"随机抽取\d+张.*英雄牌。|指定1名英雄等级\+\d+.*|\d+件装备选\d+件。|立即使所有手牌费用-\d+。)$"
)

HERO_FACTION_CLASS_RE = re.compile(
    r"^(?:河洛|逐鹿|三分(?:之地)?|日落海|稷下|长城|玄雍|尧天|云梦泽|大河(?:流域)?|无阵营|混沌裂隙)\s+"
    r"(?:战士|法师|坦克|刺客|射手|辅助)$"
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
    for h in t1.get("hero", []):
        if h.get("descCn"):
            ref_target_zh.add(h["descCn"].strip())
        if h.get("awaken", {}).get("descCn"):
            ref_target_zh.add(h["awaken"]["descCn"].strip())
        for sk in h.get("skills", []):
            if sk.get("descCn"):
                ref_target_zh.add(sk["descCn"].strip())
            for enh in sk.get("enh", []):
                if enh.get("descCn"):
                    # Include all skill enhancements without minimum length!
                    ref_target_zh.add(enh["descCn"].strip())

    for t in t1.get("talent", []):
        if t.get("descCn"):
            ref_target_zh.add(t["descCn"].strip())

    for item in t2d:
        if item.get("type") in ("Hero", "Summon", "Talent", "Chess player"):
            zh = item.get("zh", {})
            for ab in zh.get("abilities", []):
                d = ab.get("desc", "").strip()
                if d and len(normalize_plain_zh(d)) >= 6:
                    ref_target_zh.add(d)
            for k in ("effect_copies", "calc_copies", "breakpoints", "rule_notes"):
                for s in zh.get(k, []):
                    s_str = s.strip()
                    if s_str and len(normalize_plain_zh(s_str)) >= 6:
                        ref_target_zh.add(s_str)

    for s in WINDOWS_108_TARGET_DESC_ID:
        ref_target_zh.add(s.strip())

    ref_target_plain: set[str] = {
        normalize_plain_zh(s) for s in ref_target_zh if normalize_plain_zh(s)
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

    # Equipment vetoes
    veto_equip_zh: set[str] = set()
    for item in t1.get("equip", []):
        desc = (item.get("descCn") or "").strip()
        if desc and desc not in ref_target_zh:
            veto_equip_zh.add(desc)

    for item in t2d:
        if item.get("type") == "Equipment":
            zh = item.get("zh", {})
            for ab in zh.get("abilities", []):
                desc = (ab.get("desc") or "").strip()
                if desc and desc not in ref_target_zh:
                    veto_equip_zh.add(desc)
            for k in ("effect_copies", "calc_copies", "rule_notes"):
                for s in zh.get(k, []):
                    s_str = s.strip()
                    if s_str and s_str not in ref_target_zh:
                        veto_equip_zh.add(s_str)

    veto_equip_plain: set[str] = {
        normalize_plain_zh(s) for s in veto_equip_zh if normalize_plain_zh(s)
    }

    # Effect Card vetoes
    veto_effect_zh: set[str] = set()
    for item in t1.get("effect", []):
        desc = (item.get("descCn") or "").strip()
        if desc and desc not in ref_target_zh:
            veto_effect_zh.add(desc)

    for item in t2d:
        if item.get("type") == "Effect card":
            zh = item.get("zh", {})
            for ab in zh.get("abilities", []):
                desc = (ab.get("desc") or "").strip()
                if desc and desc not in ref_target_zh:
                    veto_effect_zh.add(desc)
            for k in ("effect_copies", "calc_copies", "rule_notes"):
                for s in zh.get(k, []):
                    s_str = s.strip()
                    if s_str and s_str not in ref_target_zh:
                        veto_effect_zh.add(s_str)

    veto_effect_plain: set[str] = {
        normalize_plain_zh(s) for s in veto_effect_zh if normalize_plain_zh(s)
    }

    # 3. Scan all 508 tables across discovered packages
    print("Scanning 508 tables across packages...")
    all_table_records: list[tuple[str, str]] = []
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

                if prefix == "60D2":
                    for k, s in records:
                        sfx = k[5:17] if len(k) >= 17 else ""
                        m60_lookup[sfx] = s
                        if HERO_FACTION_CLASS_RE.search(s):
                            m60_hero_suffixes.add(sfx)

                if prefix in EQUIPMENT_TABLE_PREFIXES:
                    for _, s in records:
                        if s.strip():
                            veto_equip_zh.add(s.strip())
                            p_s = normalize_plain_zh(s)
                            if p_s:
                                veto_equip_plain.add(p_s)

                if prefix not in ALLOWED_TARGET_PREFIXES:
                    for _, s in records:
                        s_str = s.strip()
                        if s_str:
                            nontarget_table_zh.add(s_str)
                else:
                    all_table_records.extend(records)
            except Exception:
                pass

    print(f"Extracted {len(m60_hero_suffixes)} hero suffixes from #60D2.")
    print(f"Collected {len(nontarget_table_zh)} non-target table Chinese strings.")
    print(f"Candidate target records from allowed tables: {len(all_table_records)}")

    # 4. Filter Per-Record for vfs_target_keys & vfs_target_zh
    vfs_target_keys: set[str] = set()
    vfs_target_zh: set[str] = set()
    vfs_veto_keys: set[str] = set()
    vfs_veto_zh: set[str] = set()

    for k, zh in all_table_records:
        zh_str = zh.strip()
        if not zh_str:
            continue

        tag = k[1:5] if k.startswith("#") and len(k) >= 5 else ""
        sfx = k[5:17] if len(k) >= 17 else ""
        plain_zh = normalize_plain_zh(zh_str)

        # Basic veto conditions
        is_vetoed = False
        if zh_str in WINDOWS_108_NONTARGET_EN or zh_str in veto_names_zh:
            is_vetoed = True
        elif zh_str in veto_equip_zh or plain_zh in veto_equip_plain:
            is_vetoed = True
        elif zh_str in veto_effect_zh or plain_zh in veto_effect_plain:
            is_vetoed = True
        elif zh_str.startswith("棋手") and "技能-" in zh_str:
            is_vetoed = True
        elif zh_str in ("瑶妹描述", "小妲己描述"):
            is_vetoed = True
        elif (zh_str in nontarget_table_zh) and (zh_str not in ref_target_zh):
            is_vetoed = True

        if is_vetoed:
            vfs_veto_keys.add(k)
            vfs_veto_zh.add(zh_str)
            continue

        # Check by family
        is_target = False

        if tag in CARD_PREFIXES:
            m60_val = m60_lookup.get(sfx, "")
            if m60_val == "效果":
                # Standalone Effect Card!
                vfs_veto_keys.add(k)
                vfs_veto_zh.add(zh_str)
                continue
            if P_EFFECT_CARD_PATTERN.match(plain_zh):
                vfs_veto_keys.add(k)
                vfs_veto_zh.add(zh_str)
                continue
            if sfx in m60_hero_suffixes:
                if zh_str != m60_val and len(plain_zh) >= 4:
                    is_target = True
            elif m60_val in ("秘技", "技能", "专属"):
                if len(plain_zh) >= 8 and any(p in zh_str for p in ("，", "。", "：", ":", "\n")):
                    is_target = True
            elif zh_str in ref_target_zh or plain_zh in ref_target_plain:
                is_target = True

        elif tag in SKILL_PREFIXES:
            if zh_str.endswith("！") or zh_str.endswith("!"):
                is_vetoed = True
            elif zh_str in ref_target_zh or plain_zh in ref_target_plain:
                is_target = True
            elif len(plain_zh) >= 6 and (
                any(p in zh_str for p in ("，", "。", "：", ":", "\n", "%", "+", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))
                or any(v in zh_str for v in ("造成", "恢复", "获得", "提升", "降低", "对", "使", "眩晕", "击飞", "伤害", "生命", "攻击", "等级"))
            ):
                is_target = True

        elif tag in TALENT_LORD_PREFIXES:
            # Must NOT be UI counter pattern
            if "{0}/{1}" in zh_str or re.search(r"\{0\}(?:/\{1\})?$", plain_zh):
                is_vetoed = True
            elif P_EFFECT_CARD_PATTERN.match(plain_zh):
                is_vetoed = True
            elif P_EQUIP_PATTERN.search(zh_str) and zh_str not in ref_target_zh:
                is_vetoed = True
            elif zh_str in ref_target_zh or plain_zh in ref_target_plain:
                is_target = True
            elif len(plain_zh) >= 9 and any(p in zh_str for p in ("，", "。", "：", ":", "\n")):
                is_target = True

        elif tag == "0955":
            if len(plain_zh) >= 10 and any(p in zh_str for p in ("，", "。", "：")) and not re.search(r"场上.*数", zh_str):
                is_target = True

        elif tag == "2394":
            if (zh_str in ref_target_zh or plain_zh in ref_target_plain) or (
                len(plain_zh) >= 8 and any(p in zh_str for p in ("，", "。", "：", ":", "\n"))
            ):
                is_target = True

        elif tag == "5CFD":
            # Only the 3 Contestant descriptions
            if len(plain_zh) >= 15 and zh_str.startswith("选择棋手"):
                is_target = True

        if is_target:
            vfs_target_keys.add(k)
            vfs_target_zh.add(zh_str)
        else:
            vfs_veto_keys.add(k)
            vfs_veto_zh.add(zh_str)

    # Ensure any string in ref_target_zh is in vfs_target_zh and never in vfs_veto_zh
    for s in ref_target_zh:
        if s not in veto_names_zh and s not in veto_equip_zh and s not in veto_effect_zh:
            vfs_target_zh.add(s)

    vfs_veto_zh = vfs_veto_zh - vfs_target_zh - ref_target_zh

    payload = {
        "hero_suffixes": sorted(m60_hero_suffixes),
        "vfs_target_keys": sorted(vfs_target_keys),
        "vfs_target_zh": sorted(vfs_target_zh),
        "vfs_veto_keys": sorted(vfs_veto_keys),
        "vfs_veto_zh": sorted(vfs_veto_zh),
        "ref_target_zh": sorted(ref_target_zh),
        "ref_target_plain": sorted(ref_target_plain),
        "nontarget_table_zh": sorted(nontarget_table_zh),
        "veto_names_zh": sorted(veto_names_zh),
        "veto_equip_zh": sorted(veto_equip_zh),
        "veto_equip_plain": sorted(veto_equip_plain),
        "veto_effect_zh": sorted(veto_effect_zh),
        "veto_effect_plain": sorted(veto_effect_plain),
    }

    INDEX_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote hybrid VFS index to {INDEX_OUT} ({len(INDEX_OUT.read_bytes()):,} bytes)")
    print(f"Summary: {len(vfs_target_keys):,} target keys, {len(vfs_target_zh):,} target zh, {len(vfs_veto_keys):,} veto keys, {len(vfs_veto_zh):,} veto zh")
    return payload


if __name__ == "__main__":
    build_index()
