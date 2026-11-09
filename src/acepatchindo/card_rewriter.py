"""Tactical Indonesian Card Rewriter and Canonical Glossary Unifier."""

from __future__ import annotations

import re
from typing import Callable

from acepatchindo.validator import validate_translation

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
    r"\bBaili Xuance\b": "Xuance",
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
    r"\bBlade of Fate\b": "Destiny",
    r"\bterkenal pedang\b": "Destiny",
    r"\bTerkenal Pedang\b": "Destiny",
    r"\bTeam Buff I\b": "Team Buff I",
    r"\bTeam Buff II\b": "Team Buff II",
    r"\bTim Buff II\b": "Team Buff II",
    r"\bTim Buff I\b": "Team Buff I",
    r"\bSemua anggota meningkatkan[·.]\s*1\b": "Team Buff I",
    r"\bSemua anggota meningkatkan[·.]\s*2\b": "Team Buff II",
    r",\s*meningkatkan semua anggota sebesar 2\b": "Team Buff II",
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

# Module-level Pre-compiled Canonical Tuples
COMPILED_CANONICAL_RELATED_CARD_RULES: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p), r) for p, r in CANONICAL_RELATED_CARD_MAP.items()
)
COMPILED_CANONICAL_HERO_NAME_RULES: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p), r) for p, r in CANONICAL_HERO_NAME_MAP.items()
)
COMPILED_CANONICAL_FACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p), r) for p, r in CANONICAL_FACTION_MAP.items()
)
COMPILED_CANONICAL_MECHANIC_RULES: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p), r) for p, r in CANONICAL_MECHANIC_MAP.items()
)

# Tier 1 Ambiguity Patterns: Level <N> Hero ... +<M>
LEVEL_N_HERO_RE = re.compile(
    r"\bLevel\s+(\d+|{[^}]+})\s+((?:(?:\[[^\]]+\]|<[^>]+>|[\u2540-\u257f]|[🌀🗡️🛡️⚡🔥✨]|\S+)\s+)*?Hero\b[^.+,\n;]*?)\s*\+\s*(\d+|{[^}]+})(?!\s*Level\b)",
    re.IGNORECASE,
)
RE_MILIKMU = re.compile(r"\bmilikmu\b")

def _fix_level_n_hero(m: re.Match[str]) -> str:
    count = m.group(1)
    hero_desc = m.group(2).strip()
    bonus = m.group(3)
    hero_desc = RE_MILIKMU.sub("sekutu", hero_desc)
    if " dan " in hero_desc and ("Core" in hero_desc or "Akomia" in hero_desc or "Arcomia" in hero_desc):
        parts = hero_desc.split(" dan ", 1)
        return f"{count} {parts[0].strip()} dan {parts[1].strip()} mendapat +{bonus} Level"
    return f"{count} {hero_desc} mendapat +{bonus} Level"


# Helpers for dynamic closures / lambdas
def _make_enact_repl(m: re.Match[str]) -> str:
    verb = m.group(1).lower()
    return "untuk diberlakukan" if verb == "enact" else f"untuk {verb}"

def _make_kartu_repl(m: re.Match[str]) -> str:
    matched = m.group(0).lower()
    return f"Kartu Hero {m.group(1)}" if "hero" in matched else f"Kartu {m.group(1)}"

def _make_game_repl(m: re.Match[str]) -> str:
    term = m.group(1)
    return "pertandingan berikutnya" if term.lower() == "game" else f"{term} berikutnya"


