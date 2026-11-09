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
    r"\bmedan tempur\b": "di arena",
    r"\bMisterius Kekuatan\b": "Kekuatan Misterius",
    r"\bMisteri Kekuatan\b": "Kekuatan Misterius",
    r"\bMysterious Power\b": "Kekuatan Misterius",
    r"\bMystical Power\b": "Kekuatan Misterius",
    r"\bGangguan Robot\b": "Glitch Robot",
    r"\bBroken Robot\b": "Glitch Robot",
    r"\bGlitch Bots\b": "Glitch Robot",
    r"\b2 Renovation\b": "2 Refresh",
    r"\bRound1\s*\{LordHp\}\b": "Round, pulihkan 1 {LordHp}",
    r"\bEternal Waktu Putaran\b": "Eternal Time Loop",
    r"\bdapat rekor 12\b": "dapat merekam 12",
    r"\bterhubung Hero\b": "Hero terhubung",
    r"\bterdekat musuh\b": "musuh terdekat",
    r"\bterjauh musuh\b": "musuh terjauh",
    r"\basli lokasi\b": "lokasi awal",
    r"\bacak Hero\b": "Hero acak",
    r"\bacak musuh\b": "musuh acak",
    r"\bekstra serangan\b": "serangan tambahan",
    r"^Memulai:": "Initiate:",
    r"\bMemulai:": "Initiate:",
    r"\bKartu Tactic(?!\s+Series)\b": "Kartu Efek",
    r"\bTactics Card(?!\s+Series)\b": "Kartu Efek",
    r"\bTactic Card(?!\s+Series)\b": "Kartu Efek",
    r"\bkartu Tactic(?!\s+Series)\b": "Kartu Efek",
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
    r"\bMo Xie\b": "Gan & Mo",
    r"\bGeneral Moye\b": "Gan & Mo",
    r"\bBaili Shouyue\b": "Shouyue",
    r"\bZhuge Liang\b": "Kongming",
    r"\bYang Yuhuan\b": "Yuhuan",
    r"\bJiang Ziya\b": "Ziya",
}

# 3. Canonical Faction Names
CANONICAL_FACTION_MAP: dict[str, str] = {
    r"\[Central Plains?\]": "[Central Plains]",
    r"\bCentral Plain(?![sS])\b": "Central Plains",
    r"\[Central Plain\]": "[Central Plains]",
    r"\[Sunset Ocean\]": "[Sunset Sea]",
    r"\[Sunset\]": "[Sunset Sea]",
    r"\[Zhulu\]": "[Zhulu Plateau]",
    r"\[Zhuolu\]": "[Zhulu Plateau]",
    r"\[Zhu Lu\]": "[Zhulu Plateau]",
    r"\[The First Lands\]": "[First Lands]",
    r"\[First Lands?\]": "[First Lands]",
}

# 4. Canonical Related Card Names
CANONICAL_RELATED_CARD_MAP: dict[str, str] = {
    r"\bMelodious Notes\b": "Melody",
    r"\bOpening Overdrive\b": "Early Game Surge",
    r"Famous Blade [•·] Life-Stealer": "Destiny",
    r"\bFamous Blade - Siming\b": "Destiny",
    r"\bFamous Sword Siming\b": "Destiny",
    r"\bFamous Sword - Siming\b": "Destiny",
    r"\bFamous Sword\b": "Destiny",
    r"\bFamous Blade\b": "Destiny",
    r"\bDestiny Totem\b": "Destiny Totem",
    r"\bAfterlife Totem\b": "Afterlife Totem",
    r"\bSeer Totem\b": "Seer Totem",
    r"\bTotem Series\b": "Totem Series",
    r"\bGeneral Series\b": "General Series",
    r"\bArcomia Core Series\b": "Arcomia Core Series",
    r"\bTier 5 Hero Exchange Vouchers\b": "Tier 5 Hero Voucher",
    r"\bTier 5 Hero Exchange Voucher\b": "Tier 5 Hero Voucher",
    r"\bGlitch Bots\b": "Glitch Robot",
    r"\"Glitch Bots\"": '"Glitch Robot"',
    r"\b(?:Lots of Friends|Plenty of Friends)\b": "Many Friends",
}

