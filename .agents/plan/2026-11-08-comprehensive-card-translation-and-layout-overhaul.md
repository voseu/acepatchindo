# Comprehensive Card Translation, Glossary Unification, Tag Alignment & CJK Word-Wrap Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate mid-word CJK line-cutting (`mil\nikmu`, `Equipme\nnt`), incomprehensible machine calques (`lexicon_id.py` word-by-word translations and `"Level <N> Hero ... +<M>"` ambiguity), tag-swallowing bugs (`tag_aligner.py`), scope veto leaks (`effect-card/`, `equipment`, `skill-kontestan/`, keyword tooltips), glossary splits, and live-server hotfix Chinese regressions across the entire Honor of Kings: Ace Indonesian Patcher.

**Architecture:** We overhaul the pipeline across 6 tightly coupled layers:
1. **VFS Scope & Entity Index (`scripts/01b_build_hybrid_vfs_index.py` & `src/acepatchindo/hybrid_classifier.py`):** Remove the artificial `KEEP_EN` vetoes on Effect Card descriptions, Equipment descriptions, Keyword Tooltips, and `Related` obtainment notes; expand `#60D2` Contestant category filters (`"棋手"`, `"棋手·秘技"`, `"任务"`, `"天赋"`); and normalize all `#60D2` card footers and Chinese Secret Skill titles into official English names.
2. **Tier 1 Matcher & Tactical Indonesian Rewriter (`src/acepatchindo/glossary.py` & `src/acepatchindo/card_rewriter.py`):** Fix the broken `ab_name == r_name` Chinese-to-English comparison in `_load_tier1_data` (recovering 109 human-translated Contestant cards), rewrite all ambiguous `"Level <N> Hero ... +<M>"` strings into clear tactical Indonesian (`"<N> Hero ... mendapat +<M> Level"`), and replace raw `lexicon_id.py` word-by-word fallback on gameplay cards with a deterministic Pattern/Clause Grammar Rewriter (`src/acepatchindo/card_rewriter.py`).
3. **Unified Glossary & Cross-Card Entity Sync (`src/acepatchindo/glossary.py`):** Enforce single canonical English terms for all mechanics (`Initiate`, `Deploy`, `Prepare`, `Revive` / `Perfect Revive`, `Arcomia Core`) and Indonesian board terms (`di arena`, `Kartu Efek`), synchronize Hero names between card titles and body descriptions (`Gan & Mo`, `Shouyue`, `Kongming`, `Yuhuan`, `Ziya`), synchronize Faction names (`[Central Plains]`, `[Sunset Sea]`, `[Zhulu Plateau]`), and synchronize parent-card references with actual generated `Related` card titles (`Melody`, `Early Game Surge`, `Destiny`, `Glitch Robot`, `Tier 5 Hero Voucher`).
4. **Precision Tag Aligner & Runtime Placeholder Spacer (`src/acepatchindo/tag_aligner.py`):** Disable whole-sentence/whole-clause tag swallowing in `reinject_skeleton_from_source` and `_wrap_exact_tag_sequence`, enforce mandatory spaces before runtime icon placeholders (`{Energy}`, `{LordExp}`, `{LordHp}`) and around numeric placeholders (`{0}`, `{1}`), and normalize fullwidth brackets `【...】` to `[...]`.
5. **CJK-Safe Smart Card Word-Wrapper (`src/acepatchindo/card_wrapper.py`):** Pre-wrap gameplay card descriptions at word boundaries (`\n` before exceeding 26 visible characters per line, ignoring XML tags and control tokens, and binding `[+-]\d+` signs to their numbers) so the game's CJK character-level renderer never slices Indonesian or English words in half at the right margin.
6. **Live Hotfix v1.9.1/v1.9.4 Coverage & Numeric-Template Runtime Fallback (`src/acepatchindo/windows_108_split.py` & `src/acepatchindo/dual_state_patch.py`):** Add all live server hotfix strings (Marco Polo, Cai Yan, Arthur, Dr Bian, Wu Zetian, Pursue Victory, Four Companions, Prepare for War, Control Sensing, Mechanism Secret Art, Angela modules, Ying Lü, Qiao Xi, and new Contestant Wu Feng) and embed a runtime numeric-skeleton fallback in `dual_state_patch.py` so future server number tweaks (`+2` -> `+3`) automatically render in Indonesian instead of reverting to Chinese.

**Tech Stack:** Python 3.12, `gzip`, `json`, `re`, `marshal`, `pytest`, `wxq_patch` (protobuf VFS patcher), Rust/MinGW (`celeslib_gui` wrapper).

**Spec:** This self-contained plan document (`/home/whise/project/project-klien/patcher/.agents/plan/2026-11-08-comprehensive-card-translation-and-layout-overhaul.md`).

## Global Constraints

- **Strict English Retention for Proper Nouns & Mechanics:** Card Titles (Hero, Effect, Talent, Contestant Skill), Equipment Names, Faction Names (`[Central Plains]`, `[Sunset Sea]`, `[Zhulu Plateau]`, `[Three Kingdoms]`, `[River Basin]`, `[Chang'an]`, `[XuanYong]`, `[稷下/Jixia]`), and Mechanic Keywords (`Initiate`, `Deploy`, `Prepare`, `Revive`, `Perfect Revive`, `Arcomia Core`, `Fleeting`, `Totem`, `Temporary Level`, `Star Source Armament`, `Flash`, `Sacrifice`, `Steal`) MUST remain in official English.
- **Canonical Glossary Decisions (Locked):**
  - `╪开团` -> **`Initiate`** (never `Engage` or `Memulai`)
  - `╨登场` -> **`Deploy`** (never `pada-entri efek` or `Deployment`)
  - `╬整备` -> **`Prepare`** (never `Preparation`)
  - `╧复生` / `╧完美复生` -> **`Revive`** / **`Perfect Revive`** (never `Resurrect` or `Resurrection`)
  - `阿科米亚核心` -> **`Arcomia Core`** (never `Akomia Core` or bare `Core`)
  - `战场 / 场上` -> **`di arena`** (never `di field` or `di medan tempur`)
  - `效果牌 / 战术牌` -> **`Kartu Efek`** (never `Kartu Tactic`)
