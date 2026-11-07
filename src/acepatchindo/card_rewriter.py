"""Tactical Indonesian Card Rewriter and Canonical Glossary Unifier."""

from __future__ import annotations

import re

# 1. Canonical Mechanics
CANONICAL_MECHANIC_MAP: dict[str, str] = {
    r"\b╪<b>Engage</b>": "╪<b>Initiate</b>",
    r"\b╪<b>Memulai</b>": "╪<b>Initiate</b>",
    r"╪Engage\b": "╪Initiate",
    r"╪Memulai\b": "╪Initiate",
    r"\bEngage\b": "Initiate",
    r"\b╬<b>Preparation</b>": "╬<b>Prepare</b>",
    r"╬Preparation\b": "╬Prepare",
    r"\befek Preparation\b": "efek Prepare",
    r"\bPreparation\b": "Prepare",
    r"\b╧<b>Resurrect</b>": "╧<b>Revive</b>",
    r"\b╧<b>Resurrection</b>": "╧<b>Revive</b>",
    r"\b╧<b>Perfect Resurrection</b>": "╧<b>Perfect Revive</b>",
    r"\b╧<b>Perfect Revival</b>": "╧<b>Perfect Revive</b>",
    r"\b╧<b>Perfect Resurrect</b>": "╧<b>Perfect Revive</b>",
    r"╧Resurrect\b": "╧Revive",
    r"╧Resurrection\b": "╧Revive",
    r"\bAkomia Core\b": "Arcomia Core",
    r"\bCore Akomia\b": "Arcomia Core",
    r"\bdi field\b": "di arena",
    r"\bdi medan tempur\b": "di arena",
    r"\bdi battlefield\b": "di arena",
    r"\bKartu Tactic\b": "Kartu Efek",
    r"\bTactics Card\b": "Kartu Efek",
    r"\bTactic Card\b": "Kartu Efek",
    r"\bkartu Tactic\b": "Kartu Efek",
    r"\bPhysical\s+darah-sucking\b": "Physical Lifesteal",
    r"\bphysical\s+darah-sucking\b": "Physical Lifesteal",
    r"\bMantra\s+darah-sucking\b": "Magic Lifesteal",
    r"\bmantra\s+darah-sucking\b": "Magic Lifesteal",
    r"\bdarah-sucking\b": "Lifesteal",
    r"\bblood-sucking\b": "Lifesteal",
    r"\bblood-smoking\b": "Lifesteal",
    r"\bdia adalah kebal ke control\b": "kebal efek CC",
    r"\bkebal ke control\b": "kebal efek CC",
}

# 2. Canonical Hero Names
CANONICAL_HERO_NAME_MAP: dict[str, str] = {
    r"\bGanjiang Moye\b": "Gan & Mo",
    r"\bBaili Shouyue\b": "Shouyue",
    r"\bZhuge Liang\b": "Kongming",
    r"\bYang Yuhuan\b": "Yuhuan",
    r"\bJiang Ziya\b": "Ziya",
}

# 3. Canonical Faction Names
CANONICAL_FACTION_MAP: dict[str, str] = {
    r"\[Central Plain\]": "[Central Plains]",
    r"\[Sunset Ocean\]": "[Sunset Sea]",
    r"\[Sunset\]": "[Sunset Sea]",
    r"\[Zhulu\]": "[Zhulu Plateau]",
}

# 4. Canonical Related Card Names
CANONICAL_RELATED_CARD_MAP: dict[str, str] = {
    r"\bMelodious Notes\b": "Melody",
    r"\bOpening Overdrive\b": "Early Game Surge",
    r"Famous Blade [•·] Life-Stealer": "Destiny",
    r"\bTier 5 Hero Exchange Vouchers\b": "Tier 5 Hero Voucher",
    r"\bTier 5 Hero Exchange Voucher\b": "Tier 5 Hero Voucher",
    r"\bGlitch Bots\b": "Glitch Robot",
    r"\"Glitch Bots\"": '"Glitch Robot"',
}

# Tier 1 Ambiguity Patterns: Level <N> Hero ... +<M>
LEVEL_N_HERO_RE = re.compile(
    r"\bLevel\s+(\d+|{[^}]+})\s+"
    r"((?:<[^>]+>|[\u2540-\u257f]|[🌀🗡️🛡️⚡🔥✨]|\S+)*\s*Hero\b[^.+;\n]*?)\s*"
    r"\+\s*(\d+|{[^}]+})(?!\s*Level)"
)


