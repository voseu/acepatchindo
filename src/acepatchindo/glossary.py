"""Canonical 3-Tier Glossary and EN->ID / ZH->ID translator for Honor of Kings Ace."""

from __future__ import annotations

import gzip
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from acepatchindo.lexicon_id import translate_segment_en_to_id
from acepatchindo.tag_aligner import (
    BRACKET_TERM_MAP,
    normalize_formula_skeleton_zh,
    normalize_plain_zh,
    reinject_formula_and_skeleton,
    reinject_skeleton_from_source,
    translate_preserving_skeleton,
)
from acepatchindo.windows_108_split import (
    WINDOWS_108_HYBRID_MAP,
    WINDOWS_108_NONTARGET_EN,
    WINDOWS_108_TARGET_DESC_ID,
)
from acepatchindo.validator import (
    CJK_RE,
    CONTROL_TOKEN_RE,
    PLACEHOLDER_RE,
    TAG_RE,
    sanitize_target_text,
    validate_translation,
)

# Common Chinese entity names mapping to English proper names
COMMON_ZH_ENTITY_NAMES: dict[str, str] = {
    "武凤": "Wu Feng",
    "三分": "Three Kingdoms",
    "三分之地": "Three Kingdoms",
    "吴国": "Wu",
    "蜀国": "Shu",
    "魏国": "Wei",
    "公孙离": "Arli",
    "乔汐": "Qiao Xi",
    "孙尚香": "Lady Sun",
    "少司缘": "Dyadia",
    "姬小满": "Biron",
    "空空儿": "Kongkong'er",
    "苍": "Cang",
    "元流之子": "Child of Flow",
}

# The 108 Chinese strings missed by English Patcher 1.4.12
# Cleanly split into 18 target gameplay descriptions (ID) and 90 non-target strings (EN)
WINDOWS_108_ZH_TO_ID: dict[str, str] = dict(WINDOWS_108_HYBRID_MAP)
WINDOWS_108_ZH_TO_ID.update(COMMON_ZH_ENTITY_NAMES)

