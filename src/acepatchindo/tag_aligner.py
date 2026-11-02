"""Tag-stripping normalization and tag-skeleton re-injection for HoK Ace strings."""

from __future__ import annotations

import re
from collections import Counter
from typing import Callable

from acepatchindo.validator import (
    CJK_RE,
    CONTROL_TOKEN_RE,
    PLACEHOLDER_RE,
    TAG_RE,
    sanitize_target_text,
    validate_translation,
)

# Canonical bracketed & keyword mechanic map (Chinese -> Tier 1 Indonesian/English label)
BRACKET_TERM_MAP: dict[str, str] = {
    "[光环]": "[Aura]",
    "[登场]": "[Play]",
    "[激发]": "[Trigger]",
    "[连携]": "[Combo]",
    "[变身]": "[Transform]",
    "[召唤]": "[Summon]",
    "[回手]": "[Bounce]",
    "[摧毁]": "[Destroy]",
    "[吞噬]": "[Devour]",
    "[护盾]": "[Shield]",
    "[阵营]": "[Faction]",
    "[职业]": "[Class]",
    "[物理]": "[Physical]",
    "[法术]": "[Magic]",
    "[真实]": "[True]",
    "[暴击]": "[Crit]",
    "[眩晕]": "[Stun]",
    "[冰冻]": "[Freeze]",
    "[灼烧]": "[Burn]",
    "[中毒]": "[Poison]",
    "[沉默]": "[Silence]",
    "[缴械]": "[Disarm]",
    "[免疫]": "[Immune]",
    "[被动]": "[Pasif]",
    "[主动]": "[Aktif]",
    "[天赋]": "[Talent]",
    "[效果牌]": "[Kartu Efek]",
    "[装备]": "[Equipment]",
    "牺牲": "Sacrifice",
    "筹备": "Preparation",
    "登场": "On Play",
    "光环": "Aura",
    "激发": "Inspire",
    "连携": "Synergy",
    "召唤": "Summon",
    "变身": "Transform",
    "复生": "Revive",
    "刷新": "Refresh",
    "临时等级": "Temporary Level",
    "真实等级": "True Level",
}

LEADING_TAGGED_PREFIX_RE = re.compile(
    r"^(\s*(?:<(?:/?[A-Za-z][^>]*|/)>|[\u2540-\u257f]|[^：:\n<])+?(?:</[A-Za-z][^>]*>)+)\s*[：:]\s*"
)


def normalize_plain_zh(text: str) -> str:
    """Strip Unity tags, control tokens, and whitespace so text matches Tier 1 descCn."""
    cleaned = TAG_RE.sub("", text)
    cleaned = CONTROL_TOKEN_RE.sub("", cleaned)
    return re.sub(r"\s+", "", cleaned).strip()