- **Hero Title == Hero Body Name (Locked):**
  - `干将莫邪` -> **`Gan & Mo`** (never `Ganjiang Moye`)
  - `百里守约` -> **`Shouyue`** (never `Baili Shouyue`)
  - `诸葛亮` -> **`Kongming`** (never `Zhuge Liang`)
  - `杨玉环` -> **`Yuhuan`** (never `Yang Yuhuan`)
  - `姜子牙` -> **`Ziya`** (never `Jiang Ziya`)
- **Parent Card Reference == Generated Related Card Title (Locked):**
  - `绕梁之音` -> **`Melody`** (never `Melodious Notes`)
  - `开局爆发` -> **`Early Game Surge`** (never `Opening Overdrive`)
  - `名刀·司命` -> **`Destiny`** (never `Famous Blade • Life-Stealer`)
  - `五阶英雄兑换券` -> **`Tier 5 Hero Voucher`** (never `Tier 5 Hero Exchange Vouchers`)
  - `故障机器人` -> **`Glitch Robot`** (never `Glitch Bots`)
- **Tactical Indonesian Phrasing:** Never output `"Level <N> Hero <target> +<M>"`. Always format as `"<N> Hero <target> mendapat +<M> Level"` (or `"Level dari <N> Hero <target> +<M>"`).
- **Validation Guard Compliance:** Every translated string MUST pass both `src/acepatchindo/validator.py::validate_translation` and `wxq_patch.translation_rules.validate_translation` (0 CJK characters, identical XML tag sequence, identical placeholder multiset, identical control token multiset `[\u2540-\u257f]`, no empty tags, identical semicolon count, no extreme expansion).

---

## File Structure & Responsibilities

- **Modify:** `scripts/01b_build_hybrid_vfs_index.py`
  - Expand `target_zh` in `data/references/hybrid_vfs_index.json` to include Effect Card descriptions, Equipment descriptions, all `#60D2` Contestant Skill categories (`"棋手"`, `"棋手·秘技"`, `"任务"`, `"天赋"`), Keyword Tooltip descriptions, and `Related` card obtainment notes, while keeping Card Titles, Equipment Names, Faction Names, and `#60D2` footer badges in `veto_title_zh` (clean official English).
- **Modify:** `src/acepatchindo/hybrid_classifier.py`
  - Remove `P_EFFECT_CARD_PATTERN` from `NON_TARGET_EN_PATTERNS` so Effect Card descriptions, Equipment descriptions, and the 6 previously vetoed Talents (`Copier`, `Genie in a Bottle`, `Five Blessings`, `Ultimate Copier`, `Reinforcements`, `Glory of the Old Guard`) are classified as `TRANSLATE_ID` instead of `KEEP_EN`.
- **Create:** `src/acepatchindo/card_rewriter.py`
  - Deterministic Indonesian tactical rewriter and pattern-grammar translator for gameplay descriptions:
    - Fixes Tier 1 `"Level <N> Hero ... +<M>"` ambiguity and unnatural Mandarin calques (`Saat memberikan efek CC milikmu`, `Saat setiap Round pertama kali...`).
    - Translates English gameplay sentences (`Effect Cards`, `Equipment`, `Contestant Skills`, `Talents`, `Tooltips`, `Related notes`) using structured clause patterns (`When/After/At the start of Combat...`, `Gain/Grant/Summon/Restore...`) instead of broken word-by-word replacement.
    - Enforces canonical glossary terms, Hero names, Faction names, Related card names, and runtime placeholder spacing (`{Energy}`, `{LordExp}`, `{LordHp}`).
- **Create:** `src/acepatchindo/card_wrapper.py`
  - CJK-safe word-wrapper (`wrap_card_description(text: str, max_width: int = 26) -> str`) that measures visible character width (stripping XML tags `<...>` and accounting for icon tokens/placeholders), binds `[+-]\d+%?` signs so `+` and `30` never split across lines, and inserts `\n` at word boundaries so the Unity CJK text box never cuts a word mid-syllable.
- **Modify:** `src/acepatchindo/tag_aligner.py`
  - Fix `_wrap_exact_tag_sequence` and `reinject_skeleton_from_source` so unmatched atomic tags wrap only the target keyword/noun phrase (or prepend mechanic badge `<a href=...><color=#ffffff>╨<b>Deploy</b></color></a>: `) instead of swallowing an entire clause or sentence; normalize `【...】` to `[...]`; ensure spaces before `{Energy}`, `{LordExp}`, `{LordHp}`.
- **Modify:** `src/acepatchindo/glossary.py`
  - Fix `_load_tier1_data` (`lords` related card matching) by bridging `rel["name"]` (English) to `zh_abs` (`ab_name` Chinese) via `tier2_wiki_details_en.json`, recovering all 109 human-translated Contestant cards.
  - Integrate `card_rewriter.py` and `card_wrapper.py` into `translate_entry` and `translate_en_to_id`.
- **Modify:** `src/acepatchindo/windows_108_split.py`
  - Add curated Indonesian translations for live hotfix v1.9.1/v1.9.4 strings (Marco Polo `+3`, Cai Yan, Arthur, Dr Bian, Wu Zetian, Pursue Victory, Four Companions, Prepare for War, Control Sensing, Mechanism Secret Art, Angela modules, Ying Lü, Qiao Xi, Wu Feng) and clean English titles for `#60D2` footers and Secret Skill titles (`神奇小鹿·奉献` -> `Magic Deer · Devotion`, `小菟送福` -> `Bunny's Blessing`, `如梦似幻` -> `Dreamlike Illusion`, `永恒时之回环` -> `Eternal Time Loop`).
- **Modify:** `src/acepatchindo/dual_state_patch.py`
  - Add runtime numeric-skeleton fallback in `Catalog` / `translate_table` so if a live server hotfix changes numbers in a known Chinese string (e.g., `等级+2` -> `等级+3`), it matches the canonical numeric template and substitutes the updated numbers into the Indonesian string while validating via `validate_translation`.
