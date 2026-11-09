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
    adapt_tier1_placeholders_to_source,
    normalize_formula_skeleton_zh,
    normalize_plain_zh,
    normalize_tag_boundary_spacing,
    reinject_formula_and_skeleton,
    reinject_skeleton_from_source,
    translate_preserving_skeleton,
)
from acepatchindo.card_rewriter import (
    CANONICAL_FACTION_MAP,
    CANONICAL_HERO_NAME_MAP,
    CANONICAL_MECHANIC_MAP,
    CANONICAL_RELATED_CARD_MAP,
    polish_indonesian_card_text,
    rewrite_en_card_to_id,
)
from acepatchindo.card_wrapper import (
    ensure_placeholder_spacing,
    normalize_brackets,
    wrap_card_description,
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
    (re.compile(r"\bon the field\b", re.I), "di arena"),
    (re.compile(r"\bon the board\b", re.I), "di papan"),
    (re.compile(r"\benters the field\b", re.I), "masuk ke arena"),
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
    "Arcomia Core",
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
    "Luban No. 7",
    "Luban No.7",
    "Luban No. 9",
    "Luban No. 4",
    "Mechanical Minion A1",
    "Mechanical Minion A2",
    "Great Wall",
    "Sunset",
    "Zhulu",
    "Cloudream",
    "Chang'an",
    "Yaotian",
    "Jixia",
    "Xuanyong",
    "Knock-Up",
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
    "Thermal Trap",
    "Electromagnetic Spring",
    "Plasma Shield",
    "Portable Mechanism",
    "Mechanical Construction",
    "Build Upgrade",
    "Many Friends",
    "Lots of Friends",
    "Plenty of Friends",
    "One Big Family",
    "Maple Leaf Dance",
    "Maple Dance",
    "Graceful Dance",
    "Strategic Decision",
    "Supreme Decision",
    "Privileged Decision",
    "Privileged Decree",
    "Strum",
    "Vibrato",
    "Pluck",
    "Eternal Time Loop",
    "Time Loop",
    "Demon God",
    "Sky Piercer",
    "Taotie Annihilation",
    "Magic Deer",
    "Deer's Protection",
    "Giant's Belt",
    "Large Rod",
    "Overlord's Platemail",
    "Guardian's Glory",
    "Savant's Wrath",
    "Void Staff",
    "Insatiable Tome",
    "Afterlife Totem",
    "Seer Totem",
    "Destiny Totem",
    "Totem Series",
    "General Series",
    "Arcomia Core Series",
    "War Song",
    "Legion Evolution",
    "Direct Source",
    "Destiny",
    "Glacial Buckler",
    "Thorn Heavy Armor",
    "Ominous Premonition",
    "Dream-Forged Windchaser",
    "Red Demon",
    "Shadow Fang",
    "Daybreak",
    "Doomsday",
    "Sword of Conquest",
    "Underworld King",
    "Mask of Agony",
    "Siegebreaker",
    "Pure Sky",
    "Endless Greatsword",
    "Sanction Sword",
    "Eye of the Phoenix",
    "Succubus Cloak",
    "Crimson Lotus Armor",
    "Moon God",
    "Frost Assault",
    "Tome of Wisdom",
    "Sanguine Dominator",
    "Grimoire of Life",
    "Mana Chalice",
    "Cocoon-Breaking Garment",
    "Spirit-Gathering Crystal",
    "Blade of Magic Law",
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


ZH_SERIES_HEADER_MAP: dict[str, str] = {
    "╉图腾系列": "╉Totem Series",
    "╊夺取系列": "╊Steal Series",
    "╋闪现系列": "╋Flash Series",
    "═临时等级系列": "═Temporary Level Series",
    "╥阿科米亚核心系列": "╥Arcomia Core Series",
    "╨登场系列": "╨Deploy Series",
    "╪开团系列": "╪Initiate Series",
    "╫牺牲系列": "╫Sacrifice Series",
    "╬整备系列": "╬Prepare Series",
    "低阶系列": "Low-Tier Series",
    "初始阵容系列": "Starting Lineup Series",
    "古币系列": "Ancient Coin Series",
    "召唤系列": "Summon Series",
    "合成系列": "Combine Series",
    "多阵营系列": "Multi-Faction Series",
    "契约系列": "Contract Series",
    "战术牌系列": "Tactics Card Series",
    "护盾系列": "Shield Series",
    "效果牌系列": "Effect Card Series",
    "无阵营系列": "Factionless Series",
    "草根系列": "Grassroots Series",
    "通用系列": "General Series",
}

SERIES_HEADER_RE = re.compile(
    r"^((?:<a\s+href=[^>]+>)?<color=#99DEB0>)([^<]*系列)(</color>(?:</a>)?)\n(.+)$",
    flags=re.S,
)
CHEST_CHOICE_RE = re.compile(r"(?:指定英雄穿戴|穿戴给英雄)，可从(.+?)中选择(\d+)件。")
HERO_CHOICE_VOUCHER_RE = re.compile(r"(\d+)选(\d+)(?:【([^】]+)】|(无阵营)的?)(\d+)阶英雄，获得(\d+)张该英雄牌。")
HERO_SPECIFIED_RE = re.compile(r"^(.*?)指定(\d+)名英雄，获得(\d+)张该英雄牌。(.*)$")
OPUS_CORRUPTION_RE = re.compile(
    r"♪|♫|Synchronis|\(Text\)|\bRiot rate\b|\d+\s*(?:Zhang|Chang)\b|Forensic|small part of the world|non-resistible|breached\.",
    flags=re.I,
)
SEMICOLON_SPLIT_RE = re.compile(r";\s*(?=[A-Z]|Pilih|Dapatkan|Memperoleh)")
NUM_FIND_RE = re.compile(r"\d+(?:\.\d+)?")
SPACES_RE = re.compile(r"[ \t]+")
NORM_SPACES_RE = re.compile(r"\s+")
CARD_HERO_NAME_INVERT_RE = re.compile(
    r"\b(Ancient Coin|Refined Ancient Coin|Central Plain|Zhulu(?: Plateau)?|Three Kingdoms|Sunset(?: Sea)?|Jixia|Great Wall|Xuanyong|Yaotian|Cloudream|Riverlands)\s+[Kk]artu(?:\s+Hero)?\b"
)
RANDOM_CARD_RE = re.compile(r"\b(\d+)\s+[Aa]cak\s+(Kartu\s+[A-Za-z ]+)\b")
SEBUAH_NUM_RE = re.compile(r"\bsebuah\s+((?:<[^>]+>\s*)*\d+)", flags=re.I)
NUM_PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")
CTRL_FIND_RE = re.compile(r"[\u2540-\u257f]")

COMPILED_VAR_SUBS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pat, flags=re.IGNORECASE), repl)
    for pat, repl in [
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
        (r"(?<![A-Za-z])Akomia Core(?![A-Za-z])", "Arcomia Core"),
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
        (r"\b([A-Z][A-Za-z0-9'&.\- ]{1,25}?)'s\s+basic\s+attacks?\b", r"Basic Attack \1"),
        (r"\b([A-Z][A-Za-z0-9'&.\- ]{1,25}?)'s\s+attacks?\b", r"serangan \1"),
        (r"\bNo\.\s*(\d+)\s+laser\s+cannon\b", r"Laser Cannon No.\1"),
        (r"\bNo\.\s*(\d+)\b", r"No.\1"),
        (r"\bBullet Damage Up\b", "Peningkatan Damage Peluru"),
        (r"\bMissile Decay Down\b", "Pengurangan Decay Rudal"),
        (r"\bPassive Cap Up\b", "Peningkatan Batas Pasif"),
        (r"\bBounce Count Up\b", "Peningkatan Jumlah Pantulan"),
        (r"\bRestore Effect Up\b", "Peningkatan Efek Pemulihan"),
        (r"\bDamage Up\b", "Peningkatan Damage"),
        (r"\bDecay Down\b", "Pengurangan Decay"),
        (r"\bCap Up\b", "Peningkatan Batas"),
        (r"\bCount Up\b", "Peningkatan Jumlah"),
        (r"\bRange Up\b", "Peningkatan Jarak"),
        (r"\bDuration Up\b", "Peningkatan Durasi"),
        (r"\bEffect Up\b", "Peningkatan Efek"),
        (r"\bLimit Up\b", "Peningkatan Batas"),
        (r"\bSpeed Up\b", "Peningkatan Kecepatan"),
        (r"\bCooldown Down\b", "Pengurangan Cooldown"),
        (r"\bknocks?\s+up\b", "memberi efek Knock-Up"),
        (r"\bknocked\s+up\b", "terkena Knock-Up"),
        (r"\bknocking\s+up\b", "memberi efek Knock-Up"),
        (r"\bknock\s+up\b", "Knock-Up"),
        (r"\bKnock-up\b", "Knock-Up"),
        (r"\bon\s+skill\s+cast\b", "saat menggunakan Skill"),
        (r"\bon\s+cast\b", "saat digunakan"),
        (r"\bon\s+casting\b", "saat menggunakan"),
        (r"\bCombat Start\b", "Awal Combat"),
        (r"\bprepares?\s+for\s+war\b", "Prepare"),
        (r"\bplayed\s+at\s+the\s+same\s+time\b", "diterjunkan bersamaan"),
        (r"\bplay\s+at\s+the\s+same\s+time\b", "diterjunkan bersamaan"),
        (r"\bhighest-Tier\s+Hero\b", "Hero Tier tertinggi"),
        (r"\byour\s+highest-Level\s+Hero\b", "Hero milikmu dengan Level tertinggi"),
        (r"\bhighest-Level\s+Hero\b", "Hero Level tertinggi"),
        (r"\bself-destructs?\b", "meledakkan diri"),
        (r"\blowest\s+HP\s+value\b", "HP terendah"),
        (r"\bhighest\s+current\s+HP\s+percentage\b", "persentase HP saat ini tertinggi"),
        (r"\bfor\s+the\s+next\s+(\d+)\s+seconds?\b", r"selama \1 detik berikutnya"),
        (r"\bstrengthening\s+cards?\b", "Kartu Penguatan"),
        (r"\ban\s+allied\s+Summon\b", "unit Summon sekutu"),
        (r"\ballied\s+Summons?\b", "unit Summon sekutu"),
        (r"\bAttack\s+mode\b", "mode serangan"),
        (r"\bpoints?\s+of\s+Attack\b", "poin Attack"),
        (r"\bAttack\s+damage\b", "Damage serangan"),
        (r"\bAttack\s+Bonus\b", "Bonus Attack"),
    ]
)