def reinject_skeleton_from_source(
    source_zh: str,
    plain_id: str,
    inner_translator: Callable[[str], str] | None = None,
    baseline_en: str | None = None,
) -> str:
    """Re-inject exact tags, placeholders, and control tokens from source_zh into plain_id."""
    tags_in_src = TAG_RE.findall(source_zh)
    ctrls_in_src = CONTROL_TOKEN_RE.findall(source_zh)
    phs_in_src = PLACEHOLDER_RE.findall(source_zh)

    result = plain_id

    # 1. If baseline_en has valid matching tags & a leading tagged keyword prefix (e.g. <a href=10>...Sacrifice...</a>:),
    #    graft that exact prefix onto plain_id's body!
    if baseline_en and TAG_RE.findall(baseline_en) == tags_in_src and tags_in_src:
        m_en = LEADING_TAGGED_PREFIX_RE.match(baseline_en)
        m_id = re.match(r"^([^:\n]{1,40}):\s*(.+)$", result, re.S)
        if m_en and m_id and TAG_RE.findall(m_en.group(1)) == tags_in_src:
            cand = sanitize_target_text(source_zh, f"{m_en.group(1)}: {m_id.group(2)}")
            if validate_translation(source_zh, cand)[0]:
                return cand

    # 2. Replace bracketed or plain keyword terms in plain_id with exact tagged equivalents from source_zh
    m_src_lead = LEADING_TAGGED_PREFIX_RE.match(source_zh)
    m_id_lead = re.match(r"^([^:\n]{1,40}):\s*(.+)$", result, re.S)
    if m_src_lead and m_id_lead:
        src_prefix = m_src_lead.group(1)
        id_kw, id_body = m_id_lead.group(1).strip(), m_id_lead.group(2)
        # Rebuild src_prefix replacing visible Chinese keyword with id_kw while preserving tags & control tokens
        prefix_tags = TAG_RE.findall(src_prefix)
        prefix_parts = TAG_RE.split(src_prefix)
        vis_slots = [
            i
            for i, p in enumerate(prefix_parts)
            if CONTROL_TOKEN_RE.sub("", p).strip()
        ]
        if len(vis_slots) == 1:
            slot_i = vis_slots[0]
            ctrl_only = "".join(CONTROL_TOKEN_RE.findall(prefix_parts[slot_i]))
            rebuilt_prefix_parts: list[str] = []
            for idx, part in enumerate(prefix_parts):
                if idx == slot_i:
                    rebuilt_prefix_parts.append(f"{ctrl_only}{id_kw}")
                else:
                    rebuilt_prefix_parts.append(part)
                if idx < len(prefix_tags):
                    rebuilt_prefix_parts.append(prefix_tags[idx])
            result = f"{''.join(rebuilt_prefix_parts)}: {id_body}"

    for m in re.finditer(
        r"((?:<(?:/?[A-Za-z][^>]*|/)>)+)"
        r"([\u2540-\u257f]*\[[^\]]+\][\u2540-\u257f]*)"
        r"((?:</[A-Za-z][^>]*>)+)",
        source_zh,
    ):
        open_tags, zh_inner, close_tags = m.groups()
        ctrls_before = "".join(CONTROL_TOKEN_RE.findall(zh_inner))
        zh_bracket = CONTROL_TOKEN_RE.sub("", zh_inner).strip()
        id_bracket = BRACKET_TERM_MAP.get(
            zh_bracket,
            inner_translator(zh_bracket) if inner_translator else zh_bracket,
        )
        tagged_id = f"{open_tags}{ctrls_before}{id_bracket}{close_tags}"
        if id_bracket in result and tagged_id not in result:
            result = result.replace(id_bracket, tagged_id, 1)

    # 3. Restore control tokens (e.g. ╫) if source had them
    if ctrls_in_src and Counter(CONTROL_TOKEN_RE.findall(result)) != Counter(ctrls_in_src):
        src_ctrl_counts = Counter(ctrls_in_src)
        cur_ctrl_counts = Counter(CONTROL_TOKEN_RE.findall(result))
        for ch, target_cnt in src_ctrl_counts.items():
            needed = target_cnt - cur_ctrl_counts[ch]
            for sep in (", ", " / ", " dan ", " "):
                while needed > 0 and sep in result:
                    result = result.replace(sep, ch, 1)
                    needed -= 1
            if needed > 0:
                result = result + (ch * needed)

    # 4. Check if candidate already passes all 7 rules
    cand = sanitize_target_text(source_zh, result)
    if (
        TAG_RE.findall(cand) == tags_in_src
        and Counter(PLACEHOLDER_RE.findall(cand)) == Counter(phs_in_src)
        and Counter(CONTROL_TOKEN_RE.findall(cand)) == Counter(ctrls_in_src)
        and not CJK_RE.search(PLACEHOLDER_RE.sub("", TAG_RE.sub("", cand)))
    ):
        ok, _ = validate_translation(source_zh, cand)
        if ok:
            return cand

    # 5. Deterministic skeleton wrapper guaranteeing exact tag, placeholder, and control token parity
    stripped_result = CONTROL_TOKEN_RE.sub("", TAG_RE.sub("", result))
    wrapped = _wrap_exact_tag_sequence(source_zh, stripped_result, inner_translator)
    return sanitize_target_text(source_zh, wrapped)