- **Modify:** `scripts/02_build_indonesian_catalog.py`
  - Rebuild `data/catalog_checkpoints/catalog.json.gz` and `data/catalog_checkpoints/en_to_id.json.gz` with the updated classifier, glossary, rewriter, tag aligner, and card wrapper.
- **Test Files:**
  - `tests/test_card_rewriter_and_wrapper.py` (New)
  - `tests/test_validator_and_aligner.py` (Modify)
  - `tests/test_glossary_and_tiers.py` (Modify)
  - `tests/test_dual_state_engine.py` (Modify)

---

### Task 1: CJK-Safe Smart Card Word-Wrapper & Runtime Placeholder Spacer

**Files:**
- Create: `src/acepatchindo/card_wrapper.py`
- Test: `tests/test_card_rewriter_and_wrapper.py`

**Interfaces:**
- Produces:
  - `ensure_placeholder_spacing(text: str) -> str`
  - `normalize_brackets(text: str) -> str`
  - `wrap_card_description(text: str, max_width: int = 26) -> str`

- [x] **Step 1: Write the failing test in `tests/test_card_rewriter_and_wrapper.py`**

```python
from acepatchindo.card_wrapper import (
    ensure_placeholder_spacing,
    normalize_brackets,
    wrap_card_description,
)
from acepatchindo.validator import validate_translation


def test_ensure_placeholder_spacing_fixes_glued_tokens():
    raw = "Memperoleh {0|1}{Energy}, memulihkan 1{LordHp} dan 4{LordExp}."
    fixed = ensure_placeholder_spacing(raw)
    assert fixed == "Memperoleh {0|1} {Energy}, memulihkan 1 {LordHp} dan 4 {LordExp}."


def test_normalize_brackets_converts_fullwidth():
    raw = "Dapat dipasang ke Hero 【Central Plains】 atau 【Sunset Sea】."
    assert normalize_brackets(raw) == "Dapat dipasang ke Hero [Central Plains] atau [Sunset Sea]."


def test_wrap_card_description_prevents_mid_word_split_and_preserves_tags():
    source_zh = "<a href=1><color=#ffffff>╨<b>登场</b></color></a>：己方穿戴装备最多的1名英雄等级+2。"
    translated = (
        "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>: "
        "1 Hero sekutu dengan Equipment terbanyak mendapat +2 Level."
    )
    wrapped = wrap_card_description(translated, max_width=26)
    assert "\n" in wrapped
    # Every visible line must be <= 26 chars and never split a word or "+2"
    import re
    for line in wrapped.split("\n"):
        visible = re.sub(r"<[^>]+>", "", line)
        assert len(visible) <= 28
        assert not line.endswith("+")
        assert not line.endswith("-")
    ok, reason = validate_translation(source_zh, wrapped)
    assert ok, f"Validation failed: {reason}"
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_card_rewriter_and_wrapper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'acepatchindo.card_wrapper'`

- [x] **Step 3: Implement `src/acepatchindo/card_wrapper.py`**

```python
"""CJK-safe card line-wrapper and runtime placeholder spacing normalizer."""

from __future__ import annotations

import re

TAG_TOKEN_RE = re.compile(r"(<(?:/?[A-Za-z][^>]*|/)>)")
RUNTIME_ICON_PLACEHOLDERS = ("{Energy}", "{LordHp}", "{LordExp}", "{Gold}", "{Coin}")

# Matches a number/placeholder glued directly to a word or runtime icon placeholder
GLUED_BEFORE_BRACE_RE = re.compile(r"([0-9A-Za-z\}])(\{(?:Energy|LordHp|LordExp|Gold|Coin)\})")
GLUED_AFTER_BRACE_RE = re.compile(r"(\{[0-9]+(?:\|[^\}]+)?\})([A-Za-z\u00C0-\u024F])")
GLUED_WORD_TO_NUM_BRACE_RE = re.compile(r"([A-Za-z\u00C0-\u024F]{2,})(\{[0-9]+(?:\|[^\}]+)?\})")
GLUED_DIGIT_TO_WORD_RE = re.compile(
    r"(?<![#=\w])(\d+)(Energy|Chess player|Renovation|Refresh|Hero|Level|Shield|Damage| kartu| Kartu)"
)


def normalize_brackets(text: str) -> str:
    """Convert Chinese fullwidth brackets 【...】 to clean ASCII [...] with spacing."""
    if not text:
        return text
    text = text.replace("【", "[").replace("】", "]")
    text = re.sub(r"([A-Za-z0-9])(\[[A-Za-z])", r"\1 \2", text)
    text = re.sub(r"(\])([A-Za-z0-9])", r"\1 \2", text)
    return text


def ensure_placeholder_spacing(text: str) -> str:
    """Ensure runtime icon placeholders ({Energy}, {LordHp}, {LordExp}) and numeric braces have spaces."""
    if not text:
        return text
    text = GLUED_BEFORE_BRACE_RE.sub(r"\1 \2", text)
    text = GLUED_AFTER_BRACE_RE.sub(r"\1 \2", text)
    text = GLUED_WORD_TO_NUM_BRACE_RE.sub(r"\1 \2", text)
    text = GLUED_DIGIT_TO_WORD_RE.sub(r"\1 \2", text)
    # Clean accidental double spaces outside tags
    text = re.sub(r" {2,}", " ", text)
    return text


def _visible_length(fragment: str) -> int:
    """Calculate approximate visible character count rendered by Unity CJK text box."""
    no_tags = TAG_TOKEN_RE.sub("", fragment)
    # Runtime icon placeholders expand to icon + label (~7 chars)
    no_tags = no_tags.replace("{Energy}", " Energy")
    no_tags = no_tags.replace("{LordHp}", " HP Kontestan")
    no_tags = no_tags.replace("{LordExp}", " EXP")
    # Numeric placeholders like {0|12} render their default value (~2 chars)
    no_tags = re.sub(r"\{[^{}]*\}", "10", no_tags)
    # Control tokens [\u2540-\u257f] render as 2-char wide inline icons
    ctrl_count = len(re.findall(r"[\u2540-\u257f]", no_tags))
    return len(no_tags) + ctrl_count


def _wrap_single_paragraph(paragraph: str, max_width: int) -> str:
    if not paragraph.strip() or _visible_length(paragraph) <= max_width:
        return paragraph

    # Tokenize by whitespace while keeping XML tags attached to their adjacent word tokens
    # First, protect spaces inside XML tags like `<a href=1>` or `<color=#ffffff>`
    protected: list[str] = []

    def _protect_tag(m: re.Match[str]) -> str:
        idx = len(protected)
        protected.append(m.group(0))
        return f"\x00TAG{idx}\x00"

    masked = TAG_TOKEN_RE.sub(_protect_tag, paragraph)
    # Bind standalone '+' or '-' to following digits so signs never wrap alone
    masked = re.sub(r"(?<=\s)([+-])\s+(\d)", r"\1\2", masked)

    words = masked.split(" ")
    restored_words: list[str] = []
    for w in words:
        if not w:
            continue
        rw = re.sub(r"\x00TAG(\d+)\x00", lambda m: protected[int(m.group(1))], w)
        restored_words.append(rw)

    lines: list[str] = []
    current_words: list[str] = []
    current_len = 0

    for word in restored_words:
        w_len = _visible_length(word)
        sep_len = 1 if current_words else 0
        if current_words and (current_len + sep_len + w_len > max_width):
            lines.append(" ".join(current_words))
            current_words = [word]
            current_len = w_len
        else:
            current_words.append(word)
            current_len += sep_len + w_len

    if current_words:
        lines.append(" ".join(current_words))

    return "\n".join(lines)


