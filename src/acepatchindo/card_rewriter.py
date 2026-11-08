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

    res = re.sub(r"(╪\s*)(<b>)?(?:Bentrokan|Clash|Confrontation|Memulai|ke\s+mulai|Initiate)\b", r"\1\g<2>Initiate", res, flags=re.I)
    if "交锋" in source_zh:
        res = re.sub(r"(<b>)?\bBentrokan\b(</b>)?", r"\g<1>Initiate\g<2>", res)

    res = re.sub(r"(╬\s*)(<b>)?(?:Siap|Ready|Preparation|Prepare)\b", r"\1\g<2>Prepare", res, flags=re.I)

    res = re.sub(r"(╧\s*)(<b>)?(?:Sempurna\s+pemulihan\.?|Perfect\s+recovery\.?|Perfect\s+Revive)\b", r"\1\g<2>Perfect Revive", res, flags=re.I)
    res = re.sub(r"(╧\s*)(<b>)?(?:bangkit\s+kembali|Recovery|Resurrect|Resurrection|Revive)\b", r"\1\g<2>Revive", res, flags=re.I)

    res = re.sub(r"(╆\s*)(<b>)?(?:Instant|Fleeting)\b", r"\1\g<2>Fleeting", res, flags=re.I)

    res = re.sub(r"(╈\s*)(<b>)?(?:Exit|Keluar|Retreat|Retire)\b", r"\1\g<2>Retire", res, flags=re.I)

    res = re.sub(r"(╦\s*)(<b>)?(?:Menggabungkan|Merge|Combine)\b", r"\1\g<2>Combine", res, flags=re.I)

    if "夺取" in source_zh:
        res = re.sub(r"(╊\s*)(<b>)?(?:Merebut|Capture|Plunder|Seizure|Snatch|Steal)\b", r"\1\g<2>Steal", res, flags=re.I)
        res = re.sub(r"\b(?:Merebut|Capture|Plunder|Seizure|Snatch)\b", "Steal", res, flags=re.I)
    if "摄灵" in source_zh:
        res = re.sub(r"(╊\s*)(<b>)?(?:Jiwa\s+Merebut|Soul\s+Snatch)\b", r"\1\g<2>Soul Snatch", res, flags=re.I)

    res = re.sub(r"\bProphet\s+Totem\b", "Seer Totem", res, flags=re.I)
    res = re.sub(r"\b(?:Pernikahan|Marriage|Karma)\s+Totem\b", "Bond Totem", res, flags=re.I)
    res = re.sub(r"\b(?:Rebirth|Reincarnation)\s+Totem\b", "Afterlife Totem", res, flags=re.I)

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

    # 11. "Draw" in match context -> Seri (never Menarik), without breaking Series
    text = re.sub(r"(?<![A-Za-z])Draw(?![A-Za-z])(?!\s+Series)", "Seri", text)

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
