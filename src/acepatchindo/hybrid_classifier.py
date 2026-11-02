"""Hybrid Gameplay Edition Classifier for Honor of Kings Ace Indonesian Patcher.

Strictly classifies catalog strings into:
1. Target gameplay descriptions (Indonesian):
   - Hero Cards (including On Play, Sacrifice, Prepare, Awaken, card mechanics)
   - Skills (Hero Skills, collapsed short summaries, Lv.10/40/100 enhancements, Combine/Summon Skills)
   - Talents (Standard, Contestant Lv.6 Exclusive, Mode/Brawl/Class Talents, Talent Cards)
   - Contestants (Active/passive skills, Secret Art rules, Secret Art Cards, ability cards)
   - Exactly the 18 Windows missing gameplay descriptions in WINDOWS_108_TARGET_DESC_ID
2. Everything else (Strictly English):
   - Standalone Names/Titles (Hero, Skill, Talent, Lord, Equipment, Effect Card names)
   - Equipment items and summaries (#ADCF, #D891, #C32E, #1881)
   - Standalone Effect Cards
   - UI, Menus, Settings, Lobby, Shop, Tutorials, Loading Tips (#341F), Events, Missions,
     Achievements (#637E), Quick-Chat, Rank Titles, Cosmetics (#E2B0), General Rules (#A360, #1F89)
   - Exactly the 90 Windows missing non-target strings in WINDOWS_108_NONTARGET_EN
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from acepatchindo.windows_108_split import (
    WINDOWS_108_NONTARGET_EN,
    WINDOWS_108_TARGET_DESC_ID,
)

DEFAULT_INDEX_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "references" / "hybrid_vfs_index.json"
)

CARD_TAGS: frozenset[str] = frozenset(
    {"23F7", "8E55", "FBF3", "5AD1", "801D", "BC6D", "5A2E", "1825", "FCC7", "6D3B", "6E60"}
)
SKILL_TAGS: frozenset[str] = frozenset(
    {"FCCD", "99AB", "4853", "865D", "CE46"}
)
TALENT_TAGS: frozenset[str] = frozenset(
    {"0955", "2394", "BCDE", "7D6E", "5CFD", "D262"}
)
VETO_TAGS: frozenset[str] = frozenset(
    {"ADCF", "D891", "C32E", "1881", "341F", "A360", "1F89", "637E", "E2B0"}
)

NORM_ZH_RE = re.compile(r"[\s\d\[\]【】{}|%pPqQ_.:：,，。！？!#═╬]+")


def normalize_zh_skeleton(s: str) -> str:
    """Strip punctuation, numbers, and tags to allow fuzzy skeleton matching."""
    return NORM_ZH_RE.sub("", s)


class HybridClassifier:
    """Deterministic classifier for Hybrid Gameplay strings."""

    def __init__(self, index_path: Path | None = None) -> None:
        path = index_path or DEFAULT_INDEX_PATH
        if not path.exists():
            raise FileNotFoundError(f"Hybrid VFS index not found at {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        self.hero_suffixes: frozenset[str] = frozenset(data.get("hero_suffixes", []))
        self.vfs_target_keys: frozenset[str] = frozenset(data.get("vfs_target_keys", []))
        self.vfs_target_zh: frozenset[str] = frozenset(data.get("vfs_target_zh", []))
        self.vfs_veto_keys: frozenset[str] = frozenset(data.get("vfs_veto_keys", []))
        self.vfs_veto_zh: frozenset[str] = frozenset(data.get("vfs_veto_zh", []))
        self.ref_target_zh: frozenset[str] = frozenset(data.get("ref_target_zh", []))
        self.ref_target_norm: frozenset[str] = frozenset(data.get("ref_target_norm", []))
        self.veto_names_zh: frozenset[str] = frozenset(data.get("veto_names_zh", []))

    def is_target_unique(self, zh_src: str, en_base: str = "") -> bool:
        """Return True if a unique Chinese string is a target gameplay description."""
        zh_clean = zh_src.strip()
        if not zh_clean:
            return False

        # 1. Hard vetoes: non-target 108, known entity names, VFS vetoes
        if zh_clean in WINDOWS_108_NONTARGET_EN or zh_clean in self.veto_names_zh:
            return False
        if zh_clean in self.vfs_veto_zh:
            return False

        # Short strings <= 4 chars without punctuation/verbs are names or tags
        if len(zh_clean) <= 4 and not any(c in zh_clean for c in "：:。，,!！?？"):
            return False

        # Voice quotes and audio lines stay English
        if zh_clean.endswith("！") or zh_clean.endswith("!") or "技能-" in zh_clean:
            if not ("造成" in zh_clean or "恢复" in zh_clean or "获得" in zh_clean):
                return False

        # 2. Positive inclusions
        if zh_clean in WINDOWS_108_TARGET_DESC_ID:
            return True
        if zh_clean in self.ref_target_zh or normalize_zh_skeleton(zh_clean) in self.ref_target_norm:
            return True
        if zh_clean in self.vfs_target_zh:
            return True

        # Gameplay mechanics pattern matching (Hero skills, combat rules, formulas)
        if any(m in zh_clean for m in ("被动：", "主动：", "被动:", "主动:", "融合技：", "融合技:", "战歌：")):
            return True
        if re.search(r"\[\d+p\d+q\d+[^\]]*\]", zh_clean) or re.search(r"\[[0-9]\]%", zh_clean):
            return True
        if any(
            kw in zh_clean
            for kw in (
                "物理伤害", "法术伤害", "真实伤害",
                "物理攻击力", "法术攻击力", "物理攻击", "法术攻击",
                "物理防御", "法术防御",
                "临时等级", "真实等级", "英雄等级",
                "生命值", "最大生命", "法力值", "护盾",
                "回合开始时", "回合结束时", "战斗开始时",
                "英雄牌", "连续施法", "共战时", "战歌：",
                "牺牲", "召唤",
            )
        ):
            return True

        return False

    def is_target_update(
        self,
        asset_hex: str,
        key: str,
        prev_en: str,
        target_en: str,
        opt_zh: str = "",
    ) -> bool:
        """Return True if an english_updates row belongs to target gameplay descriptions."""
        tag = key[1:5] if key.startswith("#") and len(key) >= 5 else ""
        suffix = key[5:17] if key.startswith("#") and len(key) >= 17 else ""

        # 1. Veto checks
        if key in self.vfs_veto_keys or tag in VETO_TAGS:
            return False
        if opt_zh and (
            opt_zh in self.veto_names_zh
            or opt_zh in WINDOWS_108_NONTARGET_EN
            or opt_zh in self.vfs_veto_zh
        ):
            return False

        # 2. Direct VFS key match
        if key in self.vfs_target_keys:
            return True

        # 3. Card table family (Hero cards matching 425 hero suffixes)
        if tag in CARD_TAGS and suffix in self.hero_suffixes:
            if opt_zh:
                if len(opt_zh) >= 10 and not opt_zh.startswith("效果") and not opt_zh.startswith("装备"):
                    return True
            elif len(target_en) >= 20:
                return True

        # 4. True skill tables
        if tag in SKILL_TAGS:
            if opt_zh:
                if len(opt_zh) >= 10 and not opt_zh.endswith("！") and not opt_zh.endswith("!"):
                    return True
            elif len(target_en) >= 20 and not target_en.endswith("!"):
                return True

        # 5. Talent tables
        if tag in TALENT_TAGS:
            if opt_zh:
                if len(opt_zh) >= 10:
                    return True
            elif len(target_en) >= 20:
                return True

        # 6. Fallback to Chinese string classification
        if opt_zh and self.is_target_unique(opt_zh, target_en):
            return True

        return False

    def classify_category(self, zh_src: str, key: str = "") -> str | None:
        """Classify into one of 4 target categories or None."""
        if not self.is_target_unique(zh_src):
            return None

        tag = key[1:5] if key.startswith("#") and len(key) >= 5 else ""
        if tag in CARD_TAGS:
            return "hero_card_desc"
        if tag in SKILL_TAGS:
            return "skill_desc"
        if tag in TALENT_TAGS:
            return "talent_desc"

        if zh_src in WINDOWS_108_TARGET_DESC_ID:
            return "contestant_desc"
        if any(w in zh_src for w in ("棋手", "秘技", "阿离", "乔汐", "武凤", "常小娥")):
            return "contestant_desc"
        if any(w in zh_src for w in ("技能", "被动：", "主动：", "物理伤害", "法术伤害")):
            return "skill_desc"
        if any(w in zh_src for w in ("天赋", "强化", "回合")):
            return "talent_desc"

        return "hero_card_desc"
