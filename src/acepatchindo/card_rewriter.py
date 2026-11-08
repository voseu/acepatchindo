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
    r"\bTier 5 Hero Exchange Vouchers\b": "Tier 5 Hero Voucher",
    r"\bTier 5 Hero Exchange Voucher\b": "Tier 5 Hero Voucher",
    r"\bGlitch Bots\b": "Glitch Robot",
    r"\"Glitch Bots\"": '"Glitch Robot"',
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

    # 6. rahasia kartu / rahasia teknik kartu / Rahasia Skill kartu
    res = re.sub(r"\b(?:rahasia\s+(?:kartu|teknik\s+kartu|teknik|skill)|Rahasia\s+(?:Teknik|Skill)\s+[Kk]artu)\b", "Kartu Secret Skill", res, flags=re.I)
    res = re.sub(r"1\s+(<[^>]+>[^<]+</[^>]+>)\s+Kartu Secret Skill\b", r"1 Kartu Secret Skill \1", res)
    res = re.sub(r"1\s+<b>([^<]+)</b>\s+Kartu Secret Skill\b", r"1 Kartu Secret Skill <b>\1</b>", res)

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

    # 13. Banyak dari Teman
    res = re.sub(r"\b(?:Lots of Friends|Plenty of Friends|Banyak dari Teman)\b", "Many Friends", res, flags=re.I)

    # Sub-card Copier: itu Kartu Hero -> Kartu Hero tersebut
    res = re.sub(r"\bitu\s+Kartu\s+Hero\b", "Kartu Hero tersebut", res, flags=re.I)

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