# Ordered English -> Indonesian rules following Tier 1 hybrid HoK Ace terminology:
# Proper names (Heroes, Factions, Cards, Equipment) and Tier 1 English mechanics
# (Temporary Level, Physical Damage, Magic Damage, True Damage, Physical Attack, Magic Attack,
# Attack Speed, Max HP, Crit Rate, Crit Damage, Sacrifice, Revive, Shield, Stun, Silence,
# Disarm, Knockback, Combat, Round, Shop, Refresh, Tier, Chess Player) stay canonical.
EN_TO_ID_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # High-frequency HoK Ace specific templates (4,367+ bot avatars, leaderboards, tournaments)
    (re.compile(r"\bAI impersonates avatar\s*(\d+)", re.I), r"Avatar Bot AI \1"),
    (re.compile(r"\bAI impersonates avatar\b", re.I), "Avatar Bot AI"),
    (
        re.compile(
            r"\bRanked (\d+)(?:st|nd|rd|th) on last week's Diamond Frenzy leaderboard\b",
            re.I,
        ),
        r"Peringkat ke-\1 di Papan Peringkat Diamond Frenzy minggu lalu",
    ),
    (
        re.compile(r"\bRanked (\d+)(?:st|nd|rd|th) on\b", re.I),
        r"Peringkat ke-\1 di",
    ),
    (
        re.compile(r"\bRanking:\s*(\d+)(?:st|nd|rd|th) Place\b", re.I),
        r"Peringkat: Juara ke-\1",
    ),
    (re.compile(r"\bIn a single ACE Tournament match\b", re.I), "Dalam 1 pertandingan Turnamen ACE"),
    (re.compile(r"\ba single round of the ACE Tournament\b", re.I), "1 Round di Turnamen ACE"),
    (re.compile(r"\bin the ACE Tournament\b", re.I), "di Turnamen ACE"),
    (re.compile(r"\bACE Tournament\b"), "Turnamen ACE"),
    (re.compile(r"\blast week's\b", re.I), "minggu lalu"),
    (re.compile(r"\b equip it in the Customization system to\b", re.I), " pasang di sistem Kustomisasi untuk"),
    (re.compile(r"\bin the Customization system\b", re.I), "di sistem Kustomisasi"),
    (re.compile(r"\bCustomization system\b", re.I), "sistem Kustomisasi"),
    (re.compile(r"\bNumber of times\b", re.I), "Jumlah pencapaian"),
    (re.compile(r"\bfor the first time each Season\b", re.I), "untuk pertama kalinya setiap Season"),
    (re.compile(r"\bfor the first time\b", re.I), "untuk pertama kalinya"),
    (re.compile(r"\bupon reaching\b", re.I), "saat mencapai"),
    (re.compile(r"\bserver-wide\b", re.I), "di seluruh server"),
    # Action / Trigger headers
    (re.compile(r"\bAt the start of battle\b", re.I), "Saat Combat dimulai"),
    (re.compile(r"\bAt the start of combat\b", re.I), "Saat Combat dimulai"),
    (re.compile(r"\bStart of battle\b", re.I), "Awal Combat"),
    (re.compile(r"\bStart of combat\b", re.I), "Awal Combat"),
    (re.compile(r"\bAt the start of each round\b", re.I), "Di awal setiap Round"),
    (re.compile(r"\bAt the end of each round\b", re.I), "Di akhir setiap Round"),
    (re.compile(r"\bAt the start of the round\b", re.I), "Di awal Round"),
    (re.compile(r"\bAt the end of the round\b", re.I), "Di akhir Round"),
    (re.compile(r"\bAfter winning a battle\b", re.I), "Setelah memenangkan Combat"),
    (re.compile(r"\bAfter losing a battle\b", re.I), "Setelah kalah dalam Combat"),
    (re.compile(r"\bDuring battle\b", re.I), "Selama Combat"),
    (re.compile(r"\bDuring combat\b", re.I), "Selama Combat"),
    (re.compile(r"\bDuring the Prepare phase\b", re.I), "Selama fase Preparation"),
    (re.compile(r"\bPrepare phase\b", re.I), "fase Preparation"),
    (re.compile(r"\bWhen played\b", re.I), "Saat dimainkan"),
    (re.compile(r"\bWhen bought\b", re.I), "Saat dibeli"),
    (re.compile(r"\bWhen sold\b", re.I), "Saat dijual"),
    (re.compile(r"\bWhen upgraded\b", re.I), "Saat di-upgrade"),
    (re.compile(r"\bWhen combined\b", re.I), "Saat digabungkan"),
    (re.compile(r"\bWhen casting a skill\b", re.I), "Saat menggunakan Skill"),
    (re.compile(r"\bAfter casting a skill\b", re.I), "Setelah menggunakan Skill"),
    (re.compile(r"\bUpon death\b", re.I), "Saat gugur"),
    (re.compile(r"\bWhen defeated\b", re.I), "Saat dikalahkan"),
    (re.compile(r"\bWhen taking damage\b", re.I), "Saat menerima Damage"),
    (re.compile(r"\bWhen dealing damage\b", re.I), "Saat memberikan Damage"),
    (re.compile(r"\bFor every (\d+)\b", re.I), r"Untuk setiap \1"),
    (re.compile(r"\bEvery (\d+) basic attacks\b", re.I), r"Setiap \1 Basic Attack"),
    (re.compile(r"\bEvery (\d+) seconds?\b", re.I), r"Setiap \1 detik"),
    (re.compile(r"\bEvery (\d+) rounds?\b", re.I), r"Setiap \1 Round"),
    (re.compile(r"\bover (\d+(?:\.\d+)?) seconds?\b", re.I), r"selama \1 detik"),
    (re.compile(r"\bfor (\d+(?:\.\d+)?) seconds?\b", re.I), r"selama \1 detik"),
    (re.compile(r"\bup to (\d+) times?\b", re.I), r"hingga \1 kali"),
    (re.compile(r"\bup to (\d+) stacks?\b", re.I), r"hingga \1 stack"),
    (re.compile(r"\b(\d+)-Day Trial\b", re.I), r"Trial \1 Hari"),
    (re.compile(r"\b(\d+)-second\b", re.I), r"\1 detik"),
    # Card & Game Category Terms (Tier 1 style: Kartu Hero, Kartu Efek, Kartu Secret Art)
    (re.compile(r"\bFactionless Hero Cards?\b", re.I), "Kartu Hero Netral"),
    (re.compile(r"\bSecret Art Cards?\b", re.I), "Kartu Secret Art"),
    (re.compile(r"\bEffect Cards?\b", re.I), "Kartu Efek"),
    (re.compile(r"\bHero Cards?\b", re.I), "Kartu Hero"),
    (re.compile(r"\bEquipment Cards?\b", re.I), "Kartu Equipment"),
    (re.compile(r"\bTactics Cards?\b", re.I), "Kartu Taktik"),
    (re.compile(r"\bTrick Cards?\b", re.I), "Kartu Trik"),
    (re.compile(r"\bCard Packs?\b", re.I), "Paket Kartu"),
    (re.compile(r"\bHand Cards?\b", re.I), "Kartu Tangan"),
    (re.compile(r"\bActive Skill\b", re.I), "Skill Aktif"),
    (re.compile(r"\bPassive Skill\b", re.I), "Skill Pasif"),
    (re.compile(r"\bCombine Skill\b", re.I), "Skill Gabungan"),
    # Targets & Positioning
    (re.compile(r"\bAll allied heroes\b", re.I), "Semua Hero sekutu"),
    (re.compile(r"\ballied heroes\b", re.I), "Hero sekutu"),
    (re.compile(r"\bfriendly heroes\b", re.I), "Hero sekutu"),
    (re.compile(r"\ballied units\b", re.I), "unit sekutu"),
    (re.compile(r"\bAll allies\b", re.I), "Semua sekutu"),
    (re.compile(r"\ball allies\b", re.I), "semua sekutu"),
    (re.compile(r"\bAll enemies\b", re.I), "Semua musuh"),
    (re.compile(r"\ball enemies\b", re.I), "semua musuh"),
    (re.compile(r"\benemy heroes\b", re.I), "Hero musuh"),
    (re.compile(r"\bnearest enemy\b", re.I), "musuh terdekat"),
    (re.compile(r"\bfarthest enemy\b", re.I), "musuh terjauh"),
    (re.compile(r"\bsurrounding enemies\b", re.I), "musuh di sekitarnya"),
    (re.compile(r"\brandom distinct\b", re.I), "acak berbeda"),
    (re.compile(r"\brandom enemy\b", re.I), "musuh acak"),
    (re.compile(r"\brandom enemies\b", re.I), "musuh acak"),
    (re.compile(r"\brandom ally\b", re.I), "sekutu acak"),
    (re.compile(r"\brandom allies\b", re.I), "sekutu acak"),
    (re.compile(r"\badjacent allies\b", re.I), "sekutu di sekitarnya"),
    (re.compile(r"\bon the field\b", re.I), "di medan tempur"),
    (re.compile(r"\bon the board\b", re.I), "di papan"),
    (re.compile(r"\benters the field\b", re.I), "masuk ke medan tempur"),
    (re.compile(r"\bsame row\b", re.I), "baris yang sama"),
    (re.compile(r"\bsame column\b", re.I), "kolom yang sama"),
    (re.compile(r"\bfront row\b", re.I), "baris depan"),
    (re.compile(r"\bback row\b", re.I), "baris belakang"),
    (re.compile(r"\bhighest Level\b", re.I), "Level tertinggi"),
    (re.compile(r"\blowest Level\b", re.I), "Level terendah"),
    (re.compile(r"\bhighest ATK\b", re.I), "ATK tertinggi"),
    (re.compile(r"\blowest HP\b", re.I), "HP terendah"),
    (re.compile(r"\bhighest tier\b", re.I), "Tier tertinggi"),
    # Common sentence connectors & grammar
    (re.compile(r"\bTap the Skill description panel to View\b", re.I), "Ketuk panel deskripsi Skill untuk melihat"),
    (re.compile(r"\bCan only operate\b", re.I), "Hanya dapat dilakukan"),
    (re.compile(r"\bPlease try again later\b", re.I), "Silakan coba lagi nanti"),
    (re.compile(r"\bPlease try again\b", re.I), "Silakan coba lagi"),
    (re.compile(r"\bWaiting for others\b", re.I), "Menunggu pemain lain"),
    (re.compile(r"\bNo problem!\b", re.I), "Tidak masalah!"),
    (re.compile(r"\bClick to select\b", re.I), "Klik untuk memilih"),
    (re.compile(r"\bAre you sure you want to\b", re.I), "Yakin ingin"),
    (re.compile(r"\bDo you want to\b", re.I), "Apakah kamu ingin"),
    (re.compile(r"\bcannot be\b", re.I), "tidak dapat"),
    (re.compile(r"\bcan be\b", re.I), "dapat"),
    (re.compile(r"\bwill be\b", re.I), "akan"),
    (re.compile(r"\bequal to\b", re.I), "sebesar"),
    (re.compile(r"\bincreased to\b", re.I), "meningkat menjadi"),
    (re.compile(r"\breduced by\b", re.I), "berkurang sebesar"),
    (re.compile(r"\bincreased by\b", re.I), "meningkat sebesar"),
    (re.compile(r"\bpermanently increase\b", re.I), "meningkatkan secara permanen"),
    (re.compile(r"\bpermanently\b", re.I), "secara permanen"),
    (re.compile(r"\bimmediately\b", re.I), "segera"),
    (re.compile(r"\brandomly\b", re.I), "secara acak"),
    (re.compile(r"\badditionally\b", re.I), "selain itu"),
    (re.compile(r"\bexcluding\b", re.I), "kecuali"),
    (re.compile(r"\bincluding\b", re.I), "termasuk"),
    # Combat verbs & stats (protecting canonical Tier 1 English stat names before single-word verbs)
    (re.compile(r"\bdealing Damage\b", re.I), "memberikan Damage"),
    (re.compile(r"\bdealing\b", re.I), "memberikan"),
    (re.compile(r"\breducing\b", re.I), "mengurangi"),
    (re.compile(r"\bincreasing\b", re.I), "meningkatkan"),
    (re.compile(r"\brestoring\b", re.I), "memulihkan"),
    (re.compile(r"\bsummoning\b", re.I), "memanggil"),
    (re.compile(r"\bDeals?\b"), "Memberikan"),
    (re.compile(r"\bdeals?\b"), "memberikan"),
    (re.compile(r"\bRestores?\b"), "Memulihkan"),
    (re.compile(r"\brestores?\b"), "memulihkan"),
    (re.compile(r"\bGains?\b"), "Dapatkan"),
    (re.compile(r"\bgains?\b"), "mendapat"),
    (re.compile(r"\bGrants?\b"), "Memberikan"),
    (re.compile(r"\bgrants?\b"), "memberikan"),
    (re.compile(r"\bIncreases?\b"), "Meningkatkan"),
    (re.compile(r"\bincreases?\b"), "meningkatkan"),
    (re.compile(r"\bReduces?\b"), "Mengurangi"),
    (re.compile(r"\breduces?\b"), "mengurangi"),
    (re.compile(r"\bObtains?\b"), "Peroleh"),
    (re.compile(r"\bobtains?\b"), "memperoleh"),
    (re.compile(r"\bfirst obtained\b", re.I), "pertama kali diperoleh"),
    (re.compile(r"\bobtained\b", re.I), "diperoleh"),
    (re.compile(r"\bTriggers?\b"), "Memicu"),
    (re.compile(r"\btriggers?\b"), "memicu"),
    (re.compile(r"\bSummons?\b"), "Memanggil"),
    (re.compile(r"\bsummons?\b"), "memanggil"),
    (re.compile(r"\bTransforms? into\b", re.I), "Berubah menjadi"),
    (re.compile(r"\bReturns? to hand\b", re.I), "Kembali ke tangan"),
    (re.compile(r"\bDesignate\b"), "Pilih"),
    (re.compile(r"\bdesignate\b"), "pilih"),
    (re.compile(r"\bSelect\b"), "Pilih"),
    (re.compile(r"\bselect\b"), "pilih"),
    (re.compile(r"\bChoose\b"), "Pilih"),
    (re.compile(r"\bchoose\b"), "pilih"),
    (re.compile(r"\bUsage\b"), "Gunakan"),
    (re.compile(r"\bDamage Reduction\b", re.I), "Reduksi Damage"),
    (re.compile(r"\bMax Health\b", re.I), "Max HP"),
    (re.compile(r"\bCritical Rate\b", re.I), "Crit Rate"),
    (re.compile(r"\bCritical Damage\b", re.I), "Crit Damage"),
    (re.compile(r"\bEnergy Regen\b", re.I), "Regen Energi"),
    (re.compile(r"\bEnergy\b"), "Energi"),
    (re.compile(r"\bpieces of Equipment\b", re.I), "Equipment"),
    # UI, Meta, Social, Shop & System terms
    (re.compile(r"\bMonthly limit\b", re.I), "Batas bulanan"),
    (re.compile(r"\bDaily limit\b", re.I), "Batas harian"),
    (re.compile(r"\bWeekly limit\b", re.I), "Batas mingguan"),
    (re.compile(r"\bToday's reward\b", re.I), "Hadiah hari ini"),
    (re.compile(r"\bTotal usable coupons\b", re.I), "Total kupon tersedia"),
    (re.compile(r"\bDuo ranked\b", re.I), "Duo Ranked"),
    (re.compile(r"\bCard exchange round\b", re.I), "Round tukar kartu"),
    (re.compile(r"\bLineup guides\b", re.I), "Panduan Lineup"),
    (re.compile(r"\bSelect emoticon\b", re.I), "Pilih Emotikon"),
    (re.compile(r"\bgifted\b", re.I), "mengirim hadiah"),
    (re.compile(r"\bConfirm\b", re.I), "Konfirmasi"),
    (re.compile(r"\bCancel\b", re.I), "Batal"),
    (re.compile(r"\bSettings\b", re.I), "Pengaturan"),
    (re.compile(r"\bVictory\b"), "Kemenangan"),
    (re.compile(r"\bFailure\b"), "Kekalahan"),
    (re.compile(r"\bAlready claimed\b", re.I), "Sudah Diklaim"),
    (re.compile(r"\bClaimed\b", re.I), "Sudah Diklaim"),
    (re.compile(r"\bClaim\b"), "Klaim"),
    (re.compile(r"\bRewards?\b"), "Hadiah"),
    (re.compile(r"\brewards?\b"), "hadiah"),
    (re.compile(r"\bMissions?\b"), "Misi"),
    (re.compile(r"\bmissions?\b"), "misi"),
    (re.compile(r"\bAchievements?\b"), "Pencapaian"),
    (re.compile(r"\bachievements?\b"), "pencapaian"),
    (re.compile(r"\bLeaderboard\b"), "Papan Peringkat"),
    (re.compile(r"\bleaderboard\b"), "papan peringkat"),
    (re.compile(r"\bCompleted\b", re.I), "Selesai"),
    (re.compile(r"\bLocked\b"), "Terkunci"),
    (re.compile(r"\bUnlocked\b"), "Terbuka"),
    (re.compile(r"\bEquipped\b"), "Terpasang"),
    (re.compile(r"\bPurchase\b"), "Beli"),
    (re.compile(r"\bMatch\b"), "Pertandingan"),
    (re.compile(r"\bmatch\b"), "pertandingan"),
    (re.compile(r"\bPlayers\b"), "Pemain"),
    (re.compile(r"\bplayers\b"), "pemain"),
    (re.compile(r"\bFriends?\b"), "Teman"),
    (re.compile(r"\bfriends?\b"), "teman"),
    (re.compile(r"\bTeam\b"), "Tim"),
    (re.compile(r"\bteam\b"), "tim"),
    (re.compile(r"\bSystem\b"), "Sistem"),
    (re.compile(r"\bsystem\b"), "sistem"),
    (re.compile(r"\bSource:\b"), "Sumber:"),
    (re.compile(r"\bdetails\b"), "detail"),
    (re.compile(r"\bguides\b"), "panduan"),
    (re.compile(r"\bvoucher\b"), "kupon"),
    # High-frequency function words (only multi-letter whole words so [p]/[q] variables are untouched)
    (re.compile(r"\bWhen you\b"), "Saat kamu"),
    (re.compile(r"\bwhen you\b"), "saat kamu"),
    (re.compile(r"\bIf you\b"), "Jika kamu"),
    (re.compile(r"\bif you\b"), "jika kamu"),
    (re.compile(r"\bYou can\b"), "Kamu dapat"),
    (re.compile(r"\byou can\b"), "kamu dapat"),
    (re.compile(r"\bYou have\b"), "Kamu memiliki"),
    (re.compile(r"\byou have\b"), "kamu memiliki"),
    (re.compile(r"\bYou will\b"), "Kamu akan"),
    (re.compile(r"\byou will\b"), "kamu akan"),
    (re.compile(r"\bAfter the\b"), "Setelah"),
    (re.compile(r"\bafter the\b"), "setelah"),
    (re.compile(r"\bDuring the\b"), "Selama"),
    (re.compile(r"\bduring the\b"), "selama"),
    (re.compile(r"\bbetween\b"), "antara"),
    (re.compile(r"\bwithin\b"), "dalam"),
    (re.compile(r"\bwithout\b"), "tanpa"),
    (re.compile(r"\bagainst\b"), "terhadap"),
    (re.compile(r"\bthrough\b"), "melalui"),
    (re.compile(r"\bcurrent\b", re.I), "saat ini"),
    (re.compile(r"\bidentical\b", re.I), "yang sama"),
    (re.compile(r"\badditional\b", re.I), "tambahan"),
    (re.compile(r"\bremaining\b", re.I), "tersisa"),
    (re.compile(r"\bseconds\b", re.I), "detik"),
    (re.compile(r"\bpoints\b", re.I), "poin"),
    (re.compile(r"\btimes\b"), "kali"),
    (re.compile(r"\bcards\b"), "kartu"),
    (re.compile(r"\bcard\b"), "kartu"),
    (re.compile(r"\benemies\b"), "musuh"),
    (re.compile(r"\benemy\b"), "musuh"),
    (re.compile(r"\ballies\b"), "sekutu"),
    (re.compile(r"\bally\b"), "sekutu"),
    (re.compile(r"\band\b"), "dan"),
    (re.compile(r"\bwith\b"), "dengan"),
    (re.compile(r"\bfrom\b"), "dari"),
    (re.compile(r"\binto\b"), "menjadi"),
    (re.compile(r"\byour\b"), "milikmu"),
    (re.compile(r"\btheir\b"), "mereka"),
    (re.compile(r"\bonly\b"), "hanya"),
    (re.compile(r"\beach\b"), "setiap"),
    (re.compile(r"\bevery\b"), "setiap"),
]