# --- Pre-compiled Polish Rules (Universal) ---
POLISH_RULES_UNIVERSAL_1: tuple[tuple[re.Pattern[str], str | Callable], ...] = (
    # Protect decimal numbers and ranges from possessive pronoun splits
    (re.compile(r"(\d+)\s*(?:miliknya|mereka)\s*\.\s*(\d+)"), r"\1.\2"),
    (re.compile(r"(\d+)\s*(?:miliknya|mereka)\s*([-~])\s*(\d+)"), r"\1\2\3"),
    # Fix Level ambiguity
    (LEVEL_N_HERO_RE, _fix_level_n_hero),
    # Specific Tier 1 syntax fixes
    (re.compile(r"\bSaat memberikan efek CC milikmu\b"), "Saat sekutu memberikan efek CC"),
    (re.compile(r"\bLevel tertinggi\s+(\d+|{[^}]+})\s+Hero\s+(\[[^\]]+\])\s+memperoleh\b"), r"\1 Hero \2 berlevel tertinggi memperoleh"),
    (re.compile(r"\bLevel tertinggi\s+(\d+|{[^}]+})\s+Hero\b"), r"\1 Hero berlevel tertinggi"),
    (re.compile(r"\bSaat setiap Round pertama kali menggunakan\b"), "Pertama kali menggunakan"),
    (re.compile(r"\b(?:sebesar\s+setengah\s+Level\s+1\s+Hero\s+lain|sebesar\s+setengah\s+Level\s+dari\s+1\s+Hero\s+sekutu\s+lain)\b"), "setara setengah Level dari 1 Hero lain"),
    (re.compile(r"\b(?:sebesar\s+Level\s+1\s+Hero\s+lain|sebesar\s+Level\s+dari\s+1\s+Hero\s+sekutu\s+lain)\b"), "setara Level dari 1 Hero lain"),
    (re.compile(r"\bmendapat Level\s+\+(\d+)\b"), r"mendapat +\1 Level"),
    (re.compile(r"\bLevel\s*:\s*\+(\d+)\b"), r"+\1 Level"),
    # 1. adalah + verb/adjective
    (re.compile(r"\badalah\s+rusak\b", re.I), "hancur"),
    (re.compile(r"\badalah\s+masuk\s+menjadi\s+Combat\b", re.I), "diterjunkan ke pertempuran"),
    (re.compile(r"\badalah\s+(meningkat|berkurang|penuh|aktif|masuk|digandakan|dihapus|dibatasi)\b", re.I), r"\1"),
    # 2. Inverted Demonstratives & Time Modifiers & Auctions
    (re.compile(r"\bsetiap\s+berikutnya\s+Round\b", re.I), "setiap Round berikutnya"),
    (re.compile(r"\bdi\s+sebelumnya\s+Round(?:\s+dari\s+Lelang)?\b", re.I), "pada Round sebelumnya"),
    (re.compile(r"\bdi\s+sebelumnya\s+Lelang\s+Round\b", re.I), "pada Lelang Putaran sebelumnya"),
    (re.compile(r"\bsebelumnya\s+Round(?:\s+dari\s+Lelang)?\b", re.I), "Round sebelumnya"),
    (re.compile(r"\bsebelumnya\s+Lelang\s+Round\b", re.I), "Lelang Putaran sebelumnya"),
    (re.compile(r"\bdari\s+berikutnya\s+game\b", re.I), "pada pertandingan berikutnya"),
    (re.compile(r"\bberikutnya\s+(Basic Attack|Round|Combat|game|pertandingan)\b", re.I), _make_game_repl),
    (re.compile(r"\bberikutnya\s+(Hero|Kartu|hari|serangan|tembakan|jari\s+teknik)\b", re.I), r"\1 berikutnya"),
    (re.compile(r"\bSaat\s+ini\s+Kartu\s+pool\b", re.I), "Card Pool saat ini"),
    (re.compile(r"\bsaat\s+ini\s+(Kartu|pertandingan|Round|Level|HP)\b", re.I), r"\1 saat ini"),
    (re.compile(r"\bini\s+(Round|Kartu|Efek|unit|pertandingan|Combat|slot|Shield)\b", re.I), r"\1 ini"),
    # 3. keping dari
    (re.compile(r"\b(\d+)\s+keping\s+dari\s+", re.I), r"\1 "),
    (re.compile(r"\bkeping\s+dari\s+", re.I), ""),
    # 4. pembawa dapat menjadi sebuah Hero dari [...] kamp & kamp
    (re.compile(r"\bpembawa\s+dapat\s+menjadi\s+(?:sebuah\s+)?Hero\s+dari\s*(\[[^\]]+\])\s*kamp\.?", re.I), r"Pemakai dapat menjadi Hero Faction \1."),
    (re.compile(r"\bpembawa\s+dapat\s+menjadi\b", re.I), "Pemakai dapat menjadi"),
    (re.compile(r"\bkamp\b", re.I), "Faction"),
    # 5. pilih X keluar dari Y & Tier
    (re.compile(r"\bpilih\s+(\d+)\s+keluar\s+dari\s+(\d+)\b", re.I), r"pilih \1 dari \2"),
    (re.compile(r"\btinggi-Tier\b", re.I), "Tier tinggi"),
    (re.compile(r"\bterendah-Level\b", re.I), "Level terendah"),
    # 6. Unify Kartu Secret Skill & eliminate duplication
    (re.compile(r"(?:Kartu\s+)?(?:Secret\s+(?:Skill|Art)|rahasia\s+(?:kartu|teknik(?:\s+kartu)?|skill)|Rahasia\s+(?:Teknik|Skill))(?:\s+kartu)?", re.I), "Kartu Secret Skill"),
    (re.compile(r"\b(?:Kartu\s+Secret\s+Skill\s+)+", re.I), "Kartu Secret Skill "),
    (re.compile(r"1\s+(<[^>]+>[^<]+</[^>]+>)\s+Kartu Secret Skill\b"), r"1 Kartu Secret Skill \1"),
    (re.compile(r"1\s+<b>([^<]+)</b>\s+Kartu Secret Skill\b"), r"1 Kartu Secret Skill <b>\1</b>"),
    # Proper nouns
    (re.compile(r"\bYing Hukum\b"), "Ying Lü"),
    (re.compile(r"\bQin Lu\b"), "Ying Lü"),
    (re.compile(r"\bPutih Lagu\b"), "Bai Ge"),
    (re.compile(r"\bXiao Xiao Little Daji\b"), "Little Daji"),
    (re.compile(r"\bSun Xiaobin\b"), "Little Sun Bin"),
    (re.compile(r"\bZhuang Xiaoyu\b"), "Little Zhuang Fish"),
    (re.compile(r"\bChang Xiao'e\b"), "Little Chang'e"),
    (re.compile(r"\bAsylum Anak rusa\b"), "Deer's Protection"),
    # Control tokens & canonical mechanics
    (re.compile(r"(╥\s*)(<b>)?(?:Almia|Accomia|Acomia|Arcomia)\s*Core", re.I), r"\1\g<2>Arcomia Core"),
    (re.compile(r"\b(?:Almia|Accomia|Acomia)\s*Core\b", re.I), "Arcomia Core"),
    (re.compile(r"ditetapkan\s+Core\s+Level\s+dari\s+Accomia", re.I), "Level Arcomia Core"),
    (re.compile(r"╥\s+(?:(<b>))?Arcomia\s*Core"), lambda m: "╥<b>Arcomia Core" if m.group(1) else "╥Arcomia Core"),
    (re.compile(r"(╪\s*)(<b>)?(?:Bentrokan|Clash|Confrontation|Memulai|ke\s+mulai|Initiate|dan\s+(?:dimulai|mulai)\s+sebuah\s+(?:tim|grup)|Initiate\s+sebuah\s+(?:tim|grup)|sebuah\s+(?:tim|grup))\b", re.I), r"\1\g<2>Initiate"),
    (re.compile(r"(╨\s*)(<b>)?(?:dan\s+Deploy|Deploy)\b", re.I), r"\1\g<2>Deploy"),
    (re.compile(r"(╬\s*)(<b>)?(?:Siap|Ready|Preparation|Prepare)\b", re.I), r"\1\g<2>Prepare"),
    (re.compile(r"(╧\s*)(<b>)?(?:Sempurna\s+pemulihan\.?|Perfect\s+recovery\.?|Perfect\s+Revive|secara\s+sempurna\s+bangkit\s+kembali)\b", re.I), r"\1\g<2>Perfect Revive"),
    (re.compile(r"(╧\s*)(<b>)?(?:bangkit\s+kembali|Recovery|Resurrect|Resurrection|Revive|Di-revive)\b", re.I), r"\1\g<2>Revive"),
    (re.compile(r"╆\s*(<b>)?(?:Instant|Fleeting)\b", re.I), r"╆\g<1>Fleeting"),
    (re.compile(r"╆\s*Kartu\s+Hero\s+acak\s+Fleeting\b", re.I), "1 Kartu Hero ╆Fleeting acak"),
    (re.compile(r"╆\s*Kartu\s+Hero\s+Fleeting\b", re.I), "Kartu Hero ╆Fleeting"),
    (re.compile(r"╈\s*(<b>)?(?:Exit|Keluar|Retreat|Retire)\b", re.I), r"╈\g<1>Retire"),
    (re.compile(r"╦\s*(<b>)?(?:Menggabungkan|Merge|Combine|penggabungan)\b", re.I), r"╦\g<1>Combine"),
    (re.compile(r"╊\s*(<b>)?(?:Jiwa\s+Merebut|Soul\s+Snatch|Roh\s+Extraction|Soul\s+Extraction)\b", re.I), r"╊\g<1>Soul Snatch"),
    (re.compile(r"╊\s*(<b>)?(?:Merebut|Capture|Plunder|Seizure|Snatch|Steal|dan\s+Steal|capturing\s+entri|merampas)\b", re.I), r"╊\g<1>Steal"),
    (re.compile(r"\bRoh\s+Extraction\b", re.I), "Soul Snatch"),
    (re.compile(r"\bke\s+Steal\b", re.I), "Steal"),
    (re.compile(r"╫\s*sacrificed\s+Hero\b", re.I), "Hero ╫Sacrifice"),
    (re.compile(r"<color=#99DEB0>dan sacrifices</color>", re.I), "<color=#99DEB0>Sacrifice</color>"),
    # Devour
    (re.compile(r"╆\s*Melahap\b", re.I), "╆Devour"),
    (re.compile(r"╬\s*Super\s+Melahap\b", re.I), "╬Super Devour"),
    (re.compile(r"╬\s*Melahap\b", re.I), "╬Devour"),
    (re.compile(r"\bProphet\s+Totem\b", re.I), "Seer Totem"),
    (re.compile(r"\b(?:Pernikahan|Marriage|Karma)\s+Totem\b", re.I), "Bond Totem"),
    (re.compile(r"\b(?:Rebirth|Reincarnation)\s+Totem\b", re.I), "Afterlife Totem"),
    (re.compile(r"\b═\s+Level\b"), "═Temporary Level"),
    (re.compile(r"\b(Totem|Steal|Flash|Temporary Level|Arcomia Core|Deploy|Initiate|Sacrifice|Prepare|Low-Tier|Starting Lineup|Ancient Coin|Summon|Combine|Multi-Faction|Contract|Tactics Card|Shield|Effect Card|Factionless|Grassroots|General)\s+Seri\b", re.I), r"\1 Series"),
    # Demon God cleanup
    (re.compile(r"\bIblis\s+Max\s+HP\s+Dewa\b", re.I), "Max HP Demon God"),
    (re.compile(r"\bIblis\s+HP\s+Dewa\b", re.I), "HP Demon God"),
    (re.compile(r"\bIblis\s+menerjang\s+Dewa\s+Kecepatan\b", re.I), "kecepatan isi Energi Demon God"),
    (re.compile(r"\bIblis\s+Energi\s+Dewa\b", re.I), "Energi Demon God"),
    (re.compile(r"\bIblis\s+pertama\s+Dewa\s+Menyerang\b", re.I), "serangan pertama Demon God"),
    (re.compile(r"\bIblis\s+Dewa\s+Slot\b", re.I), "slot Demon God"),
    (re.compile(r"\bIblis\s+Dewa\b", re.I), "Demon God"),
    (re.compile(r"\bLangit\s+Piercer\b", re.I), "Sky Piercer"),
    (re.compile(r"\bTaotie\s+Devours\s+the\s+World\b", re.I), "Taotie Annihilation"),
    (re.compile(r"\bTempat(?:kan)?\s+sebuah\s+jarak\s+dekat\s+Hero\b", re.I), "Tempatkan Hero melee"),
    (re.compile(r"\bTempat(?:kan)?\s+sebuah\s+jarak\s+jauh\s+Hero\b", re.I), "Tempatkan Hero ranged"),
    (re.compile(r"\bTempat(?:kan)?\s+tidak\s+Hero\b", re.I), "Tanpa Hero"),
    # Equipment, Totem & Destiny
    (re.compile(r"<color=([^>]+)><b>\s*Memperoleh\s+(\d+)\s+Blade of Fate\s*</b></color>", re.I), r"Memperoleh \2 Kartu <color=\1><b>Destiny</b></color>."),
    (re.compile(r"Memperoleh\s+(\d+)\s+<color=([^>]+)><b>\s*Blade of Fate\s*</b></color>", re.I), r"Memperoleh \1 Kartu <color=\2><b>Destiny</b></color>."),
    (re.compile(r"\bBlade of Fate\b", re.I), "Destiny"),
    (re.compile(r"\bTerkenal\s+Pedang(?:\s+Siming)?\b", re.I), "Destiny"),
    (re.compile(r"\bterkenal\s+pedang(?:\s+dan\s+perintah)?\b", re.I), "Destiny"),
    (re.compile(r"\bMerah\s+Iblis\b", re.I), "Red Demon"),
    (re.compile(r"\bTongkat\s+dari\s+Kehampaan\b", re.I), "Void Staff"),
    (re.compile(r"\bMurka\s+Savant\b", re.I), "Savant's Wrath"),
    (re.compile(r"\bBuku\s+dari\s+Dewa-Eaters\b", re.I), "Insatiable Tome"),
    (re.compile(r"\bSabuk\s+Raksasa\b", re.I), "Giant's Belt"),
    (re.compile(r"\bBesar\s+Rod\b", re.I), "Large Rod"),
    (re.compile(r"\bAnti-Cedera\s+Berat\s+Armor\b", re.I), "Thorn Heavy Armor"),
    (re.compile(r"\bOverlord\s+Berat\s+Armor\b", re.I), "Overlord's Platemail"),
    (re.compile(r"\bBerat\s+Armor\b", re.I), "Heavy Armor"),
    (re.compile(r"\bMenjaga\s+Glory\b", re.I), "Guardian's Glory"),
    (re.compile(r"\bGlacial\s+Badai\b", re.I), "Glacial Buckler"),
    (re.compile(r"\bAlam\s+baka\s+Totem\b", re.I), "Afterlife Totem"),
    (re.compile(r"\b(Totem|General|Arcomia Core)\s+Seri\b", re.I), r"\1 Series"),
    (re.compile(r"\[(?:Beracun Ballad - Panjang Lagu|Racun Memulihkan: Lagu dari Panjang)\]", re.I), "[Toxic Heal: Song of Longge]"),
    # Bracketed wearers: [Sunset Sea Pemakai] -> [Pemakai Sunset Sea]
    (re.compile(r"Sunset\s+Samudra", re.I), "Sunset Sea"),
    (re.compile(r"\[(?:Sunset Samudra|Sunset Sea)\s+(?:Pemakai|Wearer)\]", re.I), "[Pemakai Sunset Sea]"),
    (re.compile(r"\[Central Plains?\s+(?:Pemakai|Wearer)\]", re.I), "[Pemakai Central Plains]"),
    (re.compile(r"\[Riverlands\s+(?:Pemakai|Wearer)\]", re.I), "[Pemakai Riverlands]"),
    (re.compile(r"\[Zhulu(?: Plateau)?\s+(?:Pemakai|Wearer)\]", re.I), "[Pemakai Zhulu Plateau]"),
    (re.compile(r"\[Three Kingdoms\s+(?:Pemakai|Wearer)\]", re.I), "[Pemakai Three Kingdoms]"),
    (re.compile(r"\[(?:Factionless|Tanpa Faction)\s+(?:Pemakai|Wearer)\]", re.I), "[Pemakai Tanpa Faction]"),
    (re.compile(r"\[([^\]]+?)\s+(?:Pemakai|Wearer)\]", re.I), r"[Pemakai \1]"),
    (re.compile(r"\[Jika\s+(?:pemakai|wearer)\s+adalah\s+([^\]]+?)\]", re.I), r"[Pemakai \1]"),
    (re.compile(r"\[(?:Pemakai|Wearer)\s+adalah\s+([^\]]+?)\]", re.I), r"[Pemakai \1]"),
    (re.compile(r"\[Sunset\s+Eksklusif\s+Equipment\]", re.I), "[Sunset Sea Exclusive Equipment]"),
    (re.compile(r"\[Sunset\s+Equipment\]", re.I), "[Sunset Sea Equipment]"),
    (re.compile(r"\bSunset\s+Tank\b", re.I), "Tank [Sunset Sea]"),
    (re.compile(r"\bFactionless\s+Tank\b", re.I), "Tank [Factionless]"),
    (re.compile(r",(?=[<\[A-Za-z])"), ", "),
    # Hero and voucher calques
    (re.compile(r"\bsalinan\s+dari\s+Kartu\s+itu\s+Hero\b", re.I), "salinan Kartu Hero tersebut"),
    (re.compile(r"\bsalinan\s+dari\s+kartu\s+itu\b", re.I), "salinan Kartu Hero tersebut"),
    (re.compile(r"\bKartu\s+itu\s+Hero\b", re.I), "Kartu Hero tersebut"),
    (re.compile(r"\bitu\s+Hero\b", re.I), "Hero tersebut"),
    # Tier 3 calques elimination
    (re.compile(r"\bmati-di arena\b", re.I), "yang belum ada di arena"),
    (re.compile(r"\bmati-papan\b", re.I), "yang belum ada di arena"),
    (re.compile(r"\bwilayah\s+pada\b", re.I), "arena"),
    (re.compile(r"\bHero\s+([^.\n]+?)\s+itu\s+adalah\b", re.I), r"Hero \1 yang"),
    (re.compile(r"\bjika\s+itu\s+adalah\b", re.I), "jika merupakan"),
    (re.compile(r"\bitu\s+adalah\s+tidak\s+lebih\s+(tinggi|rendah)\s+daripada\b", re.I), r"yang tidak lebih \1 daripada"),
    (re.compile(r"\bitu\s+adalah\b", re.I), "yang"),
    (re.compile(r"\bremainder\s+dari\s+pertandingan\b", re.I), "sisa pertandingan"),
    (re.compile(r"\bremainder\s+dari\b", re.I), "sisa"),
    (re.compile(r"\bpada\s+menarik/mengalahkan\b", re.I), "saat Seri/Kalah"),
    (re.compile(r"\bke\s+(secara acak|Gunakan|gunakan|Memperoleh|memperoleh|Meningkatkan|meningkatkan|memicu|menyerang|mendapatkan|menjadi|memilih|menyalin|memanggil|enact)\b", re.I), _make_enact_repl),
    (re.compile(r"\b(\d+)\s+Acak\s+((?:(?:<[^>]+>|\[[^\]]+\]|[\u2540-\u257f]|\S+)\s+)*?(?:Kartu(?:\s+Hero)?|Hero|Faction|unit|Unit|sinar|buff|permohonan|harapan|item|target|musuh|sekutu))\b", re.I), r"\1 \2 acak"),
    (re.compile(r"\bsebuah\s+Acak\s+((?:(?:<[^>]+>|\[[^\]]+\]|[\u2540-\u257f]|\S+)\s+)*?(?:Kartu(?:\s+Hero)?|Hero|Faction|unit|Unit|sinar|buff|permohonan|harapan|item|target|musuh|sekutu))\b", re.I), r"1 \1 acak"),
    (re.compile(r"\b(\d+)\s+Acak\s+(<[^>]+>[^<]+</[^>]+>)\b", re.I), r"\1 \2 acak"),
    (re.compile(r"\bsebuah\s+Acak\s+(<[^>]+>[^<]+</[^>]+>)\b", re.I), r"1 \1 acak"),
    (re.compile(r"\b(\d+)\s+Acak\s+([A-Za-z0-9_-]+)\b", re.I), r"\1 \2 acak"),
    (re.compile(r"\bsebuah\s+Acak\s+([A-Za-z0-9_-]+)\b", re.I), r"1 \1 acak"),
    (re.compile(r"\bsebuah\s+Acak\s+", re.I), "1 unit acak "),
    (re.compile(r"\b(\d+)\s+Acak\b", re.I), r"\1 acak"),
    (re.compile(r"1\s+Lainnya\s+tertinggi-Level\s+Hero\s+sekutu\b", re.I), "1 Hero sekutu lain berlevel tertinggi"),
    (re.compile(r"\b(\d+)\s+tertinggi-Level\s+Hero\s+(musuh|sekutu)\b", re.I), r"\1 Hero \2 berlevel tertinggi"),
    (re.compile(r"\btertinggi-Level\s+Hero\s+(musuh|sekutu)\b", re.I), r"Hero \1 berlevel tertinggi"),
    (re.compile(r"\btertinggi-Level\s+(Musuh|sekutu|Hero|unit|Unit|Jarak)\b", re.I), r"\1 berlevel tertinggi"),
    (re.compile(r"\btertinggi-Level\b", re.I), "berlevel tertinggi"),
    (re.compile(r"\bterendah-Level\b", re.I), "berlevel terendah"),
    (re.compile(r"\btertinggi-Tier\b", re.I), "Tier tertinggi"),
    (re.compile(r"\bterendah-Tier\b", re.I), "Tier terendah"),
    (re.compile(r"\btertinggi-HP\b", re.I), "HP tertinggi"),
    (re.compile(r"\bterendah-HP\b", re.I), "HP terendah"),
    # Possessive pronoun misplacements & fox fire
    (re.compile(r"(\d+)\s+milikmu/(\d+)"), r"\1/\2"),
    (re.compile(r"(\d+)\s+mereka%"), r"\1%"),
    (re.compile(r"\bmenyerang\s+miliknya\s+musuh\b", re.I), "menyerang musuh"),
    (re.compile(r"\btarget\s+miliknya\s+musuh\b", re.I), "musuh target"),
    (re.compile(r"\bHero\s+kamu\s+sendiri\b", re.I), "Hero milikmu"),
    (re.compile(r"\b(\d+)\s+rubah\s+menembakkan\b", re.I), r"\1 api rubah"),
    (re.compile(r"\brubah\s+menembakkan\b", re.I), "api rubah"),
    (re.compile(r"\b(\d+)\s+fox\s*fires\b", re.I), r"\1 api rubah"),
    (re.compile(r"\bfox\s*fires\b", re.I), "api rubah"),
    (re.compile(r"\bsecara\s+acak\s+((?:<[^>]+>)*)salinan((?:</[^>]+>)*)\b", re.I), r"secara acak \1menyalin\2"),
    # Melakukan tidak & terdapat tidak
    (re.compile(r"\bMelakukan\s+tidak\s+stack\b", re.I), "Tidak dapat ditumpuk"),
    (re.compile(r"\bMelakukan\s+tidak\b", re.I), "Tidak"),
    (re.compile(r"\bjika\s+terdapat\s+tidak\s+([A-Za-z\[\] ]+?)\s+di\s+(?:Saat\s+ini\s+Kartu|Card)\s+pool\b", re.I), r"jika tidak ada \1 di Card Pool saat ini"),
    (re.compile(r"\bterdapat\s+tidak\b", re.I), "tidak ada"),
    # Spring & Qin tambahan Lu hak istimewa
    (re.compile(r"\bsebuah\s+musim\s+semi\b", re.I), "1 Spring"),
    (re.compile(r"\bmusim\s+semi\b", re.I), "Spring"),
    (re.compile(r"\bHero\s+mendapatkan\s+(\d+)\s+milikmu%\s*", re.I), r"Hero milikmu mendapat +\1% "),
    (re.compile(r"\bHero\s+mendapatkan\s+sebuah\s+milikmu\s+Ekstra\s+(\d+%?)\s*", re.I), r"Hero milikmu mendapat tambahan +\1 "),
    (re.compile(r"\b(?:Qin\s+tambahan\s+Lu\s+hak\s+istimewa|Edict\s+Enactor\s+Hak\s+istimewa)\b", re.I), "Hak istimewa tambahan Ying Lü"),
    (re.compile(r"\bmilikmu%", re.I), "%"),
    # Eternal Time Loop calque elimination
    (re.compile(r"\bsebuah\s+lebih\s+tinggi\s+Tier\b", re.I), "Tier yang lebih tinggi"),
    (re.compile(r"\bsebuah\s+lebih\s+tinggi\b", re.I), "lebih tinggi"),
    (re.compile(r"\bsebuah\s+lebih\s+banyak\s+kuat\b", re.I), "yang lebih kuat"),
    (re.compile(r"\bsebuah\s+lebih\s+kuat\b", re.I), "yang lebih kuat"),
    (re.compile(r"\bsebuah\s+lebih\b", re.I), "lebih"),
    (re.compile(r"\bcapable\s+dari\s+rekaman\b", re.I), "dapat merekam"),
    (re.compile(r"\bcapable\s+dari\b", re.I), "dapat"),
    # memindahkan menerjang / langkah pada
    (re.compile(r"\bmemindahkan\s+menerjang\b", re.I), "kesempatan berpindah"),
    (re.compile(r"\bSaat\s+(?:sebuah\s+)?[Mm]usuh\s+langkah\s+pada\s+itu\b", re.I), "Saat diinjak musuh"),
    (re.compile(r"\bsaat\s+langkah\s+pada\b", re.I), "saat diinjak"),
    (re.compile(r"sebuah\s+di\s+luar\s+arena\s+(<[^>]+>[^<]+</[^>]+>)\s+Hero\b", re.I), r"Hero \1 cadangan"),
    (re.compile(r"sebuah\s+di\s+luar\s+arena\s+Hero\b", re.I), "Hero cadangan"),
    (re.compile(r"(?:pada sisi dari\s+|di\s+)?medan\s+milikmu\s+tempur\b", re.I), "di arena milikmu"),
    (re.compile(r"\bmedan\s+tempur\b", re.I), "arena"),
    (re.compile(r"\bmedan\s+(\w+)\s+tempur\b", re.I), r"arena \1"),
    (re.compile(r"rusa\s+Level\s+adalah\s+\+30"), "Level Rusa +30"),
    (re.compile(r"\b(?:Lots of Friends|Plenty of Friends|Banyak dari Teman)\b", re.I), "Many Friends"),
    (re.compile(r"\bitu\s+Kartu\s+Hero\b", re.I), "Kartu Hero tersebut"),
    # Word order fixes: Verb + milikmu
    (re.compile(r"\b(?:semua\s+)?Riverlands\s+Hero\s+(?:mendapatkan|memperoleh)\s+milikmu\b", re.I), "semua Hero [Riverlands] milikmu memperoleh"),
    (re.compile(r"\bTank\s+Hero\s+(?:mendapatkan|memperoleh)\s+milikmu\b", re.I), "Hero Tank milikmu memperoleh"),
    (re.compile(r"\bbeku\s+Hero\s+(?:mendapatkan|memperoleh)\s+milikmu\b", re.I), "Hero milikmu yang terkena Freeze memperoleh"),
    (re.compile(r"\b(semua\s+)?Hero\s+(memicu|mendapatkan|menggunakan|memperoleh|melepaskan|menyerang|memanggil)\s+milikmu\b", re.I), r"\1Hero milikmu \2"),
    (re.compile(r"\b(semua\s+)?unit\s+(memicu|mendapatkan|menggunakan|memperoleh|melepaskan|menyerang|memanggil)\s+milikmu\b", re.I), r"\1unit milikmu \2"),
    (re.compile(r"\bHero\s+secara\s+permanen\s+milikmu\s+mendapatkan\b", re.I), "Hero milikmu memperoleh secara permanen"),
    (re.compile(r"\bHero\s+milikmu\s+akan\s+secara\s+permanen\s+mendapatkan\b", re.I), "Hero milikmu memperoleh secara permanen"),
    (re.compile(r"\bHero\s+milikmu\s+mendapatkan\b", re.I), "Hero milikmu memperoleh"),
    (re.compile(r"\bHero\s+milikmu\s+Memicu\b", re.I), "Hero milikmu memicu"),
    (re.compile(r"\bdan\s+mendapatkan\s+milikmu\b", re.I), "dan memperoleh"),
    (re.compile(r"\bmendapatkan\s+milikmu\b", re.I), "memperoleh"),
    (re.compile(r"\bSetiap waktu\b", re.I), "Setiap kali"),
    (re.compile(r"\bDi awal dari (?:Round|giliran)\b", re.I), "Saat Round dimulai"),
    (re.compile(r"\bDi awal dari Combat\b", re.I), "Saat Combat dimulai"),
    (re.compile(r"\bDi akhir dari Combat\b", re.I), "Saat Combat berakhir"),
    (re.compile(r"\btidak\s+dapat\s+disassembled\b", re.I), "tidak dapat dilepas"),
    (re.compile(r"\bTidak\s+dapat\s+disassembled\b"), "Tidak dapat dilepas"),
    (re.compile(r"\bCannot\s+be\s+disassembled\b", re.I), "Tidak dapat dilepas"),
    (re.compile(r"\bHarta\s+[Kk]artu\b"), "Kartu Treasure"),
    (re.compile(r"\bHarta\s+kartu\b", re.I), "Kartu Treasure"),
    (re.compile(r"Pilih 1 <color=#FFDD68FF>Oranye Hero \+\s*Level 3</color>\."), "Pilih 1 <color=#FFDD68FF>Hero Oranye +3 Level</color>."),
    (re.compile(r"\bOranye\s+Hero\s*\+\s*Level\s*3\b", re.I), "Hero Oranye +3 Level"),
    # Glyphs spacing & series headers
    (re.compile(r"(?<=[0-9A-Za-z+])(?<![\u2500-\u257f])([\u2500-\u257f])"), r" \1"),
    (re.compile(r"[ ]{2,}([\u2500-\u257f])"), r" \1"),
    (re.compile(r"╊\s*(?:merampas|Plunder)\b", re.I), "╊Steal"),
    (re.compile(r"([\u2500-\u257f])\s+"), r"\1"),
    (re.compile(r"\s+(</(?:color|b|i|a|size)>)"), r"\1"),
    (re.compile(r"\b(?:Kartu\s+Efek|Kartu\s+Taktik)\s+Series\b", re.I), "Effect Card Series"),
    (re.compile(r"<color=#99DEB0>Kartu Efek Series</color>"), "<color=#99DEB0>Effect Card Series</color>"),
    # Istilah Terkunci & Keberangkatan
    (re.compile(r"Pada\s+Keberangkatan\s*[:：]", re.I), "Saat keluar arena:"),
    (re.compile(r"(?<!Saat\s)Keberangkatan\s+di\s+arena\s*[:：]", re.I), "Keluar arena:"),
    (re.compile(r"(?<!Saat\s)Keberangkatan\s*[:：]", re.I), "Saat keluar arena:"),
    (re.compile(r"ke\s+Keberangkatan(?:\s+di)?\s+arena\b", re.I), "keluar dari arena"),
    (re.compile(r"Keberangkatan(?:\s+di)?\s+arena\b", re.I), "keluar dari arena"),
    (re.compile(r"\bKeberangkatan\s+arena\b", re.I), "keluar dari arena"),
    (re.compile(r"\bKeberangkatan\b", re.I), "keluar dari arena"),
    (re.compile(r"\b1\s+keluar\s+kartu\b", re.I), "1 Kartu Leave"),
    (re.compile(r"\bentri\s+Kemampuan\b", re.I), "kemampuan Trait"),
    (re.compile(r"\bChess\s+Player\b", re.I), "Contestant"),
    (re.compile(r"\bchess\s+HP\s+pemain\b", re.I), "HP Contestant"),
    (re.compile(r"\bpemain\s+Level\s+meningkatkan\b", re.I), "Level Contestant meningkat"),
    (re.compile(r"\bLevel\s+pemain\b", re.I), "Level Contestant"),
    (re.compile(r"\bHP\s+pemain\b", re.I), "HP Contestant"),
    (re.compile(r"\bEXP\s+pemain\b", re.I), "EXP Contestant"),
    (re.compile(r"\bEXP\s+Pemain\b"), "EXP Contestant"),
    (re.compile(r"\bHP\s+Pemain\b"), "HP Contestant"),
    (re.compile(r"\bPeserta\s+Level\b", re.I), "Level Contestant"),
    (re.compile(r"Level\s+lebih\s+tinggi\s+Peserta\s+Level\b", re.I), "Level Contestant yang lebih tinggi"),
    (re.compile(r"untuk\s+Peserta\s+meng-upgrade\b", re.I), "untuk menaikkan Level Contestant"),
    (re.compile(r"\bPeserta\s+mencapai\s+Level\b", re.I), "Contestant mencapai Level"),
    (re.compile(r"\bPeserta\s+dimulai\s+dengan\b", re.I), "Contestant dimulai dengan"),
    # Top-3 variations
    (re.compile(r"(?:Jika\s+kamu\s+)?[Mm]enyelesaikan\s+di\s+atas\s+3\b"), "Saat masuk 3 besar"),
    (re.compile(r"Saat\s+masuk\s+3\s+besar,?\s*mengubah\s+hadiah\s+pertandingan\s+menjadi\b", re.I), "Saat masuk 3 besar, hadiah pertandingan menjadi"),
    (re.compile(r"\bdi\s+atas\s+3\b", re.I), "3 besar"),
    # Second & Auction
    (re.compile(r"\bdetik\s+milikmu-baris\s+Hero\b", re.I), "Hero baris ke-2 milikmu"),
    (re.compile(r"\bdetik-baris\s+Hero\b", re.I), "Hero baris ke-2"),
    (re.compile(r"\bSetelah\s+(?:detik|ke-2)\s+dan\s+(?:ketiga|ke-3)\s+Lelang\b", re.I), "Setelah Lelang ke-2 dan ke-3"),
    (re.compile(r"\bdi\s+detik\s+Lelang\s+Round\b", re.I), "pada Lelang Putaran ke-2"),
    (re.compile(r"\bdetik\s+Lelang\s+Round\b", re.I), "Lelang Putaran ke-2"),
    (re.compile(r"\bDetik\s+Round\s+Lelang\b", re.I), "Lelang Putaran ke-2"),
    # Auction / Yuan patterns & Ordinals
    (re.compile(r"\bBeli\s+0\s+Gold::", re.I), "Beli 0 Gold:"),
    (re.compile(r"\b0-yuan\s+membeli:\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\b0\s+Yuan\s+Membeli:?\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\b0-yuan\s+Purchase:?\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\b0\s+Yuan\s+Purchase:?\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\b0-yuan\s+Buy:?\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\b0\s+Yuan\s+Buy:?\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\b(?:Pertama\s+Round\s+Lelang|Lelang\s+Putaran\s+ke-1|First\s+Round\s+(?:of\s+)?Auction|1st\s+Round\s+(?:of\s+)?Auction)\b", re.I), "Lelang Putaran ke-1"),
    (re.compile(r"\b(?:Kedua\s+Round\s+Lelang|Lelang\s+Putaran\s+ke-2|Second\s+Round\s+(?:of\s+)?Auction|2nd\s+Round\s+(?:of\s+)?Auction)\b", re.I), "Lelang Putaran ke-2"),
    (re.compile(r"\b(?:ketiga\s+Round\s+dari\s+Lelang|Ketiga\s+Round\s+Lelang|Lelang\s+Putaran\s+ke-3|Third\s+Round\s+(?:of\s+)?Auction|3rd\s+Round\s+(?:of\s+)?Auction)\b", re.I), "Lelang Putaran ke-3"),
    (re.compile(r"\b(?:Keempat\s+Round\s+Lelang|Lelang\s+Putaran\s+ke-4|Fourth\s+Round\s+(?:of\s+)?Auction|4th\s+Round\s+(?:of\s+)?Auction)\b", re.I), "Lelang Putaran ke-4"),
    (re.compile(r"\b(?:Kelima\s+Round\s+Lelang|Lelang\s+Putaran\s+ke-5|Fifth\s+Round\s+(?:of\s+)?Auction|5th\s+Round\s+(?:of\s+)?Auction)\b", re.I), "Lelang Putaran ke-5"),
    (re.compile(r"\bKilas\s+Balik\s+Lelang:\s*Lelang\s+Putaran\s+ke-3\b", re.I), "Kilas Balik Lelang: Lelang Putaran ke-3"),
    (re.compile(r"\b0-yuan\b", re.I), "0 Gold"),
    # papan -> arena
    (re.compile(r"\bdari\s+papan\b", re.I), "dari arena"),
    (re.compile(r"\bpada\s+papan\s+milikmu\b", re.I), "di arena milikmu"),
    (re.compile(r"\bpada\s+papan\b", re.I), "di arena"),
    (re.compile(r"\bpada-papan\s+Hero\s+Level\b", re.I), "Level Hero di arena"),
    (re.compile(r"\bpapan\s+Hero\s+Level\b", re.I), "Level Hero di arena"),
    (re.compile(r"\bHero\s+pada\s+papan\b", re.I), "Hero di arena"),
    (re.compile(r"\bdi\s+atas\s+papan\b", re.I), "di arena"),
    (re.compile(r"\bdi\s+papan\b", re.I), "di arena"),
    (re.compile(r"\bke\s+papan\b", re.I), "ke arena"),
    (re.compile(r"\bkeluar\s+papan\b", re.I), "keluar arena"),
    (re.compile(r"(?<!catur\s)\bpapan\b", re.I), "arena"),
    (re.compile(r"\bmasuk\s+field\b", re.I), "masuk ke arena"),
    (re.compile(r"\bmimpi\s+menyimpan\b", re.I), "Dream Shop"),
    # Ultimate Treasure
    (re.compile(r"Ultimate\s+Treasure\s+(?:adalah\s+(?:benar\s+)?di\s+(?:bawah|sini)|benar\s+di\s+bawah)", re.I), "Ultimate Treasure Is Right Here"),
    (re.compile(r"Pilih\s+1\s+dari\s+3\s+pamungkas\s+acak\s+harta", re.I), "Pilih 1 dari 3 Ultimate Treasure acak"),
    (re.compile(r"\bMimpi\s+Shop\b", re.I), "Dream Shop"),
    (re.compile(r"\bKartu\s+Treasure\s+Efek\b", re.I), "Kartu Efek Treasure"),
    # Faction & Divinity & Melodious Notes
    (re.compile(r"\[(?:The First Lands|First Lands?)\]", re.I), "[First Lands]"),
    (re.compile(r"\[(?:Keilahian|Suci|Divine)\]", re.I), "[Divinity]"),
    (re.compile(r"Luar\s+biasa\s+Suara\b|\bWonderful\s+Sound\b|\bMelodious\s+Notes\b", re.I), "Melody"),
    (re.compile(r"\bFirst\s+Lands\s+Kartu\s+Efek\b", re.I), "Kartu Efek [First Lands]"),
    (re.compile(r"\bkita\s+Hero\s+\[First Lands\]"), "Hero [First Lands] sekutu"),
)

