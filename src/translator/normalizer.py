"""Pre- and post-translation normalization.

Preserves HS codes, monetary amounts, dates, and proper nouns during
translation by replacing them with placeholders before translation and
restoring them afterward.
"""

import re
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# HS codes: 4-, 6-, 8-, or 10-digit codes, optionally dot-separated
_HS_CODE_RE = re.compile(
    r"\b(\d{4}(?:\.\d{2}){0,3})\b"
)

# Monetary amounts: $1,234.56 or 1 234,56 EUR etc.
_MONEY_RE = re.compile(
    r"(?:USD|EUR|AZN|TRY|RUB|GBP|\$|€|£|₼|₺|₽)\s*[\d,.]+|"
    r"[\d,.]+\s*(?:USD|EUR|AZN|TRY|RUB|GBP|manat|rubl[eё])"
    , re.IGNORECASE
)

# Dates: 2024-01-15, 15/01/2024, 15.01.2024, Jan 15 2024
_DATE_RE = re.compile(
    r"\b\d{4}[-/.]\d{2}[-/.]\d{2}\b|"
    r"\b\d{2}[-/.]\d{2}[-/.]\d{4}\b|"
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
    re.IGNORECASE,
)

# Document reference numbers: e.g. INV-2024-00123, DCL/2023/456
_DOC_REF_RE = re.compile(
    r"\b[A-Z]{2,5}[-/]\d{4}[-/]\d{3,6}\b"
)

# Proper nouns heuristic: sequences of capitalized words (2+ words)
_PROPER_NOUN_RE = re.compile(
    r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
)

# All patterns in priority order (first match wins for overlapping spans)
_PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("HS", _HS_CODE_RE),
    ("MONEY", _MONEY_RE),
    ("DATE", _DATE_RE),
    ("DOCREF", _DOC_REF_RE),
    ("PROPN", _PROPER_NOUN_RE),
]

_PLACEHOLDER_FMT = "@@{tag}{idx}@@"
_PLACEHOLDER_RE = re.compile(r"@@([A-Z]+)(\d+)@@")


class TextNormalizer:
    """Handles placeholder insertion and restoration around translation."""

    def __init__(self):
        self._store: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def pre_translate(self, text: str) -> str:
        """Replace preservable tokens with placeholders.

        Returns the modified text; internally stores the mapping.
        """
        self._store.clear()
        spans: List[Tuple[int, int, str, str]] = []  # (start, end, tag, value)

        for tag, pattern in _PATTERNS:
            for m in pattern.finditer(text):
                # Skip if this span overlaps an existing one
                new_start, new_end = m.start(), m.end()
                if any(s <= new_start < e or s < new_end <= e for s, e, _, _ in spans):
                    continue
                spans.append((new_start, new_end, tag, m.group()))

        # Sort by position (reverse) so replacements don't shift indices
        spans.sort(key=lambda s: s[0], reverse=True)

        result = text
        for idx, (start, end, tag, value) in enumerate(spans):
            placeholder = _PLACEHOLDER_FMT.format(tag=tag, idx=idx)
            self._store[placeholder] = value
            result = result[:start] + placeholder + result[end:]

        return result

    def post_translate(self, text: str) -> str:
        """Restore placeholders with original values."""
        result = text
        for placeholder, original in self._store.items():
            result = result.replace(placeholder, original)
        # Clean up any unreplaced placeholders (safety net)
        result = _PLACEHOLDER_RE.sub("", result)
        return result

    @property
    def preserved_tokens(self) -> Dict[str, str]:
        """Return the current placeholder-to-value mapping."""
        return dict(self._store)


def extract_hs_codes(text: str) -> List[str]:
    """Utility: extract all HS-code-like patterns from text."""
    return _HS_CODE_RE.findall(text)


def extract_monetary_amounts(text: str) -> List[str]:
    """Utility: extract all monetary amounts from text."""
    return _MONEY_RE.findall(text)


def extract_dates(text: str) -> List[str]:
    """Utility: extract all date patterns from text."""
    return _DATE_RE.findall(text)