def _wrap_exact_tag_sequence(
    source_zh: str,
    stripped_id: str,
    inner_translator: Callable[[str], str] | None = None,
) -> str:
    """Guarantee TAG_RE, PLACEHOLDER_RE, and CONTROL_TOKEN_RE match source_zh."""
    tokens = TAG_RE.split(source_zh)
    tags = TAG_RE.findall(source_zh)

    visible_lengths = [len(CONTROL_TOKEN_RE.sub("", t).strip()) for t in tokens]
    main_idx = visible_lengths.index(max(visible_lengths)) if visible_lengths else 0

    # Remove placeholders from stripped_id if they appear in other slots, then re-verify
    out_parts: list[str] = []
    for idx, tok in enumerate(tokens):
        tok_ctrls = "".join(CONTROL_TOKEN_RE.findall(tok))
        clean_tok = CONTROL_TOKEN_RE.sub("", tok).strip()
        if idx == main_idx:
            out_parts.append(f"{tok_ctrls}{stripped_id}")
        elif clean_tok:
            mapped = BRACKET_TERM_MAP.get(clean_tok)
            if mapped:
                out_parts.append(f"{tok_ctrls}{mapped}")
            elif not CJK_RE.search(clean_tok):
                out_parts.append(tok)
            elif inner_translator:
                tr = CONTROL_TOKEN_RE.sub("", TAG_RE.sub("", inner_translator(clean_tok)))
                tr = CJK_RE.sub("", tr).strip()
                out_parts.append(f"{tok_ctrls}{tr}")
            else:
                phs = "".join(PLACEHOLDER_RE.findall(clean_tok))
                out_parts.append(f"{tok_ctrls}{phs}")
        else:
            out_parts.append(tok_ctrls)

        if idx < len(tags):
            out_parts.append(tags[idx])

    rebuilt = "".join(out_parts)

    # Reconcile placeholders exactly
    src_ph = Counter(PLACEHOLDER_RE.findall(source_zh))
    cur_ph = Counter(PLACEHOLDER_RE.findall(rebuilt))
    if cur_ph != src_ph:
        # Remove excess placeholders if duplicated
        for ph, cnt in list(cur_ph.items()):
            while cnt > src_ph[ph]:
                rebuilt = rebuilt.replace(ph, "", 1)
                cnt -= 1
        # Append any missing placeholders
        cur_ph = Counter(PLACEHOLDER_RE.findall(rebuilt))
        for ph, cnt in src_ph.items():
            if cur_ph[ph] < cnt:
                rebuilt += ph * (cnt - cur_ph[ph])

    # Reconcile control tokens exactly
    src_ctrl = Counter(CONTROL_TOKEN_RE.findall(source_zh))
    cur_ctrl = Counter(CONTROL_TOKEN_RE.findall(rebuilt))
    if cur_ctrl != src_ctrl:
        for ch, cnt in list(cur_ctrl.items()):
            while cnt > src_ctrl[ch]:
                rebuilt = rebuilt.replace(ch, "", 1)
                cnt -= 1
        cur_ctrl = Counter(CONTROL_TOKEN_RE.findall(rebuilt))
        for ch, cnt in src_ctrl.items():
            if cur_ctrl[ch] < cnt:
                rebuilt += ch * (cnt - cur_ctrl[ch])

    return rebuilt


def translate_preserving_skeleton(
    source: str,
    segment_translator: Callable[[str], str],
) -> str:
    """Translate text segments while keeping every tag, placeholder, control token, and ';' intact."""
    if ";" in source:
        parts = source.split(";")
        translated_parts = [
            _translate_single_skeleton(p, segment_translator) for p in parts
        ]
        candidate = ";".join(translated_parts)
        return sanitize_target_text(source, candidate)
    return sanitize_target_text(
        source, _translate_single_skeleton(source, segment_translator)
    )


def _translate_single_skeleton(
    source: str,
    segment_translator: Callable[[str], str],
) -> str:
    tags = TAG_RE.findall(source)
    segments = TAG_RE.split(source)
    out: list[str] = []
    for idx, seg in enumerate(segments):
        if seg:
            ctrls = CONTROL_TOKEN_RE.findall(seg)
            if ctrls:
                sub_segs = CONTROL_TOKEN_RE.split(seg)
                rejoined: list[str] = []
                for c_idx, s in enumerate(sub_segs):
                    rejoined.append(_translate_preserving_placeholders(s, segment_translator))
                    if c_idx < len(ctrls):
                        rejoined.append(ctrls[c_idx])
                out.append("".join(rejoined))
            else:
                out.append(_translate_preserving_placeholders(seg, segment_translator))
        if idx < len(tags):
            out.append(tags[idx])
    return "".join(out)


def _translate_preserving_placeholders(
    seg: str,
    segment_translator: Callable[[str], str],
) -> str:
    if not seg or not seg.strip():
        return seg
    stripped = seg.strip()
    if stripped in BRACKET_TERM_MAP:
        return seg.replace(stripped, BRACKET_TERM_MAP[stripped], 1)

    # Protect placeholders with temporary ASCII sentinels that regex translators won't touch
    phs = PLACEHOLDER_RE.findall(seg)
    if not phs:
        return segment_translator(seg)

    protected = seg
    sentinels: list[tuple[str, str]] = []
    for i, ph in enumerate(phs):
        tok = f"__WXQPH{i}__"
        protected = protected.replace(ph, tok, 1)
        sentinels.append((tok, ph))

    translated = segment_translator(protected)
    for tok, ph in sentinels:
        translated = translated.replace(tok, ph, 1)
    return translated