# Bracketed Faction Regex
FACTION_PAT = r"(\[(?:Central Plains|Riverlands|Three Kingdoms|Sunset Sea|Zhulu Plateau|High Heaven|First Lands|Factionless|Great Wall|Jixia|Divinity)\])"
UNBRACKETED_FACTIONS = r"(?:Central Plains|Riverlands|Three Kingdoms|Sunset Sea|Zhulu Plateau|High Heaven|First Lands|Factionless|Great Wall|Jixia)"

POLISH_RULES_UNIVERSAL_2: tuple[tuple[re.Pattern[str], str | Callable], ...] = (
    (re.compile(rf"\bnon-{FACTION_PAT}\s+Hero\b", re.I), r"Hero non-\1"),
    (re.compile(rf"\bLainnya\s+{FACTION_PAT}\s+Hero\b", re.I), r"Hero \1 lainnya"),
    (re.compile(rf"(?:sebuah\s+)?Awakened\s+{FACTION_PAT}\s+Hero\b", re.I), r"Hero \1 Awakened"),
    (re.compile(rf"{FACTION_PAT}\s+Hero\s+sekutu\b", re.I), r"Hero \1 sekutu"),
    (re.compile(rf"(?:sebuah\s+)?sekutu\s+{FACTION_PAT}\s+Hero\b", re.I), r"1 Hero \1 sekutu"),
    (re.compile(rf"\bpertama\s+Hero\s+{FACTION_PAT}\s+Kartu\s+(?:kamu\s+mainkan|yang\s+kamu\s+mainkan)\b", re.I), r"Kartu Hero \1 pertama yang kamu mainkan"),
    (re.compile(rf"\bpertama\s+Hero\s+{FACTION_PAT}\s+Kartu\b", re.I), r"Kartu Hero \1 pertama"),
    (re.compile(rf"(\d+)\s+Hero\s+acak\s+{FACTION_PAT}\s+Kartu\b", re.I), r"\1 Kartu Hero \2 acak"),
    (re.compile(rf"Hero\s+acak\s+{FACTION_PAT}\s+Kartu\b", re.I), r"Kartu Hero \1 acak"),
    (re.compile(rf"non-Kartu\s+Hero\s+{FACTION_PAT}\s+acak\b", re.I), r"Kartu Hero non-\1 acak"),
    (re.compile(rf"\bHero\s+{FACTION_PAT}\s+Kartu\b", re.I), r"Kartu Hero \1"),
    (re.compile(rf"{FACTION_PAT}\s+Hero\s+(?:Card|Kartu)\b", re.I), r"Kartu Hero \1"),
    (re.compile(rf"{FACTION_PAT}\s+Kartu\s+(Hero|Efek)\b", re.I), r"Kartu \2 \1"),
    (re.compile(rf"{FACTION_PAT}\s+Kartu\b", re.I), r"Kartu \1"),
    (re.compile(rf"{FACTION_PAT}\s+Token\b", re.I), r"Token \1"),
    (re.compile(rf"{FACTION_PAT}\s+Hero\b", re.I), r"Hero \1"),
    (re.compile(r"(\d+)\s+Kartu\s+dari\s+Hero\s+berubah\s+milikmu\s+menjadi", re.I), r"\1 Kartu Hero milikmu berubah menjadi"),
    # Unbracketed Factions
    (re.compile(rf"(?:sebuah\s+)?Awakened\s+({UNBRACKETED_FACTIONS})\s+Hero\b", re.I), r"Hero [\1] Awakened"),
    (re.compile(rf"Ditargetkan\s+({UNBRACKETED_FACTIONS})\s+Hero\b", re.I), r"Hero [\1] yang ditargetkan"),
    (re.compile(rf"(?:sebuah\s+)?({UNBRACKETED_FACTIONS})\s+Hero\b", re.I), r"Hero [\1]"),
    (re.compile(rf"({UNBRACKETED_FACTIONS})\s+Kartu\s+Hero\b", re.I), r"Kartu Hero [\1]"),
    (re.compile(rf"\bKartu\s+(Hero|Efek)\s+({UNBRACKETED_FACTIONS})\b", re.I), r"Kartu \1 [\2]"),
    (re.compile(rf"\bKartu\s+({UNBRACKETED_FACTIONS})\b", re.I), r"Kartu [\1]"),
    (re.compile(r"\bKartu\s+Hero\s+Sunset\b", re.I), "Kartu Hero [Sunset Sea]"),
    (re.compile(r"\bThree\s+Kingdoms\s+Hero\b", re.I), "Hero [Three Kingdoms]"),
    (re.compile(r"\bSunset\s+Hero\b", re.I), "Hero [Sunset Sea]"),
    (re.compile(r"\bFirst\s+Lands\s+Hero\b", re.I), "Hero [First Lands]"),
    (re.compile(r"\[+(?:Kartu(?:\s+Hero)?|Hero)\s+\[([^\]]+)\]\]*", re.I), r"Kartu Hero [\1]"),
    (re.compile(r"\[+([^\[\]]*?)\[([^\]]+)\]([^\[\]]*?)\]+"), r"\1[\2]\3"),
    (re.compile(r"\[+\[([^\]]+)\]+\]*"), r"[\1]"),
    # Skill pelepasan
    (re.compile(r"Jumlah\s+dari\s+api\s+rubah\s+menggunakan", re.I), "Jumlah api rubah yang dilepaskan"),
    (re.compile(r"api\s+rubah\s+menggunakan", re.I), "api rubah yang dilepaskan"),
    (re.compile(r"Basic\s+Attack/Skill\s+menggunakan", re.I), "Basic Attack/pelepasan Skill"),
    (re.compile(r"berikutnya\s+Skill\s+menggunakan", re.I), "pelepasan Skill berikutnya"),
    (re.compile(r"Setiap\s+ke-(\d+)\s+Skill\s+menggunakan", re.I), r"Setiap pelepasan Skill ke-\1"),
    (re.compile(r"Setiap\s+ketiga\s+Skill\s+menggunakan", re.I), "Setiap pelepasan Skill ke-3"),
    (re.compile(r"Setiap\s+((?:<[^>]+>)*\d+(?:</[^>]+>)*)\s+Skill\s+menggunakan", re.I), r"Setiap \1 pelepasan Skill"),
    (re.compile(r"Setiap\s+(\d+)\s+Skill\s+menggunakan", re.I), r"Setiap \1 pelepasan Skill"),
    (re.compile(r"(?:untuk\s+)?setiap\s+((?:<[^>]+>)*\d+(?:</[^>]+>)*\s*)?Skill\s+menggunakan", re.I), r"setiap \1pelepasan Skill"),
    (re.compile(r"Skill\s+menggunakan\s+Memulihkan", re.I), "pemulihan pelepasan Skill"),
    (re.compile(r"\bSkill\s+menggunakan\b", re.I), "pelepasan Skill"),
    # Pronomina & Urutan Kata Benda
    (re.compile(r"Hero\s+mengalahkan\s+sebuah\s+milikmu\s+musuh", re.I), "Hero milikmu mengalahkan musuh"),
    (re.compile(r"Hero\s+(?:menerapkan|berlaku)\s+sebuah\s+milikmu\s+efek\s+Crowd\s+Control", re.I), "Hero milikmu memberikan efek Crowd Control"),
    (re.compile(r"(?:saat\s+)?(?:kamu\s+)?(?:memainkan|Bermain)\s+pertama\s+(\d+)\s+Awaken(?:ed)?\s+milikmu\s+Kartu\s+Hero", re.I), r"Saat kamu memainkan \1 Kartu Hero Awakened pertamamu"),
    (re.compile(r"\bsebuah\s+milikmu\s+", re.I), ""),
    (re.compile(r"\bAwaken(?:ed)?\s+milikmu\s+Kartu\b", re.I), "Kartu Hero Awakened pertamamu"),
    (re.compile(r"\bHero\s+menggunakan\s+(?:sebuah\s+)?milikmu\s+Skill\b", re.I), "Hero milikmu melepaskan Skill"),
    (re.compile(r"\bHero\s+menerapkan\s+Crowd\s+milikmu\s+Control\s+efek\b", re.I), "Hero milikmu memberikan efek Crowd Control"),
    (re.compile(r"\bHero\s+mendapatkan\s+(?:sebuah\s+)?milikmu\s+Temporary\s+Level\b", re.I), "Hero milikmu memperoleh Temporary Level"),
    (re.compile(r"\bHero\s+mendapatkan\s+(?:sebuah\s+)?milikmu\s+permanen\s+(<[^>]+>[^<]+</[^>]+>|\+?\d+)\s+Level\b", re.I), r"Hero milikmu memperoleh \1 Level permanen"),
    (re.compile(r"\bsemua\s+milikmu\s+(\[[^\]]+\])\s+Hero\b", re.I), r"semua Hero \1 milikmu"),
    (re.compile(r"\bsemua\s+milikmu\s+Hero\b", re.I), "semua Hero milikmu"),
    (re.compile(r"\bmilikmu\s+Hero\s+(\[[^\]]+\])", re.I), r"Hero \1 milikmu"),
    (re.compile(r"\bmilikmu\s+Hero\b", re.I), "Hero milikmu"),
    (re.compile(r"\bdi\s+milikmu\s+di\s+arena\b", re.I), "milikmu di arena"),
    (re.compile(r"\bdi\s+milikmu\s+bawah\s+Tier\s+3\b", re.I), "milikmu di bawah Tier 3"),
    (re.compile(r"\bdi\s+milikmu\s+Faction\b", re.I), "dengan Faction"),
    (re.compile(r"\bAcak\s+milikmu\s+Kartu\b", re.I), "Kartu acak milikmu"),
    (re.compile(r"\bmilikmu\s+Skill\b", re.I), "Skill milikmu"),
    (re.compile(r"\bCrowd\s+milikmu\s+Control\b", re.I), "Crowd Control"),
    (re.compile(r"\bmilikmu\s+Temporary\s+Level\b", re.I), "Temporary Level milikmu"),
    (re.compile(r"\bmilikmu\s+Control\s+efek\b", re.I), "efek Control milikmu"),
    (re.compile(r"\bHero'\s+Level\b", re.I), "Level Hero"),
    # Artikel Harfiah & Polisemi
    (re.compile(r"\bsebuah\s+tambahan\b", re.I), "tambahan"),
    (re.compile(r"\bsebuah\s+[Ee]kstra\b"), "ekstra"),
    (re.compile(r"\bsebuah\s+permanen\b", re.I), "secara permanen"),
    (re.compile(r"\bmemenangkan\s+sebuah\s+Combat\b", re.I), "memenangkan Combat"),
    (re.compile(r"\bkalah(?:\s+dalam)?\s+sebuah\s+Combat\b", re.I), "kalah Combat"),
    (re.compile(r"\bsebuah\s+Combat\b", re.I), "Combat"),
    (re.compile(r"\b(Target|target|melebur|Membekukan|membekukan|Pilih|pilih|memanggil|menyerang|mendapatkan|Menghancurkan|menghancurkan|Tunjuk|tunjuk)\s+sebuah\s+Hero\b", re.I), r"\1 1 Hero"),
    (re.compile(r"\bsebuah\s+sekutu\s+Hero\b", re.I), "1 Hero sekutu"),
    (re.compile(r"\bsebuah\s+Hero\s+sekutu\b", re.I), "1 Hero sekutu"),
    (re.compile(r"\bsebuah\s+Hero\b", re.I), "Hero"),
    (re.compile(r"\bsebuah\s+[Mm]usuh\b"), "musuh"),
    # Khusus Tamu & Hadiah
    (re.compile(r"(?:ekstra\s+)?Khusus\s+Tamu\s+(?:bonus|hadiah)", re.I), "hadiah bonus Undangan"),
    (re.compile(r"\bKhusus\s+Tamu\s+(?:Chess\s+Player|Contestant)\b", re.I), "Contestant Undangan"),
    (re.compile(r"\bKhusus\s+Tamu\b", re.I), "Undangan"),
    (re.compile(r"\bmenjadi\s+sebuah\s+(Starlight\s+Treasure|Rose\s+Treasure)", re.I), r"menjadi \1"),
    (re.compile(r"\bBintang\s+Warna\s+Harta\b", re.I), "Starlight Treasure"),
    (re.compile(r"\bMawar\s+Harta\b", re.I), "Rose Treasure"),
    (re.compile(r"\bTim-Lebar\s+Buff\b", re.I), "Team-Wide Buff"),
    (re.compile(r"\b(?:kamu\s+)?tempat\s+di\s+atas\s+(\d+)\b", re.I), r"masuk \1 besar"),
    (re.compile(r"\bplace\s+in\s+top\s+(\d+)\b", re.I), r"masuk \1 besar"),
    # Canonical Hero Card Names (Baili removal!)
    (re.compile(r"\bKartu\s+Baili\s+Shouyue\b", re.I), "Kartu Shouyue"),
    (re.compile(r"\bKartu\s+Baili\s+Xuance\b", re.I), "Kartu Xuance"),
    (re.compile(r"\bBaili\s+Shouyue\b", re.I), "Shouyue"),
    (re.compile(r"\bBaili\s+Xuance\b", re.I), "Xuance"),
    (re.compile(r"\b1\s+Hero\s+Shouyue\s+kartu\b", re.I), "1 Kartu Hero Shouyue"),
    (re.compile(r"\b1\s+Shouyue\s+kartu\b", re.I), "1 Kartu Hero Shouyue"),
    (re.compile(r"\bShouyue\s+kartu\b", re.I), "Kartu Shouyue"),
    (re.compile(r"\bMarco\s+kartu\b", re.I), "Kartu Hero Marco"),
    (re.compile(r"\bConsort\s+Yu\s+kartu\b", re.I), "Kartu Consort Yu"),
    (re.compile(r"\bArli\s+kartu\b", re.I), "Kartu Arli"),
    (re.compile(r"\bAscension\s+kartu\b", re.I), "Kartu Ascension"),
    (re.compile(r"\bMaster\s+Artisan\s+kartu\b", re.I), "Kartu Master Artisan"),
    (re.compile(r"\bGaris\s+depan\s+Kartu\b", re.I), "Kartu Vanguard"),
    (re.compile(r"\bProperti\s+Tambahan\s+kartu\s+acak\b", re.I), "kartu bonus atribut acak"),
    (re.compile(r"\b1\s+╊Soul\s+Snatch\s+kartu\b", re.I), "1 Kartu ╊Soul Snatch"),
    (re.compile(r"\b╊Soul\s+Snatch\s+kartu\b", re.I), "Kartu ╊Soul Snatch"),
    (re.compile(r"\b(?:sekutu\s+)?Kartu\s+Li\s+Xin\s+Efek\b", re.I), "efek kartu Li Xin sekutu"),
    (re.compile(r"\b1\s+╆Fleeting\s+Kartu\s+Hero\s+acak\b", re.I), "1 Kartu Hero ╆Fleeting acak"),
    (re.compile(r"\b╆Fleeting\s+Kartu\s+Hero\b", re.I), "Kartu Hero ╆Fleeting"),
    (re.compile(r"(\d+)\s+Tier\s+acak\s+(\d+-\d+)\s+╆Fleeting\s+Kartu\s+Hero\b", re.I), r"\1 Kartu Hero ╆Fleeting Tier \2 acak"),
    (re.compile(r"\bMainan\s+Kartu\b", re.I), "Kartu Mainan"),
    (re.compile(r"No\.7\s+menarik\s+(?:sebuah\s+)?kuat\s+<b>Kartu\s+Mainan</b>\s+dari\s+ikan\s+buntal\s+tas\s+miliknya", re.I), "Luban No.7 mengeluarkan 1 <b>Kartu Mainan</b> kuat dari tas ikan buntalnya"),
    (re.compile(r"\b2\s+Berbagi\s+adalah\s+Peduli\s+kartu\b", re.I), "2 Kartu Shared Fortune"),
    (re.compile(r"\b2\s+Shared\s+Fortune\s+kartu\b", re.I), "2 Kartu Shared Fortune"),
    (re.compile(r"\bMysterious\s+Hero\s+Kartu\b", re.I), "Kartu Hero Misterius"),
    (re.compile(r"\bLanjutan\s+Mekanisme\s+Kartu\b", re.I), "Kartu Mekanisme Tingkat Lanjut"),
    (re.compile(r"(?:sebuah\s+)?ditargetkan\s+Fleeting\s+Kartu\s+Efek\b", re.I), "Kartu Efek Fleeting bertarget"),
    (re.compile(r"\bTier\s+tinggi\s+Kartu\s+(Hero|Efek|Equipment|Taktik|Mekanisme)\b", re.I), r"Kartu \1 Tier tinggi"),
    (re.compile(r"\bTier\s+tinggi\s+Kartu\b", re.I), "Kartu Tier tinggi"),
    (re.compile(r"\bNo\s+Faction\s+Kartu\s+Hero\b", re.I), "Kartu Hero [Factionless]"),
    (re.compile(r"\bLelang\s+Kartu\s+Efek\b", re.I), "Kartu Efek Lelang"),
    (re.compile(r"\bDasar\s+Kartu\s+acak\s+Equipment\b", re.I), "Kartu Equipment Dasar acak"),
    (re.compile(r"\bDasar\s+Kartu\s+Equipment\b", re.I), "Kartu Equipment Dasar"),
    (re.compile(r"\bUmum\s+Kartu\s+Equipment\b", re.I), "Kartu Equipment Normal"),
    (re.compile(r"(\d+)\s+Mekanisme\s+kartu\b", re.I), r"\1 Kartu Mekanisme"),
    (re.compile(r"\b1\s+Ditargetkan\s+Faction\s+kartu\b", re.I), "1 Kartu Faction pilihan"),
    (re.compile(r"\bEfek\s+Panduan\s+kartu\b", re.I), "Kartu Strategi Efek"),
    (re.compile(r"\bSuper\s+Energi\s+Penyimpanan\s+kartu\b", re.I), "Kartu Super Energy Storage"),
    (re.compile(r"\bsaat\s+memainkan\s+super\s+penyimpanan\b", re.I), "saat memainkan Super Energy Storage"),
    (re.compile(r"\b1\s+<b>Tinggi\s+Stakes</b>\s+kartu\b", re.I), "1 Kartu <b>High Stakes</b>"),
    (re.compile(r"\b<b>Tinggi\s+Stakes</b>\s+kartu\b", re.I), "Kartu <b>High Stakes</b>"),
    (re.compile(r"<color=#FFE897>Master\s+Artisan</color>\s+kartu\s+efek\b", re.I), "efek kartu <color=#FFE897>Master Artisan</color>"),
    # Invert tagged card names & support control tokens and parentheses
    (re.compile(r"(\d+)\s+((?:<[^>]+>)+[\u2500-\u257fA-Za-z][A-Za-z0-9 ()'·•\-:&]+(?:</[^>]+>)+)\s+[Kk]artu\b"), r"\1 Kartu \2"),
    (re.compile(r"(<color=[^>]+>)(\d+)\s+([\u2500-\u257fA-Za-z][A-Za-z0-9 ()'·•\-:&]+)\s+[Kk]artu(</color>)"), r"\1\2 Kartu \3\4"),
    (re.compile(r"((?:<[^>]+>)+[\u2500-\u257fA-Za-z][A-Za-z0-9 ()'·•\-:&]+(?:</[^>]+>)+)\s+[Kk]artu\b(?!\s+(?:Hero|Efek|Equipment|Talent|Strategi|Mekanisme|Taktik|Biru|Pilihan))"), r"Kartu \1"),
    # Tagged edge cases
    (re.compile(r"Untuk\s+setiap\s+(\d+)\s+Kartu\s+dihapus", re.I), r"Untuk setiap \1 Kartu Hero yang dihapus"),
    (re.compile(r"\b(Assassin|Tank|Marksman|Pejuang|Mage)\s+Kartu\b", re.I), r"Kartu Hero [\1]"),
    (re.compile(r"<color=#FFE897>Membeli\s+kartu\s+di\s+Shop</color>", re.I), "<color=#FFE897>Membeli di Shop</color>"),
    (re.compile(r"(\d+)\s+Kartu\s+Ancient\s+Coin\b", re.I), r"\1 Kartu Efek Ancient Coin"),
    (re.compile(r"Pilih\s+1\s+dari\s+3\s+kartu\s+\(Hero", re.I), "Pilih 1 dari 3 Kartu Hero (Hero"),
    (re.compile(r"mendapatkan\s+1\s+Kartu\s+acak\s+Efek", re.I), "mendapatkan 1 Kartu Efek acak"),
    (re.compile(r"Memperoleh\s+1\s+kartu\s+Travel\s+Together", re.I), "Memperoleh 1 Kartu Efek Travel Together"),
    (re.compile(r"Memperoleh\s+1\s+kartu\s+Memimpin", re.I), "Memperoleh 1 Kartu Efek Command"),
    (re.compile(r"Level\s+yang\s+diberikan\s+kartu\s+Ancient\s+Coin", re.I), "Level yang diberikan oleh Kartu Efek Ancient Coin"),
    (re.compile(r"ketika\s+kartu\s+dimainkan", re.I), "saat dimainkan"),
    (re.compile(r"Setiap\s+kali\s+kamu\s+Menjual\s+atau\s+menghancurkan\s+sebuah\s+kartu\s+di\s+Tangan", re.I), "Setiap kali kamu Menjual atau menghancurkan 1 Kartu Taktik di Tangan"),
    (re.compile(r"Fleeting:\s+Memperoleh\s+1\s+salinan\s+dari\s+Kartu\s+ini", re.I), "Fleeting: Memperoleh 1 salinan Kartu Hero ini"),
    (re.compile(r"Pilih\s+(<color=[^>]+>)\s*(\d+)\s+keluar\s+dari\s+(\d+)\s*(</color>)", re.I), r"Pilih \1\2 dari \3\4"),
    (re.compile(r"(\d+)\s+keluar\s+dari\s+(\d+)"), r"\1 dari \2"),
    # Bermain / Memainkan
    (re.compile(r"Saat\s+undian\s+kartu", re.I), "Saat mengambil kartu"),
    (re.compile(r"\b1\s+tambahan\s+waktu\b", re.I), "1 kali tambahan"),
    (re.compile(r"(Kartu\s+(?:Efek|Hero|Ancient\s+Coin)|Ancient\s+Coin(?:\s+atau\s+Refined\s+Ancient\s+Coin)?)\s+kamu\s+[Bb]ermain\b"), r"\1 yang kamu mainkan"),
    (re.compile(r"Saat\s+((?:<[^>]+>)*)\s*bermain\s+(?:sebuah\s+)?Awakened\s+Kartu\s+Hero", re.I), r"Saat \1memainkan Kartu Hero Awakened"),
    (re.compile(r"Saat\s+((?:<[^>]+>)*)\s*bermain\s+(?:sebuah\s+)?Kartu\s+Hero", re.I), r"Saat \1memainkan Kartu Hero"),
    (re.compile(r"Setiap\s+kali\s+kamu\s+[Bb]ermain\b"), "Setiap kali kamu memainkan"),
    (re.compile(r"\b[Bb]ermain\s+(?:sebuah\s+|sama\s+)?Kartu\s+Hero(?:\s+yang\s+sama)?"), "memainkan Kartu Hero"),
    (re.compile(r"\bkamu\s+[Bb]ermain\b"), "kamu mainkan"),
    (re.compile(r"\bBermain:"), "Saat dimainkan:"),
    (re.compile(r"\bsaat\s+(?:kamu\s+)?bermain(?:\s*,\s*|\s*\(|\s*$)", re.I), "saat dimainkan, "),
    (re.compile(r"\bsaat\s+bermain\s+sama\s+Kartu\s+Hero\s+lagi\b", re.I), "saat memainkan Kartu Hero yang sama lagi"),
    (re.compile(r"\bsaat\s+(?:kamu\s+)?bermain\b", re.I), "saat memainkan"),
    # Chess & Unit
    (re.compile(r"\bbeku\s+chess\s+bidak\b", re.I), "unit yang terkena Freeze"),
    (re.compile(r"\bdijual\s+chess\s+bidak\b", re.I), "unit yang dijual"),
    (re.compile(r"(?:sebuah\s+)?chess\s+(?:bidak|keping)\b", re.I), "unit"),
    (re.compile(r"\bchess\s+(?:bidak|keping)\b", re.I), "unit"),
    (re.compile(r"\bMenjual\s+chess\s+bidak\b", re.I), "Menjual unit"),
    (re.compile(r"\bchess\b", re.I), "unit"),
    # Sendiri & Sekutu
    (re.compile(r"(\d+)\s+sendiri\s+Hero(\s+acak)?\b", re.I), r"\1 Hero sekutu\2"),
    (re.compile(r"\bAcak\s+1\s+sendiri\s+Hero\b", re.I), "1 Hero sekutu acak"),
    (re.compile(r"\bsemua\s+sendiri\s+Hero\b", re.I), "semua Hero sekutu"),
    (re.compile(r"\bsendiri\s+Hero'\s*", re.I), "Hero sekutu "),
    (re.compile(r"\bsendiri\s+Hero\b", re.I), "Hero sekutu"),
    (re.compile(r"\bjika\s+kamu\s+sendiri\s+(?:sebuah\s+)?Level\s+2\s+Core\b", re.I), "jika kamu memiliki Core Level 2"),
    (re.compile(r"\bkamu\s+sendiri\s+(?:sebuah\s+)?", re.I), "kamu memiliki "),
    (re.compile(r"\b(?:diri\s+)?sendiri\s+((?:Max\s+)?(?:HP|Level))\b", re.I), r"\1 diri sendiri"),
    (re.compile(r"\bmenghancurkan\s+untuk\s+mereka-4\s+Equipment\b", re.I), "menghancurkan Equipment ke-4 miliknya"),
    # Level Contestant & Bebas
    (re.compile(r"(?:saat\s+ini\s+)?pemain\s+Level\b", re.I), "Level Contestant saat ini"),
    (re.compile(r"Pemain\s+Level\s+(\d+(?:[~–-]\d+)?)\b", re.I), r"Level Contestant \1"),
    (re.compile(r"\b[Pp]emain\s+Level\b"), "Level Contestant"),
    (re.compile(r"\b[Bb]ebas\s+Refresh\b"), "Refresh gratis"),
    (re.compile(r"\bFree\s+Refresh\b", re.I), "Refresh gratis"),
    (re.compile(r"(\d+)\s+bebas\s+Shop\s+Refresh\b", re.I), r"\1 Refresh Shop gratis"),
    (re.compile(r"Bebas\s+penguatan\s+([^!.,;:\n]+?)\s+di\s+menyimpan", re.I), r"penguatan gratis \1 di Shop"),
    (re.compile(r"\bdi\s+menyimpan\b", re.I), "di Shop"),
    (re.compile(r"(?:seized\s+unit|target)\s+Tidak\s+kalah\s+Level\b", re.I), "target tidak kehilangan Level"),
    (re.compile(r"\bke\s+kalah\s+(\d+%?)\b", re.I), r"kehilangan \1"),
    (re.compile(r"\b(?:kalah|ke\s+kalah)\s+(\d+%?)\s*(?:dari\s+)?(Max\s+HP|HP|Health)\b", re.I), r"kehilangan \1 \2"),
    (re.compile(r"\b(?:kalah|ke\s+kalah)\s+(HP|Health)\b", re.I), "kehilangan HP"),
    (re.compile(r"\bkalah\s+(\d+%?)\s+dari\s+Saat\s+ini\s+Menyerang\s+mereka\b", re.I), r"kehilangan \1 Attack saat ini"),
    (re.compile(r"\b(\d+)\s+total\s+menggunakan\b", re.I), r"total \1 penggunaan"),
    (re.compile(r"\bTrait\s+[Kk]emampuan\b"), "kemampuan Trait"),
    (re.compile(r"\bDitargetkan\s+Hero\b", re.I), "Hero yang ditargetkan"),
    (re.compile(r"\bHero\s+itu\s+bertahan\s+hidup\b", re.I), "Hero yang bertahan hidup"),
    (re.compile(r"\bmereka\s+diperoleh\s+Round\s+ini\b", re.I), "yang diperoleh pada Round ini"),
    (re.compile(r"\bberuntun\s+menang\s+dari\s+setidaknya\s+(\d+)\b", re.I), r"minimal \1 Win Streak"),
    (re.compile(r"\bmeningkatkan\s+di\s+Level\s+sebesar\b", re.I), "meningkatkan Level sebesar"),
    # Sisa kata Inggris
    (re.compile(r"ini\s+Equipment\s+evolves\s+sekali\b", re.I), "Equipment ini berevolusi 1 kali"),
    (re.compile(r"\bnyawa\s+menguras\b", re.I), "Lifesteal"),
    (re.compile(r"\btumbuh\s+atas\b", re.I), "naik Level"),
    (re.compile(r"\bfictitious\b", re.I), "palsu"),
    (re.compile(r"\bMantra\s+Lifesteal\b", re.I), "Magic Lifesteal"),
    (re.compile(r"\bsebuah\s+sekutu\s+Dikalahkan\b", re.I), "Hero sekutu dikalahkan"),
    (re.compile(r"\bEvolves\s+Skill\b", re.I), "Evolusi Skill"),
    (re.compile(r"\bevolves\b", re.I), "berevolusi"),
    (re.compile(r"\bseized\s+unit\b", re.I), "target"),
    (re.compile(r"\bRepeats\s+(\d+)\s+kali\b", re.I), r"Berulang \1 kali"),
    (re.compile(r"\binjects\b", re.I), "menyuntikkan"),
    (re.compile(r"\bplundered\b", re.I), "dirampas"),
    (re.compile(r"\bplunder\b", re.I), "merampas"),
    (re.compile(r"\bequivalent\s+dari\b", re.I), "setara dengan"),
    (re.compile(r"\bmanifests\b", re.I), "muncul"),
    (re.compile(r"\badalah\s+Owned\b", re.I), "dimiliki"),
    (re.compile(r"\bSihir\s+Lifesteal\b", re.I), "Magic Lifesteal"),
    (re.compile(r"\b1\s+waktu\b", re.I), "1 kali"),
    (re.compile(r"\bmemicu\s+(?:efek\s+)?Retreat\b", re.I), "memicu efek Retire"),
    # Prepositions & "peluang ke"
    (re.compile(r"\bpeluang\s+ke\s+Kembali\s+kartu\s+ke\s+Tangan\s+milikmu\b", re.I), "peluang untuk mengembalikan kartu tersebut ke Tanganmu"),
    (re.compile(r"\bpeluang\s+ke\s+Kembali\b", re.I), "peluang untuk mengembalikan"),
    (re.compile(r"\bpeluang\s+ke\s+reflect\b", re.I), "peluang memantulkan"),
    (re.compile(r"\bpeluang\s+ke\s+inflict\s+Merobek\b", re.I), "peluang memberikan efek Rend"),
    (re.compile(r"\bpeluang\s+ke\b", re.I), "peluang untuk"),
    # Adjacent duplicates & double dots
    (re.compile(r"\bdi\s+di\s+sekitarnya\b", re.I), "di sekitarnya"),
    (re.compile(r"\bdi\s+di\b", re.I), "di"),
    (re.compile(r"mendapatkan\s*(<[^>]+>)\s*mendapatkan", re.I), r"\1mendapatkan"),
    (re.compile(r"memberikan\s+(?:memberikan\s+)?Stun\b", re.I), "memberikan efek Stun"),
    (re.compile(r"\bmereka\s+mereka\s+Level\b", re.I), "Level mereka"),
    (re.compile(r"\bmereka\s+mereka\b", re.I), "mereka"),
    (re.compile(r"\bmahkota\s+daun\s+daun\b", re.I), "mahkota daun salam"),
    (re.compile(r"\bdaun\s+daun\b", re.I), "daun salam"),
    (re.compile(r"\bKartu\s+Efek\s+Efek\b", re.I), "efek Kartu Efek"),
    (re.compile(r"(?<!\.)\.\.(?!\.)"), "."),
    # Tag boundary spacing & bracket cleanup
    (re.compile(r"([A-Za-z0-9%])(<(?![/])(?:color|b|i|a|size)\b[^>]*>)"), r"\1 \2"),
    (re.compile(r"(</(?:color|b|i|a|size)>)([A-Za-z0-9])"), r"\1 \2"),
    (re.compile(r"(</color>)(\[[^\]]+\])"), r"\1 \2"),
    (re.compile(r"(\[[^\]]+\])\s*s\b"), r"\1"),
    # Clean double spaces
    (re.compile(r" {2,}"), " "),
)