def wrap_card_description(text: str, max_width: int = 26) -> str:
    """Wrap card description lines at word boundaries so CJK renderer never splits words mid-syllable."""
    if not text or ";" in text:
        # Never wrap semicolon-delimited multi-part strings
        return text
    text = normalize_brackets(ensure_placeholder_spacing(text))
    paragraphs = text.split("\n")
    wrapped_paragraphs = [_wrap_single_paragraph(p, max_width=max_width) for p in paragraphs]
    return "\n".join(wrapped_paragraphs)
```

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/test_card_rewriter_and_wrapper.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/acepatchindo/card_wrapper.py tests/test_card_rewriter_and_wrapper.py
git commit -m "feat(wrapper): add CJK-safe card line wrapper and placeholder spacing normalizer"
```

---

### Task 2: Fix Tag Aligner Whole-Clause Swallowing & Control Character Misplacement

**Files:**
- Modify: `src/acepatchindo/tag_aligner.py:1180-1575`
- Test: `tests/test_validator_and_aligner.py`

**Interfaces:**
- Modifies:
  - `reinject_skeleton_from_source(source_zh: str, target_id: str) -> str`
  - `_wrap_exact_tag_sequence(text: str, tag_seq: str, inner_zh: str) -> str`

- [x] **Step 1: Write the failing tests in `tests/test_validator_and_aligner.py`**

```python
from acepatchindo.tag_aligner import reinject_skeleton_from_source
from acepatchindo.validator import validate_translation


def test_da_qiao_deploy_tag_does_not_swallow_entire_sentence():
    source_zh = (
        "每触发2次友方<a href=1><color=#ffffff>╨<b>登场</b></color></a>效果，"
        "大乔法力上限永久减少5点，且自身等级+1。"
    )
    raw_id = (
        "Setiap 2 kali efek Deploy sekutu terpicu, batas Mana Da Qiao "
        "berkurang 5 secara permanen dan mendapat +1 Level."
    )
    aligned = reinject_skeleton_from_source(source_zh, raw_id)
    ok, reason = validate_translation(source_zh, aligned)
    assert ok, reason
    assert "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>" in aligned
    assert not aligned.endswith("</a>.")


def test_gan_and_mo_bold_tag_wraps_only_equipment_name():
    source_zh = (
        "干将莫邪使用普通装备时，随机获得普通装备"
        "<color=#ffffff><b>干剑·莫邪</b></color>。"
    )
    raw_id = (
        "Saat Gan & Mo memakai Normal Equipment, memperoleh acak "
        "Normal Equipment Twin Blade · Male."
    )
    aligned = reinject_skeleton_from_source(source_zh, raw_id)
    ok, reason = validate_translation(source_zh, aligned)
    assert ok, reason
    assert "<color=#ffffff><b>Twin Blade · Male</b></color>" in aligned
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_validator_and_aligner.py -k "test_da_qiao or test_gan_and_mo" -v`
Expected: FAIL because `_wrap_exact_tag_sequence` wraps the entire clause when `Twin Blade · Male` or `Deploy` is not matched properly.

- [x] **Step 3: Update `src/acepatchindo/tag_aligner.py` to anchor mechanic/entity spans and prevent whole-sentence wrapping**

Update `ATOMIC_KEYWORD_ALIASES` and `_wrap_exact_tag_sequence` in `src/acepatchindo/tag_aligner.py`:
1. Add explicit alias mappings for `干剑·莫邪` (`["Twin Blade · Male", "Twin Blade · Female", "Twin Blades"]`), `登场` (`["Deploy", "Deployment"]`), `开团` (`["Initiate", "Engage"]`), `整备` (`["Prepare", "Preparation"]`), `复生` (`["Revive", "Resurrect"]`), `完美复生` (`["Perfect Revive", "Perfect Resurrection"]`), `图腾` (`["Totem"]`), `阿科米亚核心` (`["Arcomia Core", "Akomia Core"]`).
2. In `_wrap_exact_tag_sequence(text, open_tags, close_tags, ctrl_prefix, candidates)`:
   - First search for any candidate in `candidates` (longest first, case-insensitive) that is not already inside `open_tags`.
   - If the tag has a mechanic control token (`╨`, `╪`, `╬`, `╧`, `═`, `╊`, `╫`, `╪`) and no candidate appears in `text`, wrap only the matching mechanic keyword (`Deploy`, `Initiate`, `Prepare`, `Revive`, `Temporary Level`, `Steal`, `Sacrifice`, `Flash`) or insert `<open_tags><ctrl_prefix><canonical_keyword><close_tags> ` at the start of the clause—**never** wrap the entire sentence `text`!
   - If the tag is `<color=#ffffff><b>...</b></color>` or `<b>...</b>` for a proper noun/equipment name and no alias matched, wrap the capitalized English proper noun phrase at the end of the clause (e.g. `r"([A-Z][A-Za-z0-9'·•\- ]+[A-Za-z0-9])(?=[\.,;!\?]?$)"`) instead of wrapping the Indonesian verbs (`memperoleh Normal Equipment ...`).