# Tier 1 Ambiguity Patterns: Level <N> Hero ... +<M>
LEVEL_N_HERO_RE = re.compile(
    r"\bLevel\s+(\d+|{[^}]+})\s+((?:(?:\[[^\]]+\]|<[^>]+>|[\u2540-\u257f]|[🌀🗡️🛡️⚡🔥✨]|\S+)\s+)*?Hero\b[^.+,\n;]*?)\s*\+\s*(\d+|{[^}]+})(?!\s*Level\b)",
    re.IGNORECASE,
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
        r"\b(?:sebesar\s+setengah\s+Level\s+1\s+Hero\s+lain|sebesar\s+setengah\s+Level\s+dari\s+1\s+Hero\s+sekutu\s+lain)\b",
        "setara setengah Level dari 1 Hero lain",
        res,
    )
    res = re.sub(
        r"\b(?:sebesar\s+Level\s+1\s+Hero\s+lain|sebesar\s+Level\s+dari\s+1\s+Hero\s+sekutu\s+lain)\b",
        "setara Level dari 1 Hero lain",
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

    # 1. adalah + verb/adjective
    res = re.sub(r"\badalah\s+rusak\b", "hancur", res, flags=re.I)
    res = re.sub(r"\badalah\s+masuk\s+menjadi\s+Combat\b", "diterjunkan ke pertempuran", res, flags=re.I)
    res = re.sub(r"\badalah\s+(meningkat|berkurang|penuh|aktif|masuk|digandakan|dihapus|dibatasi)\b", r"\1", res, flags=re.I)

    # 2. Inverted Demonstratives & Time Modifiers
    res = re.sub(r"\bsetiap\s+berikutnya\s+Round\b", "setiap Round berikutnya", res, flags=re.I)
    res = re.sub(r"\bberikutnya\s+(Round|Combat|Hero|Kartu|hari|serangan|tembakan|jari\s+teknik)\b", r"\1 berikutnya", res, flags=re.I)
    res = re.sub(r"\bSaat\s+ini\s+Kartu\s+pool\b", "Card Pool saat ini", res, flags=re.I)
    res = re.sub(r"\bsaat\s+ini\s+(Kartu|pertandingan|Round|Level|HP)\b", r"\1 saat ini", res, flags=re.I)
    res = re.sub(r"\bini\s+(Round|Kartu|Efek|unit|pertandingan|Combat|slot|Shield)\b", r"\1 ini", res, flags=re.I)

    # 3. keping dari
    res = re.sub(r"\b(\d+)\s+keping\s+dari\s+", r"\1 ", res, flags=re.I)
    res = re.sub(r"\bkeping\s+dari\s+", "", res, flags=re.I)

    # 4. pembawa dapat menjadi sebuah Hero dari [...] kamp & kamp
    res = re.sub(r"\bpembawa\s+dapat\s+menjadi\s+(?:sebuah\s+)?Hero\s+dari\s*(\[[^\]]+\])\s*kamp\.?", r"Pemakai dapat menjadi Hero Faction \1.", res, flags=re.I)
    res = re.sub(r"\bpembawa\s+dapat\s+menjadi\b", "Pemakai dapat menjadi", res, flags=re.I)
    res = re.sub(r"\bkamp\b", "Faction", res, flags=re.I)

    # 5. pilih X keluar dari Y & Tier
    res = re.sub(r"\bpilih\s+(\d+)\s+keluar\s+dari\s+(\d+)\b", r"pilih \1 dari \2", res, flags=re.I)
    res = re.sub(r"\btinggi-Tier\b", "Tier tinggi", res, flags=re.I)
    res = re.sub(r"\bterendah-Level\b", "Level terendah", res, flags=re.I)

    # 6. Unify Kartu Secret Skill & eliminate duplication
    res = re.sub(
        r"(?:Kartu\s+)?(?:Secret\s+(?:Skill|Art)|rahasia\s+(?:kartu|teknik(?:\s+kartu)?|skill)|Rahasia\s+(?:Teknik|Skill))(?:\s+kartu)?",
        "Kartu Secret Skill",
        res,
        flags=re.I,
    )
    res = re.sub(r"\b(?:Kartu\s+Secret\s+Skill\s+)+", "Kartu Secret Skill ", res, flags=re.I)
    res = re.sub(r"1\s+(<[^>]+>[^<]+</[^>]+>)\s+Kartu Secret Skill\b", r"1 Kartu Secret Skill \1", res)
    res = re.sub(r"1\s+<b>([^<]+)</b>\s+Kartu Secret Skill\b", r"1 Kartu Secret Skill <b>\1</b>", res)

    # Contestant & proper noun mangling elimination
    if "香香" in source_zh:
        res = re.sub(r"\bharum\b", "Xiang", res)
    res = re.sub(r"\bYing Hukum\b", "Ying Lü", res)
    res = re.sub(r"\bQin Lu\b", "Ying Lü", res)
    res = re.sub(r"\bPutih Lagu\b", "Bai Ge", res)
    res = re.sub(r"\bXiao Xiao Little Daji\b", "Little Daji", res)
    res = re.sub(r"\bSun Xiaobin\b", "Little Sun Bin", res)
    res = re.sub(r"\bZhuang Xiaoyu\b", "Little Zhuang Fish", res)
    res = re.sub(r"\bChang Xiao'e\b", "Little Chang'e", res)
    res = re.sub(r"\bAsylum Anak rusa\b", "Deer's Protection", res)
    if "扫拂" in source_zh:
        res = re.sub(r"\b<b>Menyapu</b>", "<b>Strum</b>", res)
        res = re.sub(r"\bmelalui Menyapu\b", "melalui Strum", res)
        res = re.sub(r"\bMenyapu\b", "Strum", res)
    if "横扫" in source_zh:
        res = re.sub(r"\bStrum\b", "Tebasan", res)
        res = re.sub(r"\bMenyapu\s+musuh\s+di\s+depan\b", "Menebas musuh di depan", res)

    # Control token & canonical mechanic normalization
    res = re.sub(r"(╥\s*)(<b>)?(?:Almia|Accomia|Acomia|Arcomia)\s*Core", r"\1\g<2>Arcomia Core", res, flags=re.I)
    res = re.sub(r"\b(?:Almia|Accomia|Acomia)\s*Core\b", "Arcomia Core", res, flags=re.I)
    res = re.sub(r"ditetapkan\s+Core\s+Level\s+dari\s+Accomia", "Level Arcomia Core", res, flags=re.I)
    res = re.sub(r"╥\s+(?:(<b>))?Arcomia\s*Core", lambda m: "╥<b>Arcomia Core" if m.group(1) else "╥Arcomia Core", res)

    res = re.sub(
        r"(╪\s*)(<b>)?(?:Bentrokan|Clash|Confrontation|Memulai|ke\s+mulai|Initiate|dan\s+(?:dimulai|mulai)\s+sebuah\s+(?:tim|grup)|Initiate\s+sebuah\s+(?:tim|grup)|sebuah\s+(?:tim|grup))\b",
        r"\1\g<2>Initiate",
        res,
        flags=re.I,
    )
    if "交锋" in source_zh:
        res = re.sub(r"(<b>)?\bBentrokan\b(</b>)?", r"\g<1>Initiate\g<2>", res)

    res = re.sub(r"(╨\s*)(<b>)?(?:dan\s+Deploy|Deploy)\b", r"\1\g<2>Deploy", res, flags=re.I)
    res = re.sub(r"(╬\s*)(<b>)?(?:Siap|Ready|Preparation|Prepare)\b", r"\1\g<2>Prepare", res, flags=re.I)

    res = re.sub(
        r"(╧\s*)(<b>)?(?:Sempurna\s+pemulihan\.?|Perfect\s+recovery\.?|Perfect\s+Revive|secara\s+sempurna\s+bangkit\s+kembali)\b",
        r"\1\g<2>Perfect Revive",
        res,
        flags=re.I,
    )
    res = re.sub(
        r"(╧\s*)(<b>)?(?:bangkit\s+kembali|Recovery|Resurrect|Resurrection|Revive|Di-revive)\b",
        r"\1\g<2>Revive",
        res,
        flags=re.I,
    )

    res = re.sub(r"╆\s*(<b>)?(?:Instant|Fleeting)\b", r"╆\g<1>Fleeting", res, flags=re.I)
    res = re.sub(r"╆\s*Kartu\s+Hero\s+acak\s+Fleeting\b", "╆Fleeting Kartu Hero acak", res, flags=re.I)
    res = re.sub(r"╆\s*Kartu\s+Hero\s+Fleeting\b", "╆Fleeting Kartu Hero", res, flags=re.I)
    res = re.sub(r"╈\s*(<b>)?(?:Exit|Keluar|Retreat|Retire)\b", r"╈\g<1>Retire", res, flags=re.I)
    res = re.sub(r"╦\s*(<b>)?(?:Menggabungkan|Merge|Combine|penggabungan)\b", r"╦\g<1>Combine", res, flags=re.I)

    res = re.sub(r"╊\s*(<b>)?(?:Jiwa\s+Merebut|Soul\s+Snatch|Roh\s+Extraction|Soul\s+Extraction)\b", r"╊\g<1>Soul Snatch", res, flags=re.I)
    res = re.sub(r"╊\s*(<b>)?(?:Merebut|Capture|Plunder|Seizure|Snatch|Steal|dan\s+Steal|capturing\s+entri|merampas)\b", r"╊\g<1>Steal", res, flags=re.I)
    if "夺取" in source_zh:
        res = re.sub(r"(?<!Soul\s)\b(?:Merebut|Capture|Plunder|Seizure|Snatch|merampas)\b", "Steal", res, flags=re.I)
    res = re.sub(r"\bRoh\s+Extraction\b", "Soul Snatch", res, flags=re.I)
    res = re.sub(r"\bke\s+Steal\b", "Steal", res, flags=re.I)

    res = re.sub(r"╫\s*sacrificed\s+Hero\b", "Hero ╫Sacrifice", res, flags=re.I)
    res = re.sub(r"<color=#99DEB0>dan sacrifices</color>", "<color=#99DEB0>Sacrifice</color>", res, flags=re.I)

    # Devour
    res = re.sub(r"╆\s*Melahap\b", "╆Devour", res, flags=re.I)
    res = re.sub(r"╬\s*Super\s+Melahap\b", "╬Super Devour", res, flags=re.I)
    res = re.sub(r"╬\s*Melahap\b", "╬Devour", res, flags=re.I)

    res = re.sub(r"\bProphet\s+Totem\b", "Seer Totem", res, flags=re.I)
    res = re.sub(r"\b(?:Pernikahan|Marriage|Karma)\s+Totem\b", "Bond Totem", res, flags=re.I)
    res = re.sub(r"\b(?:Rebirth|Reincarnation)\s+Totem\b", "Afterlife Totem", res, flags=re.I)
    if "因缘图腾" in source_zh or "姻缘图腾" in source_zh:
        res = re.sub(r"\b(?:Destiny|Ikatan)\s+Totem\b", "Bond Totem", res, flags=re.I)
        res = re.sub(r"\b╉(?:Destiny|Ikatan)\s+Totem\b", "╉Bond Totem", res, flags=re.I)
    if "命运图腾" in source_zh:
        res = re.sub(r"\bDestiny\s+Totem\b", "Fate Totem", res, flags=re.I)
        res = re.sub(r"\b╉Destiny\s+Totem\b", "╉Fate Totem", res, flags=re.I)
        res = re.sub(r"<color=#FFE897>╉Fate\s+╉Totem</color>", "<color=#FFE897>╉Fate Totem</color>", res)

    res = re.sub(r"\b═\s+Level\b", "═Temporary Level", res)

    res = re.sub(
        r"\b(Totem|Steal|Flash|Temporary Level|Arcomia Core|Deploy|Initiate|Sacrifice|Prepare|Low-Tier|Starting Lineup|Ancient Coin|Summon|Combine|Multi-Faction|Contract|Tactics Card|Shield|Effect Card|Factionless|Grassroots|General)\s+Seri\b",
        r"\1 Series",
        res,
        flags=re.I,
    )

    # Demon God cleanup
    res = re.sub(r"\bIblis\s+Max\s+HP\s+Dewa\b", "Max HP Demon God", res, flags=re.I)
    res = re.sub(r"\bIblis\s+HP\s+Dewa\b", "HP Demon God", res, flags=re.I)
    res = re.sub(r"\bIblis\s+menerjang\s+Dewa\s+Kecepatan\b", "kecepatan isi Energi Demon God", res, flags=re.I)
    res = re.sub(r"\bIblis\s+Energi\s+Dewa\b", "Energi Demon God", res, flags=re.I)
    res = re.sub(r"\bIblis\s+pertama\s+Dewa\s+Menyerang\b", "serangan pertama Demon God", res, flags=re.I)
    res = re.sub(r"\bIblis\s+Dewa\s+Slot\b", "slot Demon God", res, flags=re.I)
    res = re.sub(r"\bIblis\s+Dewa\b", "Demon God", res, flags=re.I)
    res = re.sub(r"\bLangit\s+Piercer\b", "Sky Piercer", res, flags=re.I)
    res = re.sub(r"\bTaotie\s+Devours\s+the\s+World\b", "Taotie Annihilation", res, flags=re.I)
    res = re.sub(r"\bTempat(?:kan)?\s+sebuah\s+jarak\s+dekat\s+Hero\b", "Tempatkan Hero melee", res, flags=re.I)
    res = re.sub(r"\bTempat(?:kan)?\s+sebuah\s+jarak\s+jauh\s+Hero\b", "Tempatkan Hero ranged", res, flags=re.I)
    res = re.sub(r"\bTempat(?:kan)?\s+tidak\s+Hero\b", "Tanpa Hero", res, flags=re.I)

    # Equipment, Totem & Series fixes
    res = re.sub(r"\bTerkenal\s+Pedang\s+Siming\b", "Destiny", res, flags=re.I)
    res = re.sub(r"\bMerah\s+Iblis\b", "Red Demon", res, flags=re.I)
    res = re.sub(r"\bTongkat\s+dari\s+Kehampaan\b", "Void Staff", res, flags=re.I)
    res = re.sub(r"\bMurka\s+Savant\b", "Savant's Wrath", res, flags=re.I)
    res = re.sub(r"\bBuku\s+dari\s+Dewa-Eaters\b", "Insatiable Tome", res, flags=re.I)
    res = re.sub(r"\bSabuk\s+Raksasa\b", "Giant's Belt", res, flags=re.I)
    res = re.sub(r"\bBesar\s+Rod\b", "Large Rod", res, flags=re.I)
    res = re.sub(r"\bAnti-Cedera\s+Berat\s+Armor\b", "Thorn Heavy Armor", res, flags=re.I)
    res = re.sub(r"\bOverlord\s+Berat\s+Armor\b", "Overlord's Platemail", res, flags=re.I)
    res = re.sub(r"\bBerat\s+Armor\b", "Heavy Armor", res, flags=re.I)
    res = re.sub(r"\bMenjaga\s+Glory\b", "Guardian's Glory", res, flags=re.I)
    res = re.sub(r"\bGlacial\s+Badai\b", "Glacial Buckler", res, flags=re.I)
    res = re.sub(r"\bAlam\s+baka\s+Totem\b", "Afterlife Totem", res, flags=re.I)
    res = re.sub(r"\b(Totem|General|Arcomia Core)\s+Seri\b", r"\1 Series", res, flags=re.I)
    res = re.sub(r"\[(?:Beracun Ballad - Panjang Lagu|Racun Memulihkan: Lagu dari Panjang)\]", "[Toxic Heal: Song of Longge]", res, flags=re.I)

    # Bracketed wearers: [Sunset Samudra Pemakai] -> [Pemakai Sunset Sea]
    res = re.sub(r"Sunset\s+Samudra", "Sunset Sea", res, flags=re.I)
    res = re.sub(r"\[(?:Sunset Samudra|Sunset Sea)\s+(?:Pemakai|Wearer)\]", "[Pemakai Sunset Sea]", res, flags=re.I)
    res = re.sub(r"\[Central Plains?\s+(?:Pemakai|Wearer)\]", "[Pemakai Central Plains]", res, flags=re.I)
    res = re.sub(r"\[Riverlands\s+(?:Pemakai|Wearer)\]", "[Pemakai Riverlands]", res, flags=re.I)
    res = re.sub(r"\[Zhulu(?: Plateau)?\s+(?:Pemakai|Wearer)\]", "[Pemakai Zhulu Plateau]", res, flags=re.I)
    res = re.sub(r"\[Three Kingdoms\s+(?:Pemakai|Wearer)\]", "[Pemakai Three Kingdoms]", res, flags=re.I)
    res = re.sub(r"\[(?:Factionless|Tanpa Faction)\s+(?:Pemakai|Wearer)\]", "[Pemakai Tanpa Faction]", res, flags=re.I)
    res = re.sub(r"\[([^\]]+?)\s+(?:Pemakai|Wearer)\]", r"[Pemakai \1]", res, flags=re.I)
    res = re.sub(r"\[Jika\s+(?:pemakai|wearer)\s+adalah\s+([^\]]+?)\]", r"[Pemakai \1]", res, flags=re.I)
    res = re.sub(r"\[(?:Pemakai|Wearer)\s+adalah\s+([^\]]+?)\]", r"[Pemakai \1]", res, flags=re.I)
    res = re.sub(r",(?=[<\[A-Za-z])", ", ", res)

    # Hero and voucher calques
    res = re.sub(r"\bsalinan\s+dari\s+Kartu\s+itu\s+Hero\b", "salinan Kartu Hero tersebut", res, flags=re.I)
    res = re.sub(r"\bsalinan\s+dari\s+kartu\s+itu\b", "salinan Kartu Hero tersebut", res, flags=re.I)
    res = re.sub(r"\bKartu\s+itu\s+Hero\b", "Kartu Hero tersebut", res, flags=re.I)
    res = re.sub(r"\bitu\s+Hero\b", "Hero tersebut", res, flags=re.I)

    # Tier 3 calques elimination:
    # 1. off-field / off-board
    res = re.sub(r"\bmati-di arena\b", "yang belum ada di arena", res, flags=re.I)
    res = re.sub(r"\bmati-papan\b", "yang belum ada di arena", res, flags=re.I)
    res = re.sub(r"\bwilayah\s+pada\b", "arena", res, flags=re.I)

    # 2. that is / itu adalah
    res = re.sub(r"\bHero\s+([^.\n]+?)\s+itu\s+adalah\b", r"Hero \1 yang", res, flags=re.I)
    res = re.sub(r"\bjika\s+itu\s+adalah\b", "jika merupakan", res, flags=re.I)
    res = re.sub(r"\bitu\s+adalah\s+tidak\s+lebih\s+(tinggi|rendah)\s+daripada\b", r"yang tidak lebih \1 daripada", res, flags=re.I)
    res = re.sub(r"\bitu\s+adalah\b", "yang", res, flags=re.I)

    # 3. ke <verb> & untranslated remainder
    res = re.sub(r"\bremainder\s+dari\s+pertandingan\b", "sisa pertandingan", res, flags=re.I)
    res = re.sub(r"\bremainder\s+dari\b", "sisa", res, flags=re.I)
    res = re.sub(r"\bpada\s+menarik/mengalahkan\b", "saat Seri/Kalah", res, flags=re.I)
    res = re.sub(
        r"\bke\s+(secara acak|Gunakan|gunakan|Memperoleh|memperoleh|Meningkatkan|meningkatkan|memicu|menyerang|mendapatkan|menjadi|memilih|menyalin|memanggil|enact)\b",
        lambda m: "untuk diberlakukan" if m.group(1).lower() == "enact" else f"untuk {m.group(1).lower()}",
        res,
        flags=re.I,
    )

    # 4. sebuah Acak / <N> Acak / highest-Level
    res = re.sub(
        r"\b(\d+)\s+Acak\s+((?:(?:<[^>]+>|\[[^\]]+\]|[\u2540-\u257f]|\S+)\s+)*?(?:Kartu(?:\s+Hero)?|Hero|Faction|unit|Unit|sinar|buff|permohonan|harapan|item|target|musuh|sekutu))\b",
        r"\1 \2 acak",
        res,
        flags=re.I,
    )
    res = re.sub(
        r"\bsebuah\s+Acak\s+((?:(?:<[^>]+>|\[[^\]]+\]|[\u2540-\u257f]|\S+)\s+)*?(?:Kartu(?:\s+Hero)?|Hero|Faction|unit|Unit|sinar|buff|permohonan|harapan|item|target|musuh|sekutu))\b",
        r"1 \1 acak",
        res,
        flags=re.I,
    )
    res = re.sub(r"\b(\d+)\s+Acak\s+(<[^>]+>[^<]+</[^>]+>)\b", r"\1 \2 acak", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+Acak\s+(<[^>]+>[^<]+</[^>]+>)\b", r"1 \1 acak", res, flags=re.I)
    res = re.sub(r"\b(\d+)\s+Acak\s+([A-Za-z0-9_-]+)\b", r"\1 \2 acak", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+Acak\s+([A-Za-z0-9_-]+)\b", r"1 \1 acak", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+Acak\s+", "1 unit acak ", res, flags=re.I)
    res = re.sub(r"\b(\d+)\s+Acak\b", r"\1 acak", res, flags=re.I)
    res = re.sub(r"1\s+Lainnya\s+tertinggi-Level\s+Hero\s+sekutu\b", "1 Hero sekutu lain berlevel tertinggi", res, flags=re.I)
    res = re.sub(r"\b(\d+)\s+tertinggi-Level\s+Hero\s+(musuh|sekutu)\b", r"\1 Hero \2 berlevel tertinggi", res, flags=re.I)
    res = re.sub(r"\btertinggi-Level\s+Hero\s+(musuh|sekutu)\b", r"Hero \1 berlevel tertinggi", res, flags=re.I)
    res = re.sub(r"\btertinggi-Level\s+(Musuh|sekutu|Hero|unit|Unit|Jarak)\b", r"\1 berlevel tertinggi", res, flags=re.I)
    res = re.sub(r"\btertinggi-Level\b", "berlevel tertinggi", res, flags=re.I)
    res = re.sub(r"\bterendah-Level\b", "berlevel terendah", res, flags=re.I)
    res = re.sub(r"\btertinggi-Tier\b", "Tier tertinggi", res, flags=re.I)
    res = re.sub(r"\bterendah-Tier\b", "Tier terendah", res, flags=re.I)
    res = re.sub(r"\btertinggi-HP\b", "HP tertinggi", res, flags=re.I)
    res = re.sub(r"\bterendah-HP\b", "HP terendah", res, flags=re.I)

    # 5. Possessive pronoun misplacements & fox fire
    res = re.sub(r"(\d+)\s+milikmu/(\d+)", r"\1/\2", res)
    res = re.sub(r"(\d+)\s+mereka%", r"\1%", res)
    res = re.sub(r"\bmenyerang\s+miliknya\s+musuh\b", "menyerang musuh", res, flags=re.I)
    res = re.sub(r"\btarget\s+miliknya\s+musuh\b", "musuh target", res, flags=re.I)
    res = re.sub(r"\bHero\s+kamu\s+sendiri\b", "Hero milikmu", res, flags=re.I)
    res = re.sub(r"\b(\d+)\s+rubah\s+menembakkan\b", r"\1 api rubah", res, flags=re.I)
    res = re.sub(r"\brubah\s+menembakkan\b", "api rubah", res, flags=re.I)
    res = re.sub(r"\b(\d+)\s+fox\s*fires\b", r"\1 api rubah", res, flags=re.I)
    res = re.sub(r"\bfox\s*fires\b", "api rubah", res, flags=re.I)
    res = re.sub(r"\bsecara\s+acak\s+((?:<[^>]+>)*)salinan((?:</[^>]+>)*)\b", r"secara acak \1menyalin\2", res, flags=re.I)

    # 7. Melakukan tidak & terdapat tidak
    res = re.sub(r"\bMelakukan\s+tidak\s+stack\b", "Tidak dapat ditumpuk", res, flags=re.I)
    res = re.sub(r"\bMelakukan\s+tidak\b", "Tidak", res, flags=re.I)
    res = re.sub(r"\bjika\s+terdapat\s+tidak\s+([A-Za-z\[\] ]+?)\s+di\s+(?:Saat\s+ini\s+Kartu|Card)\s+pool\b", r"jika tidak ada \1 di Card Pool saat ini", res, flags=re.I)
    res = re.sub(r"\bterdapat\s+tidak\b", "tidak ada", res, flags=re.I)

    # 8. musim semi -> Spring
    res = re.sub(r"\bsebuah\s+musim\s+semi\b", "1 Spring", res, flags=re.I)
    res = re.sub(r"\bmusim\s+semi\b", "Spring", res, flags=re.I)

    # 9. milikmu% & Qin tambahan Lu hak istimewa
    res = re.sub(r"\bHero\s+mendapatkan\s+(\d+)\s+milikmu%\s*", r"Hero milikmu mendapat +\1% ", res, flags=re.I)
    res = re.sub(r"\bHero\s+mendapatkan\s+sebuah\s+milikmu\s+Ekstra\s+(\d+%?)\s*", r"Hero milikmu mendapat tambahan +\1 ", res, flags=re.I)
    res = re.sub(r"\b(?:Qin\s+tambahan\s+Lu\s+hak\s+istimewa|Edict\s+Enactor\s+Hak\s+istimewa)\b", "Hak istimewa tambahan Ying Lü", res, flags=re.I)
    res = re.sub(r"\bmilikmu%", "%", res, flags=re.I)

    # 11. Eternal Time Loop calque elimination
    res = re.sub(r"\bsebuah\s+lebih\s+tinggi\s+Tier\b", "Tier yang lebih tinggi", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+lebih\s+tinggi\b", "lebih tinggi", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+lebih\s+banyak\s+kuat\b", "yang lebih kuat", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+lebih\s+kuat\b", "yang lebih kuat", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+lebih\b", "lebih", res, flags=re.I)
    res = re.sub(r"\bcapable\s+dari\s+rekaman\b", "dapat merekam", res, flags=re.I)
    res = re.sub(r"\bcapable\s+dari\b", "dapat", res, flags=re.I)

    # 12. memindahkan menerjang / langkah pada
    res = re.sub(r"\bmemindahkan\s+menerjang\b", "kesempatan berpindah", res, flags=re.I)
    res = re.sub(r"\bSaat\s+(?:sebuah\s+)?[Mm]usuh\s+langkah\s+pada\s+itu\b", "Saat diinjak musuh", res, flags=re.I)
    res = re.sub(r"\bsaat\s+langkah\s+pada\b", "saat diinjak", res, flags=re.I)

    # 13. Off-field hero tag protection
    res = re.sub(r"sebuah\s+di\s+luar\s+arena\s+(<[^>]+>[^<]+</[^>]+>)\s+Hero\b", r"Hero \1 cadangan", res, flags=re.I)
    res = re.sub(r"sebuah\s+di\s+luar\s+arena\s+Hero\b", "Hero cadangan", res, flags=re.I)

    # 14. Medan tempur pronoun split
    res = re.sub(r"(?:pada sisi dari\s+|di\s+)?medan\s+milikmu\s+tempur\b", "di arena milikmu", res, flags=re.I)
    res = re.sub(r"\bmedan\s+tempur\b", "arena", res, flags=re.I)
    res = re.sub(r"\bmedan\s+(\w+)\s+tempur\b", r"arena \1", res, flags=re.I)

    # 15. Jing Mirror Image
    if "镜像" in source_zh:
        res = re.sub(r"<color=#ffffff><b>cermin</b></color>", "<color=#ffffff><b>Mirror Image</b></color>", res, flags=re.I)
        res = re.sub(r"<b>cermin</b>", "<b>Mirror Image</b>", res, flags=re.I)
        res = re.sub(r"<color=#FFE897>cermin</color>", "<color=#FFE897>Mirror Image</color>", res, flags=re.I)
        res = re.sub(r"<b>cermin</b>\s*kartu\b", "kartu <b>Mirror Image</b>", res, flags=re.I)
        res = re.sub(r"\bcermin\s+Kartu\b", "Kartu Mirror Image", res, flags=re.I)
        res = re.sub(r"\bcermin\s+salinan\b", "salinan Mirror Image", res, flags=re.I)

    # 16. Yao Mei deer level phrasing
    res = re.sub(r"rusa\s+Level\s+adalah\s+\+30", "Level Rusa +30", res, flags=re.I)

    # 13. Banyak dari Teman
    res = re.sub(r"\b(?:Lots of Friends|Plenty of Friends|Banyak dari Teman)\b", "Many Friends", res, flags=re.I)

    # Sub-card Copier: itu Kartu Hero -> Kartu Hero tersebut
    res = re.sub(r"\bitu\s+Kartu\s+Hero\b", "Kartu Hero tersebut", res, flags=re.I)

    # Word order fixes: Verb + milikmu
    res = re.sub(r"\b(?:semua\s+)?Riverlands\s+Hero\s+(?:mendapatkan|memperoleh)\s+milikmu\b", "semua Hero [Riverlands] milikmu memperoleh", res, flags=re.I)
    res = re.sub(r"\bTank\s+Hero\s+(?:mendapatkan|memperoleh)\s+milikmu\b", "Hero Tank milikmu memperoleh", res, flags=re.I)
    res = re.sub(r"\bbeku\s+Hero\s+(?:mendapatkan|memperoleh)\s+milikmu\b", "Hero milikmu yang terkena Freeze memperoleh", res, flags=re.I)
    res = re.sub(r"\b(semua\s+)?Hero\s+(memicu|mendapatkan|menggunakan|memperoleh|melepaskan|menyerang|memanggil)\s+milikmu\b", r"\1Hero milikmu \2", res, flags=re.I)
    res = re.sub(r"\b(semua\s+)?unit\s+(memicu|mendapatkan|menggunakan|memperoleh|melepaskan|menyerang|memanggil)\s+milikmu\b", r"\1unit milikmu \2", res, flags=re.I)
    res = re.sub(r"\bHero\s+secara\s+permanen\s+milikmu\s+mendapatkan\b", "Hero milikmu memperoleh secara permanen", res, flags=re.I)
    res = re.sub(r"\bHero\s+milikmu\s+akan\s+secara\s+permanen\s+mendapatkan\b", "Hero milikmu memperoleh secara permanen", res, flags=re.I)
    res = re.sub(r"\bHero\s+milikmu\s+mendapatkan\b", "Hero milikmu memperoleh", res, flags=re.I)
    res = re.sub(r"\bHero\s+milikmu\s+Memicu\b", "Hero milikmu memicu", res, flags=re.I)
    res = re.sub(r"\bdan\s+mendapatkan\s+milikmu\b", "dan memperoleh", res, flags=re.I)
    res = re.sub(r"\bmendapatkan\s+milikmu\b", "memperoleh", res, flags=re.I)
    res = re.sub(r"\bSetiap waktu\b", "Setiap kali", res, flags=re.I)
    res = re.sub(r"\bDi awal dari (?:Round|giliran)\b", "Saat Round dimulai", res, flags=re.I)
    res = re.sub(r"\bDi awal dari Combat\b", "Saat Combat dimulai", res, flags=re.I)
    res = re.sub(r"\bDi akhir dari Combat\b", "Saat Combat berakhir", res, flags=re.I)

    # Equipment & Treasure headers
    if "唯一" in source_zh:
        res = re.sub(r"<b>\s*(?:hanya|Unique)\s*</b>", "<b>Unik</b>", res, flags=re.I)
        res = re.sub(r"<color=#ffffff>\s*(?:hanya|Unique)\s*</color>", "<color=#ffffff>Unik</color>", res, flags=re.I)
        res = re.sub(r"<color=#ffffff><b>\s*(?:hanya|Unique)\s*</b></color>", "<color=#ffffff><b>Unik</b></color>", res, flags=re.I)
        res = re.sub(r"\bhanya\b", "Unik", res, flags=re.I)

    res = re.sub(r"\btidak\s+dapat\s+disassembled\b", "tidak dapat dilepas", res, flags=re.I)
    res = re.sub(r"\bTidak\s+dapat\s+disassembled\b", "Tidak dapat dilepas", res)
    res = re.sub(r"\bCannot\s+be\s+disassembled\b", "Tidak dapat dilepas", res, flags=re.I)
    res = re.sub(r"\bHarta\s+[Kk]artu\b", "Kartu Treasure", res)
    res = re.sub(r"\bHarta\s+kartu\b", "Kartu Treasure", res, flags=re.I)
    res = re.sub(r"Pilih 1 <color=#FFDD68FF>Oranye Hero \+\s*Level 3</color>\.", "Pilih 1 <color=#FFDD68FF>Hero Oranye +3 Level</color>.", res)
    res = re.sub(r"\bOranye\s+Hero\s*\+\s*Level\s*3\b", "Hero Oranye +3 Level", res, flags=re.I)

    # --- TUGAS 2: Card draw vs match draw ---
    if "抽" in source_zh:
        res = re.sub(r"\b(?:Seri|menarik)\s+(\d+|[A-Za-z<]+)\s*kartu\b", r"Ambil \1 kartu", res, flags=re.I)
        res = re.sub(r"\b(?:Seri|menarik)\s+sebuah\s+([A-Za-z0-9 ·•\-\[\]]+)\s+Kartu\b", r"Ambil 1 Kartu \1", res, flags=re.I)
        res = re.sub(r"\b(?:Seri|menarik)\s+sebuah\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\b(?:Seri|menarik)\s+1\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\bmenarik\s+kartu\b", "mengambil kartu", res, flags=re.I)

    if "平局" not in source_zh:
        res = re.sub(r"\bSeri\s+(\d+|[A-Za-z<]+)\s*kartu\b", r"Ambil \1 kartu", res, flags=re.I)
        res = re.sub(r"\bSeri\s+sebuah\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\bSeri\s+1\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\bSeri\b(?!\s*[/–-]|\s*Kalah|\s*Defeat)", "Ambil", res)

    # --- TUGAS 3: Box-Drawing Glyphs Spacing & Series Headers ---
    res = re.sub(r"(?<=[0-9A-Za-z+])(?<![\u2500-\u257f])([\u2500-\u257f])", r" \1", res)
    res = re.sub(r"[ ]{2,}([\u2500-\u257f])", r" \1", res)
    res = re.sub(r"╊\s*(?:merampas|Plunder)\b", "╊Steal", res, flags=re.I)
    res = re.sub(r"╆\s*Kartu\s+Hero\s+acak\s+Fleeting\b", "╆Fleeting Kartu Hero acak", res, flags=re.I)
    res = re.sub(r"╆\s*Kartu\s+Hero\s+Fleeting\b", "╆Fleeting Kartu Hero", res, flags=re.I)
    res = re.sub(r"([\u2500-\u257f])\s+", r"\1", res)
    res = re.sub(r"\s+(</(?:color|b|i|a|size)>)", r"\1", res)

    res = re.sub(r"\b(?:Kartu\s+Efek|Kartu\s+Taktik)\s+Series\b", "Effect Card Series", res, flags=re.I)
    res = re.sub(r"<color=#99DEB0>Kartu Efek Series</color>", "<color=#99DEB0>Effect Card Series</color>", res)

    # --- TUGAS 4: Master Plan Terms & Anti-Calque ---
    # 1. Istilah Terkunci & Keberangkatan
    res = re.sub(r"Pada\s+Keberangkatan\s*[:：]", "Saat keluar arena:", res, flags=re.I)
    res = re.sub(r"(?<!Saat\s)Keberangkatan\s+di\s+arena\s*[:：]", "Keluar arena:", res, flags=re.I)
    res = re.sub(r"(?<!Saat\s)Keberangkatan\s*[:：]", "Saat keluar arena:", res, flags=re.I)
    res = re.sub(r"ke\s+Keberangkatan(?:\s+di)?\s+arena\b", "keluar dari arena", res, flags=re.I)
    res = re.sub(r"Keberangkatan(?:\s+di)?\s+arena\b", "keluar dari arena", res, flags=re.I)
    res = re.sub(r"\bKeberangkatan\s+arena\b", "keluar dari arena", res, flags=re.I)
    res = re.sub(r"\bKeberangkatan\b", "keluar dari arena", res, flags=re.I)
    res = re.sub(r"\b1\s+keluar\s+kartu\b", "1 Kartu Leave", res, flags=re.I)
    res = re.sub(r"\bentri\s+Kemampuan\b", "kemampuan Trait", res, flags=re.I)

    res = re.sub(r"\bChess\s+Player\b", "Contestant", res, flags=re.I)
    res = re.sub(r"\bchess\s+HP\s+pemain\b", "HP Contestant", res, flags=re.I)
    res = re.sub(r"\bpemain\s+Level\s+meningkatkan\b", "Level Contestant meningkat", res, flags=re.I)
    res = re.sub(r"\bLevel\s+pemain\b", "Level Contestant", res, flags=re.I)
    res = re.sub(r"\bHP\s+pemain\b", "HP Contestant", res, flags=re.I)
    res = re.sub(r"\bEXP\s+pemain\b", "EXP Contestant", res, flags=re.I)
    res = re.sub(r"\bEXP\s+Pemain\b", "EXP Contestant", res)
    res = re.sub(r"\bHP\s+Pemain\b", "HP Contestant", res)
    res = re.sub(r"\bdi\s+papan\b", "di arena", res, flags=re.I)
    res = re.sub(r"\bke\s+papan\b", "ke arena", res, flags=re.I)
    res = re.sub(r"\bkeluar\s+papan\b", "keluar arena", res, flags=re.I)

    # 2. Ultimate Treasure
    res = re.sub(r"Ultimate\s+Treasure\s+(?:adalah\s+(?:benar\s+)?di\s+(?:bawah|sini)|benar\s+di\s+bawah)", "Ultimate Treasure Is Right Here", res, flags=re.I)
    res = re.sub(r"Pilih\s+1\s+dari\s+3\s+pamungkas\s+acak\s+harta", "Pilih 1 dari 3 Ultimate Treasure acak", res, flags=re.I)
    res = re.sub(r"\bMimpi\s+Shop\b", "Dream Shop", res, flags=re.I)
    res = re.sub(r"\bKartu\s+Treasure\s+Efek\b", "Kartu Efek Treasure", res, flags=re.I)

    # 3. Faction & Divinity & Melodious Notes
    FACTION_PAT = r"(\[(?:Central Plains|Riverlands|Three Kingdoms|Sunset Sea|Zhulu Plateau|High Heaven|First Lands|Factionless|Great Wall|Jixia|Divinity)\])"
    res = re.sub(r"\[(?:The First Lands|First Lands?)\]", "[First Lands]", res, flags=re.I)
    res = re.sub(r"\[(?:Keilahian|Suci|Divine)\]", "[Divinity]", res, flags=re.I)
    res = re.sub(r"Luar\s+biasa\s+Suara\b|\bWonderful\s+Sound\b|\bMelodious\s+Notes\b", "Melody", res, flags=re.I)
    res = re.sub(r"\bFirst\s+Lands\s+Kartu\s+Efek\b", "Kartu Efek [First Lands]", res, flags=re.I)
    res = re.sub(r"\bkita\s+Hero\s+\[First Lands\]", "Hero [First Lands] sekutu", res, flags=re.I)

    res = re.sub(rf"\bnon-{FACTION_PAT}\s+Hero\b", r"Hero non-\1", res, flags=re.I)
    res = re.sub(rf"\bLainnya\s+{FACTION_PAT}\s+Hero\b", r"Hero \1 lainnya", res, flags=re.I)
    res = re.sub(rf"(?:sebuah\s+)?Awakened\s+{FACTION_PAT}\s+Hero\b", r"Hero \1 Awakened", res, flags=re.I)
    res = re.sub(rf"{FACTION_PAT}\s+Hero\s+sekutu\b", r"Hero \1 sekutu", res, flags=re.I)
    res = re.sub(rf"(?:sebuah\s+)?sekutu\s+{FACTION_PAT}\s+Hero\b", r"1 Hero \1 sekutu", res, flags=re.I)
    res = re.sub(rf"\bpertama\s+Hero\s+{FACTION_PAT}\s+Kartu\s+(?:kamu\s+mainkan|yang\s+kamu\s+mainkan)\b", r"Kartu Hero \1 pertama yang kamu mainkan", res, flags=re.I)
    res = re.sub(rf"\bpertama\s+Hero\s+{FACTION_PAT}\s+Kartu\b", r"Kartu Hero \1 pertama", res, flags=re.I)
    res = re.sub(rf"\bHero\s+{FACTION_PAT}\s+Kartu\b", r"Kartu Hero \1", res, flags=re.I)
    res = re.sub(rf"{FACTION_PAT}\s+Hero\s+(?:Card|Kartu)\b", r"Kartu Hero \1", res, flags=re.I)
    res = re.sub(rf"{FACTION_PAT}\s+Kartu\s+(Hero|Efek)\b", r"Kartu \2 \1", res, flags=re.I)
    res = re.sub(rf"{FACTION_PAT}\s+Token\b", r"Token \1", res, flags=re.I)
    res = re.sub(rf"{FACTION_PAT}\s+Hero\b", r"Hero \1", res, flags=re.I)
    res = re.sub(r"(\d+)\s+Kartu\s+dari\s+Hero\s+berubah\s+milikmu\s+menjadi", r"\1 Kartu Hero milikmu berubah menjadi", res, flags=re.I)

    # 4. Skill menggunakan
    res = re.sub(r"Jumlah\s+dari\s+api\s+rubah\s+menggunakan", "Jumlah api rubah yang dilepaskan", res, flags=re.I)
    res = re.sub(r"api\s+rubah\s+menggunakan", "api rubah yang dilepaskan", res, flags=re.I)
    res = re.sub(r"Basic\s+Attack/Skill\s+menggunakan", "Basic Attack/pelepasan Skill", res, flags=re.I)
    res = re.sub(r"berikutnya\s+Skill\s+menggunakan", "pelepasan Skill berikutnya", res, flags=re.I)
    res = re.sub(r"Setiap\s+ke-(\d+)\s+Skill\s+menggunakan", r"Setiap pelepasan Skill ke-\1", res, flags=re.I)
    res = re.sub(r"Setiap\s+ketiga\s+Skill\s+menggunakan", "Setiap pelepasan Skill ke-3", res, flags=re.I)
    res = re.sub(r"Setiap\s+((?:<[^>]+>)*\d+(?:</[^>]+>)*)\s+Skill\s+menggunakan", r"Setiap \1 pelepasan Skill", res, flags=re.I)
    res = re.sub(r"Setiap\s+(\d+)\s+Skill\s+menggunakan", r"Setiap \1 pelepasan Skill", res, flags=re.I)
    res = re.sub(r"(?:untuk\s+)?setiap\s+((?:<[^>]+>)*\d+(?:</[^>]+>)*\s*)?Skill\s+menggunakan", r"setiap \1pelepasan Skill", res, flags=re.I)
    res = re.sub(r"Skill\s+menggunakan\s+Memulihkan", "pemulihan pelepasan Skill", res, flags=re.I)
    res = re.sub(r"\bSkill\s+menggunakan\b", "pelepasan Skill", res, flags=re.I)

    # 5. Pronomina & Urutan Kata Benda
    res = re.sub(r"Hero\s+mengalahkan\s+sebuah\s+milikmu\s+musuh", "Hero milikmu mengalahkan musuh", res, flags=re.I)
    res = re.sub(r"Hero\s+(?:menerapkan|berlaku)\s+sebuah\s+milikmu\s+efek\s+Crowd\s+Control", "Hero milikmu memberikan efek Crowd Control", res, flags=re.I)
    res = re.sub(r"(?:saat\s+)?(?:kamu\s+)?(?:memainkan|Bermain)\s+pertama\s+(\d+)\s+Awaken(?:ed)?\s+milikmu\s+Kartu\s+Hero", r"Saat kamu memainkan \1 Kartu Hero Awakened pertamamu", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+milikmu\s+", "", res, flags=re.I)
    res = re.sub(r"\bAwaken(?:ed)?\s+milikmu\s+Kartu\b", "Kartu Hero Awakened pertamamu", res, flags=re.I)

    res = re.sub(r"\bHero\s+menggunakan\s+(?:sebuah\s+)?milikmu\s+Skill\b", "Hero milikmu melepaskan Skill", res, flags=re.I)
    res = re.sub(r"\bHero\s+menerapkan\s+Crowd\s+milikmu\s+Control\s+efek\b", "Hero milikmu memberikan efek Crowd Control", res, flags=re.I)
    res = re.sub(r"\bHero\s+mendapatkan\s+(?:sebuah\s+)?milikmu\s+Temporary\s+Level\b", "Hero milikmu memperoleh Temporary Level", res, flags=re.I)
    res = re.sub(r"\bHero\s+mendapatkan\s+(?:sebuah\s+)?milikmu\s+permanen\s+(<[^>]+>[^<]+</[^>]+>|\+?\d+)\s+Level\b", r"Hero milikmu memperoleh \1 Level permanen", res, flags=re.I)
    res = re.sub(r"\bsemua\s+milikmu\s+(\[[^\]]+\])\s+Hero\b", r"semua Hero \1 milikmu", res, flags=re.I)
    res = re.sub(r"\bmilikmu\s+Skill\b", "Skill milikmu", res, flags=re.I)
    res = re.sub(r"\bCrowd\s+milikmu\s+Control\b", "Crowd Control", res, flags=re.I)
    res = re.sub(r"\bmilikmu\s+Temporary\s+Level\b", "Temporary Level milikmu", res, flags=re.I)
    res = re.sub(r"\bmilikmu\s+Control\s+efek\b", "efek Control milikmu", res, flags=re.I)
    res = re.sub(r"\bHero'\s+Level\b", "Level Hero", res, flags=re.I)

    # 6. Artikel Harfiah & Polisemi
    res = re.sub(r"\bsebuah\s+tambahan\b", "tambahan", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+[Ee]kstra\b", "ekstra", res)
    res = re.sub(r"\bsebuah\s+permanen\b", "secara permanen", res, flags=re.I)
    res = re.sub(r"\bmemenangkan\s+sebuah\s+Combat\b", "memenangkan Combat", res, flags=re.I)
    res = re.sub(r"\bkalah(?:\s+dalam)?\s+sebuah\s+Combat\b", "kalah Combat", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+Combat\b", "Combat", res, flags=re.I)

    res = re.sub(r"\b(Target|target|melebur|Membekukan|membekukan|Pilih|pilih|memanggil|menyerang|mendapatkan|Menghancurkan|menghancurkan|Tunjuk|tunjuk)\s+sebuah\s+Hero\b", r"\1 1 Hero", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+sekutu\s+Hero\b", "1 Hero sekutu", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+Hero\s+sekutu\b", "1 Hero sekutu", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+Hero\b", "Hero", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+[Mm]usuh\b", "musuh", res)

    # 7. Khusus Tamu & Hadiah
    res = re.sub(r"(?:ekstra\s+)?Khusus\s+Tamu\s+(?:bonus|hadiah)", "hadiah bonus Undangan", res, flags=re.I)
    res = re.sub(r"\bKhusus\s+Tamu\s+(?:Chess\s+Player|Contestant)\b", "Contestant Undangan", res, flags=re.I)
    res = re.sub(r"\bKhusus\s+Tamu\b", "Undangan", res, flags=re.I)
    res = re.sub(r"\bmenjadi\s+sebuah\s+(Starlight\s+Treasure|Rose\s+Treasure)", r"menjadi \1", res, flags=re.I)
    res = re.sub(r"\bBintang\s+Warna\s+Harta\b", "Starlight Treasure", res, flags=re.I)
    res = re.sub(r"\bMawar\s+Harta\b", "Rose Treasure", res, flags=re.I)
    res = re.sub(r"\bTim-Lebar\s+Buff\b", "Team-Wide Buff", res, flags=re.I)
    res = re.sub(r"\b(?:kamu\s+)?tempat\s+di\s+atas\s+(\d+)\b", r"masuk \1 besar", res, flags=re.I)
    res = re.sub(r"\bplace\s+in\s+top\s+(\d+)\b", r"masuk \1 besar", res, flags=re.I)

    # 8. <Nama> kartu -> Kartu <Nama> & Tag Kartu
    res = re.sub(r"\bKartu\s+Shouyue\b", "Kartu Baili Shouyue", res)
    res = re.sub(r"\bShouyue\s+kartu\b", "Kartu Baili Shouyue", res, flags=re.I)
    res = re.sub(r"\bMarco\s+kartu\b", "Kartu Marco Polo", res, flags=re.I)
    res = re.sub(r"\bConsort\s+Yu\s+kartu\b", "Kartu Consort Yu", res, flags=re.I)
    res = re.sub(r"\bArli\s+kartu\b", "Kartu Arli", res, flags=re.I)
    res = re.sub(r"\bAscension\s+kartu\b", "Kartu Ascension", res, flags=re.I)
    res = re.sub(r"\bMaster\s+Artisan\s+kartu\b", "Kartu Master Artisan", res, flags=re.I)
    res = re.sub(r"\bGaris\s+depan\s+Kartu\b", "Kartu Vanguard", res, flags=re.I)
    res = re.sub(r"\bProperti\s+Tambahan\s+kartu\s+acak\b", "kartu bonus atribut acak", res, flags=re.I)
    res = re.sub(r"\b1\s+╊Soul\s+Snatch\s+kartu\b", "1 Kartu ╊Soul Snatch", res, flags=re.I)
    res = re.sub(r"\b╊Soul\s+Snatch\s+kartu\b", "Kartu ╊Soul Snatch", res, flags=re.I)
    res = re.sub(r"\b(?:sekutu\s+)?Kartu\s+Li\s+Xin\s+Efek\b", "efek kartu Li Xin sekutu", res, flags=re.I)
    res = re.sub(r"\b1\s+╆Fleeting\s+Kartu\s+Hero\s+acak\b", "1 Kartu Hero ╆Fleeting acak", res, flags=re.I)
    res = re.sub(r"\b╆Fleeting\s+Kartu\s+Hero\b", "Kartu Hero ╆Fleeting", res, flags=re.I)
    res = re.sub(r"\b2\s+Berbagi\s+adalah\s+Peduli\s+kartu\b", "2 Kartu Sharing Is Caring", res, flags=re.I)
    res = re.sub(r"(\d+)\s+Mekanisme\s+kartu\b", r"\1 Kartu Mekanisme", res, flags=re.I)
    res = re.sub(r"\b1\s+Ditargetkan\s+Faction\s+kartu\b", "1 Kartu Faction pilihan", res, flags=re.I)
    res = re.sub(r"\bEfek\s+Panduan\s+kartu\b", "Kartu Strategi Efek", res, flags=re.I)
    res = re.sub(r"\bSuper\s+Energi\s+Penyimpanan\s+kartu\b", "Kartu Super Energy Storage", res, flags=re.I)
    res = re.sub(r"\bsaat\s+memainkan\s+super\s+penyimpanan\b", "saat memainkan Super Energy Storage", res, flags=re.I)
    res = re.sub(r"\b1\s+<b>Tinggi\s+Stakes</b>\s+kartu\b", "1 Kartu <b>High Stakes</b>", res, flags=re.I)
    res = re.sub(r"\b<b>Tinggi\s+Stakes</b>\s+kartu\b", "Kartu <b>High Stakes</b>", res, flags=re.I)
    res = re.sub(r"<color=#FFE897>Master\s+Artisan</color>\s+kartu\s+efek\b", "efek kartu <color=#FFE897>Master Artisan</color>", res, flags=re.I)
    res = re.sub(r"(\d+)\s+((?:<a[^>]*>)?(?:<color=[^>]+>|<b>)[^<>]+?(?:</b>|</color>)(?:</a>)?)\s+kartu\b", r"\1 Kartu \2", res, flags=re.I)
    res = re.sub(r"(?:</color>|</b>)\s*kartu\b", lambda m: m.group(0).replace("kartu", "Kartu"), res)

    # 9. Bermain / Memainkan
    res = re.sub(r"Saat\s+undian\s+kartu", "Saat mengambil kartu", res, flags=re.I)
    res = re.sub(r"\b1\s+tambahan\s+waktu\b", "1 kali tambahan", res, flags=re.I)
    res = re.sub(r"(Kartu\s+(?:Efek|Hero|Ancient\s+Coin)|Ancient\s+Coin(?:\s+atau\s+Refined\s+Ancient\s+Coin)?)\s+kamu\s+[Bb]ermain\b", r"\1 yang kamu mainkan", res)
    res = re.sub(r"Saat\s+((?:<[^>]+>)*)\s*bermain\s+(?:sebuah\s+)?Awakened\s+Kartu\s+Hero", r"Saat \1memainkan Kartu Hero Awakened", res, flags=re.I)
    res = re.sub(r"Saat\s+((?:<[^>]+>)*)\s*bermain\s+(?:sebuah\s+)?Kartu\s+Hero", r"Saat \1memainkan Kartu Hero", res, flags=re.I)
    res = re.sub(r"Setiap\s+kali\s+kamu\s+[Bb]ermain\b", "Setiap kali kamu memainkan", res)
    res = re.sub(r"\b[Bb]ermain\s+(?:sebuah\s+|sama\s+)?Kartu\s+Hero(?:\s+yang\s+sama)?", "memainkan Kartu Hero", res)
    res = re.sub(r"\bkamu\s+[Bb]ermain\b", "kamu mainkan", res)
    res = re.sub(r"\bBermain:", "Saat dimainkan:", res)
    res = re.sub(r"\bsaat\s+(?:kamu\s+)?bermain(?:\s*,\s*|\s*\(|\s*$)", "saat dimainkan, ", res, flags=re.I)
    res = re.sub(r"\bsaat\s+bermain\s+sama\s+Kartu\s+Hero\s+lagi\b", "saat memainkan Kartu Hero yang sama lagi", res, flags=re.I)
    res = re.sub(r"\bsaat\s+(?:kamu\s+)?bermain\b", "saat memainkan", res, flags=re.I)

    # 10. Chess & Unit
    res = re.sub(r"\bbeku\s+chess\s+bidak\b", "unit yang terkena Freeze", res, flags=re.I)
    res = re.sub(r"\bdijual\s+chess\s+bidak\b", "unit yang dijual", res, flags=re.I)
    res = re.sub(r"(?:sebuah\s+)?chess\s+(?:bidak|keping)\b", "unit", res, flags=re.I)
    res = re.sub(r"\bchess\s+(?:bidak|keping)\b", "unit", res, flags=re.I)
    res = re.sub(r"\bMenjual\s+chess\s+bidak\b", "Menjual unit", res, flags=re.I)
    res = re.sub(r"\bchess\b", "unit", res, flags=re.I)

    # 11. Sendiri & Sekutu
    res = re.sub(r"(\d+)\s+sendiri\s+Hero(\s+acak)?\b", r"\1 Hero sekutu\2", res, flags=re.I)
    res = re.sub(r"\bAcak\s+1\s+sendiri\s+Hero\b", "1 Hero sekutu acak", res, flags=re.I)
    res = re.sub(r"\bsemua\s+sendiri\s+Hero\b", "semua Hero sekutu", res, flags=re.I)
    res = re.sub(r"\bsendiri\s+Hero'\s*", "Hero sekutu ", res, flags=re.I)
    res = re.sub(r"\bsendiri\s+Hero\b", "Hero sekutu", res, flags=re.I)
    res = re.sub(r"\bjika\s+kamu\s+sendiri\s+(?:sebuah\s+)?Level\s+2\s+Core\b", "jika kamu memiliki Core Level 2", res, flags=re.I)
    res = re.sub(r"\bkamu\s+sendiri\s+(?:sebuah\s+)?", "kamu memiliki ", res, flags=re.I)
    res = re.sub(r"\b(?:diri\s+)?sendiri\s+((?:Max\s+)?(?:HP|Level))\b", r"\1 diri sendiri", res, flags=re.I)
    res = re.sub(r"\bmenghancurkan\s+untuk\s+mereka-4\s+Equipment\b", "menghancurkan Equipment ke-4 miliknya", res, flags=re.I)

    # 12. Level Contestant, Bebas, Kalah Stat
    res = re.sub(r"(?:saat\s+ini\s+)?pemain\s+Level\b", "Level Contestant saat ini", res, flags=re.I)
    res = re.sub(r"Pemain\s+Level\s+(\d+(?:[~–-]\d+)?)\b", r"Level Contestant \1", res, flags=re.I)
    res = re.sub(r"\b[Pp]emain\s+Level\b", "Level Contestant", res)

    res = re.sub(r"\b[Bb]ebas\s+Refresh\b", "Refresh gratis", res)
    res = re.sub(r"\bFree\s+Refresh\b", "Refresh gratis", res, flags=re.I)
    res = re.sub(r"(\d+)\s+bebas\s+Shop\s+Refresh\b", r"\1 Refresh Shop gratis", res, flags=re.I)
    res = re.sub(r"Bebas\s+penguatan\s+([^!.,;:\n]+?)\s+di\s+menyimpan", r"penguatan gratis \1 di Shop", res, flags=re.I)
    res = re.sub(r"\bdi\s+menyimpan\b", "di Shop", res, flags=re.I)

    res = re.sub(r"(?:seized\s+unit|target)\s+Tidak\s+kalah\s+Level\b", "target tidak kehilangan Level", res, flags=re.I)
    res = re.sub(r"\bke\s+kalah\s+(\d+%?)\b", r"kehilangan \1", res, flags=re.I)
    res = re.sub(r"\b(?:kalah|ke\s+kalah)\s+(\d+%?)\s*(?:dari\s+)?(Max\s+HP|HP|Health)\b", r"kehilangan \1 \2", res, flags=re.I)
    res = re.sub(r"\b(?:kalah|ke\s+kalah)\s+(HP|Health)\b", "kehilangan HP", res, flags=re.I)
    res = re.sub(r"\bkalah\s+(\d+%?)\s+dari\s+Saat\s+ini\s+Menyerang\s+mereka\b", r"kehilangan \1 Attack saat ini", res, flags=re.I)

    res = re.sub(r"\b(\d+)\s+total\s+menggunakan\b", r"total \1 penggunaan", res, flags=re.I)
    res = re.sub(r"\bTrait\s+[Kk]emampuan\b", "kemampuan Trait", res)
    res = re.sub(r"\bDitargetkan\s+Hero\b", "Hero yang ditargetkan", res, flags=re.I)
    res = re.sub(r"\bHero\s+itu\s+bertahan\s+hidup\b", "Hero yang bertahan hidup", res, flags=re.I)
    res = re.sub(r"\bmereka\s+diperoleh\s+Round\s+ini\b", "yang diperoleh pada Round ini", res, flags=re.I)
    res = re.sub(r"\bberuntun\s+menang\s+dari\s+setidaknya\s+(\d+)\b", r"minimal \1 Win Streak", res, flags=re.I)
    res = re.sub(r"\bmeningkatkan\s+di\s+Level\s+sebesar\b", "meningkatkan Level sebesar", res, flags=re.I)

    # 13. Sisa kata Inggris
    res = re.sub(r"ini\s+Equipment\s+evolves\s+sekali\b", "Equipment ini berevolusi 1 kali", res, flags=re.I)
    res = re.sub(r"\bnyawa\s+menguras\b", "Lifesteal", res, flags=re.I)
    res = re.sub(r"\btumbuh\s+atas\b", "naik Level", res, flags=re.I)
    res = re.sub(r"\bfictitious\b", "palsu", res, flags=re.I)
    res = re.sub(r"\bMantra\s+Lifesteal\b", "Magic Lifesteal", res, flags=re.I)
    res = re.sub(r"\bsebuah\s+sekutu\s+Dikalahkan\b", "Hero sekutu dikalahkan", res, flags=re.I)
    res = re.sub(r"\bEvolves\s+Skill\b", "Evolusi Skill", res, flags=re.I)
    res = re.sub(r"\bevolves\b", "berevolusi", res, flags=re.I)
    res = re.sub(r"\bseized\s+unit\b", "target", res, flags=re.I)

    res = re.sub(r"\bRepeats\s+(\d+)\s+kali\b", r"Berulang \1 kali", res, flags=re.I)
    res = re.sub(r"\binjects\b", "menyuntikkan", res, flags=re.I)
    res = re.sub(r"\bplundered\b", "dirampas", res, flags=re.I)
    res = re.sub(r"\bplunder\b", "merampas", res, flags=re.I)
    res = re.sub(r"\bequivalent\s+dari\b", "setara dengan", res, flags=re.I)
    res = re.sub(r"\bmanifests\b", "muncul", res, flags=re.I)
    res = re.sub(r"\badalah\s+Owned\b", "dimiliki", res, flags=re.I)
    res = re.sub(r"\bSihir\s+Lifesteal\b", "Magic Lifesteal", res, flags=re.I)
    res = re.sub(r"\b1\s+waktu\b", "1 kali", res, flags=re.I)
    res = re.sub(r"\bmemicu\s+(?:efek\s+)?Retreat\b", "memicu efek Retire", res, flags=re.I)

    # Ensure tag boundary spacing
    res = re.sub(r"([A-Za-z0-9%])(<(?![/])(?:color|b|i|a|size)\b[^>]*>)", r"\1 \2", res)
    res = re.sub(r"(</(?:color|b|i|a|size)>)([A-Za-z0-9])", r"\1 \2", res)

    # Clean double spaces
    res = re.sub(r" {2,}", " ", res)
    return res


def rewrite_en_card_to_id(source_zh: str, baseline_en: str) -> str:
    """Translate and restructure non-Tier-1 English card text into natural Indonesian."""
    if not baseline_en:
        return baseline_en

    text = baseline_en

    # Contestant & Sub-Card Alias Normalization using source_zh guards
    if "香香" in source_zh:
        text = re.sub(r"\b(?:fragrant|Xiangxiang|Shangguan)\b", "Xiang", text, flags=re.I)
    if "嬴律" in source_zh:
        text = re.sub(r"\b(?:Ying Law|Ying Lu|Yinglü|Qin Lu)\b", "Ying Lü", text, flags=re.I)
    if "白歌" in source_zh:
        text = re.sub(r"\bWhite Song\b", "Bai Ge", text, flags=re.I)
        text = re.sub(r"\bImprovisation\b", "Improvised Creation", text, flags=re.I)
    if "小妲己" in source_zh:
        text = re.sub(r"\bXiao Xiao Little Daji\b", "Little Daji", text, flags=re.I)
    if "常小娥" in source_zh:
        text = re.sub(r"\bChang Xiao'e\b", "Little Chang'e", text, flags=re.I)
        text = re.sub(r"\bXiaotu's Blessing\b", "Little Rabbit's Blessing", text, flags=re.I)
        text = re.sub(r"\bXiaotu's Aid\b", "Little Rabbit's Aid", text, flags=re.I)
        text = re.sub(r"\bXiaotu\b", "Si Kelinci", text, flags=re.I)
    if "庄小鱼" in source_zh:
        text = re.sub(r"\bZhuang Xiaoyu\b", "Little Zhuang Fish", text, flags=re.I)
    if "孙小宾" in source_zh:
        text = re.sub(r"\bSun Xiaobin\b", "Little Sun Bin", text, flags=re.I)
    if "弈星" in source_zh:
        text = re.sub(r"\bYixing\b", "Yi Xing", text, flags=re.I)
        text = re.sub(r"\bCommand the Situation\b", "Seizing Momentum", text, flags=re.I)
    if "明先生" in source_zh:
        text = re.sub(r"\bMr\.\s*Ming\b", "Mister Ming", text, flags=re.I)
    if "瑶妹" in source_zh:
        text = re.sub(r"\bYaria\b", "Yao Mei", text, flags=re.I)
        text = re.sub(r"\b(?:Magical Fawn|Magic Fawn|Magical [Dd]eer)\b", "Magic Deer", text, flags=re.I)
    if "扫拂" in source_zh:
        text = re.sub(r"\b(?:Sweeping|Sweep)\b", "Strum", text, flags=re.I)
    if "魔神" in source_zh:
        text = re.sub(r"\bDemon God's Max HP\b", "Max HP Demon God", text, flags=re.I)
        text = re.sub(r"\bDemon God's HP\b", "HP Demon God", text, flags=re.I)
        text = re.sub(r"\bDemon God's (?:Energy )?Charge Speed\b", "kecepatan isi Energi Demon God", text, flags=re.I)
        text = re.sub(r"\bDemon God's charging Speed\b", "kecepatan isi Energi Demon God", text, flags=re.I)
        text = re.sub(r"\bDemon God's first Attack\b", "serangan pertama Demon God", text, flags=re.I)
        text = re.sub(r"\bDemon God(?:'s)? [Ss]lot\b", "slot Demon God", text, flags=re.I)
        text = re.sub(r"\bDemon God position\b", "slot Demon God", text, flags=re.I)
        text = re.sub(r"\bHalberd of (?:Heavenly Might|the Sky|Sky)\b", "Sky Piercer", text, flags=re.I)
        text = re.sub(r"\bTaotie Devours the World\b", "Taotie Annihilation", text, flags=re.I)
        text = re.sub(r"\bwhich lands at\b", "yang mendarat di", text, flags=re.I)
        text = re.sub(r"\bdescends to join\b", "turun ke", text, flags=re.I)

    # Pre-lexicon structural rewrites
    text = re.sub(r"\bwhen\s+your\s+Hero(?:es)?\s+defeats?\s+an\s+enemy\b", "saat Hero milikmu mengalahkan musuh", text, flags=re.I)
    text = re.sub(r"\bwhen\s+your\s+Hero(?:es)?\s+(?:applies|apply|inflicts?)\s+a\s+Crowd\s+Control\s+effect\b", "saat Hero milikmu memberikan efek Crowd Control", text, flags=re.I)
    text = re.sub(r"\bplay\s+your\s+first\s+(\d+)\s+Awakened\s+Hero\s+(?:Cards|cards)\b", r"memainkan \1 Kartu Hero Awakened pertamamu", text, flags=re.I)
    text = re.sub(r"\bThe\s+first\s+(\[[^\]]+\])\s+Hero\s+Card\s+you\s+Play\b", r"Kartu Hero \1 pertama yang kamu mainkan", text, flags=re.I)
    text = re.sub(r"\bfirst\s+(\[[^\]]+\])\s+Hero\s+Card\s+you\s+Play\b", r"Kartu Hero \1 pertama yang kamu mainkan", text, flags=re.I)
    text = re.sub(r"\b(\[[^\]]+\])\s+Hero\s+Cards?\b", r"Kartu Hero \1", text, flags=re.I)
    text = re.sub(r"\ban?\s+off-(?:field|board)\s+(<[^>]+>)?\s*(Tier\s+\d+|\d+-Tier)\s+Hero\b", r"Hero \1\2 yang belum ada di arena", text, flags=re.I)
    text = re.sub(r"\boff-(?:field|board)\s+call\b", "panggilan bantuan luar arena", text, flags=re.I)
    text = re.sub(r"\boff-(?:field|board)\b", "di luar arena", text, flags=re.I)
    text = re.sub(r"\bHero(?:es)?\s+you\s+own\s+that\s+(?:is|are)\s+at\s+least\s+[Ll]evel\s+(\d+)\b", r"Hero milikmu minimal Level \1", text, flags=re.I)
    text = re.sub(r"\bthat\s+is\s+(\d+)\s+Tier\s+higher\b", r"yang \1 Tier lebih tinggi", text, flags=re.I)
    text = re.sub(r"\bthat\s+is\s+not\s+higher\s+than\b", "yang tidak melebihi", text, flags=re.I)
    text = re.sub(r"\bthat\s+is\s+not\s+lower\s+than\b", "yang tidak lebih rendah daripada", text, flags=re.I)
    text = re.sub(r"\bif\s+it\s+is\s+a\s+Tier\s+(\d+)\s+Hero\b", r"jika Hero Tier \1", text, flags=re.I)
    text = re.sub(r"\bto\s+randomly\b", "untuk secara acak", text, flags=re.I)
    text = re.sub(r"\bto\s+enact\b", "untuk diberlakukan", text, flags=re.I)
    text = re.sub(r"\bfor\s+the\s+remainder\s+of\s+the\s+match\b", "selama sisa pertandingan", text, flags=re.I)
    text = re.sub(r"\bby\s+an\s+amount\s+equal\s+to\b", "sebesar", text, flags=re.I)
    text = re.sub(r"\bdepending\s+on\s+whether\b", "tergantung apakah", text, flags=re.I)
    text = re.sub(r"\bon\s+draw/defeat\b", "saat Seri/Kalah", text, flags=re.I)
    text = re.sub(r"\bDraw/Defeat\b", "Seri/Kalah", text, flags=re.I)
    text = re.sub(r"\b(\d+)\s+fox\s*fires\b", r"\1 api rubah", text, flags=re.I)
    text = re.sub(r"\bfox\s*fires\b", "api rubah", text, flags=re.I)
    text = re.sub(r"\bfoxfire\b", "api rubah", text, flags=re.I)

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

    # 11. "Draw" translations:
    if "平局" in source_zh:
        text = re.sub(r"(?<![A-Za-z])Draw(?![A-Za-z])(?!\s+Series)", "Seri", text)
    else:
        text = re.sub(r"\bDraw/Defeat\b", "Seri/Kalah", text, flags=re.I)
        text = re.sub(r"\bDefeat/Draw\b", "Kalah/Seri", text, flags=re.I)
        text = re.sub(r"\bDefeat\s+or\s+Draw\b", "Kalah atau Seri", text, flags=re.I)

    if "抽" in source_zh:
        text = re.sub(r"\bDraws?\s+(\d+)\s+cards?\b", r"Ambil \1 kartu", text, flags=re.I)
        text = re.sub(r"\bDraws?\s+a\s+Blue\s+Card\b", "Ambil 1 Kartu Biru", text, flags=re.I)
        text = re.sub(r"\bDraws?\s+(\d+)\s+([A-Za-z0-9 ·•\-\[\]]+)\b", r"Ambil \1 \2", text, flags=re.I)
        text = re.sub(r"\bDraws?\s+a\s+([A-Za-z0-9 ·•\-\[\]]+)\b", r"Ambil 1 \1", text, flags=re.I)
        text = re.sub(r"\bDraws?\b", "Ambil", text, flags=re.I)

    # 12. "Mystical Power" -> Mystical Power (never Mystical Kekuatan / Misterius Kekuatan)
    text = re.sub(r"\bMystical Kekuatan\b", "Mystical Power", text, flags=re.I)
    text = re.sub(r"\bMisterius Kekuatan\b", "Mystical Power", text, flags=re.I)

    # 13. Common structured card verbs:
    text = re.sub(r"\b(\d+)\s+pieces?\s+of\s+", r"\1 ", text, flags=re.I)
    text = re.sub(r"\bThe bearer can become a Hero of the\s*(\[[^\]]+\])\s*camp\.?", r"Pemakai dapat menjadi Hero Faction \1.", text, flags=re.I)
    text = re.sub(r"\bchoose\s+(\d+)\s+out\s+of\s+(\d+)\b", r"pilih \1 dari \2", text, flags=re.I)
    text = re.sub(r"\bDoes not stack\b", "Tidak dapat ditumpuk", text, flags=re.I)
    text = re.sub(r"\bif there is no\s+([A-Za-z\[\] ]+?)\s+in the Current Card pool\b", r"jika tidak ada \1 di Card Pool saat ini", text, flags=re.I)
    text = re.sub(r"\b(?:Lots of Friends|Plenty of Friends)\b", "Many Friends", text, flags=re.I)
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