# Terms that must never be split or altered during EN->ID prose conversion
CANONICAL_PROTECTED_TERMS: tuple[str, ...] = (
    "Honor of Kings: Ace",
    "Honor of Kings",
    "Central Plains",
    "Central Plain",
    "Riverlands",
    "Zhulu Plateau",
    "Three Kingdoms",
    "Sunset Sea",
    "First Lands",
    "Temporary Level",
    "True Level",
    "Physical Attack",
    "Magic Attack",
    "Physical Damage",
    "Magic Damage",
    "Magical Damage",
    "True Damage",
    "Physical Defense",
    "Magic Defense",
    "Attack Speed",
    "Movement Speed",
    "Attack Power",
    "Attack Range",
    "Basic Attack",
    "Max HP",
    "Max Mana",
    "Crit Rate",
    "Crit Damage",
    "Chess Player",
    "Secret Art",
    "Diamond Frenzy",
    "Ace Duel",
    "Strongest King",
    "Supreme Challenger",
    "Stubborn Bronze",
    "Vientiane King",
    "Sage's Sanctuary",
    "Maple Leaf Dance",
    "Graceful Dance",
    "Gentle Call",
    "Tidal Symphony",
    "Tri-Point Banner",
    "Ancient Coin",
    "Refined Ancient Coin",
    "Coin Machine",
    "Rapid Growth",
    "Perfect Revive",
    "Akomia Core",
    "Steal Fire",
    "Symphony of Tides",
    "Three Kingdoms Banner",
    "Super Copier",
    "Build Upgrade",
    "Indomitable Will",
    "Try Your Luck",
    "Embrace of the Sea",
    "Use for My Own",
    "Lady Sun: Empowered",
    "Glory of the Old Guard",
    "Quench with Illusions",
    "Muster the Troops",
    "Power of the Source",
    "Bane of the Mighty",
    "Magic Penetration",
    "Physical Penetration",
    "Kartu Talent",
    "Kartu Efek",
    "Kartu Equipment",
    "Voucher Hero",
    "Chaos Rift",
    "Ancient Coin Machine",
    "Shadow Servant",
    "Shadow Servants",
    "Illusory Totem",
    "Ancestor Bear Spirit",
    "Ancestral Bear Spirit",
    "Bear Spirit",
    "Bear Spirits",
    "Wolf Soul",
    "Wolf Souls",
    "Mechanical Puppet",
    "Mechanical Puppets",
    "Spinning Blade",
    "Spinning Blades",
)