- [x] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_validator_and_aligner.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/acepatchindo/tag_aligner.py tests/test_validator_and_aligner.py
git commit -m "fix(tag-aligner): prevent whole-sentence tag swallowing and anchor mechanic/entity tags"
```

---

### Task 3: Tactical Indonesian Rewriter & Unified Glossary Engine (`src/acepatchindo/card_rewriter.py`)

**Files:**
- Create: `src/acepatchindo/card_rewriter.py`
- Modify: `tests/test_card_rewriter_and_wrapper.py`

**Interfaces:**
- Produces:
  - `CANONICAL_MECHANIC_MAP: dict[str, str]`
  - `CANONICAL_HERO_NAME_MAP: dict[str, str]`
  - `CANONICAL_RELATED_CARD_MAP: dict[str, str]`
  - `polish_indonesian_card_text(source_zh: str, text_id: str, baseline_en: str = "") -> str`
  - `rewrite_en_card_to_id(source_zh: str, baseline_en: str) -> str`

- [x] **Step 1: Write failing tests in `tests/test_card_rewriter_and_wrapper.py` covering all screenshot defects**

```python
from acepatchindo.card_rewriter import (
    polish_indonesian_card_text,
    rewrite_en_card_to_id,
)


def test_fixes_tier1_level_n_hero_ambiguity():
    # Allain
    zh_allain = "<a href=1><color=#ffffff>╨<b>登场</b></color></a>：己方穿戴装备最多的1名英雄等级+2。"
    raw_allain = "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>: Level 1 Hero milikmu yang memakai Equipment terbanyak +2."
    fixed = polish_indonesian_card_text(zh_allain, raw_allain)
    assert "Level 1 Hero" not in fixed
    assert "1 Hero sekutu dengan Equipment terbanyak mendapat +2 Level" in fixed

    # Dolia
    zh_dolia = "<a href=1><color=#ffffff>╨<b>登场</b></color></a>：随机3名英雄及<a href=11><color=#ffffff>🌀<b>阿科米亚核心</b></color></a>等级+1。"
    raw_dolia = "<a href=1><color=#ffffff>╨<b>Deploy</b></color></a>: Level 3 Hero acak dan <a href=11><color=#ffffff>🌀<b>Akomia Core</b></color></a> +1."
    fixed_dolia = polish_indonesian_card_text(zh_dolia, raw_dolia)
    assert "Level 3 Hero" not in fixed_dolia
    assert "3 Hero acak" in fixed_dolia
    assert "Arcomia Core" in fixed_dolia
    assert "+1 Level" in fixed_dolia


def test_unifies_glossary_and_entity_names():
    raw = (
        "<a href=3><color=#ffffff>╪<b>Engage</b></color></a>: Saat Ganjiang Moye, "
        "Baili Shouyue, Zhuge Liang, Yang Yuhuan, atau Jiang Ziya berada di field "
        "atau di medan tempur, efek Preparation memberikan Kartu Tactic dan Akomia Core."
    )
    fixed = polish_indonesian_card_text("", raw)
    assert "Initiate" in fixed
    assert "Gan & Mo" in fixed
    assert "Shouyue" in fixed
    assert "Kongming" in fixed
    assert "Yuhuan" in fixed
    assert "Ziya" in fixed
    assert "di arena" in fixed
    assert "Prepare" in fixed
    assert "Kartu Efek" in fixed
    assert "Arcomia Core" in fixed