def polish_indonesian_card_text(source_zh: str, text_id: str, baseline_en: str = "") -> str:
    """Polish Indonesian card description: fix Tier 1 calques, ambiguities, and canonical locks."""
    if not text_id:
        return text_id

    res = text_id

    # 1. Enforce Related Card Title sync
    for rx, repl in COMPILED_CANONICAL_RELATED_CARD_RULES:
        res = rx.sub(repl, res)

    # 2. Enforce Canonical Hero Names
    for rx, repl in COMPILED_CANONICAL_HERO_NAME_RULES:
        res = rx.sub(repl, res)

    # 3. Enforce Canonical Factions
    for rx, repl in COMPILED_CANONICAL_FACTION_RULES:
        res = rx.sub(repl, res)

    # 4. Enforce Canonical Mechanics
    for rx, repl in COMPILED_CANONICAL_MECHANIC_RULES:
        res = rx.sub(repl, res)

    # 5. First Universal Pass
    for rx, repl in POLISH_RULES_UNIVERSAL_1:
        res = rx.sub(repl, res)

    # 6. Context-dependent rules
    if "香香" in source_zh:
        res = re.sub(r"\bharum\b", "Xiang", res)
    if "扫拂" in source_zh:
        res = re.sub(r"\b<b>Menyapu</b>", "<b>Strum</b>", res)
        res = re.sub(r"\bmelalui Menyapu\b", "melalui Strum", res)
        res = re.sub(r"\bMenyapu\b", "Strum", res)
    if "横扫" in source_zh:
        res = re.sub(r"\bStrum\b", "Tebasan", res)
        res = re.sub(r"\bMenyapu\s+musuh\s+di\s+depan\b", "Menebas musuh di depan", res)
    if "交锋" in source_zh:
        res = re.sub(r"(<b>)?\bBentrokan\b(</b>)?", r"\g<1>Initiate\g<2>", res)
    if "夺取" in source_zh:
        res = re.sub(r"(?<!Soul\s)\b(?:Merebut|Capture|Plunder|Seizure|Snatch|merampas)\b", "Steal", res, flags=re.I)
    if "因缘图腾" in source_zh or "姻缘图腾" in source_zh:
        res = re.sub(r"\b(?:Destiny|Ikatan)\s+Totem\b", "Bond Totem", res, flags=re.I)
        res = re.sub(r"\b╉(?:Destiny|Ikatan)\s+Totem\b", "╉Bond Totem", res, flags=re.I)
    if "命运图腾" in source_zh:
        res = re.sub(r"\bDestiny\s+Totem\b", "Fate Totem", res, flags=re.I)
        res = re.sub(r"\b╉Destiny\s+Totem\b", "╉Fate Totem", res, flags=re.I)
        res = re.sub(r"<color=#FFE897>╉Fate\s+╉Totem</color>", "<color=#FFE897>╉Fate Totem</color>", res)
    if "镜像" in source_zh:
        res = re.sub(r"<color=#ffffff><b>cermin</b></color>", "<color=#ffffff><b>Mirror Image</b></color>", res, flags=re.I)
        res = re.sub(r"<b>cermin</b>", "<b>Mirror Image</b>", res, flags=re.I)
        res = re.sub(r"<color=#FFE897>cermin</color>", "<color=#FFE897>Mirror Image</color>", res, flags=re.I)
        res = re.sub(r"<b>cermin</b>\s*kartu\b", "kartu <b>Mirror Image</b>", res, flags=re.I)
        res = re.sub(r"\bcermin\s+Kartu\b", "Kartu Mirror Image", res, flags=re.I)
        res = re.sub(r"\bcermin\s+salinan\b", "salinan Mirror Image", res, flags=re.I)
    if "唯一" in source_zh:
        res = re.sub(r"<b>\s*(?:hanya|Unique)\s*</b>", "<b>Unik</b>", res, flags=re.I)
        res = re.sub(r"<color=#ffffff>\s*(?:hanya|Unique)\s*</color>", "<color=#ffffff>Unik</color>", res, flags=re.I)
        res = re.sub(r"<color=#ffffff><b>\s*(?:hanya|Unique)\s*</b></color>", "<color=#ffffff><b>Unik</b></color>", res, flags=re.I)
        res = re.sub(r"\bhanya\b", "Unik", res, flags=re.I)
    if "抽" in source_zh:
        res = re.sub(r"\b(?:Seri|menarik)\s+(\d+|[A-Za-z<]+)\s*kartu\b", r"Ambil \1 kartu", res, flags=re.I)
        res = re.sub(r"\b(?:Seri|menarik)\s+sebuah\s+([A-Za-z0-9 ·•\-\[\]]+)\s+Kartu\b", r"Ambil 1 Kartu \1", res, flags=re.I)
        res = re.sub(r"\b(?:Seri|menarik)\s+sebuah\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\b(?:Seri|menarik)\s+1\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\bmenarik\s+kartu\b", "mengambil kartu", res, flags=re.I)
    if "平局" in source_zh:
        res = re.sub(r"\b(?:Menarik|menarik)\s+(?:adalah\s+tidak\s+dihitung|lakukan\s+tidak\s+jumlah|tidak\s+dihitung)\b", "Seri tidak dihitung", res, flags=re.I)
        res = re.sub(r"\bDraws?\s+(?:are\s+not|not)\s+counted\b", "Seri tidak dihitung", res, flags=re.I)
        res = re.sub(r"\bties\s+are\s+not\s+counted\b", "Seri tidak dihitung", res, flags=re.I)
        res = re.sub(r"\bMenarik\b(?!\s*[/–-]|\s*Kalah|\s*Defeat)", "Seri", res)
    else:
        res = re.sub(r"\bSeri\s+(\d+|[A-Za-z<]+)\s*kartu\b", r"Ambil \1 kartu", res, flags=re.I)
        res = re.sub(r"\bSeri\s+sebuah\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\bSeri\s+1\b", "Ambil 1", res, flags=re.I)
        res = re.sub(r"\bSeri\b(?!\s*[/–-]|\s*Kalah|\s*Defeat)", "Ambil", res)
    if "第二" in source_zh and "秒" not in source_zh:
        res = re.sub(r"\bdetik\b", "ke-2", res, flags=re.I)
    if "棋手" in source_zh:
        res = re.sub(r"\bPeserta\b", "Contestant", res, flags=re.I)
    if "时光虹吸" in source_zh:
        res = re.sub(r"(?:<color=#99DEB0>)?1\s+kali\s+Menyerap(?:</color>)?(?:\s+Kartu)?", "<color=#99DEB0>1 Kartu Time Siphon</color>", res, flags=re.I)
        res = re.sub(r"\b1\s+kali\s+Menyerap\b", "1 Kartu Time Siphon", res, flags=re.I)
    if "点星" in source_zh:
        res = re.sub(r"(?:<color=#99DEB0>)?(\d+)\s+Bintang-Poin\s+Kartu(?:</color>)?", r"<color=#99DEB0>\1 Kartu Star Point</color>", res, flags=re.I)
        res = re.sub(r"\bBintang-Poin\s+Kartu\b", "Kartu Star Point", res, flags=re.I)
        res = re.sub(r"\bBintang-Poin\b", "Star Point", res, flags=re.I)
    if "珍品宝箱" in source_zh:
        res = re.sub(r"\bLangka\s+Peti\b|\bRare\s+Chests?\b", "Treasure Chest", res, flags=re.I)
    if "众星闪耀" in source_zh:
        res = re.sub(r"\bCahaya\s+bintang\s+Shimmer\b|\bStarlight\s+Shimmer\b", "Starry Radiance", res, flags=re.I)
    if "星绘秘宝" in source_zh:
        res = re.sub(r"\b(?:sebuah\s+)?Bintang\s+Cat\s+Harta\b|\bStar\s+Paint(?:ing)?\s+Treasure\b", "Star Painting Treasure", res, flags=re.I)
    if "蔷薇奖励" in source_zh:
        res = re.sub(r"\bMawar\s+Hadiah\b", "Rose Reward", res, flags=re.I)
    if "开局狂飙" in source_zh:
        res = re.sub(r"\b(?:Membuka\s+Sprint|awal\s+menerjang|Lebih\s+awal\s+game\s+Surge(?:\s+kartu)?|Early\s+Game\s+Surges?|Fast\s+Start)\b", "Early Game Surge", res, flags=re.I)
    if "妙音" in source_zh:
        res = re.sub(r"\b(?:Wondrous\s+Note|Mistis\s+Suara|Melodious\s+Suara|Melodious\s+Notes?)\b", "Melody", res, flags=re.I)
    if "全员增幅" in source_zh:
        res = re.sub(r"\b(?:Semua-Hero|Semua-Anggota)\s+Meningkatkan\b", "Team-Wide Buff", res, flags=re.I)
        res = re.sub(r"\bSemua\s+anggota\s+meningkatkan[·.]\s*1\b", "Team Buff I", res, flags=re.I)
        res = re.sub(r"\bSemua\s+anggota\s+meningkatkan[·.]\s*2\b", "Team Buff II", res, flags=re.I)
        res = re.sub(r"\bTim\s+Buff\s+II\b", "Team Buff II", res, flags=re.I)
        res = re.sub(r"\bTim\s+Buff\s+I\b", "Team Buff I", res, flags=re.I)
        res = re.sub(r",\s*meningkatkan\s+semua\s+anggota\s+sebesar\s+2\b", "Team Buff II", res, flags=re.I)
    if "离场" in source_zh and ("获得1张离场" in source_zh or "获得1张" in source_zh):
        res = re.sub(r"\b1\s+Kartu\s+Leave\b", "1 Kartu Departure", res, flags=re.I)
        res = re.sub(r"\bKartu\s+Leave\b", "Kartu Departure", res, flags=re.I)
    if "有福同享" in source_zh:
        res = re.sub(r"\b2\s+Kartu\s+Sharing\s+Is\s+Caring\b", "2 Kartu Shared Fortune", res, flags=re.I)
        res = re.sub(r"\bSharing\s+Is\s+Caring\b", "Shared Fortune", res, flags=re.I)
    if "好运连连" in source_zh:
        res = re.sub(r"\[semoga\s+berhasil\]", "[Good Luck]", res, flags=re.I)
        res = re.sub(r"\bGood\s+Luck\s+Streak\b", "[Good Luck]", res, flags=re.I)
        res = re.sub(r"(</color>)\s*(\[Good Luck\])", r"\1 \2", res)
    if "平局" in source_zh:
        res = re.sub(r"\b(?:kalah|gagal)\s*/\s*menarik\b", "kalah/seri", res, flags=re.I)
        res = re.sub(r"\b(?:kalah|defeat)\s+atau\s+ambil\b", "kalah atau seri", res, flags=re.I)
        res = re.sub(r"\bKalah/Ambil\b", "Kalah/Seri", res)
        res = re.sub(r"\bmenarik\s+adalah\s+tidak\s+dihitung\b", "Seri tidak dihitung", res, flags=re.I)
        res = re.sub(r"\bmenarik\s+lakukan\s+tidak\s+jumlah\b", "Seri tidak dihitung", res, flags=re.I)
        res = re.sub(r"\bmenarik\s+tidak\s+dihitung\b", "Seri tidak dihitung", res, flags=re.I)
        res = re.sub(r"\bMenarik\b", "Seri", res)
        res = re.sub(r"\bmenarik\b", "seri", res)

    # 7. Series / Totem OPUS-MT baseline repairs
    if "╫牺牲" in source_zh:
        sub_cand = re.sub(
            r"Mendapatkan\s+<color=#99DEB0>4\s+kartu</color>\s+Hero.*",
            "Segera memperoleh <color=#99DEB0>4</color> Kartu Hero <a href=10><color=#99DEB0>╫Sacrifice</color></a>. Saat Hero milikmu memicu <a href=10><color=#99DEB0>╫Sacrifice</color></a>, memperoleh <color=#99DEB0>1</color> Kartu Hero <a href=10><color=#99DEB0>╫Sacrifice</color></a> (maks. <color=#99DEB0>4</color> per Round).",
            res,
            flags=re.S,
        )
        if validate_translation(source_zh, sub_cand)[0]:
            res = sub_cand
    if "╬备战" in source_zh or "╬整备" in source_zh:
        sub_cand = re.sub(
            r"Mendapatkan\s+<color=#99DEB0>4\s+kartu</color>\s+Hero.*",
            "Segera memperoleh <color=#99DEB0>4</color> Kartu Hero <a href=10><color=#99DEB0>╬Prepare</color></a>. Saat Hero milikmu memicu <a href=10><color=#99DEB0>╬Prepare</color></a>, memperoleh <color=#99DEB0>1</color> Kartu Hero <a href=10><color=#99DEB0>╬Prepare</color></a> (maks. <color=#99DEB0>4</color> per Round).",
            res,
            flags=re.S,
        )
        if validate_translation(source_zh, sub_cand)[0]:
            res = sub_cand
    if "╉图腾" in source_zh and "系列" in source_zh:
        sub_cand = re.sub(
            r"Mendapatkan\s+segera\s+<color=#99DEB0>4</color>.*",
            "Segera memperoleh <color=#99DEB0>4</color> Kartu Hero Seri Summon dan ╉<color=#99DEB0>Totem</color>. Saat memanggil unit (termasuk unit Summon dan ╉Totem), peroleh <color=#99DEB0>1</color> Kartu Hero Seri Summon dan ╉<color=#99DEB0>Totem</color> (maks. <color=#99DEB0>4 kartu</color> per Round).",
            res,
            flags=re.S,
        )
        if validate_translation(source_zh, sub_cand)[0]:
            res = sub_cand
    if "召唤单位（召唤物、图腾）时" in source_zh:
        sub_cand = re.sub(
            r"Summoned\s+Unit\s+yang\s+masuk\s+field.*",
            "Saat memanggil unit Summon (unit Summon atau Totem), memperoleh tambahan Shield sebesar <color=#99DEB0>100</color> + Level pemanggil × <color=#99DEB0>80%</color>.",
            res,
            flags=re.S,
        )
        if validate_translation(source_zh, sub_cand)[0]:
            res = sub_cand

    # 8. Second Universal Pass
    for rx, repl in POLISH_RULES_UNIVERSAL_2:
        res = rx.sub(repl, res)

    return res