def polish_indonesian_card_text(source_zh: str, text_id: str, baseline_en: str = "") -> str:
    """Polish Indonesian card description: fix Tier 1 calques, ambiguities, and canonical locks."""
    if not text_id:
        return text_id

    res = text_id

    # Enforce Related Card Title sync
    for pattern, repl in CANONICAL_RELATED_CARD_MAP.items():
        res = re.sub(pattern, repl, res)

    # Enforce Canonical Hero Names
    for pattern, repl in CANONICAL_HERO_NAME_MAP.items():
        res = re.sub(pattern, repl, res)

    # Enforce Canonical Factions
    for pattern, repl in CANONICAL_FACTION_MAP.items():
        res = re.sub(pattern, repl, res)

    # Enforce Canonical Mechanics
    for pattern, repl in CANONICAL_MECHANIC_MAP.items():
        res = re.sub(pattern, repl, res)

    # Fix Tier 1 "Level <N> Hero ... +<M>" ambiguity
    # e.g. "Level 1 Hero milikmu yang memakai Equipment terbanyak +2" ->
    #      "1 Hero sekutu yang memakai Equipment terbanyak mendapat +2 Level"
    def _fix_level_n_hero(m: re.Match[str]) -> str:
        count = m.group(1)
        hero_desc = m.group(2).strip()
        bonus = m.group(3)
        # Normalize "milikmu" to "sekutu" in card text
        hero_desc = re.sub(r"\bmilikmu\b", "sekutu", hero_desc)
        # Check if hero_desc has "dan ... +1" or similar
        if " dan " in hero_desc and ("Core" in hero_desc or "Akomia" in hero_desc or "Arcomia" in hero_desc):
            parts = hero_desc.split(" dan ", 1)
            return f"{count} {parts[0].strip()} dan {parts[1].strip()} mendapat +{bonus} Level"
        return f"{count} {hero_desc} mendapat +{bonus} Level"

    res = LEVEL_N_HERO_RE.sub(_fix_level_n_hero, res)

    # Specific Tier 1 syntax fixes
    res = re.sub(r"\bSaat memberikan efek CC milikmu\b", "Saat sekutu memberikan efek CC", res)
    res = re.sub(
        r"\bLevel tertinggi\s+(\d+|{[^}]+})\s+Hero\s+(\[[^\]]+\])\s+memperoleh\b",
        r"\1 Hero \2 berlevel tertinggi memperoleh",
        res,
    )
    res = re.sub(
        r"\bLevel tertinggi\s+(\d+|{[^}]+})\s+Hero\b",
        r"\1 Hero berlevel tertinggi",
        res,
    )
    res = re.sub(
        r"\bSaat setiap Round pertama kali menggunakan\b",
        "Pertama kali menggunakan",
        res,
    )
    res = re.sub(
        r"\bsebesar setengah Level 1 Hero lain\b",
        "sebesar setengah Level dari 1 Hero sekutu lain",
        res,
    )
    res = re.sub(
        r"\bmendapat Level\s+\+(\d+)\b",
        r"mendapat +\1 Level",
        res,
    )
    res = re.sub(
        r"\bLevel\s*:\s*\+(\d+)\b",
        r"+\1 Level",
        res,
    )

    # Clean double spaces
    res = re.sub(r" {2,}", " ", res)
    return res