COMPILED_GLOSSARY_CLEANUP_RULES: tuple[tuple[re.Pattern[str], str | Callable], ...] = (
    (
        re.compile(
            r"\bke\s+(me[a-z]+|ber[a-z]+|ter[a-z]+|di[a-z]+|memper[a-z]+|meng[a-z]+|meny[a-z]+|men[a-z]+|mem[a-z]+|mel[a-z]+|mer[a-z]+)\b",
            re.I,
        ),
        lambda m: f"untuk {m.group(1).lower()}",
    ),
    (re.compile(r"\b(Basic Attack)(?:\s+\1)+\b", re.I), r"\1"),
    (
        re.compile(
            r"\b(meningkatkan|mengurangi|menambah|menurunkan)\s+([^.,;:\n]{1,40}?)\s+oleh\s+(?=(?:<[^>]+>\s*)*[\d\[{+-])",
            re.I,
        ),
        r"\1 \2 sebesar ",
    ),
    (re.compile(r"\bLuban\s+Tidak(?:\.\s*|\s+)(\d+)\b"), r"Luban No.\1"),
    (re.compile(r"\bTidak\.\s*(\d+)\b"), r"No.\1"),
    (re.compile(r"\bHebat Dinding\b"), "Great Wall"),
    (re.compile(r"\bMechanical Minion sebuah(\d+)\b"), r"Mechanical Minion A\1"),
    (re.compile(r"\bmementalkan\s+atas\b", re.I), "Knock-Up"),
    (re.compile(r"\bDamage\s+Atas\b", re.I), "Peningkatan Damage"),
    (re.compile(r"\bDecay\s+Bawah\b", re.I), "Pengurangan Decay"),
    (re.compile(r"\bBatas\s+Atas\b", re.I), "Peningkatan Batas"),
    (re.compile(r"\bpada\s+skill\s+menggunakan\b", re.I), "saat menggunakan Skill"),
    (re.compile(r"\bpada\s+menggunakan\b", re.I), "saat digunakan"),
    (re.compile(r"\bdasar\s+([A-Z][A-Za-z0-9'&.\- ]{1,25}?)\s+serangan\b"), r"Basic Attack \1"),
    (re.compile(r"\bdasar\s+serangan\b"), "Basic Attack"),
    (
        re.compile(
            r"\bmelompat\s+menjadi\s+(?:sebuah\s+)?padat\s+(?:musuh\s+)?(?:area|grup|formasi|gugus)(?:\s+dari\s+musuh)?\b",
            re.I,
        ),
        "melompat ke area terpadat musuh",
    ),
    (re.compile(r"\bmelompat\s+menjadi\s+padat\s+musuh\s+formasi\b", re.I), "melompat ke formasi musuh yang padat"),
    (
        re.compile(
            r"\bmelompat\s+(?:dengan\s+suci\s+pedang\s+)?menjadi\s+(?:sebuah\s+)?padat\s+(?:grup|area|formasi)(?:\s+dari\s+musuh)?\b",
            re.I,
        ),
        "melompat ke area terpadat musuh",
    ),
    (
        re.compile(r"\bmenerjang\s+menjadi\s+(?:sebuah\s+)?padat\s+(?:musuh\s+)?(?:area|grup|formasi|gugus)\b", re.I),
        "menerjang ke area terpadat musuh",
    ),
    (
        re.compile(
            r"\bmelemparkan\s+sebuah\s+bom\s+pada\s+(?:sebuah\s+)?padat\s+(?:musuh\s+)?(?:area|grup|formasi|gugus)\b",
            re.I,
        ),
        "melemparkan bom ke area terpadat musuh",
    ),
    (
        re.compile(r"\b(?:sebuah\s+)?padat\s+(?:musuh\s+)?(?:area|grup|formasi|gugus)(?:\s+dari\s+musuh)?\b", re.I),
        "area terpadat musuh",
    ),
    (re.compile(r"\bEnergi\s+bola\s+itu\s+(?:orbit\s+dia|mengelilinginya)\b", re.I), "Bola Energi yang mengelilinginya"),
    (re.compile(r"\bBola\s+energi\s+itu\s+(?:orbit\s+dia|mengelilinginya)\b", re.I), "Bola Energi yang mengelilinginya"),
    (re.compile(r"\bitu\s+orbit\s+dia\b", re.I), "yang mengelilinginya"),
    (re.compile(r"\bitu\s+mengelilinginya\b", re.I), "yang mengelilinginya"),
    (re.compile(r"\bsebuah\s+padat\b", re.I), "area terpadat"),
    (re.compile(r"sempurna kebangkitan", re.I), "Perfect Revive"),
    (re.compile(r"\bTemporary Level\s+atas\b", re.I), "Peningkatan Temporary Level"),
    (re.compile(r"\bsebuah\s+((?:<[^>]+>\s*)*\d+)", re.I), r"\1"),
    (re.compile(r"\badalah\s+milikmu\b", re.I), "milikmu"),
    (re.compile(r"\bCombat\s+Mulai\b", re.I), "Awal Combat"),
    (re.compile(r"\bPreparation\s+untuk\s+perang\b", re.I), "Prepare"),
    (re.compile(r"\bbermain\s+pada\s+saat\s+yang\s+sama\b", re.I), "diterjunkan bersamaan"),
    (re.compile(r"\btertinggi-Tier\s+Hero\b", re.I), "Hero Tier tertinggi"),
    (re.compile(r"\btertinggi\s+milikmu-Level\s+Hero\b", re.I), "Hero milikmu dengan Level tertinggi"),
    (re.compile(r"\bdiri\s+sendiri-menghancurkan\b", re.I), "meledakkan diri"),
    (re.compile(r"\bnilai\s+terendah\s+HP\b", re.I), "HP terendah"),
    (re.compile(r"\bnilai\s+tertinggi\s+HP\s+saat\s+ini\s+persentase\b", re.I), "persentase HP saat ini tertinggi"),
    (re.compile(r"\buntuk\s+berikutnya\s+(\d+)\s+detik\b", re.I), r"selama \1 detik berikutnya"),
    (re.compile(r"\bpenguatan\s+kartu\b", re.I), "Kartu Penguatan"),
    (re.compile(r"\bsebuah\s+sekutu\s+Memanggil\b", re.I), "unit Summon sekutu"),
    (re.compile(r"(\+\d+%?)\s+Menyerang\b"), r"\1 Attack"),
    (re.compile(r"\bMenyerang\s+mode\b", re.I), "mode serangan"),
    (re.compile(r"\bpoin\s+dari\s+Menyerang\b", re.I), "poin Attack"),
    (re.compile(r"\bMenyerang\s+kerusakan\b", re.I), "Damage serangan"),
    (re.compile(r"\bBonus\s+Menyerang\b", re.I), "Bonus Attack"),
)

GLOSSARY_LITERAL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("[Hebat Dinding]", "[Great Wall]"),
    ("Mechanical Minion sebuah1", "Mechanical Minion A1"),
    ("Mechanical Minion sebuah2", "Mechanical Minion A2"),
    ("orbit di sekitarnya", "mengelilinginya"),
    ("Kartu Effect", "Kartu Efek"),
    ("kartu Effect", "kartu Efek"),
    ("Sementara Level", "Temporary Level"),
    ("sementara Level", "Temporary Level"),
    ("Nyata Level", "True Level"),
    ("nyata Level", "True Level"),
    ("Cepat Growth", "pertumbuhan lebih cepat"),
    ("cepat growth", "pertumbuhan lebih cepat"),
)


def apply_glossary_cleanup(text: str) -> str:
    out = text
    for old, new in GLOSSARY_LITERAL_REPLACEMENTS:
        if old in out:
            out = out.replace(old, new)
    for pat, repl in COMPILED_GLOSSARY_CLEANUP_RULES:
        if callable(repl):
            out = pat.sub(repl, out)
        else:
            out = pat.sub(repl, out)
    return out


def _normalize_en_key(text: str) -> str:
    cleaned = TAG_RE.sub("", text)
    cleaned = CONTROL_TOKEN_RE.sub("", cleaned)
    return NORM_SPACES_RE.sub(" ", cleaned).strip().lower()


