"""CJK-safe card line-wrapper and runtime placeholder spacing normalizer."""

from __future__ import annotations

import re

TAG_TOKEN_RE = re.compile(r"(<(?:/?[A-Za-z][^>]*|/)>)")
RUNTIME_ICON_PLACEHOLDERS = ("{Energy}", "{LordHp}", "{LordExp}", "{Gold}", "{Coin}")

# Matches a number/letter/brace glued directly to a runtime icon placeholder
GLUED_BEFORE_ICON_BRACE_RE = re.compile(
    r"([0-9A-Za-z\u00C0-\u024F\}])(\{(?:Energy|LordHp|LordExp|Gold|Coin)\})"
)
GLUED_AFTER_ICON_BRACE_RE = re.compile(
    r"(\{(?:Energy|LordHp|LordExp|Gold|Coin)\})([0-9A-Za-z\u00C0-\u024F])"
)

# Numeric/variable placeholders like {0}, {0|12}
GLUED_AFTER_NUM_BRACE_RE = re.compile(r"(\{[0-9]+(?:\|[^\}]+)?\})([A-Za-z\u00C0-\u024F])")
GLUED_WORD_TO_NUM_BRACE_RE = re.compile(r"([A-Za-z\u00C0-\u024F]{2,})(\{[0-9]+(?:\|[^\}]+)?\})")
GLUED_NUM_TO_NUM_BRACE_RE = re.compile(r"(\d+)(\{[0-9]+(?:\|[^\}]+)?\})")

# Glued digits and words outside tags/attributes
GLUED_DIGIT_TO_WORD_RE = re.compile(
    r"(?<![#=\w])(\d+)(Energy|Chess player|Renovation|Refresh|Hero|Level|Shield|Damage|kartu|Kartu)\b"
)
GLUED_PLUS_MINUS_DIGIT_TO_WORD_RE = re.compile(
    r"([+-]\d+)([A-Za-z\u00C0-\u024F])"
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

    # Protect tags first to avoid messing up attributes like <color=#ffffff>
    protected_tags: list[str] = []

    def _mask_tag(m: re.Match[str]) -> str:
        idx = len(protected_tags)
        protected_tags.append(m.group(0))
        return f"\x00TAG{idx}\x00"

    masked = TAG_TOKEN_RE.sub(_mask_tag, text)

    # Specific common glued typo in game/references
    masked = re.sub(r"\bfails2Renovation\b", "fails, 2 Renovation", masked)
    masked = re.sub(r"\bgagal2Refresh\b", "gagal, +2 Refresh", masked)

    masked = GLUED_BEFORE_ICON_BRACE_RE.sub(r"\1 \2", masked)
    masked = GLUED_AFTER_ICON_BRACE_RE.sub(r"\1 \2", masked)
    masked = GLUED_AFTER_NUM_BRACE_RE.sub(r"\1 \2", masked)
    masked = GLUED_WORD_TO_NUM_BRACE_RE.sub(r"\1 \2", masked)
    masked = GLUED_NUM_TO_NUM_BRACE_RE.sub(r"\1 \2", masked)
    masked = GLUED_DIGIT_TO_WORD_RE.sub(r"\1 \2", masked)
    masked = GLUED_PLUS_MINUS_DIGIT_TO_WORD_RE.sub(r"\1 \2", masked)

    # Clean double spaces
    masked = re.sub(r" {2,}", " ", masked)

    # Restore tags
    restored = re.sub(
        r"\x00TAG(\d+)\x00",
        lambda m: protected_tags[int(m.group(1))],
        masked,
    )
    return restored


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
