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
   - UI, Menus, Settings, Lobby, Shop, Tutorials (#D262, #7D6E), Loading Tips (#341F), Events, Missions,
     Achievements (#637E), Quick-Chat, Rank Titles, Cosmetics (#E2B0), General Rules (#A360, #1F89)
   - Exactly the 90 Windows missing non-target strings in WINDOWS_108_NONTARGET_EN
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from acepatchindo.tag_aligner import (
    normalize_formula_skeleton_zh,
    normalize_plain_zh,
)
from acepatchindo.windows_108_split import (
    WINDOWS_108_NONTARGET_EN,
    WINDOWS_108_TARGET_DESC_ID,
)

DEFAULT_INDEX_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "references" / "hybrid_vfs_index.json"
)

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

CARD_TAGS: frozenset[str] = frozenset(
    {"23F7", "8E55", "FBF3", "5AD1", "801D", "BC6D", "5A2E", "1825", "FCC7", "6D3B", "6E60", "60D2"}
)
SKILL_TAGS: frozenset[str] = frozenset(
    {"FCCD", "99AB", "4853", "865D", "CE46"}
)
TALENT_TAGS: frozenset[str] = frozenset(
    {"BCDE", "75CA", "9344", "31CF", "A40D", "BE08", "1632", "E222", "E378", "0977", "BF5A", "CEDB", "0955", "2394", "5CFD"}
)

EQUIPMENT_TAGS: frozenset[str] = frozenset(
    {"ADCF", "D891", "C32E", "1881"}
)
P_UNIT_FLAVOR_RE = re.compile(r"^(?:可爱的小鹿|它最大的职责就是挨打|机器仆从|训练用人偶|404\s*Error)")


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
        self.vfs_target_plain: frozenset[str] = frozenset(
            normalize_plain_zh(s) for s in self.vfs_target_zh if len(normalize_plain_zh(s)) >= 6
        )
        self.vfs_veto_keys: frozenset[str] = frozenset(data.get("vfs_veto_keys", []))
        self.vfs_veto_zh: frozenset[str] = frozenset(data.get("vfs_veto_zh", []))
        self.vfs_veto_sfx: frozenset[str] = frozenset(data.get("vfs_veto_sfx", []))
        self.ref_target_zh: frozenset[str] = frozenset(data.get("ref_target_zh", []))
        self.ref_target_plain: frozenset[str] = frozenset(data.get("ref_target_plain", []))
        self.ref_target_skel: frozenset[str] = frozenset(data.get("ref_target_skel", []))
        self.nontarget_table_zh: frozenset[str] = frozenset(data.get("nontarget_table_zh", []))
        self.veto_names_zh: frozenset[str] = frozenset(data.get("veto_names_zh", []))
        self.veto_equip_zh: frozenset[str] = frozenset(data.get("veto_equip_zh", []))
        self.veto_equip_plain: frozenset[str] = frozenset(data.get("veto_equip_plain", []))
        self.veto_effect_zh: frozenset[str] = frozenset(data.get("veto_effect_zh", []))
        self.veto_effect_plain: frozenset[str] = frozenset(data.get("veto_effect_plain", []))

    def is_target_unique(self, zh_src: str, en_base: str = "") -> bool:
        """Return True if a unique Chinese string is a target gameplay description."""
        zh_clean = zh_src.strip()
        if not zh_clean:
            return False

        # 1. Hard vetoes: non-target 108, training dummy, pure item titles
        if zh_clean in WINDOWS_108_NONTARGET_EN or zh_clean in ("狼牙部落的图腾雕像", "狼牙部落的图腾雕像+"):
            return False
        if P_UNIT_FLAVOR_RE.search(zh_clean):
            return False
        # Standalone Series category headers veto: Keep official English category names
        if re.fullmatch(r"[\u2540-\u257f]?[^，。；：\n]{1,10}系列", zh_clean):
            return False

        p_zh = normalize_plain_zh(zh_clean)

        # 2. Authoritative positive references (checked BEFORE veto_names_zh & nontarget_table_zh!)
        if (
            zh_clean in WINDOWS_108_TARGET_DESC_ID
            or zh_clean in self.ref_target_zh
            or p_zh in self.ref_target_plain
        ):
            return True

        # Check composite series cards: if body is target, card is target
        m_ser = re.match(
            r"^((?:<a\s+href=[^>]+>)?<color=#99DEB0>)([^<]*系列)(</color>(?:</a>)?)\n(.+)$",
            zh_clean,
            flags=re.S,
        )
        if m_ser and self.is_target_unique(m_ser.group(4), en_base):
            return True

        skel_zh = normalize_formula_skeleton_zh(zh_clean)
        if (
            len(p_zh) >= 6
            and skel_zh in self.ref_target_skel
            and zh_clean not in self.nontarget_table_zh
        ):
            return True

        # 3. Known entity/hero/talent names veto
        if zh_clean in self.veto_names_zh:
            return False

        # 4. Hard isolation against all ~470 non-target tables
        if zh_clean in self.nontarget_table_zh:
            return False

        # 5. Target VFS strings
        if zh_clean in self.vfs_target_zh or (len(p_zh) >= 6 and p_zh in self.vfs_target_plain):
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

        # 1. Immediate rejection if not in allowed target prefixes
        if tag not in ALLOWED_TARGET_PREFIXES:
            return False

        if tag == "60D2":
            if not opt_zh:
                return False
            p_zh = normalize_plain_zh(opt_zh)
            if not (
                len(p_zh) >= 8
                and any(p in opt_zh for p in ("，", "。", "：", ":", "\n", "+", "-"))
                and not P_UNIT_FLAVOR_RE.search(p_zh)
                and p_zh not in self.veto_names_zh
            ):
                return False

        if opt_zh:
            if opt_zh in WINDOWS_108_TARGET_DESC_ID or opt_zh in self.ref_target_zh:
                return True
            if (
                opt_zh in WINDOWS_108_NONTARGET_EN
                or opt_zh in self.veto_names_zh
                or opt_zh in self.nontarget_table_zh
            ):
                return False
            if self.is_target_unique(opt_zh, target_en):
                return True

        # 2. Veto check (key or suffix)
        if key in self.vfs_veto_keys or suffix in self.vfs_veto_sfx:
            return False

        # 3. Direct match in target keys from VFS index
        if key in self.vfs_target_keys:
            return True
        if tag in CARD_TAGS - {"60D2"} and suffix in self.hero_suffixes and suffix not in self.vfs_veto_sfx:
            if len(target_en) >= 15:
                return True
        if tag in SKILL_TAGS and suffix not in self.vfs_veto_sfx:
            if len(target_en) >= 18 and not target_en.endswith("!") and "Skill-" not in target_en:
                return True

        return False

    def classify_category(self, zh_src: str, key: str = "") -> str | None:
        """Classify into one of 4 target categories or None."""
        if not self.is_target_unique(zh_src):
            return None

        tag = key[1:5] if key.startswith("#") and len(key) >= 5 else ""
        if tag in CARD_TAGS:
            return "hero_card_desc"
        if tag in EQUIPMENT_TAGS:
            return "equipment_desc"
        if tag in SKILL_TAGS:
            return "skill_desc"
        if tag in TALENT_TAGS:
            return "talent_desc"

        if zh_src in WINDOWS_108_TARGET_DESC_ID:
            return "contestant_desc"
        if any(w in zh_src for w in ("棋手", "秘技", "阿离", "乔汐", "武凤", "常小娥", "安琪拉")):
            return "contestant_desc"
        if any(w in zh_src for w in ("技能", "被动：", "主动：", "物理伤害", "法术伤害")):
            return "skill_desc"
        if any(w in zh_src for w in ("天赋", "强化", "回合")):
            return "talent_desc"

        return "hero_card_desc"


_GLOBAL_HYBRID_CLASSIFIER: HybridClassifier | None = None


def get_hybrid_classifier(index_path: Path | None = None) -> HybridClassifier:
    """Return a cached singleton instance of HybridClassifier."""
    global _GLOBAL_HYBRID_CLASSIFIER
    if _GLOBAL_HYBRID_CLASSIFIER is None or index_path is not None:
        _GLOBAL_HYBRID_CLASSIFIER = HybridClassifier(index_path=index_path)
    return _GLOBAL_HYBRID_CLASSIFIER