def test_syncs_parent_card_references_to_related_card_titles():
    en_celestial = "Gain 3 Melodious Notes."
    id_celestial = rewrite_en_card_to_id("获得3张绕梁之音。", en_celestial)
    assert "Melody" in id_celestial
    assert "Melodious Notes" not in id_celestial

    en_glimmer = "Restore 1{LordHp}. Gain 2 Famous Blade • Life-Stealer."
    id_glimmer = rewrite_en_card_to_id("恢复1{LordHp}，获得2张名刀·司命。", en_glimmer)
    assert "Destiny" in id_glimmer
    assert "Famous Blade" not in id_glimmer
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_card_rewriter_and_wrapper.py -k "test_fixes_tier1 or test_unifies_glossary or test_syncs_parent" -v`
Expected: FAIL with `ImportError`

- [x] **Step 3: Implement `src/acepatchindo/card_rewriter.py`**

Implement `src/acepatchindo/card_rewriter.py` with:
1. **Canonical Glossary Replacements (`polish_indonesian_card_text`):**
   - `╪<b>Engage</b>` / `╪<b>Memulai</b>` / `╪Engage` / `╪Memulai` -> `╪<b>Initiate</b>` / `╪Initiate`
   - `╬<b>Preparation</b>` / `╬Preparation` / `efek Preparation` -> `╬<b>Prepare</b>` / `╬Prepare` / `efek Prepare`
   - `╧<b>Resurrect</b>` / `╧<b>Resurrection</b>` -> `╧<b>Revive</b>`
   - `╧<b>Perfect Resurrection</b>` / `╧<b>Perfect Revival</b>` -> `╧<b>Perfect Revive</b>`
   - `Akomia Core` -> `Arcomia Core`
   - `di field` / `di medan tempur` / `di battlefield` -> `di arena`
   - `Kartu Tactic` / `Tactics Card` / `Tactic Card` -> `Kartu Efek`
   - Hero name synchronization:
     - `Ganjiang Moye` -> `Gan & Mo`
     - `Baili Shouyue` -> `Shouyue`
     - `Zhuge Liang` -> `Kongming`
     - `Yang Yuhuan` -> `Yuhuan`
     - `Jiang Ziya` -> `Ziya`
   - Faction name synchronization:
     - `[Central Plain]` -> `[Central Plains]`
     - `[Sunset Ocean]` / `[Sunset]` -> `[Sunset Sea]`
     - `[Zhulu]` -> `[Zhulu Plateau]`
   - Related card title synchronization:
     - `Melodious Notes` -> `Melody`
     - `Opening Overdrive` -> `Early Game Surge`
     - `Famous Blade • Life-Stealer` / `Famous Blade · Life-Stealer` -> `Destiny`
     - `Tier 5 Hero Exchange Vouchers` / `Tier 5 Hero Exchange Voucher` -> `Tier 5 Hero Voucher`
     - `"Glitch Bots"` / `Glitch Bots` -> `Glitch Robot`
2. **Regex Rewriters for Ambiguous Tier 1 `"Level <N> Hero ... +<M>"` Patterns:**
   - Pattern `r"\bLevel\s+(\d+|{[^}]+})\s+(Hero\b[^.+;\n]*?)\s*\+\s*(\d+|{[^}]+})(?!\s*Level)"` -> `r"\1 \2 mendapat +\3 Level"`
   - Pattern `r"\bLevel\s+(\d+|{[^}]+})\s+((?:<[^>]+>|[\u2540-\u257f]|\S)+\s+Hero\b[^.+;\n]*?)\s*\+\s*(\d+|{[^}]+})(?!\s*Level)"` -> `r"\1 \2 mendapat +\3 Level"`
   - Specific Tier 1 syntax fixes:
     - `Saat memberikan efek CC milikmu` -> `Saat sekutu memberikan efek CC`
     - `Level tertinggi (\d+) Hero (\[[^\]]+\]) memperoleh` -> `\1 Hero \2 berlevel tertinggi memperoleh`
     - `Saat setiap Round pertama kali menggunakan` -> `Pertama kali menggunakan` (with `setiap Round` at clause end)
     - `sebesar setengah Level 1 Hero lain` -> `sebesar setengah Level dari 1 Hero sekutu lain`
3. **Structured Clause Pattern Rewriter (`rewrite_en_card_to_id`) for Non-Tier-1 Cards (Effect Cards, Equipment, Remaining Contestant Cards, Tooltips, Related Notes):**
   - Pre-normalize English source with canonical entity names (`Melody`, `Early Game Surge`, `Destiny`, `Glitch Robot`, `Tier 5 Hero Voucher`, `Initiate`, `Deploy`, `Prepare`, `Revive`, `Arcomia Core`, `Gan & Mo`, `Shouyue`, `Kongming`, `Yuhuan`, `Ziya`).
   - Apply high-precision sentence/clause templates before falling back to phrase translation:
     - Fix polysemous mistranslations in `lexicon_id.py`:
       - `Record all non-Awakened` -> `Mencatat semua ... non-Awakened` (never `Rekor`)
       - `from now on` -> `mulai sekarang` (never `dari Sekarang pada`)
       - `these Cards` / `this Card` -> `Kartu ini` (never `ini Kartu`)
       - `next Round` / `of the next Round` -> `Round berikutnya` (never `berikutnya Round`)
       - `connected Hero` / `linked Hero` -> `Hero yang terhubung` (never `terhubung Hero`)
       - `nearest enemy` -> `musuh terdekat` (never `terdekat musuh`)
       - `original location` -> `lokasi awal` (never `asli lokasi`)
       - `your Heroes gain (\d+)` -> `Hero sekutu mendapat +\1` (never `Hero mendapatkan \1 milikmu`)
       - `Heroes that survive Combat retain` -> `Hero yang bertahan hidup hingga akhir Combat mempertahankan`
       - `little dodder` -> `Xiao Tu` (never `kecil dodder`)
       - `Draw` (in Win/Loss/Draw context) -> `Seri` (never `Menarik`)

- [x] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_card_rewriter_and_wrapper.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/acepatchindo/card_rewriter.py tests/test_card_rewriter_and_wrapper.py
git commit -m "feat(rewriter): add tactical Indonesian card rewriter and canonical glossary unifier"
```

---

### Task 4: Fix Tier 1 Contestant (`lords`) Related Card Matching & Integrate Rewriter into `glossary.py`

**Files:**
- Modify: `src/acepatchindo/glossary.py:880-950` and `src/acepatchindo/glossary.py:1140-1295`
- Test: `tests/test_glossary_and_tiers.py`

**Interfaces:**
- Modifies:
  - `GlossaryEngine._load_tier1_data()`
  - `GlossaryEngine.translate_entry(source_zh: str, baseline_en: str | None = None) -> tuple[str, str]`
  - `GlossaryEngine.translate_en_to_id(en_text: str, source_zh: str = "") -> str`

- [x] **Step 1: Write failing test in `tests/test_glossary_and_tiers.py` for Tier 1 Contestant related cards**

```python
from acepatchindo.glossary import get_glossary_engine


def test_tier1_contestant_related_cards_match_chinese_source():
    glossary = get_glossary_engine()
    # "一叶双生" (One Leaf, Twin Life / One Leaf, Two Lives) exists in tier1_wiki_id.json
    zh_one_leaf = (
        "位移时，在原地生成1个继承30%最大生命值的分身，分身阵亡时晕眩最近的敌人。"
        "分身无法普攻，生成时嘲讽最近的敌人2秒。"
    )
    translated, tier = glossary.translate_entry(
        zh_one_leaf,
        baseline_en="When shifting, creates a clone at the original location with 30% Max HP. Upon death, it stuns the nearest enemy. The clone cannot Attack and taunts the nearest enemy for 2 seconds upon creation.",
    )
    assert tier == "tier1"
    assert "asli lokasi" not in translated
    assert "terdekat musuh" not in translated
    assert "klon" in translated.lower() or "bayangan" in translated.lower()
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_glossary_and_tiers.py -k "test_tier1_contestant_related_cards" -v`
Expected: FAIL because `tier` is `"tier3_en_id"` and `translated` contains `"asli lokasi"`.