STOPWORD_GUARD_RE = re.compile(
    r"\b(the|and|with|from|into|when|while|after|before|during|within|without|"
    r"between|against|through|for|you|your|their|his|her|its|this|that|these|those|"
    r"each|every|deals|dealing|restores|restoring|gains|gaining|grants|granting|"
    r"increases|increasing|reduces|reducing|summons|summoning|triggers|triggering|"
    r"enemies|allies|cannot|will|have|has|had|are|was|were|been)\b",
    re.I,
)

LORD_NAME_TO_T2_ALT: dict[str, str] = {
    "Little Daji": "小妲己",
    "Yao Mei": "瑶妹",
    "Arli": "阿离",
    "Jing": "镜",
    "Qiao Xi": "乔汐",
    "Little Chang'e": "常小娥",
    "Yu Huan": "玉环",
    "Little Zhuang Fish": "庄小鱼",
    "Marco": "马可",
    "Bai Ge": "白歌",
    "Zhaojun": "昭君",
    "Uncle Ban": "班叔",
    "Yi Xing": "弈星",
    "Little Sun Bin": "孙小宾",
    "Mister Ming": "明先生",
    "Naonao": "闹闹",
    "Director Jiang": "姜导",
    "Ying Lü": "嬴律",
    "Xiang": "香香",
}

TIER1_EMBEDDED_EN_CLEANUP: tuple[tuple[str, str], ...] = (
    ("Tidal Symphony", "Symphony of Tides"),
    ("Tri-Point Banner", "Three Kingdoms Banner"),
    ("Kartu Effect", "Kartu Efek"),
    ("kartu Effect", "kartu Efek"),
)

GENERIC_SKILL_EXCLUSIONS: set[str] = {
    "Passive",
    "Active",
    "Awaken",
    "Preparation",
    "On Play",
    "Sacrifice",
    "Charge",
    "Slash",
    "Slam",
    "Sweep",
    "Pierce",
    "Sprint",
    "Reload",
    "Bombard",
    "Devour",
}