# --- Pre-compiled Rewrite Rules (Universal) ---
REWRITE_RULES_UNIVERSAL: tuple[tuple[re.Pattern[str], str | Callable], ...] = (
    # Structural rewrites
    (re.compile(r"\bwhen\s+your\s+Hero(?:es)?\s+defeats?\s+an\s+enemy\b", re.I), "saat Hero milikmu mengalahkan musuh"),
    (re.compile(r"\bwhen\s+your\s+Hero(?:es)?\s+(?:applies|apply|inflicts?)\s+a\s+Crowd\s+Control\s+effect\b", re.I), "saat Hero milikmu memberikan efek Crowd Control"),
    (re.compile(r"\bplay\s+your\s+first\s+(\d+)\s+Awakened\s+Hero\s+(?:Cards|cards)\b", re.I), r"memainkan \1 Kartu Hero Awakened pertamamu"),
    (re.compile(r"\bThe\s+first\s+(\[[^\]]+\])\s+Hero\s+Card\s+you\s+Play\b", re.I), r"Kartu Hero \1 pertama yang kamu mainkan"),
    (re.compile(r"\bfirst\s+(\[[^\]]+\])\s+Hero\s+Card\s+you\s+Play\b", re.I), r"Kartu Hero \1 pertama yang kamu mainkan"),
    (re.compile(r"\b(\[[^\]]+\])\s+Hero\s+Cards?\b", re.I), r"Kartu Hero \1"),
    (re.compile(rf"(\d+)\s+random\s+(?:\[)?(?:The\s+)?({UNBRACKETED_FACTIONS})(?:\])?\s+Hero\s+Cards?\b", re.I), r"\1 Kartu Hero [\2] acak"),
    (re.compile(rf"a\s+random\s+non-(?:\[)?(?:The\s+)?({UNBRACKETED_FACTIONS})(?:\])?\s+Hero\s+Card\b", re.I), r"1 Kartu Hero non-[\1] acak"),
    (re.compile(rf"a\s+random\s+(?:\[)?(?:The\s+)?({UNBRACKETED_FACTIONS})(?:\])?\s+Hero\s+Card\b", re.I), r"1 Kartu Hero [\1] acak"),
    (re.compile(rf"random\s+(?:\[)?(?:The\s+)?({UNBRACKETED_FACTIONS})(?:\])?\s+Hero\s+Cards?\b", re.I), r"Kartu Hero [\1] acak"),
    (re.compile(rf"(?:\[)?(?:The\s+)?({UNBRACKETED_FACTIONS})(?:\])?\s+Hero\s+Cards?\b", re.I), r"Kartu Hero [\1]"),
    (re.compile(r"\ban?\s+off-(?:field|board)\s+(<[^>]+>)?\s*(Tier\s+\d+|\d+-Tier)\s+Hero\b", re.I), r"Hero \1\2 yang belum ada di arena"),
    (re.compile(r"\boff-(?:field|board)\s+call\b", re.I), "panggilan bantuan luar arena"),
    (re.compile(r"\boff-(?:field|board)\b", re.I), "di luar arena"),
    (re.compile(r"\bHero(?:es)?\s+you\s+own\s+that\s+(?:is|are)\s+at\s+least\s+[Ll]evel\s+(\d+)\b", re.I), r"Hero milikmu minimal Level \1"),
    (re.compile(r"\bthat\s+is\s+(\d+)\s+Tier\s+higher\b", re.I), r"yang \1 Tier lebih tinggi"),
    (re.compile(r"\bthat\s+is\s+not\s+higher\s+than\b", re.I), "yang tidak melebihi"),
    (re.compile(r"\bthat\s+is\s+not\s+lower\s+than\b", re.I), "yang tidak lebih rendah daripada"),
    (re.compile(r"\bif\s+it\s+is\s+a\s+Tier\s+(\d+)\s+Hero\b", re.I), r"jika Hero Tier \1"),
    (re.compile(r"\bto\s+randomly\b", re.I), "untuk secara acak"),
    (re.compile(r"\bto\s+enact\b", re.I), "untuk diberlakukan"),
    (re.compile(r"\bfor\s+the\s+remainder\s+of\s+the\s+match\b", re.I), "selama sisa pertandingan"),
    (re.compile(r"\bby\s+an\s+amount\s+equal\s+to\b", re.I), "sebesar"),
    (re.compile(r"\bdepending\s+on\s+whether\b", re.I), "tergantung apakah"),
    (re.compile(r"\bon\s+draw/defeat\b", re.I), "saat Seri/Kalah"),
    (re.compile(r"\bDraw/Defeat\b", re.I), "Seri/Kalah"),
    (re.compile(r"\b(\d+)\s+fox\s*fires\b", re.I), r"\1 api rubah"),
    (re.compile(r"\bfox\s*fires\b", re.I), "api rubah"),
    (re.compile(r"\bfoxfire\b", re.I), "api rubah"),
    # Second, auction, yuan, top 3
    (re.compile(r"\byour\s+second-row\s+Hero(?:es)?\b", re.I), "Hero baris ke-2 milikmu"),
    (re.compile(r"\bsecond-row\s+Hero(?:es)?\b", re.I), "Hero baris ke-2"),
    (re.compile(r"\bAfter\s+the\s+(?:second|2nd)\s+and\s+(?:third|3rd)\s+[Aa]uctions?,?\s*", re.I), "Setelah Lelang ke-2 dan ke-3, "),
    (re.compile(r"\bsecond\s+[Aa]uction\s+[Rr]ound\b", re.I), "Lelang Putaran ke-2"),
    (re.compile(r"\bSecond\s+Round\s+Auction\b", re.I), "Lelang Putaran ke-2"),
    (re.compile(r"\b0\s+Yuan\s+Purchase:?\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\b0\s+Yuan\s+Buy:?\s*", re.I), "Beli 0 Gold: "),
    (re.compile(r"\bWhen\s+placing\s+in\s+the\s+top\s+3\b", re.I), "Saat masuk 3 besar"),
    (re.compile(r"\bIf\s+you\s+finish\s+in\s+the\s+top\s+3\b", re.I), "Saat masuk 3 besar"),
    (re.compile(r"\bRecord all\b", re.I), "Mencatat semua"),
    (re.compile(r"\bRecord\b"), "Mencatat"),
    (re.compile(r"\bFrom now on,?\s*", re.I), "Mulai sekarang, "),
    (re.compile(r"\bfrom now on\b", re.I), "mulai sekarang"),
    (re.compile(r"\bthese Cards\b", re.I), "Kartu ini"),
    (re.compile(r"\bthis Card\b", re.I), "Kartu ini"),
    (re.compile(r"\bof the next Round\b", re.I), "pada Round berikutnya"),
    (re.compile(r"\bnext Round\b", re.I), "Round berikutnya"),
    (re.compile(r"\b(?:connected|linked)\s+Hero\b", re.I), "Hero yang terhubung"),
    (re.compile(r"\bnearest enemy\b", re.I), "musuh terdekat"),
    (re.compile(r"\boriginal location\b", re.I), "lokasi awal"),
    (re.compile(r"\byour Heroes gain\s+(\d+)\b", re.I), r"Hero sekutu mendapat +\1"),
    (re.compile(r"\ballied heroes gain\s+(\+?\d+%?)\b", re.I), r"Hero sekutu mendapat \1"),
    (re.compile(r"\bHeroes that survive Combat retain\b", re.I), "Hero yang bertahan hidup saat Combat mempertahankan"),
    (re.compile(r"\blittle dodder\b", re.I), "Xiao Tu"),
    (re.compile(r"\bMystical Kekuatan\b", re.I), "Mystical Power"),
    (re.compile(r"\bMisterius Kekuatan\b", re.I), "Mystical Power"),
    (re.compile(r"\b(\d+)\s+pieces?\s+of\s+", re.I), r"\1 "),
    (re.compile(r"\bThe bearer can become a Hero of the\s*(\[[^\]]+\])\s*camp\.?", re.I), r"Pemakai dapat menjadi Hero Faction \1."),
    (re.compile(r"\bchoose\s+(\d+)\s+out\s+of\s+(\d+)\b", re.I), r"pilih \1 dari \2"),
    (re.compile(r"\bDoes not stack\b", re.I), "Tidak dapat ditumpuk"),
    (re.compile(r"\bif there is no\s+([A-Za-z\[\] ]+?)\s+in the Current Card pool\b", re.I), r"jika tidak ada \1 di Card Pool saat ini"),
    (re.compile(r"\b(?:Lots of Friends|Plenty of Friends)\b", re.I), "Many Friends"),
    (re.compile(r"\bGain\s+(\d+)\s+([A-Za-z0-9 ·•\-\[\]]+)\."), r"Memperoleh \1 \2."),
    (re.compile(r"\bGain\s+(\d+)\s+([A-Za-z0-9 ·•\-\[\]]+)"), r"Memperoleh \1 \2"),
    (re.compile(r"\bRestore\s+(\d+)\{LordHp\}\."), r"Memulihkan \1 {LordHp}."),
    (re.compile(r"\bRestore\s+(\d+)\{LordHp\}"), r"Memulihkan \1 {LordHp}"),
    (re.compile(r"\bAfter use,?\s*", re.I), "Setelah digunakan, "),
    (re.compile(r"\bcreates a clone at\b", re.I), "menciptakan clone di"),
    (re.compile(r"\bwith 30% Max HP\b", re.I), "dengan 30% Max HP"),
    (re.compile(r"\bUpon death,?\s*", re.I), "Saat gugur, "),
    (re.compile(r"\bit stuns\b", re.I), "memberikan stun kepada"),
    (re.compile(r"\bThe clone cannot Attack\b", re.I), "Clone tidak dapat Attack"),
    (re.compile(r"\band taunts the nearest enemy for\b", re.I), "dan memprovokasi musuh terdekat selama"),
    (re.compile(r"\bupon creation\b", re.I), "saat diciptakan"),
)


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

    # Sync canonical proper names first
    for rx, repl in COMPILED_CANONICAL_RELATED_CARD_RULES:
        text = rx.sub(repl, text)
    for rx, repl in COMPILED_CANONICAL_HERO_NAME_RULES:
        text = rx.sub(repl, text)
    for rx, repl in COMPILED_CANONICAL_FACTION_RULES:
        text = rx.sub(repl, text)
    for rx, repl in COMPILED_CANONICAL_MECHANIC_RULES:
        text = rx.sub(repl, text)

    # Universal structural rewrites
    for rx, repl in REWRITE_RULES_UNIVERSAL:
        text = rx.sub(repl, text)

    # Draw translations
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

    return polish_indonesian_card_text(source_zh, text, baseline_en)