- [x] **Step 3: Fix `_load_tier1_data` in `src/acepatchindo/glossary.py` and wire `card_rewriter` + `card_wrapper`**

In `src/acepatchindo/glossary.py`:
1. In `_load_tier1_data`, build an English-to-Chinese ability name lookup from `tier2_wiki_details_en.json` (`lords` -> `abilities` / `related`) and `catalog.unique` so when `rel.get("name")` in `tier1_wiki_id.json` is in English (`"One Leaf, Twin Life"`, `"Magic Deer · Devotion"`, `"Short-Term Plan"`, etc.), it maps accurately to the Chinese `ab_desc` in `zh_abs` (and also matches by positional index when `len(l["related"]) == len(zh_rel)`).
2. In `translate_entry` and `translate_en_to_id`, pass the translated string through `polish_indonesian_card_text`, `reinject_skeleton_from_source`, `ensure_placeholder_spacing`, `normalize_brackets`, and (when the string is a gameplay card description) `wrap_card_description`.

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/test_glossary_and_tiers.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/acepatchindo/glossary.py tests/test_glossary_and_tiers.py
git commit -m "fix(glossary): bridge Tier 1 contestant related cards and integrate tactical rewriter"
```

---

### Task 5: Expand VFS Target Scope (`Effect Cards`, `Equipment`, `Contestant Skills`, `Tooltips`, `Related Notes`) & Normalize `#60D2` Footers

**Files:**
- Modify: `scripts/01b_build_hybrid_vfs_index.py:270-530`
- Modify: `src/acepatchindo/hybrid_classifier.py:70-213`
- Modify: `src/acepatchindo/windows_108_split.py`
- Test: `tests/test_glossary_and_tiers.py`

**Interfaces:**
- Modifies:
  - `data/references/hybrid_vfs_index.json`
  - `HybridClassifier.classify_unique(source_zh: str, baseline_en: str = "") -> str`
  - `HybridClassifier.classify_update(asset: str, key: str, prev_en: str, target_en: str, opt_zh: str = "") -> str`

- [x] **Step 1: Write failing tests in `tests/test_glossary_and_tiers.py` for Effect Cards, Equipment, `#60D2` Contestant categories, and Keyword Tooltips**

```python
from acepatchindo.hybrid_classifier import get_hybrid_classifier


def test_classifier_includes_effect_cards_equipment_and_all_contestant_skills():
    clf = get_hybrid_classifier()
    # Effect Card description (e.g., Sharpening Weapons Before Battle)
    assert clf.is_target_unique(
        "获得1件普通装备，本回合己方英雄获得25%物理攻击加成。",
        "Gain 1 Normal Equipment. Allied heroes gain +25% Physical Attack this Round.",
    )
    # Contestant card with #60D2 = "棋手" (Prestigious Lineage)
    assert clf.is_target_unique(
        "每回合首次刷新商店免费，且额外获得{0|3}{Energy}。",
        "The first Shop Refresh each Round is free and grants {0|3}{Energy}.",
    )
    # Previously vetoed Talent (Copier)
    assert clf.is_target_unique(
        "每使用3张效果牌，随机获得1张效果牌。",
        "For every 3 Effect Cards used, gain 1 random Effect Card.",
    )
    # Card Titles and #60D2 category badges must remain KEEP_EN (non-target)
    assert not clf.is_target_unique("临阵磨枪", "Sharpening Weapons Before Battle")
    assert not clf.is_target_unique("效果", "Effect")
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_glossary_and_tiers.py -k "test_classifier_includes_effect_cards" -v`
Expected: FAIL because `Sharpening Weapons Before Battle`, `Prestigious Lineage`, and `Copier` are currently vetoed (`False`).

- [x] **Step 3: Update `scripts/01b_build_hybrid_vfs_index.py`, `src/acepatchindo/hybrid_classifier.py`, and `src/acepatchindo/windows_108_split.py`**

1. In `scripts/01b_build_hybrid_vfs_index.py`:
   - Remove `veto_effect_zh` and `veto_equip_zh` description vetoes (keep **titles/names** in `veto_title_zh` so Card Titles and Equipment Names stay in official English!).
   - Expand line 488 `#60D2` category check from `("秘技", "技能", "专属")` to `("秘技", "技能", "专属", "棋手", "棋手·秘技", "任务", "天赋", "效果", "装备")`.
   - Include Keyword Tooltip descriptions (`Fleeting`, `Arcomia Core`, `Totem`, `Deploy`, `Prepare`, `Temporary Level`, `Star Source Armament`, `Initiate`, `Flash`, `Sacrifice`, `Revive`) and `Related` obtainment notes (`Obtain from...`, `Obtain by...`) in `target_zh`.
   - Re-run `python3 scripts/01b_build_hybrid_vfs_index.py` to regenerate `data/references/hybrid_vfs_index.json`.
2. In `src/acepatchindo/hybrid_classifier.py`:
   - Remove `P_EFFECT_CARD_PATTERN` from `NON_TARGET_EN_PATTERNS`.
   - Ensure `is_target_unique` and `is_target_update` translate all gameplay descriptions while keeping short Proper Noun Titles (`len <= 32` without sentence verbs/punctuation) in English.