def rewrite_en_card_to_id(source_zh: str, baseline_en: str) -> str:
    """Translate and restructure non-Tier-1 English card text into natural Indonesian."""
    if not baseline_en:
        return baseline_en

    text = baseline_en

    # Sync canonical proper names first
    for pattern, repl in CANONICAL_RELATED_CARD_MAP.items():
        text = re.sub(pattern, repl, text)
    for pattern, repl in CANONICAL_HERO_NAME_MAP.items():
        text = re.sub(pattern, repl, text)
    for pattern, repl in CANONICAL_FACTION_MAP.items():
        text = re.sub(pattern, repl, text)
    for pattern, repl in CANONICAL_MECHANIC_MAP.items():
        text = re.sub(pattern, repl, text)

    # Fix broken calques from lexicon_id.py
    # 1. "Record" verb -> Mencatat (never Rekor)
    text = re.sub(r"\bRecord all\b", "Mencatat semua", text, flags=re.I)
    text = re.sub(r"\bRecord\b", "Mencatat", text)

    # 2. "from now on" -> mulai sekarang (never dari Sekarang pada)
    text = re.sub(r"\bFrom now on,?\s*", "Mulai sekarang, ", text, flags=re.I)
    text = re.sub(r"\bfrom now on\b", "mulai sekarang", text, flags=re.I)

    # 3. "these Cards" / "this Card" -> Kartu ini (never ini Kartu)
    text = re.sub(r"\bthese Cards\b", "Kartu ini", text, flags=re.I)
    text = re.sub(r"\bthis Card\b", "Kartu ini", text, flags=re.I)

    # 4. "next Round" / "of the next Round" -> Round berikutnya (never berikutnya Round)
    text = re.sub(r"\bof the next Round\b", "pada Round berikutnya", text, flags=re.I)
    text = re.sub(r"\bnext Round\b", "Round berikutnya", text, flags=re.I)

    # 5. "connected Hero" -> Hero yang terhubung (never terhubung Hero)
    text = re.sub(r"\b(?:connected|linked)\s+Hero\b", "Hero yang terhubung", text, flags=re.I)

    # 6. "nearest enemy" -> musuh terdekat (never terdekat musuh)
    text = re.sub(r"\bnearest enemy\b", "musuh terdekat", text, flags=re.I)

    # 7. "original location" -> lokasi awal (never asli lokasi)
    text = re.sub(r"\boriginal location\b", "lokasi awal", text, flags=re.I)

    # 8. "your Heroes gain N" -> Hero sekutu mendapat +N
    text = re.sub(r"\byour Heroes gain\s+(\d+)\b", r"Hero sekutu mendapat +\1", text, flags=re.I)
    text = re.sub(r"\ballied heroes gain\s+(\+?\d+%?)\b", r"Hero sekutu mendapat \1", text, flags=re.I)

    # 9. "Heroes that survive Combat retain" -> Hero yang bertahan hidup saat Combat mempertahankan
    text = re.sub(
        r"\bHeroes that survive Combat retain\b",
        "Hero yang bertahan hidup saat Combat mempertahankan",
        text,
        flags=re.I,
    )

    # 10. "little dodder" -> Xiao Tu
    text = re.sub(r"\blittle dodder\b", "Xiao Tu", text, flags=re.I)

    # 11. "Draw" in match context -> Seri (never Menarik)
    text = re.sub(r"\bDraw\b", "Seri", text)

    # 12. "Mystical Power" -> Mystical Power (never Mystical Kekuatan / Misterius Kekuatan)
    text = re.sub(r"\bMystical Kekuatan\b", "Mystical Power", text, flags=re.I)
    text = re.sub(r"\bMisterius Kekuatan\b", "Mystical Power", text, flags=re.I)

    # 13. Common structured card verbs:
    text = re.sub(r"\bGain\s+(\d+)\s+([A-Za-z0-9 ·•\-\[\]]+)\.", r"Memperoleh \1 \2.", text)
    text = re.sub(r"\bGain\s+(\d+)\s+([A-Za-z0-9 ·•\-\[\]]+)", r"Memperoleh \1 \2", text)
    text = re.sub(r"\bRestore\s+(\d+)\{LordHp\}\.", r"Memulihkan \1 {LordHp}.", text)
    text = re.sub(r"\bRestore\s+(\d+)\{LordHp\}", r"Memulihkan \1 {LordHp}", text)
    text = re.sub(r"\bAfter use,?\s*", "Setelah digunakan, ", text, flags=re.I)
    text = re.sub(r"\bcreates a clone at\b", "menciptakan clone di", text, flags=re.I)
    text = re.sub(r"\bwith 30% Max HP\b", "dengan 30% Max HP", text, flags=re.I)
    text = re.sub(r"\bUpon death,?\s*", "Saat gugur, ", text, flags=re.I)
    text = re.sub(r"\bit stuns\b", "memberikan stun kepada", text, flags=re.I)
    text = re.sub(r"\bThe clone cannot Attack\b", "Clone tidak dapat Attack", text, flags=re.I)
    text = re.sub(r"\band taunts the nearest enemy for\b", "dan memprovokasi musuh terdekat selama", text, flags=re.I)
    text = re.sub(r"\bupon creation\b", "saat diciptakan", text, flags=re.I)

    return polish_indonesian_card_text(source_zh, text, baseline_en)
