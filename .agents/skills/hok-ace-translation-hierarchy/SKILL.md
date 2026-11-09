---
name: hok-ace-translation-hierarchy
description: Use when building the Indonesian glossary, scraping reference websites, or translating Honor of Kings Ace strings from Chinese or English into Indonesian.
---

# HoK: Ace 3-Tier Translation Hierarchy & ID Hybrid Specification

## Overview

All translations in **ID Hybrid** mode (`data/catalog_checkpoints/catalog.json.gz`) MUST strictly follow the **3-Tier Reference Hierarchy** and the **Locked Canonical Glossary** below (`src/acepatchindo/glossary.py` and `src/acepatchindo/card_rewriter.py`).

## Scope of `ID Hybrid` Mode (`HybridClassifier`)

- **Translated to Natural Tactical Bahasa Indonesia:**
  - All **`5,621`** active gameplay descriptions in `catalog["unique"]` (including the **`58`** gameplay descriptions in `WINDOWS_108_TARGET_DESC_ID`) and all **`15,397`** active `catalog["english_updates"]` entries across:
    1. Hero Active & Passive Skill Descriptions
    2. Hero Awakening Descriptions
    3. Effect Card (Tactic / Secret Skill) Descriptions
    4. Equipment Descriptions
    5. Talent & Sub-Card Descriptions
    6. Contestant (Lord / Chess Player) Skill & Related Card Descriptions
- **Kept in Canonical English (Hard Vetoed from Indonesian Translation):**
  - All `35,862` non-target entries in `catalog["unique"]` (including `50` UI/title strings in `WINDOWS_108_NONTARGET_EN`, pure equipment names such as `Wolf Tribe Totem Statue` / `Wolf Tooth Tribe Totem Statue+`, Hero Names, Card Titles, Talent Titles, Menu/UI Chrome, and training dummy debug strings).

## Locked Canonical Glossary (Must Remain English)

1. **Bracketed Faction Names (Always Bracketed After Head Noun, e.g. `Hero [Central Plains]`):**
   - `[Central Plains]`, `[Sunset Sea]`, `[Zhulu Plateau]`, `[Three Kingdoms]`, `[Riverlands]`, `[High Heaven]`, `[First Lands]`, `[Factionless]`, `[Great Wall]`, `[Jixia]`
2. **Core Mechanics & Tokens:**
   - `Initiate` (`╪Initiate`), `Deploy` (`╨Deploy`), `Prepare` (`╬Prepare`), `Sacrifice` (`╫Sacrifice`), `Revive` (`╧Revive`), `Perfect Revive` (`╧Perfect Revive`), `Temporary Level` (`═Temporary Level`), `Fleeting` (`╆Fleeting`), `Defeat` (`╇Defeat`), `Retire` (`╈Retire`), `Totem` (`╉Totem`: `Seer Totem`, `Bond Totem`, `Afterlife Totem`, `Fate Totem`), `Steal` (`╊Steal`), `Soul Snatch` (`╊Soul Snatch`), `Arcomia Core`, `Combine`, `[Divinity]`
3. **Contestant (Lord) Names:**
   - `Xiang`, `Ying Lü`, `Bai Ge`, `Little Daji`, `Little Sun Bin`, `Little Zhuang Fish`, `Little Chang'e` (and role noun `Contestant`, never `Peserta` or `Chess Player`).
4. **Canonical Hero & Sub-Card Title Sync (Must Match Standalone Title in `catalog["unique"]`):**
   - **Heroes:** `干将莫邪` -> `'Gan & Mo'`, `百里守约` -> `'Shouyue'` (never `Baili Shouyue`), `百里玄策` -> `'Xuance'` (never `Baili Xuance`), `诸葛亮` -> `'Kongming'`, `杨玉环` -> `'Yuhuan'`, `姜子牙` -> `'Ziya'`.
   - **Sub-Cards & Tokens:** `妙音` / `绕梁之音` -> `'Melody'`, `开局狂飙` / `开局爆发` -> `'Early Game Surge'`, `时光虹吸` -> `'Time Siphon'`, `点星` -> `'Star Point'`, `珍品宝箱` -> `'Treasure Chest'`, `全员增幅` -> `'Team-Wide Buff'`, `全员增幅·一` -> `'Team Buff I'`, `全员增幅·二` -> `'Team Buff II'`, `众星闪耀` -> `'Starry Radiance'`, `离场` (card) -> `'Departure'`, `有福同享` -> `'Shared Fortune'`, `超级储能` -> `'Super Energy Storage'`, `星绘秘宝` -> `'Star Painting Treasure'`, `蔷薇秘宝` -> `'Rose Treasure'`, `星彩秘宝` -> `'Starlight Treasure'`, `蔷薇奖励` -> `'Rose Reward'`, `名刀·司命` -> `'Destiny'`, `五阶英雄兑换券` -> `'Tier 5 Hero Voucher'`, `故障机器人` -> `'Glitch Robot'`, `好运连连` -> `'[Good Luck]'`.
5. **Series Headers & `#60D2` Footers:**
   - Leading `<color=#99DEB0>... Series</color>` headers (`Summon Series`, `General Series`, `Combine Series`, `╬Prepare Series`, `═Temporary Level Series`, etc.) and trailing `#60D2` footers (`Cannot be copied`, `Unstackable`, `Disappears after triggering`, etc.) remain in canonical English.

## The 3-Tier Authority Rule (`ThreeTierGlossary`)

1. **Tier 1 (`data/references/tier1_wiki_id.json` + `curated_t1_pairs` in `src/acepatchindo/glossary.py`):**
   - Primary Indonesian reference from `https://hok-ace-translate-id.netlify.app/` and curated verified translations.
   - Matched via exact Chinese key, normalized plain Chinese, or formula skeleton (`tier1_formula_zh_to_id`, ranked by exact `RUNTIME_BRACKET_TOKEN_RE` and numeric match).
2. **Tier 2 (`data/references/tier2_wiki_en.json` & `tier2_wiki_details_en.json`):**
   - Secondary English reference from `https://hokace.wiki/`, rewritten into tactical Bahasa Indonesia via `rewrite_en_card_to_id` + `polish_indonesian_card_text`.
3. **Tier 3 (`ZH -> EN -> ID` Fallback):**
   - Uses validated English baseline (`work/v2_baseline/catalog_en_full.json.gz`) rewritten and polished through `card_rewriter.py`, `tag_aligner.py`, and wrapped to `<= 34` visible characters via `card_wrapper.py`.