3. In `src/acepatchindo/windows_108_split.py`:
   - Add clean English translations for untranslated Chinese Secret Skill titles (`神奇小鹿·奉献` -> `Magic Deer · Devotion`, `小菟送福` -> `Bunny's Blessing`, `如梦似幻` -> `Dreamlike Illusion`, `永恒时之回环` -> `Eternal Time Loop`) and `#60D2` footers (`效果` -> `Effect`, `装备` -> `Equipment`, `技能` -> `Skill`, `棋手` -> `Contestant`, `棋手·秘技` -> `Secret Skill`, `任务` -> `Quest`, `天赋` -> `Talent`, `大河流域` -> `River Basin`, `日落海` -> `Sunset Sea`, `三分之地` -> `Three Kingdoms`).
   - Add curated Indonesian translations for live hotfix v1.9.1/v1.9.4 strings (Marco Polo `+3`, Cai Yan, Arthur, Dr Bian, Wu Zetian, Pursue Victory `乘胜追击`, Four Companions `四人同行`, Prepare for War `厉兵秣马`, Control Sensing `控制感应`, Mechanism Secret Art `机关秘术`, Angela modules, Ying Lü, Qiao Xi, and Wu Feng `武凤`).

- [x] **Step 4: Run `scripts/01b_build_hybrid_vfs_index.py` and run tests**

Run:
```bash
PYTHONPATH=src python3 scripts/01b_build_hybrid_vfs_index.py
PYTHONPATH=src pytest tests/test_glossary_and_tiers.py -v
```
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add scripts/01b_build_hybrid_vfs_index.py src/acepatchindo/hybrid_classifier.py src/acepatchindo/windows_108_split.py data/references/hybrid_vfs_index.json tests/test_glossary_and_tiers.py
git commit -m "feat(scope): include effect cards, equipment, all contestant skills, tooltips, and v1.9.4 hotfixes"
```

---

### Task 6: Runtime Numeric-Template Fallback in `dual_state_patch.py` for Live Balance Hotfixes

**Files:**
- Modify: `src/acepatchindo/dual_state_patch.py:28-173`
- Test: `tests/test_dual_state_engine.py`

**Interfaces:**
- Modifies:
  - `Catalog.__init__(self, data: dict)`
  - `translate_table(raw: bytes, asset: int | str, catalog: Catalog, *, build_output: bool = True)`

- [x] **Step 1: Write failing test in `tests/test_dual_state_engine.py` simulating a live server balance hotfix (`+2` -> `+3`)**

```python
from acepatchindo.dual_state_patch import render_table_catalog_source


def test_numeric_template_fallback_handles_live_balance_hotfix(tmp_path):
    # Verify that when catalog.unique has Marco Polo with "+2",
    # a live server protobuf record with "+3" automatically substitutes "+3"
    # into the Indonesian translation and passes validate_translation!
    ...
```

- [x] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_dual_state_engine.py -k "test_numeric_template_fallback" -v`
Expected: FAIL (`count["unknown"] == 1`, string stays in Chinese).

- [x] **Step 3: Implement Numeric-Template Skeleton Lookup in `src/acepatchindo/dual_state_patch.py`**

In `render_table_catalog_source` (`src/acepatchindo/dual_state_patch.py`):
1. Define `_NUM_TOKEN_RE = re.compile(r"(?<![#=\w])\d+(?:\.\d+)?%?")` (ignoring numbers inside `<a href=1>`, `<color=#ffffff>`, or `{0|1}`).
2. During `Catalog.__init__`, index `self._zh_num_templates: dict[str, tuple[list[str], str]]` for all entries in `self.unique` where `len(zh) >= 8`:
   - Replace standalone numbers outside tags/placeholders with `\x01N{i}\x01`.
   - If the target translation contains the exact same multiset of standalone numbers, store the template in `self._zh_num_templates`.
3. In `translate_table`, when `cand is None` on line 143 (`CJK_RE.search(source)`):
   - Compute the numeric skeleton of `source`.
   - If found in `catalog._zh_num_templates`, substitute the new numbers from `source` into the target template, run `validate_translation(source, cand)`, and if valid, use `cand`!

- [x] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/test_dual_state_engine.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/acepatchindo/dual_state_patch.py tests/test_dual_state_engine.py
git commit -m "feat(dual-state): add runtime numeric-template fallback for live server balance hotfixes"
```

---

### Task 7: Rebuild Indonesian Catalog, Patch Worker Modules, Repack Executable & Verify Full Test Suite

**Files:**
- Modify: `scripts/02_build_indonesian_catalog.py`
- Run: `scripts/03_patch_worker_modules.py`
- Run: `scripts/05_repack_windows_exe.py`
- Test: `tests/` (Full Suite)

- [x] **Step 1: Rebuild `catalog.json.gz` and `en_to_id.json.gz`**

Run:
```bash
PYTHONPATH=src python3 scripts/02_build_indonesian_catalog.py
```
Expected: `Validation failures: 0`, all target unique and `english_updates` entries built and validated cleanly.

- [x] **Step 2: Patch Worker Modules and Repack Windows Executable**

Run:
```bash
PYTHONPATH=src python3 scripts/03_patch_worker_modules.py
PYTHONPATH=src python3 scripts/05_repack_windows_exe.py
```
Expected: Worker modules compiled, SHA-256 digest updated, and `Honor of Kings Ace Indonesian Patcher.exe` repacked cleanly.

- [x] **Step 3: Run Full Automated Verification Suite & Spot-Check Every Screenshot Defect**

Run:
```bash
PYTHONPATH=src pytest -v
```
Expected: 100% of tests pass (`0` failures), including verification of:
- Zero `"Level <N> Hero ... +<M>"` strings remaining in `catalog.json.gz`.
- Zero glued `{Energy}` / `{LordHp}` / `{LordExp}` placeholders (`1Energy`, `45Energy`).
- Zero whole-sentence tag swallows (`Da Qiao`, `Gan & Mo`, `Money Makes Might`).
- Zero glossary splits (`Engage`/`Memulai`, `Preparation`, `Resurrect`, `Akomia Core`, `di field`/`di medan tempur`, `Ganjiang Moye`, `Baili Shouyue`, `Zhuge Liang`, `Melodious Notes`, `Opening Overdrive`).
- All card descriptions wrapped cleanly within `<= 28` visible characters per line.

- [x] **Step 4: Refresh Graft Graph & Commit**

```bash
graft build
git status
```
