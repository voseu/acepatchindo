"""Exact mirror of wxq_patch.translation_rules validation plus target sanitizer."""

from __future__ import annotations

import re
from collections import Counter

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
TAG_RE = re.compile(r"<(?:/?[A-Za-z][^>]*|/)>")
PLACEHOLDER_RE = re.compile(
    r"\{[^{}]*\}|%(?:\d+\$)?[-+0 #]*(?:\d+|\*)?(?:\.\d+)?[diuoxXfFeEgGaAcspn%](?![A-Za-z])"
)
CONTROL_TOKEN_RE = re.compile(r"[\u2540-\u257f]")


def strip_non_text(value: str) -> str:
    value = PLACEHOLDER_RE.sub("", TAG_RE.sub("", value))
    return CONTROL_TOKEN_RE.sub("", value)


def validate_translation(source: str, translated: object) -> tuple[bool, str]:
    if not isinstance(translated, str) or not translated.strip():
        return (False, "empty")
    visible_translation = PLACEHOLDER_RE.sub("", TAG_RE.sub("", translated))
    if CJK_RE.search(visible_translation):
        return (False, "still_chinese")
    source_tags = TAG_RE.findall(source)
    translated_tags = TAG_RE.findall(translated)
    angle_bracket_label = source.startswith("<{") and source.endswith(">")
    if source_tags != translated_tags and not angle_bracket_label:
        return (False, "tags_changed")
    if Counter(PLACEHOLDER_RE.findall(source)) != Counter(
        PLACEHOLDER_RE.findall(translated)
    ):
        return (False, "placeholders_changed")
    if Counter(CONTROL_TOKEN_RE.findall(source)) != Counter(
        CONTROL_TOKEN_RE.findall(translated)
    ):
        return (False, "control_tokens_changed")
    if ";" in source and source.count(";") != translated.count(";"):
        return (False, "semicolons_changed")
    if len(source) >= 4 and len(translated) > max(len(source) * 8, 48):
        return (False, "extreme_expansion")
    return (True, "ok")


def sanitize_target_text(source: str, translated: str) -> str:
    """Ensure target text never introduces unauthorized ';' or violates semicolon count."""
    if ";" not in source and ";" in translated:
        # Protect HTML entities if any, otherwise replace ';' with ','
        translated = translated.replace(";", ",")
    elif ";" in source and translated.count(";") != source.count(";"):
        needed = source.count(";")
        parts = translated.split(";")
        if len(parts) - 1 > needed:
            head = ";".join(parts[: needed + 1])
            tail = ",".join(parts[needed + 1 :])
            translated = f"{head},{tail}" if tail else head
        elif len(parts) - 1 < needed:
            missing = needed - (len(parts) - 1)
            for sep in (", ", ". ", " — ", " - "):
                while missing > 0 and sep in translated:
                    translated = translated.replace(sep, "; ", 1)
                    missing -= 1
            if missing > 0:
                translated = translated + (";" * missing)
    return translated