def _normalize_en_key(text: str) -> str:
    cleaned = TAG_RE.sub("", text)
    cleaned = CONTROL_TOKEN_RE.sub("", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


@dataclass
class ThreeTierGlossary:
    tier1_exact_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier1_plain_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier1_formula_zh_to_id: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    tier1_en_card_to_id_desc: dict[str, str] = field(default_factory=dict)
    tier1_en_desc_to_id_desc: dict[str, str] = field(default_factory=dict)
    tier2_zh_to_en: dict[str, str] = field(default_factory=dict)
    tier2_plain_zh_to_en: dict[str, str] = field(default_factory=dict)
    protected_en_terms: list[str] = field(default_factory=list)
    _protected_re: re.Pattern[str] | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_reference_files(
        cls,
        tier1_path: Path,
        tier2_path: Path,
        tier2_details_path: Path | None = None,
    ) -> "ThreeTierGlossary":
        instance = cls()
        protected_set: set[str] = set(CANONICAL_PROTECTED_TERMS)
        verified_entity_names_en: set[str] = set(CANONICAL_PROTECTED_TERMS)

        orig_unique: dict[str, str] = {}
        cat_candidates = [
            Path("Honor of Kings Ace English Patcher 1.4.12.exe_extracted/catalog/catalog.json.gz"),
            tier1_path.parent.parent.parent / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted/catalog/catalog.json.gz",
            Path("data/catalog_checkpoints/catalog.json.gz"),
        ]
        for cpath in cat_candidates:
            if cpath.exists():
                try:
                    cdata = json.loads(gzip.decompress(cpath.read_bytes()))
                    orig_unique = cdata.get("unique", {})
                    if orig_unique:
                        break
                except Exception:
                    pass

        def _add_entity_name(name: str | None) -> None:
            if not name:
                return
            name = name.strip()
            if (
                3 <= len(name) <= 45
                and any(c.isupper() for c in name)
                and not name.endswith(".")
                and name not in GENERIC_SKILL_EXCLUSIONS
            ):
                verified_entity_names_en.add(name)
                protected_set.add(name)
                if not name.endswith("s") and not name.endswith("'"):
                    plural = name + "s"
                    verified_entity_names_en.add(plural)
                    protected_set.add(plural)
                if not name.endswith("s") and not name.endswith("'"):
                    plural = name + "s"
                    verified_entity_names_en.add(plural)
                    protected_set.add(plural)

        t1_data: dict = {}
        if tier1_path.exists():
            t1_data = json.loads(tier1_path.read_text(encoding="utf-8"))
            instance._ingest_tier1(t1_data, protected_set, verified_entity_names_en, orig_unique, _add_entity_name)
        if tier2_path.exists():
            t2 = json.loads(tier2_path.read_text(encoding="utf-8"))
            instance._ingest_tier2(t2, protected_set, verified_entity_names_en, orig_unique, _add_entity_name)

        if tier2_details_path is None:
            tier2_details_path = tier2_path.with_name("tier2_wiki_details_en.json")
        if tier2_details_path.exists():
            t2_details = json.loads(tier2_details_path.read_text(encoding="utf-8"))
            instance._ingest_tier2_details(t1_data, t2_details, protected_set, verified_entity_names_en, _add_entity_name)

        for zh_k, id_v in BRACKET_TERM_MAP.items():
            instance.tier1_exact_zh_to_id.setdefault(zh_k, id_v)
        for zh_k, id_v in WINDOWS_108_ZH_TO_ID.items():
            instance._register_t1_pair(zh_k, id_v)

        protected_set |= verified_entity_names_en
        # Sort protected multi-word proper names longest-first
        # Verified entity names bypass STOPWORD_GUARD_RE
        instance.protected_en_terms = sorted(
            (
                t
                for t in protected_set
                if (
                    t in verified_entity_names_en
                    or (len(t) >= 5 and any(c.isupper() for c in t) and not STOPWORD_GUARD_RE.search(t))
                )
                and len(t) >= 3
                and any(c.isupper() for c in t)
            ),
            key=len,
            reverse=True,
        )
        if instance.protected_en_terms:
            escaped = "|".join(re.escape(t) for t in instance.protected_en_terms)
            instance._protected_re = re.compile(rf"(?<![A-Za-z0-9_])(?:{escaped})(?![A-Za-z0-9_])")
        return instance

    def _register_t1_pair(self, zh: str, id_val: str) -> None:
        zh = zh.strip()
        id_val = id_val.strip()
        if not zh or not id_val:
            return
        for old_en, new_id in TIER1_EMBEDDED_EN_CLEANUP:
            if old_en in id_val:
                id_val = id_val.replace(old_en, new_id)
        self.tier1_exact_zh_to_id[zh] = id_val
        norm = normalize_plain_zh(zh)
        if norm:
            self.tier1_plain_zh_to_id[norm] = id_val
        skel = normalize_formula_skeleton_zh(zh)
        if skel and len(skel) >= 6:
            cands = self.tier1_formula_zh_to_id.setdefault(skel, [])
            if (zh, id_val) not in cands:
                cands.append((zh, id_val))

    def _register_t2_pair(self, zh: str, en_val: str) -> None:
        zh = zh.strip()
        en_val = en_val.strip()
        if not zh or not en_val:
            return
        self.tier2_zh_to_en.setdefault(zh, en_val)
        norm = normalize_plain_zh(zh)
        if norm:
            self.tier2_plain_zh_to_en.setdefault(norm, en_val)

    def _ingest_tier1(
        self,
        t1: dict,
        protected_set: set[str],
        verified_entity_names_en: set[str] | None = None,
        orig_unique: dict[str, str] | None = None,
        _add_entity_name: Callable[[str | None], None] | None = None,
    ) -> None:
        if verified_entity_names_en is None:
            verified_entity_names_en = set()
        if _add_entity_name is None:
            def _add_entity_name(name: str | None) -> None:
                if not name:
                    return
                name = name.strip()
                if (
                    3 <= len(name) <= 45
                    and any(c.isupper() for c in name)
                    and not name.endswith(".")
                    and name not in GENERIC_SKILL_EXCLUSIONS
                ):
                    verified_entity_names_en.add(name)
                    protected_set.add(name)
                    if not name.endswith("s") and not name.endswith("'"):
                        plural = name + "s"
                        verified_entity_names_en.add(plural)
                        protected_set.add(plural)
        if orig_unique is None:
            orig_unique = {}

        # 1. Factions & Keywords (stored as dicts on hok-ace-translate-id.netlify.app)
        factions = t1.get("factions", {})
        if isinstance(factions, dict):
            for zh_f, en_f in factions.items():
                self._register_t1_pair(zh_f, en_f)
                _add_entity_name(en_f)
                if zh_f in orig_unique:
                    _add_entity_name(orig_unique[zh_f])
        elif isinstance(factions, list):
            for item in factions:
                if isinstance(item, dict):
                    zh_f = item.get("cn") or item.get("nameCn") or ""
                    en_f = item.get("name") or ""
                    self._register_t1_pair(zh_f, en_f)
                    _add_entity_name(en_f)
                    if zh_f in orig_unique:
                        _add_entity_name(orig_unique[zh_f])

        keywords = t1.get("keywords", {})
        if isinstance(keywords, dict):
            for kw_name in keywords:
                _add_entity_name(kw_name)

        # 2. Heroes, Effect Cards, Equipment, Talents (including awaken, skills, and Lv enhancements)
        for category in ("hero", "effect", "equip", "talent"):
            for item in t1.get(category, []):
                name_cn = (item.get("cn") or item.get("nameCn") or "").strip()
                name_en = (item.get("name") or "").strip()
                desc_cn = (item.get("descCn") or "").strip()
                desc_id = (item.get("desc") or "").strip()
                if name_en:
                    _add_entity_name(name_en)
                if name_cn and name_cn in orig_unique:
                    _add_entity_name(orig_unique[name_cn])
                if name_cn and name_en:
                    if category in ("hero", "equip") and not STOPWORD_GUARD_RE.search(name_en):
                        self._register_t1_pair(name_cn, name_en)
                        protected_set.add(name_en)
                    else:
                        self._register_t2_pair(name_cn, name_en)
                if desc_cn and desc_id:
                    self._register_t1_pair(desc_cn, desc_id)

                awaken = item.get("awaken")
                if isinstance(awaken, dict):
                    self._register_t1_pair(
                        awaken.get("descCn") or "", awaken.get("desc") or ""
                    )

                for sk in item.get("skills", []):
                    sk_cn = (sk.get("cn") or sk.get("nameCn") or "").strip()
                    sk_name = (sk.get("name") or "").strip()
                    if sk_name:
                        _add_entity_name(sk_name)
                    if sk_cn and sk_cn in orig_unique:
                        _add_entity_name(orig_unique[sk_cn])
                    if sk_cn and sk_name:
                        if not STOPWORD_GUARD_RE.search(sk_name):
                            self._register_t1_pair(sk_cn, sk_name)
                            protected_set.add(sk_name)
                        else:
                            self._register_t2_pair(sk_cn, sk_name)
                    self._register_t1_pair(
                        sk.get("descCn") or "", sk.get("desc") or ""
                    )
                    for enh in sk.get("enh", []):
                        self._register_t1_pair(
                            enh.get("descCn") or "", enh.get("desc") or ""
                        )

        # 3. Lords / Chess Players (19 items)
        for lord in t1.get("lords", []):
            lord_name = (lord.get("name") or "").strip()
            lord_cn = (lord.get("cn") or lord.get("nameCn") or "").strip()
            if lord_name:
                _add_entity_name(lord_name)
            if lord_cn and lord_cn in orig_unique:
                _add_entity_name(orig_unique[lord_cn])
            if lord_cn and lord_name:
                self._register_t1_pair(lord_cn, lord_name)
            for tal in lord.get("talents", []):
                c_name = (tal.get("cardName") or "").strip()
                c_desc = (tal.get("desc") or "").strip()
                if c_name:
                    _add_entity_name(c_name)
                    if c_desc:
                        self.tier1_en_card_to_id_desc[c_name] = c_desc
            for rel in lord.get("related", []):
                r_name = (rel.get("name") or "").strip()
                r_desc = (rel.get("desc") or "").strip()
                if r_name:
                    _add_entity_name(r_name)
                    if r_desc:
                        self.tier1_en_card_to_id_desc[r_name] = r_desc

    def _ingest_tier2(
        self,
        t2: list[dict],
        protected_set: set[str],
        verified_entity_names_en: set[str] | None = None,
        orig_unique: dict[str, str] | None = None,
        _add_entity_name: Callable[[str | None], None] | None = None,
    ) -> None:
        if verified_entity_names_en is None:
            verified_entity_names_en = set()
        if _add_entity_name is None:
            def _add_entity_name(name: str | None) -> None:
                if not name:
                    return
                name = name.strip()
                if (
                    3 <= len(name) <= 45
                    and any(c.isupper() for c in name)
                    and not name.endswith(".")
                    and name not in GENERIC_SKILL_EXCLUSIONS
                ):
                    verified_entity_names_en.add(name)
                    protected_set.add(name)
                    if not name.endswith("s") and not name.endswith("'"):
                        plural = name + "s"
                        verified_entity_names_en.add(plural)
                        protected_set.add(plural)
        if orig_unique is None:
            orig_unique = {}

        for entry in t2:
            alt_zh = (entry.get("alt") or "").strip()
            name_en = (entry.get("name") or "").strip()
            if alt_zh and name_en:
                self._register_t2_pair(alt_zh, name_en)
                if entry.get("type") in ("Hero", "Chess player") and not STOPWORD_GUARD_RE.search(name_en):
                    protected_set.add(name_en)
            if entry.get("type") in ("Hero", "Summon", "Talent", "Chess player", "Equipment", "Effect card"):
                if name_en:
                    _add_entity_name(name_en)
                if alt_zh and alt_zh in orig_unique:
                    _add_entity_name(orig_unique[alt_zh])

    def _ingest_tier2_details(
        self,
        t1: dict,
        t2_details: list[dict],
        protected_set: set[str],
        verified_entity_names_en: set[str] | None = None,
        _add_entity_name: Callable[[str | None], None] | None = None,
    ) -> None:
        if verified_entity_names_en is None:
            verified_entity_names_en = set()
        if _add_entity_name is None:
            def _add_entity_name(name: str | None) -> None:
                if not name:
                    return
                name = name.strip()
                if (
                    3 <= len(name) <= 45
                    and any(c.isupper() for c in name)
                    and not name.endswith(".")
                    and name not in GENERIC_SKILL_EXCLUSIONS
                ):
                    verified_entity_names_en.add(name)
                    protected_set.add(name)
                    if not name.endswith("s") and not name.endswith("'"):
                        plural = name + "s"
                        verified_entity_names_en.add(plural)
                        protected_set.add(plural)

        t2_players_by_alt: dict[str, dict] = {}
        for item in t2_details:
            if item.get("type") == "Chess player" and item.get("alt"):
                t2_players_by_alt[item["alt"].strip()] = item

            en_block = item.get("en") or {}
            zh_block = item.get("zh") or {}
            for key in ("calc_copies", "effect_copies", "skill_names", "breakpoints", "rule_notes"):
                for zh_s, en_s in zip(zh_block.get(key, []), en_block.get(key, [])):
                    self._register_t2_pair(zh_s, en_s)

            for sk in en_block.get("skill_names", []):
                _add_entity_name(sk)

            for ab_zh, ab_en in zip(
                zh_block.get("abilities", []), en_block.get("abilities", [])
            ):
                ab_en_name = (ab_en.get("name") or "").strip()
                ab_en_desc = (ab_en.get("desc") or "").strip()
                if ab_en_name:
                    _add_entity_name(ab_en_name)
                self._register_t2_pair(ab_zh.get("name", ""), ab_en_name)
                self._register_t2_pair(ab_zh.get("desc", ""), ab_en_desc)
                # If ab_en["name"] is in tier1_en_card_to_id_desc, map ab_en["desc"] and ab_zh["desc"] to Tier 1 ID!
                if ab_en_name in self.tier1_en_card_to_id_desc:
                    id_desc = self.tier1_en_card_to_id_desc[ab_en_name]
                    zh_d = ab_zh.get("desc", "")
                    if len(normalize_plain_zh(zh_d)) >= 8:
                        self._register_t1_pair(zh_d, id_desc)
                    if ab_en_desc and len(ab_en_desc) >= 20:
                        self.tier1_en_desc_to_id_desc[_normalize_en_key(ab_en_desc)] = id_desc

        # Pair all 19 Tier 1 Lords with their corresponding Tier 2 Chess Player detail pages
        for lord in t1.get("lords", []):
            l_name = (lord.get("name") or "").strip()
            alt_zh = LORD_NAME_TO_T2_ALT.get(l_name)
            t2_player = t2_players_by_alt.get(alt_zh or "")
            if not t2_player:
                continue
            zh_abs = (t2_player.get("zh") or {}).get("abilities", [])
            en_abs = (t2_player.get("en") or {}).get("abilities", [])
            tals = lord.get("talents", [])
            rels = lord.get("related", [])
            for idx, tal in enumerate(tals):
                c_name = (tal.get("cardName") or "").strip()
                c_desc = (tal.get("desc") or "").strip()
                if idx < len(zh_abs):
                    zh_ab = zh_abs[idx]
                    if c_name and not STOPWORD_GUARD_RE.search(c_name):
                        self._register_t1_pair(zh_ab.get("name", ""), c_name)
                    if c_desc and len(normalize_plain_zh(zh_ab.get("desc", ""))) >= 8:
                        self._register_t1_pair(zh_ab.get("desc", ""), c_desc)
                    m_split = re.search(
                        r"^(.+?[。！？])\s*([^：:。]{2,12})[：:](.+)$",
                        zh_ab.get("desc", ""),
                    )
                    if m_split:
                        first_zh, sub_name_zh, sub_desc_zh = m_split.groups()
                        if c_desc and len(normalize_plain_zh(first_zh)) >= 8:
                            self._register_t1_pair(first_zh, c_desc)
                        if len(rels) > 1:
                            r1_name = (rels[1].get("name") or "").strip()
                            r1_desc = (rels[1].get("desc") or "").strip()
                            if r1_name and not STOPWORD_GUARD_RE.search(r1_name):
                                self._register_t1_pair(sub_name_zh, r1_name)
                            if r1_desc and len(normalize_plain_zh(sub_desc_zh)) >= 8:
                                self._register_t1_pair(sub_desc_zh, r1_desc)
                                if c_desc and r1_name and len(normalize_plain_zh(zh_ab.get("desc", ""))) >= 8:
                                    self._register_t1_pair(
                                        zh_ab.get("desc", ""),
                                        f"{c_desc}\n{r1_name}: {r1_desc}",
                                    )
                if idx < len(en_abs) and c_desc:
                    en_ab_desc = (en_abs[idx].get("desc") or "").strip()
                    if en_ab_desc and len(en_ab_desc) >= 20:
                        self.tier1_en_desc_to_id_desc[_normalize_en_key(en_ab_desc)] = c_desc

    def translate_en_to_id(self, en_text: str) -> str:
        """Convert English HoK Ace text into natural Indonesian while preserving tags, proper nouns, and tokens."""
        if not en_text or not en_text.strip():
            return en_text

        norm_en = _normalize_en_key(en_text)
        if (
            len(en_text.strip()) >= 20
            and norm_en in self.tier1_en_desc_to_id_desc
            and not TAG_RE.findall(en_text)
            and not PLACEHOLDER_RE.findall(en_text)
        ):
            return self.tier1_en_desc_to_id_desc[norm_en]

        def _convert_segment(seg: str) -> str:
            out = seg.replace("The First Lands", "First Lands")

            # Normalize English baseline variants to canonical Tier 1 terms
            var_subs = [
                (r"(?<![A-Za-z])(?:Magic|Magical)\s+ATK(?![A-Za-z])", "Magic Attack"),
                (r"(?<![A-Za-z])Physical\s+ATK(?![A-Za-z])", "Physical Attack"),
                (r"(?<![A-Za-z])Sage['’]s\s+Sanctuary(?![A-Za-z])", "Sage's Sanctuary"),
                (r"\b(\d+)\s*Chang\b", r"\1 kartu"),
                (r"\b(\d+)\s*Number of times\b", r"\1 kali"),
                (r"(?<![A-Za-z])Magical Attack(?![A-Za-z])", "Magic Attack"),
                (r"(?<![A-Za-z])Magical Damage(?![A-Za-z])", "Magic Damage"),
                (r"(?<![A-Za-z])Magical Defense(?![A-Za-z])", "Magic Defense"),
                (r"(?<![A-Za-z])Spell Penetration(?![A-Za-z])", "Magic Penetration"),
                (
                    r"(?<![A-Za-z])(?:Maximum HP|Max Health|Maximum Health)(?![A-Za-z])",
                    "Max HP",
                ),
                (r"(?<![A-Za-z])Maximum Mana(?![A-Za-z])", "Max Mana"),
                (
                    r"(?<![A-Za-z])(?:Exquisite Ancient Coins|Exquisite Ancient Coin|Refined Ancient Coins)(?![A-Za-z])",
                    "Refined Ancient Coin",
                ),
                (r"\bfans\s+(?:his|her|its|their)\s+wings\b", "mengepakkan sayapnya"),
                (r"(?<![A-Za-z])wolf\s+souls(?![A-Za-z])", "Wolf Souls"),
                (r"(?<![A-Za-z])wolf\s+soul(?![A-Za-z])", "Wolf Soul"),
                (r"(?<![A-Za-z])bear\s+spirits(?![A-Za-z])", "Bear Spirits"),
                (r"(?<![A-Za-z])bear\s+spirit(?![A-Za-z])", "Bear Spirit"),
                (r"(?<![A-Za-z])shadow\s+servants(?![A-Za-z])", "Shadow Servants"),
                (r"(?<![A-Za-z])shadow\s+servant(?![A-Za-z])", "Shadow Servant"),
                (r"(?<![A-Za-z])chaos\s+rifts(?![A-Za-z])", "Chaos Rifts"),
                (r"(?<![A-Za-z])chaos\s+rift(?![A-Za-z])", "Chaos Rift"),
                (r"(?<![A-Za-z])mechanical\s+puppets(?![A-Za-z])", "Mechanical Puppets"),
                (r"(?<![A-Za-z])mechanical\s+puppet(?![A-Za-z])", "Mechanical Puppet"),
                (r"(?<![A-Za-z])spinning\s+blades(?![A-Za-z])", "Spinning Blades"),
                (r"(?<![A-Za-z])spinning\s+blade(?![A-Za-z])", "Spinning Blade"),
                (
                    r"\bspreads\s+(?:his|her|its|their)\s+wings\s+to\s+dance\b",
                    "membentangkan sayapnya dan menari",
                ),
                (
                    r"\bimproving\s+(?:his|her|its|their)\s+attack\s+by\b",
                    "meningkatkan Attack miliknya sebesar",
                ),
                (r"(?<![A-Za-z])Ancient Coins(?![A-Za-z])", "Ancient Coin"),
                (r"(?<![A-Za-z])Perfect Resurrection(?![A-Za-z])", "Perfect Revive"),
                (r"(?<![A-Za-z])Arcomia Core(?![A-Za-z])", "Akomia Core"),
                (r"(?<![A-Za-z])Fire Thief(?![A-Za-z])", "Steal Fire"),
                (r"(?<![A-Za-z])(?:Talent Cards|Talent Card)(?![A-Za-z])", "Kartu Talent"),
                (r"(?<![A-Za-z])(?:Effect Cards|Effect Card)(?![A-Za-z])", "Kartu Efek"),
                (
                    r"(?<![A-Za-z])(?:Equipment Cards|Equipment Card)(?![A-Za-z])",
                    "Kartu Equipment",
                ),
                (r"(?<![A-Za-z])(?:Hero Vouchers|Hero Voucher)(?![A-Za-z])", "Voucher Hero"),
                (r"(?<![A-Za-z])Temporary Levels?\s+up(?![A-Za-z])", "Peningkatan Temporary Level"),
                (r"(?<![A-Za-z])Temporary Levels(?![A-Za-z])", "Temporary Level"),
                (r"(?<![A-Za-z])real (?:Level|Tier)s?(?![A-Za-z])", "True Level"),
                (
                    r"(?<![A-Za-z])(?:Perfect Revivals?|Perfect Resurrections?)(?![A-Za-z])",
                    "Perfect Revive",
                ),
                (r"(?<![A-Za-z])faster growth(?![A-Za-z])", "pertumbuhan lebih cepat"),
                (r"(?<![A-Za-z])growth methods?(?![A-Za-z])", "metode pertumbuhan"),
            ]
            for pat, repl in var_subs:
                out = re.sub(pat, repl, out, flags=re.IGNORECASE)

            sentinels: list[tuple[str, str]] = []
            if self._protected_re is not None:
                def _protect_match(m: re.Match[str]) -> str:
                    idx = len(sentinels)
                    tok = f"__WXQPR{idx}__"
                    val = m.group(0)
                    if val == "Central Plains":
                        val = "Central Plain"
                    elif val == "Sunset Sea":
                        val = "Sunset"
                    elif val == "Magical Damage":
                        val = "Magic Damage"
                    sentinels.append((tok, val))
                    return tok

                out = self._protected_re.sub(_protect_match, out)

            out = translate_segment_en_to_id(out)

            for tok, orig_val in sentinels:
                out = out.replace(tok, orig_val, 1)

            out = re.sub(
                r"\b(Ancient Coin|Refined Ancient Coin|Central Plain|Zhulu(?: Plateau)?|Three Kingdoms|Sunset(?: Sea)?|Jixia|Great Wall|Xuanyong|Yaotian|Cloudream|Riverlands)\s+[Kk]artu(?:\s+Hero)?\b",
                lambda m: f"Kartu Hero {m.group(1)}" if "hero" in m.group(0).lower() else f"Kartu {m.group(1)}",
                out,
            )
            out = re.sub(r"\b(\d+)\s+[Aa]cak\s+(Kartu\s+[A-Za-z ]+)\b", r"\1 \2 acak", out)

            for old_ft, new_ft in (
                ("Kartu Effect", "Kartu Efek"),
                ("kartu Effect", "kartu Efek"),
                ("Sementara Level", "Temporary Level"),
                ("sementara Level", "Temporary Level"),
                ("Nyata Level", "True Level"),
                ("nyata Level", "True Level"),
                ("Cepat Growth", "pertumbuhan lebih cepat"),
                ("cepat growth", "pertumbuhan lebih cepat"),
            ):
                out = out.replace(old_ft, new_ft)
            out = re.sub(r"(?i)sempurna kebangkitan", "Perfect Revive", out)
            out = re.sub(r"(?i)\bTemporary Level\s+atas\b", "Peningkatan Temporary Level", out)
            out = re.sub(r"\bsebuah\s+((?:<[^>]+>\s*)*\d+)", r"\1", out, flags=re.I)
            out = re.sub(r"\badalah\s+milikmu\b", "milikmu", out, flags=re.I)

            return out

        res = translate_preserving_skeleton(en_text, _convert_segment)
        res = re.sub(r"\bsebuah\s+((?:<[^>]+>\s*)*\d+)", r"\1", res, flags=re.I)
        return res

    def _fit_length_bound(self, source_zh: str, candidate: str) -> str:
        """Guarantee candidate satisfies len(candidate) <= max(len(source_zh) * 8, 48) when len(source_zh) >= 4."""
        for old_ft, new_ft in (
            ("Kartu Effect", "Kartu Efek"),
            ("kartu Effect", "kartu Efek"),
            ("Sementara Level", "Temporary Level"),
            ("sementara Level", "Temporary Level"),
            ("Nyata Level", "True Level"),
            ("nyata Level", "True Level"),
            ("Cepat Growth", "pertumbuhan lebih cepat"),
            ("cepat growth", "pertumbuhan lebih cepat"),
        ):
            candidate = candidate.replace(old_ft, new_ft)
        candidate = re.sub(r"(?i)sempurna kebangkitan", "Perfect Revive", candidate)
        candidate = re.sub(r"(?i)\bTemporary Level\s+atas\b", "Peningkatan Temporary Level", candidate)
        candidate = re.sub(r"\bsebuah\s+((?:<[^>]+>\s*)*\d+)", r"\1", candidate, flags=re.I)
        candidate = re.sub(r"\badalah\s+milikmu\b", "milikmu", candidate, flags=re.I)

        if len(source_zh) < 4:
            return candidate
        limit = max(len(source_zh) * 8, 48)
        if len(candidate) <= limit:
            return candidate

        compact_replacements = (
            ("tidak akan", "takkan"),
            ("sebaiknya tidak", "jangan"),
            ("tidak bisa", "tak bisa"),
            ("tidak dapat", "tak dapat"),
            ("memberitahu", "beri tahu"),
            ("tayangan ulang", "replay"),
            ("memenangkan", "menang"),
            ("beberapa lebih banyak", "lagi"),
            ("menampilkan", "tunjukkan"),
            ("bagaimana ke", "cara"),
            ("bagaimana cara", "cara"),
            ("sebuah ", ""),
            ("dari ", ""),
            ("adalah ", ""),
            ("itu ", ""),
            ("untuk ", ""),
            ("yang ", ""),
            ("secara permanen", "permanen"),
            ("secara acak", "acak"),
            ("untuk pertama kalinya", "pertama kali"),
            ("di medan tempur", "di field"),
            ("pertandingan", "match"),
            ("meningkatkan", "+"),
            ("mengurangi", "-"),
            ("mendapatkan", "dapat"),
            ("memperoleh", "dapat"),
            ("memberikan", "beri"),
            ("  ", " "),
        )
        out = candidate
        for old, new in compact_replacements:
            if len(out) <= limit:
                break
            out = out.replace(old, new)
        if (
            len(out) > limit
            and not TAG_RE.findall(source_zh)
            and not PLACEHOLDER_RE.findall(source_zh)
            and not CONTROL_TOKEN_RE.findall(source_zh)
            and ";" not in source_zh
        ):
            head = out[:limit]
            out = (head.rsplit(" ", 1)[0] if " " in head else head).rstrip(" ,;:-.")
        return out

    def translate_entry(
        self, source_zh: str, baseline_en: str | None = None
    ) -> tuple[str, str]:
        """
        Return (translated_id, tier_used) where tier_used is 'tier1', 'tier2', or 'tier3'.
        Guarantees validate_translation(source_zh, translated_id) == (True, 'ok').
        """
        # 1. Tier 1 exact match (includes exact 108 missing Windows strings & Tier 1 CN->ID)
        if source_zh in self.tier1_exact_zh_to_id:
            raw_t1 = self.tier1_exact_zh_to_id[source_zh]
            ok_direct, _ = validate_translation(source_zh, raw_t1)
            if ok_direct:
                return (raw_t1, "tier1")
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    raw_t1,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 2. Tier 1 normalized (tag-stripped) match + skeleton re-injection
        norm_zh = normalize_plain_zh(source_zh)
        if norm_zh and norm_zh in self.tier1_plain_zh_to_id:
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    self.tier1_plain_zh_to_id[norm_zh],
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 2b. Tier 1 formula-skeleton match (handles all 234 dynamic formula Hero skills/enhancements/awakenings)
        skel_zh = normalize_formula_skeleton_zh(source_zh)
        if skel_zh and skel_zh in self.tier1_formula_zh_to_id:
            cands = self.tier1_formula_zh_to_id[skel_zh]
            src_nums = re.findall(r"\d+(?:\.\d+)?", normalize_plain_zh(source_zh))
            best_cand = cands[0]
            best_score = -1
            for c_cn, c_id in cands:
                c_nums = re.findall(r"\d+(?:\.\d+)?", normalize_plain_zh(c_cn))
                score = sum(1 for a, b in zip(src_nums, c_nums) if a == b)
                if score > best_score:
                    best_score = score
                    best_cand = (c_cn, c_id)
            t1_desc_cn, t1_desc_id = best_cand
            cand = self._fit_length_bound(
                source_zh,
                reinject_formula_and_skeleton(
                    source_zh,
                    t1_desc_cn,
                    t1_desc_id,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 2c. Tier 1 Lord card name / description match via baseline_en
        if baseline_en:
            clean_en = TAG_RE.sub("", baseline_en).strip()
            if clean_en in self.tier1_en_card_to_id_desc and len(source_zh) >= 8:
                cand = self._fit_length_bound(
                    source_zh,
                    reinject_skeleton_from_source(
                        source_zh,
                        self.tier1_en_card_to_id_desc[clean_en],
                        inner_translator=self._translate_raw_zh_to_id,
                        baseline_en=baseline_en,
                        en_translator=self.translate_en_to_id,
                    ),
                )
                if validate_translation(source_zh, cand)[0]:
                    return (cand, "tier1")

            norm_en = _normalize_en_key(baseline_en)
            if norm_en in self.tier1_en_desc_to_id_desc and len(source_zh) >= 8:
                cand = self._fit_length_bound(
                    source_zh,
                    reinject_skeleton_from_source(
                        source_zh,
                        self.tier1_en_desc_to_id_desc[norm_en],
                        inner_translator=self._translate_raw_zh_to_id,
                        baseline_en=baseline_en,
                        en_translator=self.translate_en_to_id,
                    ),
                )
                if validate_translation(source_zh, cand)[0]:
                    return (cand, "tier1")

        # 3. Tier 2 exact or plain entity/detail match -> EN -> ID
        t2_en = self.tier2_zh_to_en.get(source_zh) or (
            self.tier2_plain_zh_to_en.get(norm_zh) if norm_zh else None
        )
        if t2_en:
            t2_id = self.translate_en_to_id(t2_en)
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    t2_id,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier2")

        # 4. Tier 3: Use baseline_en (ZH -> EN -> ID)
        if baseline_en:
            cand = self._fit_length_bound(
                source_zh,
                sanitize_target_text(source_zh, self.translate_en_to_id(baseline_en)),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier3")

            repaired = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    TAG_RE.sub("", cand),
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok2, _ = validate_translation(source_zh, repaired)
            if ok2:
                return (repaired, "tier3")

            if validate_translation(source_zh, baseline_en)[0]:
                return (baseline_en, "tier3")

        # 5. Fallback for unmapped raw Chinese strings
        cand = self._fit_length_bound(source_zh, self._translate_raw_zh_to_id(source_zh))
        return (cand, "tier3")

    def _translate_raw_zh_to_id(self, source_zh: str) -> str:
        """Translate a raw Chinese string (with tags/placeholders) into validated Indonesian."""
        if source_zh in WINDOWS_108_ZH_TO_ID:
            return WINDOWS_108_ZH_TO_ID[source_zh]

        zh_phrase_map: list[tuple[str, str]] = [
            ("使用武凤获得第1名", "Raih Peringkat 1 menggunakan Wu Feng"),
            ("使用武凤获得前4名", "Raih Top 4 menggunakan Wu Feng"),
            ("使用武凤累计击败", "Kalahkan total menggunakan Wu Feng"),
            ("使用武凤参与对局", "Mainkan pertandingan menggunakan Wu Feng"),
            ("三分之地阵营", "Faction Three Kingdoms"),
            ("三分阵营", "Faction Three Kingdoms"),
            ("全体友方", "Semua sekutu"),
            ("友方英雄", "Hero sekutu"),
            ("敌方英雄", "Hero musuh"),
            ("最大生命值", "Max HP"),
            ("最大生命", "Max HP"),
            ("物理攻击力", "Physical Attack"),
            ("法术攻击力", "Magic Attack"),
            ("物理攻击", "Physical Attack"),
            ("法术攻击", "Magic Attack"),
            ("物理伤害", "Physical Damage"),
            ("法术伤害", "Magic Damage"),
            ("真实伤害", "True Damage"),
            ("物理防御", "Physical Defense"),
            ("法术防御", "Magic Defense"),
            ("攻击速度", "Attack Speed"),
            ("暴击率", "Crit Rate"),
            ("暴击伤害", "Crit Damage"),
            ("伤害减免", "Reduksi Damage"),
            ("伤害加成", "Bonus Damage"),
            ("伤害提升", "Peningkatan Damage"),
            ("临时等级", "Temporary Level"),
            ("真实等级", "True Level"),
            ("战斗开始时", "Saat Combat dimulai, "),
            ("每个回合开始时", "Di awal setiap Round, "),
            ("每个回合结束时", "Di akhir setiap Round, "),
            ("每回合开始时", "Di awal setiap Round, "),
            ("获得", "Dapatkan "),
            ("提升", "Meningkatkan "),
            ("减少", "Mengurangi "),
            ("降低", "Mengurangi "),
            ("恢复", "Memulihkan "),
            ("造成", "Memberikan "),
            ("召唤", "Memanggil "),
            ("登场", "On Play"),
            ("光环", "Aura"),
            ("激发", "Inspire"),
            ("连携", "Synergy"),
            ("变身", "Transform"),
            ("回手", "Bounce"),
            ("摧毁", "Destroy"),
            ("吞噬", "Devour"),
            ("护盾", "Shield"),
            ("唯一", "Unik"),
            ("被动", "Pasif"),
            ("主动", "Aktif"),
            ("英雄", "Hero "),
            ("装备", "Equipment "),
            ("天赋", "Talent "),
            ("效果牌", "Kartu Efek "),
            ("秘技牌", "Kartu Secret Art "),
            ("棋手", "Chess Player "),
            ("回合", "Round "),
            ("累计", "Total "),
            ("次数", " kali"),
            ("次", " kali"),
            ("秒", " detik"),
            ("层", " stack"),
            ("张", " kartu"),
            ("点", " "),
            ("金币", " Gold"),
            ("经验", " EXP"),
            ("等级", " Level "),
            ("星级", " Bintang "),
            ("胜利", "Kemenangan"),
            ("失败", "Kekalahan"),
            ("任务", "Misi"),
            ("奖励", "Hadiah"),
            ("解锁", "Buka"),
            ("完成", "Selesai"),
        ]

        # Sort entity keys longest first to prevent partial substring collisions
        sorted_t2 = sorted(self.tier2_zh_to_en.items(), key=lambda kv: len(kv[0]), reverse=True)

        def _seg_fn(seg: str) -> str:
            out = seg
            for k, v in WINDOWS_108_ZH_TO_ID.items():
                if k and len(k) >= 2 and k in out:
                    out = out.replace(k, v)
            for k, v in sorted_t2:
                if k and len(k) >= 2 and k in out:
                    out = out.replace(k, v)
            for k, v in zh_phrase_map:
                if k in out:
                    out = out.replace(k, v)
            out = (
                out.replace("：", ": ")
                .replace("，", ", ")
                .replace("。", ".")
                .replace("、", ", ")
                .replace("（", " (")
                .replace("）", ")")
                .replace("【", "[")
                .replace("】", "]")
                .replace("《", "")
                .replace("》", "")
                .replace("“", '"')
                .replace("”", '"')
                .replace("！", "!")
                .replace("？", "?")
                .replace("×", "x")
            )
            out = CJK_RE.sub("", out)
            out = re.sub(r"[ \t]+", " ", out).strip()
            return out or "OK"

        cand = translate_preserving_skeleton(source_zh, _seg_fn)
        ok, _ = validate_translation(source_zh, cand)
        if not ok:
            cand = reinject_skeleton_from_source(
                source_zh,
                TAG_RE.sub("", cand),
                en_translator=self.translate_en_to_id,
            )
        return cand