@dataclass
class ThreeTierGlossary:
    tier1_exact_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier1_plain_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier1_formula_zh_to_id: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    tier1_en_card_to_id_desc: dict[str, str] = field(default_factory=dict)
    tier1_en_desc_to_id_desc: dict[str, str] = field(default_factory=dict)
    tier2_zh_to_en: dict[str, str] = field(default_factory=dict)
    tier2_plain_zh_to_en: dict[str, str] = field(default_factory=dict)
    orig_unique: dict[str, str] = field(default_factory=dict)
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
        instance.orig_unique = orig_unique
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
                    if desc_cn in orig_unique:
                        en_desc = orig_unique[desc_cn]
                        if en_desc and len(en_desc) >= 20:
                            self.tier1_en_desc_to_id_desc[_normalize_en_key(en_desc)] = desc_id

                if category == "talent":
                    linked_list = item.get("linked") or []
                    if len(linked_list) == 1 and desc_cn:
                        rhs = ""
                        if "：" in desc_cn:
                            lhs, rhs = desc_cn.split("：", 1)
                        elif "。" in desc_cn:
                            lhs, rhs = desc_cn.split("。", 1)
                        if len(normalize_plain_zh(rhs)) >= 5:
                            lk_desc = (linked_list[0].get("desc") or "").strip()
                            m_pfx = re.match(r"^([^:]+):\s*(.+)$", lk_desc, flags=re.DOTALL)
                            if m_pfx:
                                body = m_pfx.group(2).strip()
                                lk_desc_clean = body[0].upper() + body[1:] if body else ""
                            else:
                                lk_desc_clean = lk_desc
                            self._register_t1_pair(rhs.strip(), lk_desc_clean)
                            if rhs.strip() in orig_unique:
                                en_rhs = orig_unique[rhs.strip()]
                                if en_rhs and len(en_rhs) >= 15:
                                    self.tier1_en_desc_to_id_desc[_normalize_en_key(en_rhs)] = lk_desc_clean

                awaken = item.get("awaken")
                if isinstance(awaken, dict):
                    awk_cn = (awaken.get("descCn") or "").strip()
                    awk_id = (awaken.get("desc") or "").strip()
                    if awk_cn and awk_id:
                        self._register_t1_pair(awk_cn, awk_id)
                        if awk_cn in orig_unique:
                            en_awk = orig_unique[awk_cn]
                            if en_awk and len(en_awk) >= 20:
                                self.tier1_en_desc_to_id_desc[_normalize_en_key(en_awk)] = awk_id

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
                    sk_desc_cn = (sk.get("descCn") or "").strip()
                    sk_desc_id = (sk.get("desc") or "").strip()
                    if sk_desc_cn and sk_desc_id:
                        self._register_t1_pair(sk_desc_cn, sk_desc_id)
                        if sk_desc_cn in orig_unique:
                            en_sk = orig_unique[sk_desc_cn]
                            if en_sk and len(en_sk) >= 20:
                                self.tier1_en_desc_to_id_desc[_normalize_en_key(en_sk)] = sk_desc_id
                    for enh in sk.get("enh", []):
                        enh_desc_cn = (enh.get("descCn") or "").strip()
                        enh_desc_id = (enh.get("desc") or "").strip()
                        if enh_desc_cn and enh_desc_id:
                            self._register_t1_pair(enh_desc_cn, enh_desc_id)
                            if enh_desc_cn in orig_unique:
                                en_enh = orig_unique[enh_desc_cn]
                                if en_enh and len(en_enh) >= 20:
                                    self.tier1_en_desc_to_id_desc[_normalize_en_key(en_enh)] = enh_desc_id

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
                        if " · " in r_name:
                            self.tier1_en_card_to_id_desc[r_name.replace(" · ", " • ")] = r_desc
                            self.tier1_en_card_to_id_desc[r_name.replace(" · ", ": ")] = r_desc
                        elif " • " in r_name:
                            self.tier1_en_card_to_id_desc[r_name.replace(" • ", " · ")] = r_desc
                            self.tier1_en_card_to_id_desc[r_name.replace(" • ", ": ")] = r_desc
                        elif ": " in r_name:
                            self.tier1_en_card_to_id_desc[r_name.replace(": ", " · ")] = r_desc
                            self.tier1_en_card_to_id_desc[r_name.replace(": ", " • ")] = r_desc

        # Register Yao Mei tag-matched Tier 1 pairs
        self._register_t1_pair(
            "小鹿等级+30，获得一件<color=#FFE897>小鹿的庇护</color>。",
            "Level Rusa +30, dan dapatkan 1 <color=#FFE897>Deer's Protection</color>.",
        )
        self._register_t1_pair(
            "小鹿等级+30，并获得1件<color=#FFE897>小鹿的庇护</color>。",
            "Level Rusa +30, dan dapatkan 1 <color=#FFE897>Deer's Protection</color>.",
        )
        self._register_t1_pair(
            "小鹿等级+30，获得一件小鹿的庇护。",
            "Level Rusa +30, dan dapatkan 1 Deer's Protection.",
        )

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

                        # Match related card by name reference in c_desc or zh_ab
                        matched_rel = None
                        for rel in rels:
                            rel_name = (rel.get("name") or "").strip()
                            rel_name_cn = (rel.get("nameCn") or "").strip()
                            if rel_name and rel_name in c_desc:
                                matched_rel = rel
                                break
                            if rel_name_cn and (rel_name_cn in sub_name_zh or rel_name_cn in first_zh):
                                matched_rel = rel
                                break
                        if not matched_rel and len(rels) == 1:
                            matched_rel = rels[0]

                        if matched_rel:
                            r_name = (matched_rel.get("name") or "").strip()
                            r_desc = (matched_rel.get("desc") or "").strip()
                            if r_name and not STOPWORD_GUARD_RE.search(r_name):
                                self._register_t1_pair(sub_name_zh, r_name)
                            if r_desc and len(normalize_plain_zh(sub_desc_zh)) >= 8:
                                self._register_t1_pair(sub_desc_zh, r_desc)
                                if c_desc and r_name and len(normalize_plain_zh(zh_ab.get("desc", ""))) >= 8:
                                    self._register_t1_pair(
                                        zh_ab.get("desc", ""),
                                        f"{c_desc}\n{r_name}: {r_desc}",
                                    )
                if idx < len(en_abs) and c_desc:
                    en_ab_desc = (en_abs[idx].get("desc") or "").strip()
                    if en_ab_desc and len(en_ab_desc) >= 20:
                        self.tier1_en_desc_to_id_desc[_normalize_en_key(en_ab_desc)] = c_desc

            # Direct registration for all related cards
            for rel_idx, rel in enumerate(rels):
                r_name = (rel.get("name") or "").strip()
                r_name_cn = (rel.get("nameCn") or "").strip()
                r_desc = (rel.get("desc") or "").strip()
                if not r_desc:
                    continue

                if r_name:
                    self.tier1_en_card_to_id_desc[r_name] = r_desc
                    if " · " in r_name:
                        self.tier1_en_card_to_id_desc[r_name.replace(" · ", " • ")] = r_desc
                        self.tier1_en_card_to_id_desc[r_name.replace(" · ", ": ")] = r_desc
                    elif " • " in r_name:
                        self.tier1_en_card_to_id_desc[r_name.replace(" • ", " · ")] = r_desc
                        self.tier1_en_card_to_id_desc[r_name.replace(" • ", ": ")] = r_desc
                    elif ": " in r_name:
                        self.tier1_en_card_to_id_desc[r_name.replace(": ", " · ")] = r_desc
                        self.tier1_en_card_to_id_desc[r_name.replace(": ", " • ")] = r_desc

                matched_ab = None
                for ab_idx, ab in enumerate(zh_abs):
                    ab_name = (ab.get("name") or "").strip()
                    en_ab_name = (
                        (en_abs[ab_idx].get("name") or "").strip()
                        if ab_idx < len(en_abs)
                        else ""
                    )
                    if (r_name_cn and ab_name == r_name_cn) or (
                        r_name and en_ab_name and r_name.lower() == en_ab_name.lower()
                    ):
                        matched_ab = ab
                        break

                if matched_ab:
                    ab_desc = (matched_ab.get("desc") or "").strip()
                    if len(normalize_plain_zh(ab_desc)) >= 8:
                        self._register_t1_pair(ab_desc, r_desc)

        # Arli One Leaf, Twin Life variants
        zh_one_leaf_variants = [
            "位移时，在原地生成1个继承30%最大生命值的分身，分身阵亡时晕眩最近的敌人。分身无法普攻，生成时嘲讽最近的敌人2秒。",
            "转移时在原地创造1个具有30%最大生命值，退场时会眩晕周围敌人的分身，分身无法攻击且召唤时嘲讽周围敌人2秒。",
            "转移时在原地创造1个具有30%最大生命值，阵亡时会眩晕周围敌人的分身，分身无法攻击且被创造时嘲讽周围敌人2秒。",
            "转移时在原地创造1个具有30%最大生命值，╈<b>退场</b>时会眩晕周围敌人的分身，分身无法攻击且召唤时嘲讽周围敌人2秒。",
        ]
        en_one_leaf_variants = [
            "When shifting, creates a clone at the original location with 30% Max HP. Upon death, it stuns the nearest enemy. The clone cannot Attack and taunts the nearest enemy for 2 seconds upon creation.",
            "Upon shifting, create a clone at the original position with 30% Max HP that stuns nearby enemies upon withdrawal. The clone cannot Attack and taunts nearby enemies for 2 seconds upon summoning.",
            "When transferring, create a clone at the original spot with 30% Max HP. When the clone ╈<b>is defeated</b>, it stuns nearby enemies. The clone cannot Attack and taunts nearby enemies for 2 seconds upon summoning.",
            "When shifting, create a clone at the original location with 30% Max HP. Upon death, it stuns nearby enemies. The clone cannot Attack and taunts nearby enemies for 2 seconds upon creation.",
        ]
        id_one_leaf = (
            "Saat berpindah, membuat 1 sosok tiruan di posisi asal dengan 30% Max HP, "
            "yang akan memberikan Stun ke musuh sekitarnya saat gugur; sosok ini tidak dapat menyerang, "
            "dan memberikan Taunt ke musuh sekitarnya selama 2 detik saat dibuat."
        )
        for zh_v in zh_one_leaf_variants:
            self._register_t1_pair(zh_v, id_one_leaf)
        for en_v in en_one_leaf_variants:
            self.tier1_en_desc_to_id_desc[_normalize_en_key(en_v)] = id_one_leaf
        self.tier1_en_card_to_id_desc["One Leaf, Twin Life"] = id_one_leaf
        self.tier1_en_card_to_id_desc["One Leaf, Two Lives"] = id_one_leaf

        # Yao Mei Magic Deer variants
        self._register_t1_pair(
            "小鹿等级+30，并获得1件<color=#ffffff><b>小鹿的庇护</b></color>。",
            "Level Rusa +30, dan peroleh 1 <color=#ffffff><b>Deer's Protection</b></color>.",
        )
        self._register_t1_pair(
            "小鹿等级+30，获得一件<color=#FFE897>小鹿的庇护</color>。",
            "Level Rusa +30, dan peroleh 1 <color=#FFE897>Deer's Protection</color>.",
        )
        self._register_t1_pair(
            "小鹿等级+30，获得1件小鹿的庇护。",
            "Level Rusa +30, dan peroleh 1 Deer's Protection.",
        )
        self._register_t1_pair(
            "小鹿可以穿戴普通装备，且立即穿戴1件<b>极寒风暴</b>，等级+10。",
            "Rusa dapat memakai Normal Equipment, dan langsung memakai 1 <b>Glacial Buckler</b>, Level +10.",
        )
        self._register_t1_pair(
            "小鹿可以穿戴装备，且立即穿戴1件<b>极寒风暴</b>，等级+10。",
            "Rusa dapat memakai Equipment, dan langsung memakai 1 <b>Glacial Buckler</b>, Level +10.",
        )
        self._register_t1_pair(
            "小鹿可以穿戴装备，且立即穿戴1件<color=#FFE897>极寒风暴</color>。",
            "Rusa dapat memakai Equipment, dan langsung memakai 1 <color=#FFE897>Glacial Buckler</color>.",
        )
        for en_v in [
            "Deer Level +30, and gain 1 Deer's Protection.",
            "Fawn Level +30, and gain 1 Deer's Protection.",
        ]:
            self.tier1_en_desc_to_id_desc[_normalize_en_key(en_v)] = "Level Rusa +30, dan peroleh 1 Deer's Protection."
        self.tier1_en_card_to_id_desc["Giant Plushie"] = "Level Rusa +30, dan peroleh 1 Deer's Protection."
        self.tier1_en_card_to_id_desc["Huge Plushie"] = "Level Rusa +30, dan peroleh 1 Deer's Protection."
        self.tier1_en_card_to_id_desc["Magic Deer · Heavy Armor"] = "Rusa dapat memakai Equipment, dan langsung memakai 1 Glacial Buckler."
        self.tier1_en_card_to_id_desc["Magic Deer: Heavy Armor"] = "Rusa dapat memakai Equipment, dan langsung memakai 1 Glacial Buckler."

        yao_deer_map = [
            (
                [
                    "小鹿阵亡时，会将自身等级以<a href=3130011>═<b>临时等级</b></a>均分给你的英雄。",
                    "小鹿阵亡时，会将自身等级以═<b>临时等级</b>均分给你的英雄。",
                    "小鹿阵亡均分等级",
                ],
                [
                    "When the deer dies, its Level is distributed equally among your Heroes as Temporary Level.",
                    "When the deer is Defeated, its own Level is distributed equally among your heroes as Temporary Level.",
                    "Deer death shares levels",
                ],
                "Saat rusa gugur, Level miliknya akan dibagi rata sebagai Temporary Level ke seluruh Hero milikmu.",
                ["Magic Deer · Devotion", "Magic Deer: Devotion"],
            ),
            (
                [
                    "小鹿等级翻倍。",
                ],
                [
                    "Deer Level is doubled.",
                    "deer Level is doubled.",
                ],
                "Level rusa menjadi dua kali lipat.",
                ["Magic Deer · Resonance", "Magic Deer: Resonance"],
            ),
            (
                [
                    "开战时，小鹿会在附近生成1个自身的复制体。如果本局获得过5次胜利，小鹿等级+12（当前胜利次数：{Yao_Count:0}）。",
                    "开战时，小鹿会在附近生成一个自身的复制体。如果本局获得过5次胜利，小鹿等级+12（胜利次数：{Yao_Count:0}）。",
                ],
                [
                    "At the start of combat, Yao generates a Copy of herself nearby. If you have achieved 5 victories this match, Yao +12 Levels (Current victories: {Yao_Count:0}).",
                ],
                "Saat Combat dimulai, rusa akan membuat 1 salinan dirinya di dekatnya. Jika sudah menang 5 kali dalam pertandingan ini, Level rusa +12 (jumlah menang saat ini: {Yao_Count:0}).",
                ["Magic Deer · Twin", "Magic Deer: Twin"],
            ),
        ]
        for zh_list, en_list, id_desc, card_names in yao_deer_map:
            for zh_v in zh_list:
                self._register_t1_pair(zh_v, id_desc)
            for en_v in en_list:
                self.tier1_en_desc_to_id_desc[_normalize_en_key(en_v)] = id_desc
            for c_name in card_names:
                self.tier1_en_card_to_id_desc[c_name] = id_desc

        # Explicit registration for Bai Ge's Burst of Inspiration card
        self._register_t1_pair(
            "释放3道剑气，斩击手牌中随机3张非觉醒英雄牌，将每张牌斩为2张╆转瞬版复制。",
            "Melepaskan 3 tebasan energi pedang, menebas 3 Kartu Hero non-Awaken secara acak di tangan, membelah setiap kartu menjadi 2 salinan ╆Fleeting.",
        )
        self._register_t1_pair(
            "释放3道剑气，斩击手牌中随机3张非觉醒英雄牌，将每张牌斩为2张转瞬版复制。",
            "Melepaskan 3 tebasan energi pedang, menebas 3 Kartu Hero non-Awaken secara acak di tangan, membelah setiap kartu menjadi 2 salinan Fleeting.",
        )

        # Curated Tier 1 replacements for Opus-MT corrupted / control token cards
        curated_t1_pairs = [
            (
                "指定<color=#99DEB0>1名</color>英雄（每名英雄限1次）。每场战斗开始时，该英雄获得<a href=17><color=#99DEB0>╧完美复生</color></a>。",
                "Pilih <color=#99DEB0>1</color> Hero (maks. 1 kali per Hero). Saat setiap Combat dimulai, Hero tersebut memperoleh <a href=17><color=#99DEB0>╧Perfect Revive</color></a>.",
            ),
            (
                "你在战斗中╧复生的英雄，会无敌<color=#99DEB0>3秒</color>，并且获得<color=#99DEB0>300%</color>攻击速度和<color=#99DEB0>100%</color>暴击率（不可叠加）。",
                "Hero milikmu yang ╧Revive saat Combat menjadi Kebal selama <color=#99DEB0>3 detik</color>, serta memperoleh <color=#99DEB0>+300%</color> Attack Speed dan <color=#99DEB0>+100%</color> Crit Rate (tidak dapat ditumpuk).",
            ),
            (
                "回合开始时，获得0{Energy}。每在当前棋手等级停留1回合，额外获得1{Energy}，至多4{Energy}。",
                "Saat Round dimulai, peroleh 0 {Energy}. Setiap bertahan 1 Round pada Level Contestant saat ini, peroleh +1 {Energy} tambahan (maks. 4 {Energy}).",
            ),
            (
                "己方英雄触发<color=#99DEB0>╬整备</color>时，所有英雄获得场上<color=#99DEB0>╬整备</color>英雄数量x<color=#99DEB0>1.5</color>的等级。",
                "Saat Hero sekutu memicu <color=#99DEB0>╬Prepare</color>, semua Hero memperoleh Level sebesar jumlah Hero <color=#99DEB0>╬Prepare</color> di arena x <color=#99DEB0>1.5</color>.",
            ),
            (
                "你的英雄每次触发<color=#99DEB0>╬整备</color>时，己方英雄<color=#99DEB0>+1.5%</color>最大生命值。",
                "Setiap kali Hero milikmu memicu <color=#99DEB0>╬Prepare</color>, Hero sekutu memperoleh <color=#99DEB0>+1.5%</color> Max HP.",
            ),
            (
                "战斗开始时，己方英雄每次释放技能，所有英雄获得<color=#99DEB0>1%</color>物理吸血和<color=#99DEB0>1%</color>法术吸血（上限<color=#99DEB0>30%</color>）。",
                "Saat Combat dimulai, setiap kali Hero sekutu mengeluarkan Skill, semua Hero memperoleh <color=#99DEB0>1%</color> Physical Lifesteal dan <color=#99DEB0>1%</color> Magical Lifesteal (maks. <color=#99DEB0>30%</color>).",
            ),
            (
                "立即获得<color=#99DEB0>3张╬整备</color>英雄牌。你的英雄触发<color=#99DEB0>╬整备</color>时，获得<color=#99DEB0>1张</color>╬整备英雄牌（每回合最多<color=#99DEB0>3张</color>）。",
                "Segera peroleh <color=#99DEB0>3 Kartu Hero ╬Prepare</color>. Saat Hero milikmu memicu <color=#99DEB0>╬Prepare</color>, peroleh <color=#99DEB0>1</color> Kartu Hero ╬Prepare (maks. <color=#99DEB0>3</color> per Round).",
            ),
            (
                "立即获得<color=#99DEB0>4张牺牲</color>英雄牌。你的英雄触发<color=#99DEB0>牺牲</color>时，获得<color=#99DEB0>1张</color>牺牲英雄牌（每回合最多<color=#99DEB0>4张</color>）。",
                "Segera peroleh <color=#99DEB0>4 Kartu Hero Sacrifice</color>. Saat Hero milikmu memicu <color=#99DEB0>Sacrifice</color>, peroleh <color=#99DEB0>1</color> Kartu Hero Sacrifice (maks. <color=#99DEB0>4</color> per Round).",
            ),
            (
                "召唤单位时（召唤物，图腾），它额外获得<color=#99DEB0>100</color>+其召唤者等级x<color=#99DEB0>80%</color>的═临时等级。每回合前<color=#99DEB0>15</color>个召唤单位获得╧完美复生。",
                "Saat memanggil unit (Summon atau Totem), unit tersebut memperoleh <color=#99DEB0>100</color> + <color=#99DEB0>80%</color> Level pemanggilnya sebagai ═Temporary Level. <color=#99DEB0>15</color> unit panggilan pertama tiap Round memperoleh ╧Perfect Revive.",
            ),
            (
                "限定远程。攻击速度<color=#99DEB0>+60%</color>、暴击率<color=#99DEB0>+30%</color>，攻击速度上限突破至<color=#99DEB0>6.0</color>。\n普通攻击额外分裂<color=#99DEB0>2</color>道，每道造成<color=#99DEB0>60%</color>物理伤害。",
                "Khusus Ranged. Attack Speed <color=#99DEB0>+60%</color>, Crit Rate <color=#99DEB0>+30%</color>, dan batas Attack Speed meningkat menjadi <color=#99DEB0>6.0</color>.\nBasic Attack terbelah menjadi <color=#99DEB0>2</color> proyektil tambahan yang masing-masing memberikan <color=#99DEB0>60%</color> Physical Damage.",
            ),
            (
                "若你战斗失败2次，获得9{LordExp}。",
                "Jika kamu kalah Combat 2 kali, peroleh 9 {LordExp}.",
            ),
            (
                "若你战斗胜利2次，获得10{Energy}。",
                "Jika kamu menang Combat 2 kali, peroleh 10 {Energy}.",
            ),
            (
                "<color=#ffffffbf>被动：</color>可在水域内化身人鱼形态，强化普攻。\n<color=#ffffffbf>主动：</color>创造一片水域，<color=#9ff5d0>恢复友军生命值</color>和<color=#86ccfd>法力值</color>。",
                "<color=#ffffffbf>Pasif:</color> Berubah menjadi wujud putri duyung di area air dan memperkuat Basic Attack.\n<color=#ffffffbf>Aktif:</color> Menciptakan area air yang <color=#9ff5d0>memulihkan HP</color> dan <color=#86ccfd>Mana</color> sekutu.",
            ),
            (
                "累积弹奏5次琵琶，获得1张秘技牌<color=#FFE897>惊鸿调</color>，每回合限1次。\n<color=#FFE897>惊鸿调</color>：使用记录的前5次的指法来弹奏琵琶，并触发对应的效果。",
                "Mainkan Pipa 5 kali untuk memperoleh 1 Kartu Secret Skill <color=#FFE897>Graceful Melody</color> (maks. 1 kali per Round).\n<color=#FFE897>Graceful Melody</color>: Mainkan Pipa menggunakan 5 teknik petikan terakhir yang tercatat dan picu efeknya masing-masing.",
            ),
            (
                "累积弹奏6次琵琶，获得1张秘技牌<color=#FFE897>惊鸿调</color>，限2张。\n<color=#FFE897>惊鸿调</color>：使用记录的前6次的指法来弹奏琵琶，并触发对应的效果。",
                "Mainkan Pipa 6 kali untuk memperoleh 1 Kartu Secret Skill <color=#FFE897>Graceful Melody</color> (maks. 2 kartu).\n<color=#FFE897>Graceful Melody</color>: Mainkan Pipa menggunakan 6 teknik petikan terakhir yang tercatat dan picu efeknya masing-masing.",
            ),
            (
                "累积弹奏5次琵琶，获得1张秘技牌<b>惊鸿调</b>，每回合限1次。",
                "Mainkan Pipa 5 kali untuk memperoleh 1 Kartu Secret Skill <b>Graceful Melody</b> (maks. 1 kali per Round).",
            ),
            (
                "累积弹奏6次琵琶，获得1张秘技牌<b>惊鸿调</b>，限2张。",
                "Mainkan Pipa 6 kali untuk memperoleh 1 Kartu Secret Skill <b>Graceful Melody</b> (maks. 2 kartu).",
            ),
            (
                "╥阿科米亚核心不再分配等级，变为:<color=#FFE897>将阿尔米亚核心等级*10的生命值分配给【海都】英雄，装备多的优先</color>。",
                "╥Arcomia Core tidak lagi membagikan Level, melainkan:<color=#FFE897> membagikan HP sebesar 10x Level Arcomia Core ke Hero [Sunset Sea], diprioritaskan bagi yang memakai Equipment terbanyak</color>.",
            ),
            (
                "╥阿科米亚核心等级分配时，<color=#FFE897>优先分配给穿戴最多装备的海都英雄</color>。",
                "Saat Level ╥Arcomia Core dibagikan, <color=#FFE897>prioritaskan Hero [Sunset Sea]</color> yang memakai Equipment terbanyak.",
            ),
            (
                "每次<color=#FFE897>手动刷新</color>商店时，╥阿科米亚核心等级+2。",
                "Setiap kali <color=#FFE897>Refresh manual</color> Shop, Level ╥Arcomia Core +2.",
            ),
            (
                "打出：╥阿科米亚核心等级+2。",
                "Saat dimainkan: Level ╥Arcomia Core +2.",
            ),
            (
                "<b>唯一</b>\n任意英雄╦合成时，自身等级+1。无法拆卸。",
                "<b>Unik</b>\nSaat Hero mana pun ╦Combine, Level pemakai +1. Tidak dapat dilepas.",
            ),
            (
                "<color=#ffffff><b>唯一</b></color>。任意英雄<color=#ffffff>╦<b>合成</b></color>时，自身等级+1。无法拆卸。",
                "<color=#ffffff><b>Unik</b></color>. Saat Hero mana pun <color=#ffffff>╦<b>Combine</b></color>, Level pemakai +1. Tidak dapat dilepas.",
            ),
            (
                "你的英雄每次触发<a href=11><color=#99DEB0>╬整备</color></a>时，己方英雄<color=#99DEB0>+1%</color>最大生命值。",
                "Setiap kali Hero milikmu memicu <a href=11><color=#99DEB0>╬Prepare</color></a>, Hero sekutu memperoleh <color=#99DEB0>+1%</color> Max HP.",
            ),
            (
                "<color=#FFE897>╊夺取效果</color>变为摄取12级。",
                "Efek <color=#FFE897>╊Steal</color> meningkat menjadi mencuri 12 Level.",
            ),
            (
                "指定1名英雄获取词条能力，<color=#FFE897>╊夺取：10%物理攻击力</color>。",
                "Pilih 1 Hero untuk memperoleh Trait Ability: <color=#FFE897>╊Steal: 10% Physical Attack</color>.",
            ),
            (
                "指定1名英雄获取词条能力，<color=#FFE897>╊夺取：20等级</color>。",
                "Pilih 1 Hero untuk memperoleh Trait Ability: <color=#FFE897>╊Steal: 20 Level</color>.",
            ),
            (
                "指定1名英雄获取词条能力，<color=#FFE897>╊摄灵：20等级</color>。",
                "Pilih 1 Hero untuk memperoleh Trait Ability: <color=#FFE897>╊Soul Snatch: 20 Level</color>.",
            ),
            (
                "<b>唯一</b>\n穿戴者获得╊摄灵效果。无法拆卸。",
                "<b>Unik</b>\nPemakai mendapatkan efek ╊Soul Snatch. Tidak dapat dilepas.",
            ),
            (
                "获得3张<color=#FFE897>╪交锋</color>效果英雄牌。",
                "Peroleh 3 Kartu Hero dengan Efek <color=#FFE897>╪Initiate</color>.",
            ),
            # Da Qiao variant
            (
                "你的英雄每触发2次<a href=1><color=#ffffff>╨<b>登场</b></color></a>效果，大乔的法力值上限永久-5且等级+1。",
                "Setiap 2 kali Hero milikmu memicu efek <a href=1><color=#ffffff>╨<b>Deploy</b></color></a>, Max Mana Da Qiao berkurang 5 secara permanen dan mendapat +1 Level.",
            ),
            # Tugas 2 Control Token cards
            (
                "<b>唯一</b>\n穿戴者获得╊夺取效果。无法拆卸。",
                "<b>Unik</b>\nPemakai memperoleh efek ╊Steal. Tidak dapat dilepas.",
            ),
            (
                "战斗中全部友军阵亡时，盘古重生，并额外获得回合数x10的═临时等级。",
                "Saat semua unit sekutu gugur dalam Combat, Pangu bangkit kembali dan memperoleh ═Temporary Level sebesar 10x jumlah Round.",
            ),
            (
                "战斗开始时，你的英雄获得<color=#99DEB0>35</color>═临时等级。战斗结束时，存活英雄的此等级转化为永久等级。",
                "Saat Combat dimulai, Hero milikmu memperoleh <color=#99DEB0>35</color> ═Temporary Level. Saat Combat berakhir, Hero yang bertahan hidup mengubah Level ini menjadi Level permanen.",
            ),
            (
                "战斗开始时，将<color=#99DEB0>1200</color>═临时等级随机分配给你的英雄。",
                "Saat Combat dimulai, bagikan <color=#99DEB0>1200</color> ═Temporary Level secara acak kepada Hero milikmu.",
            ),
            (
                "战斗开始及之后每3秒获得场上友军穿戴不屈意志数量x2的<a><color=#FFE897>═临时等级</color></a>。阵亡时，将自身等级的30%平均分配给穿戴不屈意志的友军。",
                "Saat Combat dimulai dan setiap 3 detik setelahnya, peroleh <a><color=#FFE897>═Temporary Level</color></a> sebesar 2x jumlah sekutu di arena yang memakai Indomitable Will. Saat gugur, bagikan 30% Level miliknya secara merata ke sekutu yang memakai Indomitable Will.",
            ),
            (
                "混沌裂隙英雄获得2次╧完美复生。",
                "Hero Chaos Rift memperoleh 2 kali ╧Perfect Revive.",
            ),
            (
                "立即获得<color=#99DEB0>1张闪现援兵</color>。回合开始时，获得<color=#99DEB0>1张闪现援兵</color>：卡牌<color=#99DEB0>5选2</color>（具有╋闪现词条的英雄牌）。",
                "Segera peroleh <color=#99DEB0>1 Flash Reinforcement</color>. Saat Round dimulai, peroleh <color=#99DEB0>1 Flash Reinforcement</color>: pilih <color=#99DEB0>2 dari 5</color> Kartu Hero dengan trait ╋Flash.",
            ),
            (
                "英雄╦合成时等级额外+3。",
                "Saat Hero ╦Combine, peroleh +3 Level tambahan.",
            ),
            (
                "每进行4次英雄<a href=13><color=#ffffff>╦<b>合成</b></color></a>，白歌获得1张<color=#ffffff><b>即兴创作</b></color>。",
                "Setiap 4 kali Hero <a href=13><color=#ffffff>╦<b>Combine</b></color></a>, Bai Ge memperoleh 1 <color=#ffffff><b>Improvised Creation</b></color>.",
            ),
            (
                "立即获得<color=#99DEB0>2张╪开团</color>英雄牌。己方单位触发<color=#99DEB0>╪开团</color>时，获得<color=#99DEB0>1张╪开团</color>英雄牌（每回合最多<color=#99DEB0>3张</color>）。",
                "Segera peroleh <color=#99DEB0>2 Kartu Hero ╪Initiate</color>. Saat unit sekutu memicu <color=#99DEB0>╪Initiate</color>, peroleh <color=#99DEB0>1 Kartu Hero ╪Initiate</color> (maks. <color=#99DEB0>3 kartu</color> per Round).",
            ),
            (
                "打出后，本回合上场的英雄牌，会额外附带1个无效果的╨登场词条。",
                "Setelah dimainkan, Kartu Hero yang dimainkan Round ini mendapat 1 trait ╨Deploy tambahan tanpa efek.",
            ),
            (
                "获得1张╊夺取：指定1名英雄获取词条能力，╊夺取。",
                "Peroleh 1 Kartu ╊Steal: pilih 1 Hero untuk mendapatkan kemampuan trait ╊Steal.",
            ),
            (
                "随机获得<color=#99DEB0>1张</color>具有╊夺取词条的英雄牌。",
                "Peroleh secara acak <color=#99DEB0>1</color> Kartu Hero dengan trait ╊Steal.",
            ),
            (
                "你的英雄触发<color=#99DEB0>夺取</color>时，所有英雄等级<color=#99DEB0>+6</color>。",
                "Saat Hero milikmu memicu <color=#99DEB0>Steal</color>, semua Hero memperoleh <color=#99DEB0>+6 Level</color>.",
            ),
            (
                "立即获得<color=#99DEB0>1张夺取援兵</color>。回合开始时，获得<color=#99DEB0>2张夺取援兵</color>：随机获得<color=#99DEB0>1张</color>具有╊夺取词条的英雄牌。",
                "Segera peroleh <color=#99DEB0>1 Steal Reinforcement</color>. Saat Round dimulai, peroleh <color=#99DEB0>2 Steal Reinforcement</color>: peroleh secara acak <color=#99DEB0>1</color> Kartu Hero dengan trait ╊Steal.",
            ),
            (
                "己方英雄触发牺牲时，场上随机<color=#99DEB0>1名</color>╫牺牲英雄获得该英雄总等级x<color=#99DEB0>35%</color>的等级。",
                "Saat Hero sekutu memicu Sacrifice, <color=#99DEB0>1</color> Hero ╫Sacrifice acak di arena memperoleh Level sebesar <color=#99DEB0>35%</color> dari total Level Hero tersebut.",
            ),
            (
                "战斗中，你<color=#99DEB0>第4次触发英雄的╫牺牲效果</color>时，所有已阵亡的╫牺牲英雄将会╧完美复生并获得<color=#99DEB0>200</color>临时等级。",
                "Saat Combat, saat kamu <color=#99DEB0>memicu efek ╫Sacrifice Hero untuk ke-4 kalinya</color>, semua Hero ╫Sacrifice yang telah gugur akan ╧Perfect Revive dan memperoleh <color=#99DEB0>200</color> Temporary Level.",
            ),
            (
                "战斗中，你<color=#FFE897>第4次触发英雄的╫牺牲效果</color>时，所有已阵亡的╫牺牲英雄将会╧完美复生。",
                "Saat Combat, saat kamu <color=#FFE897>memicu efek ╫Sacrifice Hero untuk ke-4 kalinya</color>, semua Hero ╫Sacrifice yang telah gugur akan ╧Perfect Revive.",
            ),
            (
                "<color=#FFE897>╋闪现英雄击败敌方单位</color>时，会立刻╋闪现至最近的敌人处，并无敌0.5秒。",
                "Saat <color=#FFE897>Hero ╋Flash mengalahkan unit musuh</color>, ia langsung ╋Flash ke musuh terdekat dan menjadi Kebal selama 0.5 detik.",
            ),
            (
                "转移时在原地创造1个具有30%最大生命值，╈<b>退场</b>时会眩晕周围敌人的分身，分身无法攻击且召唤时嘲讽周围敌人2秒。",
                "Saat berpindah tempat, membuat 1 sosok tiruan di posisi asal dengan 30% Max HP yang memberikan Stun ke musuh di sekitarnya saat ╈<b>Retire</b>. Sosok ini tidak dapat menyerang dan memberikan Taunt ke musuh di sekitarnya selama 2 detik saat dipanggil.",
            ),
            (
                "<color=#98CBFF>╈退场</color>关键词在<color=#98CBFF>棋盘上的</color>英雄被卖出时触发，局内是多触发退场效果，还是保持阵容战力，全看你的抉择",
                "Keyword <color=#98CBFF>╈Retire</color> terpicu saat Hero <color=#98CBFF>di arena</color> dijual; dalam pertandingan, pilih antara memicu efek Retire atau mempertahankan kekuatan tempur Hero.",
            ),
            (
                "战斗开始时，若你<color=#FFE897>至少有2名【大河】英雄</color>，随机在其周围1格召唤<color=#FFE897>╉命运图腾</color>：消灭击败该╉图腾的敌人。",
                "Saat Combat dimulai, jika kamu <color=#FFE897>memiliki minimal 2 Hero [Riverlands]</color>, panggil secara acak <color=#FFE897>╉Fate Totem</color> di sekitarnya (radius 1 petak): musuh yang mengalahkan ╉Totem ini akan musnah.",
            ),
            (
                "战斗开始时，若你<color=#FFE897>至少有2名【大河】英雄</color>，随机在其周围1格召唤<color=#FFE897>╉命运图腾</color>：消灭击败该图腾的敌人。",
                "Saat Combat dimulai, jika kamu <color=#FFE897>memiliki minimal 2 Hero [Riverlands]</color>, panggil secara acak <color=#FFE897>╉Fate Totem</color> di sekitarnya (radius 1 petak): musuh yang mengalahkan Totem ini akan musnah.",
            ),
            (
                "战斗开始时，己方每阵亡<color=#99DEB0>2名</color>英雄，随机在己方战场内召唤<a href=321><color=#99DEB0>╉命运图腾</color></a>：消灭击败该<a href=321><color=#99DEB0>╉图腾</color></a>的敌人。每场最多<color=#99DEB0>2</color>次。",
                "Saat Combat dimulai, setiap <color=#99DEB0>2</color> Hero sekutu gugur, panggil secara acak <a href=321><color=#99DEB0>╉Fate Totem</color></a> di arena sekutu: mengeliminasi musuh yang mengalahkan <a href=321><color=#99DEB0>╉Totem</color></a> tersebut (maks. <color=#99DEB0>2</color> kali per pertandingan).",
            ),
            (
                "战斗开始时，己方每阵亡<color=#99DEB0>2名</color>英雄，随机在己方战场内召唤<color=#99DEB0>命运图腾</color>：消灭击败该图腾的敌人。每场最多<color=#99DEB0>2</color>次。",
                "Saat Combat dimulai, setiap <color=#99DEB0>2</color> Hero sekutu gugur, panggil secara acak <color=#99DEB0>Fate Totem</color> di arena sekutu: mengeliminasi musuh yang mengalahkan Totem tersebut (maks. <color=#99DEB0>2</color> kali per pertandingan).",
            ),
            (
                "你的所有╉图腾会失效，使附近1格的1名英雄获得相应效果。\n╉先知图腾：友方单位阵亡时，获得其10%的═临时等级。\n╉往生图腾：每5秒嘲讽周围1格敌人，自身物理及法术防御+20，持续2秒。\n╉姻缘图腾：普攻5次或释放技能时自身永久+1级。",
                "Semua ╉Totem milikmu dinonaktifkan dan memberikan efek ke 1 Hero di sekitarnya dalam 1 petak.\n╉Seer Totem: Saat unit sekutu gugur, peroleh 10% dari ═Temporary Level miliknya.\n╉Afterlife Totem: Setiap 5 detik, memberikan Taunt ke musuh di sekitarnya dalam 1 petak, serta memperoleh +20 Physical dan Magic Defense selama 2 detik.\n╉Bond Totem: Memperoleh +1 Level permanen setelah 5 Basic Attack atau mengeluarkan Skill.",
            ),
            (
                "战斗开始时，飞行器连接的英雄会随机获得自身10%-40%等级数的═临时等级。",
                "Saat Combat dimulai, Hero yang terhubung dengan Pesawat akan memperoleh ═Temporary Level secara acak sebesar 10%-40% dari Level miliknya.",
            ),
            (
                "<color=#FFE897>╊摄灵效果英雄击败敌方英雄</color>时，将其灵魂复活（无卡牌效果），满法力值作战，持续5秒。",
                "Saat <color=#FFE897>Hero berefek ╊Soul Snatch mengalahkan Hero musuh</color>, jiwa musuh dibangkitkan (tanpa efek kartu) untuk bertarung dengan Mana penuh selama 5 detik.",
            ),
            (
                "你的<color=#FFE897>╊摄灵效果英雄击败敌方英雄</color>时，将永久夺取对方3级。",
                "Saat <color=#FFE897>Hero berefek ╊Soul Snatch milikmu mengalahkan Hero musuh</color>, curi 3 Level lawan secara permanen.",
            ),
            (
                "指定1名英雄获取词条能力，<color=#FFE897>╊摄灵：10%物理攻击力</color>。",
                "Pilih 1 Hero untuk mendapatkan kemampuan trait <color=#FFE897>╊Soul Snatch: +10% Physical Attack</color>.",
            ),
            (
                "<color=#ffffff><b>唯一</b></color>。穿戴者获得<color=#ffffff>╊<b>摄灵</b></color>。无法拆卸。",
                "<color=#ffffff><b>Unik</b></color>. Pemakai memperoleh <color=#ffffff>╊<b>Soul Snatch</b></color>. Tidak dapat dilepas.",
            ),
            # Tugas 3 Tag-Swallowing cards
            (
                "干将莫邪在场时，获得普通装备<color=#ffffff><b>双剑·雄</b></color>及<color=#ffffff><b>双剑·雌</b></color>。",
                "Saat Gan & Mo berada di arena, peroleh Normal Equipment <color=#ffffff><b>Twin Blades: Male</b></color> dan <color=#ffffff><b>Twin Blades: Female</b></color>.",
            ),
            (
                "获得1张基础装备牌及1张<color=#ffffff><b>险中求富</b></color>并开始记录胜场。",
                "Peroleh 1 Kartu Basic Equipment dan 1 <color=#ffffff><b>Seeking wealth in danger</b></color>, lalu mulai mencatat jumlah kemenangan.",
            ),
            (
                "获得1张天赋牌<color=#FFE897>站这别动</color>：指定1个阵位，每过<color=#FFE897>2回合</color>，获得1张此格上的英雄牌。",
                "Peroleh 1 Kartu Talent <color=#FFE897>Stay Put</color>: pilih 1 petak arena; setiap <color=#FFE897>2 Round</color>, peroleh 1 Kartu Hero yang berada di petak tersebut.",
            ),
            (
                "<color=#ffffff><b>唯一</b></color>。提升10点物理及法术防御力，替穿戴<color=#ffffff>怒莲之刺</color>的英雄承担伤害。",
                "<color=#ffffff><b>Unik</b></color>. Physical dan Magic Defense +10. Menanggung Damage menggantikan Hero yang memakai <color=#ffffff>Thorn of the Angry Lotus</color>.",
            ),
            (
                "回合开始时，随机获得<color=#99DEB0>4张</color>你人数最多阵营的英雄牌。",
                "Saat Round dimulai, peroleh <color=#99DEB0>4</color> Kartu Hero acak dari Faction dengan jumlah Hero terbanyak milikmu.",
            ),
            (
                "<color=#FFE897>商店购买</color>额外花费1能量，<color=#FFE897>出售英雄牌</color>额外获得1能量。",
                "<color=#FFE897>Pembelian di Shop</color> membutuhkan +1 Energy tambahan, sedangkan <color=#FFE897>menjual Kartu Hero</color> memberikan +1 Energy tambahan.",
            ),
            (
                "战斗开始时，<color=#FFE897>已觉醒英雄</color>获得40点物理攻击力和40点法术攻击力。",
                "Saat Combat dimulai, <color=#FFE897>Hero yang sudah Awaken</color> memperoleh +40 Physical Attack dan +40 Magic Attack.",
            ),
            (
                "战斗开始时，你的<color=#FFE897>已觉醒英雄</color>获得50点物理攻击力和50点法术攻击力。若所有己方英雄已觉醒，则再获得20%物理及法术吸血。",
                "Saat Combat dimulai, <color=#FFE897>Hero milikmu yang sudah Awaken</color> memperoleh +50 Physical Attack dan +50 Magic Attack. Jika semua Hero sekutu sudah Awaken, peroleh tambahan +20% Physical dan Magical Lifesteal.",
            ),
            (
                "打出<color=#FFE897>3阶英雄牌</color>，额外+6级。",
                "Saat memainkan <color=#FFE897>Kartu Hero Tier 3</color>, peroleh +6 Level tambahan.",
            ),
            (
                "持续时间提升至3秒，并将敌人<color=#86ccfd>法力值清空</color>",
                "Durasi meningkat menjadi 3 detik dan <color=#86ccfd>menguras habis Mana</color> musuh",
            ),
            (
                "棋手每次<color=#FFE897>受到的伤害</color>减少2点。",
                "Setiap kali Contestant <color=#FFE897>menerima Damage</color>, kurangi sebesar 2.",
            ),
            (
                "<color=#99DEB0>召唤╉图腾</color>，己方所有【大河】英雄获得相当于<a><color=#99DEB0>╉<b>图腾</b></color></a>等级<color=#99DEB0>50%</color>的<a>═临时等级</a>。",
                "<color=#99DEB0>Panggil ╉Totem</color>. Semua Hero [Riverlands] sekutu memperoleh Level sebesar <a><color=#99DEB0>╉<b>Totem</b></color></a> x <color=#99DEB0>50%</color> sebagai <a>═Temporary Level</a>.",
            ),
            (
                "等级最高的<color=#99DEB0>2名</color>己方英雄首次阵亡后，会随机以<color=#99DEB0>1%</color>、<color=#99DEB0>10%</color>、<color=#99DEB0>20%</color>、<color=#99DEB0>30%</color>的生命值<a href=16><color=#99DEB0>╧复生</color></a>。",
                "Saat <color=#99DEB0>2</color> Hero sekutu dengan Level tertinggi gugur untuk pertama kalinya, mereka akan secara acak memiliki <color=#99DEB0>1%</color>, <color=#99DEB0>10%</color>, <color=#99DEB0>20%</color>, atau <color=#99DEB0>30%</color> HP saat <a href=16><color=#99DEB0>╧Revive</color></a>.",
            ),
            (
                "<color=#99DEB0>通用系列</color>\n等级最高的<color=#99DEB0>2名</color>己方英雄首次阵亡后，会随机以<color=#99DEB0>1%</color>、<color=#99DEB0>10%</color>、<color=#99DEB0>20%</color>、<color=#99DEB0>30%</color>的生命值<a href=16><color=#99DEB0>╧复生</color></a>。",
                "<color=#99DEB0>General Series</color>\nSaat <color=#99DEB0>2</color> Hero sekutu dengan Level tertinggi gugur untuk pertama kalinya, mereka akan secara acak memiliki <color=#99DEB0>1%</color>, <color=#99DEB0>10%</color>, <color=#99DEB0>20%</color>, atau <color=#99DEB0>30%</color> HP saat <a href=16><color=#99DEB0>╧Revive</color></a>.",
            ),
            (
                "摄灵效果英雄击败敌方英雄时，将其灵魂复活（无卡牌效果），满法力值作战，持续<color=#00FF00>8</color>秒。",
                "Saat Hero berefek Soul Snatch mengalahkan Hero musuh, jiwa musuh dibangkitkan (tanpa efek kartu) untuk bertarung dengan Mana penuh selama <color=#00FF00>8</color> detik.",
            ),
            (
                "你在战斗中<a href=16><color=#99DEB0>╧复生</color></a>的英雄，会无敌<color=#99DEB0>3秒</color>，并且获得<color=#99DEB0>300%</color>攻击速度和<color=#99DEB0>100%</color>暴击率（不可叠加）。",
                "Hero milikmu yang <a href=16><color=#99DEB0>╧Revive</color></a> saat Combat menjadi Kebal selama <color=#99DEB0>3 detik</color>, serta memperoleh <color=#99DEB0>+300%</color> Attack Speed dan <color=#99DEB0>+100%</color> Crit Rate (tidak dapat ditumpuk).",
            ),
            (
                "<a href=10><color=#99DEB0>╫牺牲系列</color></a>\n你在战斗中<a href=16><color=#99DEB0>╧复生</color></a>的英雄，会无敌<color=#99DEB0>3秒</color>，并且获得<color=#99DEB0>300%</color>攻击速度和<color=#99DEB0>100%</color>暴击率（不可叠加）。",
                "<a href=10><color=#99DEB0>╫Sacrifice Series</color></a>\nHero milikmu yang <a href=16><color=#99DEB0>╧Revive</color></a> saat Combat menjadi Kebal selama <color=#99DEB0>3 detik</color>, serta memperoleh <color=#99DEB0>+300%</color> Attack Speed dan <color=#99DEB0>+100%</color> Crit Rate (tidak dapat ditumpuk).",
            ),
            (
                "己方英雄触发<a href=11><color=#99DEB0>╬整备</color></a>时，所有英雄获得场上<a href=11><color=#99DEB0>╬整备</color></a>英雄数量x<color=#99DEB0>1.5</color>的等级。",
                "Saat Hero sekutu memicu <a href=11><color=#99DEB0>╬Prepare</color></a>, semua Hero memperoleh Level sebesar jumlah Hero <a href=11><color=#99DEB0>╬Prepare</color></a> di arena x <color=#99DEB0>1.5</color>.",
            ),
            (
                "<a href=11><color=#99DEB0>╬整备系列</color></a>\n己方英雄触发<a href=11><color=#99DEB0>╬整备</color></a>时，所有英雄获得场上<a href=11><color=#99DEB0>╬整备</color></a>英雄数量x<color=#99DEB0>1.5</color>的等级。",
                "<a href=11><color=#99DEB0>╬Prepare Series</color></a>\nSaat Hero sekutu memicu <a href=11><color=#99DEB0>╬Prepare</color></a>, semua Hero memperoleh Level sebesar jumlah Hero <a href=11><color=#99DEB0>╬Prepare</color></a> di arena x <color=#99DEB0>1.5</color>.",
            ),
            (
                "战斗开始时，若己方有<color=#99DEB0>至少2个</color>阵营，所有英雄获得<color=#99DEB0>20</color>×阵营数的等级。",
                "Saat Combat dimulai, jika sekutu memiliki <color=#99DEB0>minimal 2</color> Faction, semua Hero memperoleh Level sebesar <color=#99DEB0>20</color> x jumlah Faction.",
            ),
            (
                "<color=#99DEB0>多阵营系列</color>\n战斗开始时，若己方有<color=#99DEB0>至少2个</color>阵营，所有英雄获得<color=#99DEB0>20</color>×阵营数的等级。",
                "<color=#99DEB0>Multi-Faction Series</color>\nSaat Combat dimulai, jika sekutu memiliki <color=#99DEB0>minimal 2</color> Faction, semua Hero memperoleh Level sebesar <color=#99DEB0>20</color> x jumlah Faction.",
            ),
            (
                "回合开始时，<color=#FFE897>╥阿科米亚核心失去20级</color>，获得10能量。每回合最多触发1次。",
                "Saat Round dimulai, <color=#FFE897>╥Arcomia Core kehilangan 20 Level</color> dan memperoleh 10 Energy (maks. 1 kali per Round).",
            ),
            (
                "<color=#98CBFF>╈退场</color>关键词在<color=#98CBFF>棋盘上的</color>英雄被卖出时触发，实战中需要在效果触发和英雄战力之间做决断。",
                "Keyword <color=#98CBFF>╈Retire</color> terpicu saat Hero <color=#98CBFF>di arena</color> dijual, dalam pertandingan perlu memilih antara memicu efek Retire atau mempertahankan kekuatan tempur Hero.",
            ),
            ("抽2张牌。", "Ambil 2 kartu."),
            ("抽3张牌。", "Ambil 3 kartu."),
            ("抽<color=#99DEB0>2张</color>牌。", "Ambil <color=#99DEB0>2</color> kartu."),
            ("抽取1张3阶及以下的英雄牌。", "Ambil 1 Kartu Hero Tier 3 ke bawah."),
            ("指定1名英雄获取词条能力，<color=#FFE897>╨登场：抽1张牌</color>。", "Pilih 1 Hero untuk memperoleh kemampuan Trait: <color=#FFE897>╨Deploy: Ambil 1 kartu</color>."),
            ("每3次普攻抽出蓝牌", "Ambil 1 Kartu Biru setiap 3 Basic Attack"),
            (
                "你的英雄触发<a href=200><color=#99DEB0>╊夺取</color></a>时，所有英雄等级<color=#99DEB0>+6</color>。",
                "Saat Hero milikmu memicu <a href=200><color=#99DEB0>╊Steal</color></a>, semua Hero memperoleh <color=#99DEB0>+6</color> Level.",
            ),
            (
                "<a href=200><color=#99DEB0>╊夺取系列</color></a>\n你的英雄触发<a href=200><color=#99DEB0>╊夺取</color></a>时，所有英雄等级<color=#99DEB0>+6</color>。",
                "<a href=200><color=#99DEB0>╊Steal Series</color></a>\nSaat Hero milikmu memicu <a href=200><color=#99DEB0>╊Steal</color></a>, semua Hero memperoleh <color=#99DEB0>+6</color> Level.",
            ),
            (
                "<color=#FFE897>╊夺取效果英雄击败敌方英雄</color>时，将其灵魂复活（无卡牌效果），满法力值作战，持续5秒。",
                "Saat <color=#FFE897>Hero berefek ╊Steal milikmu mengalahkan Hero musuh</color>, bangkitkan jiwanya (tanpa efek Kartu) untuk bertarung dengan Mana penuh selama 5 detik.",
            ),
            (
                "指定1名英雄获取词条能力，<color=#FFE897>╊夺取：20等级</color>。",
                "Tentukan 1 Hero untuk memperoleh kemampuan Trait: <color=#FFE897>╊Steal: 20 Level</color>.",
            ),
            (
                "获得1张随机的╆转瞬英雄牌。",
                "Mendapatkan 1 ╆Fleeting Kartu Hero acak.",
            ),
            (
                "立即获得<color=#99DEB0>4张</color>召唤、╉<color=#99DEB0>图腾系列</color>英雄牌。召唤单位时（含召唤物，╉图腾），获得<color=#99DEB0>1张</color>召唤、╉<color=#99DEB0>图腾系列</color>英雄牌（每回合最多<color=#99DEB0>4张</color>）。",
                "Segera memperoleh <color=#99DEB0>4</color> Kartu Hero Seri Summon dan ╉<color=#99DEB0>Totem</color>. Saat memanggil unit (termasuk unit Summon dan ╉Totem), peroleh <color=#99DEB0>1</color> Kartu Hero Seri Summon dan ╉<color=#99DEB0>Totem</color> (maks. <color=#99DEB0>4 kartu</color> per Round).",
            ),
            (
                "立即获得<color=#99DEB0>4张</color><a href=10><color=#99DEB0>╫牺牲</color></a>英雄牌。你的英雄触发<a href=10><color=#99DEB0>╫牺牲</color></a>时，获得<color=#99DEB0>1张</color><a href=10><color=#99DEB0>╫牺牲</color></a>英雄牌（每回合最多<color=#99DEB0>4张</color>）。",
                "Segera memperoleh <color=#99DEB0>4</color> Kartu Hero <a href=10><color=#99DEB0>╫Sacrifice</color></a>. Saat Hero milikmu memicu <a href=10><color=#99DEB0>╫Sacrifice</color></a>, peroleh <color=#99DEB0>1</color> Kartu Hero <a href=10><color=#99DEB0>╫Sacrifice</color></a> (maks. <color=#99DEB0>4</color> per Round).",
            ),
            (
                "立即获得<color=#99DEB0>4张牺牲</color>英雄牌。你的英雄触发<color=#99DEB0>牺牲</color>时，获得<color=#99DEB0>1张</color>牺牲英雄牌（每回合最多<color=#99DEB0>4张</color>）。",
                "Segera memperoleh <color=#99DEB0>4 Kartu Hero Sacrifice</color>. Saat Hero milikmu memicu <color=#99DEB0>Sacrifice</color>, peroleh <color=#99DEB0>1</color> Kartu Hero Sacrifice (maks. <color=#99DEB0>4</color> per Round).",
            ),
            (
                "立即获得<color=#99DEB0>4张</color>召唤、<a href=321><color=#99DEB0>╉图腾</color></a>系列英雄牌。<color=#99DEB0>召唤单位时（含召唤物，<a href=321><color=#99DEB0>╉图腾</color></a>）</color>，获得<color=#99DEB0>1张</color>召唤、<a href=321><color=#99DEB0>╉图腾</color></a>系列英雄牌（每回合最多<color=#99DEB0>4张</color>）。",
                "Segera memperoleh <color=#99DEB0>4</color> Kartu Hero Seri Summon dan <a href=321><color=#99DEB0>╉Totem</color></a>. <color=#99DEB0>Saat memanggil unit (termasuk unit Summon dan <a href=321><color=#99DEB0>╉Totem</color></a>)</color>, peroleh <color=#99DEB0>1</color> Kartu Hero Seri Summon dan <a href=321><color=#99DEB0>╉Totem</color></a> (maks. <color=#99DEB0>4</color> per Round).",
            ),
        ]
        for zh_c, id_c in curated_t1_pairs:
            self._register_t1_pair(zh_c, id_c)

    def translate_en_to_id(self, en_text: str, source_zh: str = "") -> str:
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
            cand = self.tier1_en_desc_to_id_desc[norm_en]
            return self._finalize_output(source_zh, cand, en_text)

        def _convert_segment(seg: str) -> str:
            seg = rewrite_en_card_to_id(source_zh, seg)
            out = seg.replace("The First Lands", "First Lands")

            for pat, repl in COMPILED_VAR_SUBS:
                out = pat.sub(repl, out)

            sentinels: list[tuple[str, str]] = []
            if self._protected_re is not None:
                def _protect_match(m: re.Match[str]) -> str:
                    idx = len(sentinels)
                    tok = f"__WXQPR{idx}__"
                    val = m.group(0)
                    if val == "Magical Damage":
                        val = "Magic Damage"
                    sentinels.append((tok, val))
                    return tok

                out = self._protected_re.sub(_protect_match, out)

            out = translate_segment_en_to_id(out)

            for tok, orig_val in sentinels:
                out = out.replace(tok, orig_val, 1)

            # Re-run card rewriter post-translation to restore proper nouns and natural Indonesian structures
            out = rewrite_en_card_to_id(source_zh, out)

            out = CARD_HERO_NAME_INVERT_RE.sub(
                lambda m: f"Kartu Hero {m.group(1)}" if "hero" in m.group(0).lower() else f"Kartu {m.group(1)}",
                out,
            )
            out = RANDOM_CARD_RE.sub(r"\1 \2 acak", out)
            out = apply_glossary_cleanup(out)
            return out

        res = translate_preserving_skeleton(en_text, _convert_segment)
        res = SEBUAH_NUM_RE.sub(r"\1", res)
        return self._finalize_output(source_zh, res, en_text)

    def _fit_length_bound(self, source_zh: str, candidate: str) -> str:
        """Guarantee candidate satisfies len(candidate) <= max(len(source_zh) * 8, 48) when len(source_zh) >= 4."""
        candidate = apply_glossary_cleanup(candidate)

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
            ("di medan tempur", "di arena"),
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

    def _finalize_output(self, source_zh: str, text: str, baseline_en: str = "") -> str:
        """Apply canonical glossary polishing, placeholder spacing, bracket normalization, and card wrapping."""
        if not text:
            return text

        candidate = rewrite_en_card_to_id(source_zh, text)
        ok_r, _ = validate_translation(source_zh, candidate)
        if not ok_r:
            candidate = reinject_skeleton_from_source(
                source_zh,
                TAG_RE.sub("", candidate),
                inner_translator=self._translate_raw_zh_to_id,
                baseline_en=baseline_en,
                en_translator=self.translate_en_to_id,
            )

        candidate = polish_indonesian_card_text(source_zh, candidate, baseline_en)
        candidate = ensure_placeholder_spacing(normalize_brackets(candidate))
        if ";" not in source_zh and ";" in candidate:
            candidate = SEMICOLON_SPLIT_RE.sub(". ", candidate)
            candidate = sanitize_target_text(source_zh, candidate)
        bounded = self._fit_length_bound(source_zh, candidate)
        if (";" in source_zh or ";" not in bounded) and len(bounded) > 20:
            wrapped = wrap_card_description(bounded, max_width=26, source_zh=source_zh)
            if validate_translation(source_zh, wrapped)[0]:
                return wrapped
        return bounded

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
            adapted_t1 = adapt_tier1_placeholders_to_source(source_zh, raw_t1)
            ok_direct, _ = validate_translation(source_zh, adapted_t1)
            if ok_direct:
                return (self._finalize_output(source_zh, adapted_t1, baseline_en or ""), "tier1")
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    adapted_t1,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier1")

        # 1b. Composite Talent Series header+body splitter
        m_ser = SERIES_HEADER_RE.match(source_zh)
        if m_ser:
            canon_header = ZH_SERIES_HEADER_MAP.get(m_ser.group(2), m_ser.group(2).replace("系列", " Series"))
            body_zh = m_ser.group(4)
            body_en = baseline_en.split("\n", 1)[1] if (baseline_en and "\n" in baseline_en) else baseline_en
            body_id, body_tier = self.translate_entry(body_zh, baseline_en=body_en)
            full_cand = f"{m_ser.group(1)}{canon_header}{m_ser.group(3)}\n{body_id}"
            if validate_translation(source_zh, full_cand)[0]:
                return (self._finalize_output(source_zh, full_cand, baseline_en or ""), body_tier)

        # 2. Tier 1 normalized (tag-stripped) match + skeleton re-injection
        norm_zh = normalize_plain_zh(source_zh)
        if norm_zh and norm_zh in self.tier1_plain_zh_to_id:
            raw_t1 = self.tier1_plain_zh_to_id[norm_zh]
            adapted_t1 = adapt_tier1_placeholders_to_source(source_zh, raw_t1)
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    adapted_t1,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier1")

        # 2b. Tier 1 formula-skeleton match (handles all 234 dynamic formula Hero skills/enhancements/awakenings)
        skel_zh = normalize_formula_skeleton_zh(source_zh)
        if skel_zh and skel_zh in self.tier1_formula_zh_to_id:
            cands = self.tier1_formula_zh_to_id[skel_zh]
            src_nums = NUM_FIND_RE.findall(normalize_plain_zh(source_zh))
            best_cand = cands[0]
            best_score = -1
            for c_cn, c_id in cands:
                c_nums = NUM_FIND_RE.findall(normalize_plain_zh(c_cn))
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
            has_chunk_slice = any(
                bc in cand
                for bc in (
                    "<color=#ffffffbf> Pasif: Basic Attack",
                    "<color=#ffffffbf> di depannya",
                    "<color=#ffffffbf> pipa dan mengaktifkan",
                    "<color=#d487e4> bola energi yang",
                    "<color=#d487e4> Saat bola",
                )
            )
            if ok and not has_chunk_slice:
                return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier1")

        # 2c. Tier 1 description match via baseline_en
        if baseline_en:
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
                    return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier1")

        # 2e. Contestant Name-Stripped Tier 1 Lookup
        CONTESTANT_NAMES_ZH = (
            "香香", "嬴律", "孙小宾", "小妲己", "庄小鱼", "弈星",
            "明先生", "玉环", "班叔", "瑶妹", "闹闹", "阿离",
            "安琪拉", "武凤", "姜导", "常小娥", "昭君", "白歌",
            "马可", "乔汐",
        )
        for alt in CONTESTANT_NAMES_ZH:
            if alt in source_zh:
                stripped = source_zh.replace(f"{alt}的", "").replace(alt, "")
                norm_p = normalize_plain_zh(stripped)
                if norm_p and len(norm_p) >= 6:
                    variants = [
                        norm_p,
                        norm_p.replace("开战时", "战斗开始时"),
                        norm_p.replace("开局时", "比赛开始时"),
                        norm_p.replace("{Energy}", "点能量"),
                        norm_p.replace("开战时", "战斗开始时").replace("{Energy}", "点能量"),
                        norm_p.replace("开局时", "比赛开始时").replace("{Energy}", "点能量"),
                    ]
                    for v in variants:
                        if v in self.tier1_plain_zh_to_id:
                            raw_t1 = self.tier1_plain_zh_to_id[v]
                            adapted_t1 = adapt_tier1_placeholders_to_source(source_zh, raw_t1)
                            cand = self._fit_length_bound(
                                source_zh,
                                reinject_skeleton_from_source(
                                    source_zh,
                                    adapted_t1,
                                    inner_translator=self._translate_raw_zh_to_id,
                                    baseline_en=baseline_en,
                                    en_translator=self.translate_en_to_id,
                                ),
                            )
                            if validate_translation(source_zh, cand)[0]:
                                return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier1")

                skel = normalize_formula_skeleton_zh(stripped)
                if skel and len(skel) >= 6:
                    skel_variants = [
                        skel,
                        skel.replace("开战时", "战斗开始时"),
                        skel.replace("开局时", "比赛开始时"),
                        skel.replace("{Energy}", "点能量"),
                        skel.replace("开战时", "战斗开始时").replace("{Energy}", "点能量"),
                        skel.replace("开局时", "比赛开始时").replace("{Energy}", "点能量"),
                    ]
                    for sv in skel_variants:
                        if sv in self.tier1_formula_zh_to_id:
                            cands = self.tier1_formula_zh_to_id[sv]
                            t1_desc_cn, t1_desc_id = cands[0]
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
                            if validate_translation(source_zh, cand)[0]:
                                return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier1")
                break

        # 2f. Equipment Selection Chests Deterministic Parser
        m_chest = CHEST_CHOICE_RE.search(source_zh)
        if m_chest:
            raw_items = m_chest.group(1).split("、")
            count = m_chest.group(2)
            CHEST_EQUIPMENT_MAP = {
                "名刀·司命": "Destiny",
                "极寒风暴": "Glacial Buckler",
                "反伤重甲": "Thorn Heavy Armor",
                "近卫荣耀": "Guardian's Glory",
                "不祥征兆": "Ominous Premonition",
                "霸者重装": "Overlord's Platemail",
                "噬神之书": "Insatiable Tome",
                "虚无法杖": "Void Staff",
                "博学者之怒": "Savant's Wrath",
                "铸梦·逐风": "Dream-Forged Windchaser",
                "红魔": "Red Demon",
                "影牙": "Shadow Fang",
                "破晓": "Daybreak",
                "末世": "Doomsday",
                "征服之剑": "Sword of Conquest",
                "冥王": "Underworld King",
                "痛苦面具": "Mask of Agony",
                "破军": "Siegebreaker",
                "纯净苍穹": "Pure Sky",
                "无尽巨剑": "Endless Greatsword",
                "制裁之剑": "Sanction Sword",
                "不死鸟之眼": "Eye of the Phoenix",
                "魔女斗篷": "Succubus Cloak",
                "红莲炎甲": "Crimson Lotus Armor",
                "月神": "Moon God",
                "寒霜侵袭": "Frost Assault",
                "贤者之书": "Tome of Wisdom",
                "炽热支配者": "Sanguine Dominator",
                "生命魔典": "Grimoire of Life",
                "法源之杯": "Mana Chalice",
                "破茧之衣": "Cocoon-Breaking Garment",
                "聚灵水晶": "Spirit-Gathering Crystal",
                "魔律之刃": "Blade of Magic Law",
            }
            resolved_items = []
            for it in raw_items:
                it = it.strip()
                name = CHEST_EQUIPMENT_MAP.get(it) or self.orig_unique.get(it) or it
                resolved_items.append(name)
            if len(resolved_items) > 1:
                items_str = f"{', '.join(resolved_items[:-1])}, atau {resolved_items[-1]}"
            else:
                items_str = resolved_items[0] if resolved_items else ""
            chest_id = f"Dipakai oleh Hero target. Pilih {count} dari {items_str}."
            if validate_translation(source_zh, chest_id)[0]:
                return (self._finalize_output(source_zh, chest_id, baseline_en or ""), "tier2")

        # 2g. Hero Choice Vouchers Deterministic Parser
        m_v1 = HERO_CHOICE_VOUCHER_RE.search(source_zh)
        if m_v1:
            pool = m_v1.group(1)
            pick = m_v1.group(2)
            faction_cn = m_v1.group(3)
            factionless = m_v1.group(4)
            tier = m_v1.group(5)
            copies = m_v1.group(6)
            ZH_FACTION_MAP = {
                "三分之地": "Three Kingdoms",
                "三分": "Three Kingdoms",
                "大河流域": "Riverlands",
                "大河": "Riverlands",
                "日落海": "Sunset Sea",
                "河洛": "Central Plains",
                "玄雍": "Xuanyong",
                "逐鹿": "Zhulu Plateau",
                "长城守卫军": "Great Wall",
                "长城": "Great Wall",
                "稷下学院": "Jixia",
                "稷下": "Jixia",
                "尧天": "Yaotian",
                "云梦泽": "Cloudream",
                "云梦": "Cloudream",
                "海都": "Sunset Sea",
            }
            if factionless:
                voucher_id = f"Pilih {pick} dari {pool} Hero tanpa Faction Tier {tier}, lalu peroleh {copies} salinan Kartu Hero tersebut."
            else:
                f_en = ZH_FACTION_MAP.get(faction_cn) or faction_cn
                voucher_id = f"Pilih {pick} dari {pool} Hero [{f_en}] Tier {tier}, lalu peroleh {copies} salinan Kartu Hero tersebut."
            if validate_translation(source_zh, voucher_id)[0]:
                return (self._finalize_output(source_zh, voucher_id, baseline_en or ""), "tier2")

        m_v2 = HERO_SPECIFIED_RE.search(source_zh)
        if m_v2:
            pfx_zh = m_v2.group(1).strip()
            count = m_v2.group(2)
            copies = m_v2.group(3)
            sfx_zh = m_v2.group(4).strip()
            if not pfx_zh and not sfx_zh:
                v_id = f"Pilih {count} Hero, lalu peroleh {copies} salinan Kartu Hero tersebut."
                if validate_translation(source_zh, v_id)[0]:
                    return (self._finalize_output(source_zh, v_id, baseline_en or ""), "tier2")

        # 2d. Exact-tag baseline_en match: If baseline_en carries exact tags, translate preserving skeleton
        # Guarded against upstream Opus-MT corruption
        if baseline_en:
            if not OPUS_CORRUPTION_RE.search(baseline_en):
                b_tags = TAG_RE.findall(baseline_en)
                src_tags = TAG_RE.findall(source_zh)
                if b_tags and b_tags == src_tags:
                    cand_en = translate_preserving_skeleton(baseline_en, self.translate_en_to_id)
                    cand_en = sanitize_target_text(source_zh, cand_en)
                    cand_en = normalize_tag_boundary_spacing(source_zh, cand_en)
                    if validate_translation(source_zh, cand_en)[0]:
                        return (self._finalize_output(source_zh, cand_en, baseline_en), "tier2")

        # 3. Tier 2 exact or plain entity/detail match -> EN -> ID
        t2_en = self.tier2_zh_to_en.get(source_zh) or (
            self.tier2_plain_zh_to_en.get(norm_zh) if norm_zh else None
        )
        if t2_en:
            t2_id = self.translate_en_to_id(t2_en, source_zh=source_zh)
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
                return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier2")

        # 4. Tier 3: Use baseline_en (ZH -> EN -> ID)
        if baseline_en:
            cand = self._fit_length_bound(
                source_zh,
                sanitize_target_text(source_zh, self.translate_en_to_id(baseline_en, source_zh=source_zh)),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier3")

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
                return (self._finalize_output(source_zh, repaired, baseline_en or ""), "tier3")

            if validate_translation(source_zh, baseline_en)[0]:
                return (self._finalize_output(source_zh, baseline_en, baseline_en or ""), "tier3")

        # 5. Fallback for unmapped raw Chinese strings
        cand = self._fit_length_bound(source_zh, self._translate_raw_zh_to_id(source_zh))
        return (self._finalize_output(source_zh, cand, baseline_en or ""), "tier3")

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
            ("登场", "Deploy"),
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
            out = SPACES_RE.sub(" ", out).strip()
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


_GLOBAL_GLOSSARY_ENGINE: ThreeTierGlossary | None = None


def get_glossary_engine() -> ThreeTierGlossary:
    """Return a cached singleton instance of ThreeTierGlossary loaded from reference files."""
    global _GLOBAL_GLOSSARY_ENGINE
    if _GLOBAL_GLOSSARY_ENGINE is None:
        refs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "references"
        if not refs_dir.exists():
            refs_dir = Path("data/references")
        t1_path = refs_dir / "tier1_wiki_id.json"
        t2_path = refs_dir / "tier2_wiki_en.json"
        t2_details_path = refs_dir / "tier2_wiki_details_en.json"
        _GLOBAL_GLOSSARY_ENGINE = ThreeTierGlossary.from_reference_files(
            t1_path,
            t2_path,
            tier2_details_path=t2_details_path,
        )
    return _GLOBAL_GLOSSARY_ENGINE


