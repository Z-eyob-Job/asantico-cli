"""PII redaction for raw work order text.

Pure domain layer: no I/O, no network, no LLM calls. This module replaces
tenant PII (name, phone, email, unit number) with stable tokens before any
text leaves the machine, and restores those tokens for local display only.

Tokens are numbered per category in order of first appearance (NAME_1, PHONE_1,
EMAIL_1, UNIT_1, ...) and the same original value always maps to the same
token, so restoration is an exact round trip.
"""

import re

# Email addresses, for example james.obrien@example.com
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

# North American phone numbers: 206-555-0142, (206) 555-0188, 206.555.0190
_PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}")

# Unit / apartment numbers. Only the number is tokenized; the cue word stays.
_UNIT_RE = re.compile(
    r"(?P<pre>\b(?:unit|apt|apartment|suite|ste)\s+#?)(?P<num>\d+[A-Za-z]?)\b",
    re.IGNORECASE,
)

# A single name word. Each word must contain a lowercase letter, so ALL-CAPS
# redaction tokens such as PHONE_1, EMAIL_1, UNIT_1, or NAME_1 are never
# absorbed into a following name (which would otherwise produce a malformed
# doubled token like NAME_1_1 and break the round trip). Covers plain names
# (Marcus, Lee) and apostrophe or hyphen names (O'Brien, Mary-Jane).
_NAME_WORD = r"(?:[A-Z][a-z]*(?:['\-][A-Za-z]+)+|[A-Z][a-z]+)"

# Tenant names introduced by a cue word, for example "Tenant James O'Brien".
# Only the name is tokenized; the cue word stays. Restricting to cue words
# avoids redacting Asantico property names such as "Clark Roadhouse".
# The cue word is case-insensitive (scoped inline) but the name itself must
# stay case-sensitive so it does not bleed into following lowercase words.
_NAME_RE = re.compile(
    r"(?P<pre>(?i:\b(?:tenant|resident|wife|husband|mr|mrs|ms|contact|attn)\b)\.?:?\s+)"
    r"(?P<name>" + _NAME_WORD + r"(?:\s+" + _NAME_WORD + r")+)"
)


def redact(text: str) -> tuple[str, dict[str, str]]:
    """Replace tenant PII in text with stable tokens.

    Detects and tokenizes email addresses, phone numbers, unit numbers, and
    cue-introduced tenant names. The same original value always maps to the
    same token within a single call.

    Args:
        text: The raw work order text, possibly containing PII.

    Returns:
        A tuple of (redacted_text, mapping) where mapping is token -> original
        and can be passed to restore for an exact round trip.
    """
    mapping: dict[str, str] = {}
    counters: dict[str, int] = {"NAME": 0, "PHONE": 0, "EMAIL": 0, "UNIT": 0}
    assigned: dict[tuple[str, str], str] = {}

    def token_for(category: str, original: str) -> str:
        key = (category, original)
        if key in assigned:
            return assigned[key]
        counters[category] += 1
        token = f"{category}_{counters[category]}"
        assigned[key] = token
        mapping[token] = original
        return token

    def whole_sub(category: str):
        def _sub(match: re.Match[str]) -> str:
            return token_for(category, match.group(0))

        return _sub

    def group_sub(category: str, group: str):
        def _sub(match: re.Match[str]) -> str:
            original = match.group(group)
            token = token_for(category, original)
            prefix = match.group(0)[: match.start(group) - match.start(0)]
            return prefix + token

        return _sub

    # Email and phone first so their digits are not mistaken for unit numbers.
    text = _EMAIL_RE.sub(whole_sub("EMAIL"), text)
    text = _PHONE_RE.sub(whole_sub("PHONE"), text)
    text = _UNIT_RE.sub(group_sub("UNIT", "num"), text)
    text = _NAME_RE.sub(group_sub("NAME", "name"), text)
    return text, mapping


def restore(text: str, mapping: dict[str, str]) -> str:
    """Reverse redaction tokens back to their original values.

    For local display only. Longer tokens are restored first so that a token
    like NAME_1 is never matched inside NAME_10.

    Args:
        text: Redacted text containing tokens.
        mapping: Token -> original mapping produced by redact.

    Returns:
        The text with every known token replaced by its original value.
    """
    for token in sorted(mapping, key=len, reverse=True):
        text = text.replace(token, mapping[token])
    return text
