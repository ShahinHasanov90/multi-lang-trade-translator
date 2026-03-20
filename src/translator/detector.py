"""Language detection for trade documents.

Combines script-based analysis (Latin vs Cyrillic, special characters)
with statistical detection via langdetect, tuned for short trade texts.
"""

import re
from typing import Optional, Tuple

try:
    from langdetect import detect_langs, LangDetectException
    _HAS_LANGDETECT = True
except ImportError:
    _HAS_LANGDETECT = False


# ---------------------------------------------------------------------------
# Character-set patterns
# ---------------------------------------------------------------------------

_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_LATIN_RE = re.compile(r"[A-Za-z]")
# Azerbaijani-specific Latin characters
_AZ_SPECIAL_RE = re.compile(r"[\u0259\u018F\u00E7\u00C7\u011F\u011E\u0131\u0130\u00F6\u00D6\u015F\u015E\u00FC\u00DC]")
# Turkish-specific (overlaps with AZ but lacks schwa)
_TR_SPECIAL_RE = re.compile(r"[\u00E7\u00C7\u011F\u011E\u0131\u0130\u00F6\u00D6\u015F\u015E\u00FC\u00DC]")
_SCHWA_RE = re.compile(r"[\u0259\u018F]")  # Unique to Azerbaijani


SUPPORTED = {"en", "ru", "az", "tr"}


def _script_analysis(text: str) -> Tuple[Optional[str], float, str]:
    """Heuristic detection based on character scripts.

    Returns (language_or_None, confidence, script_name).
    """
    cyrillic_count = len(_CYRILLIC_RE.findall(text))
    latin_count = len(_LATIN_RE.findall(text))
    az_special = len(_AZ_SPECIAL_RE.findall(text))
    schwa_count = len(_SCHWA_RE.findall(text))
    total = cyrillic_count + latin_count

    if total == 0:
        return None, 0.0, "unknown"

    # Predominantly Cyrillic -> Russian
    if cyrillic_count / total > 0.6:
        return "ru", min(0.95, cyrillic_count / total), "cyrillic"

    # Latin script -- distinguish EN, AZ, TR
    if latin_count / total > 0.6:
        if schwa_count > 0:
            return "az", 0.90, "latin"
        if az_special > 0:
            # Could be AZ or TR; lean TR unless schwa present
            return "tr", 0.70, "latin"
        return "en", 0.75, "latin"

    return None, 0.0, "mixed"


def _statistical_detection(text: str) -> Tuple[Optional[str], float]:
    """Use langdetect for statistical language identification."""
    if not _HAS_LANGDETECT:
        return None, 0.0
    try:
        results = detect_langs(text)
    except LangDetectException:
        return None, 0.0
    if not results:
        return None, 0.0
    best = results[0]
    lang = best.lang
    # Map langdetect codes to our supported set
    if lang not in SUPPORTED:
        return lang, float(best.prob)
    return lang, float(best.prob)


def detect_language(text: str) -> Tuple[str, float, Optional[str]]:
    """Detect the language of *text*.

    Returns (language_code, confidence, script).
    Falls back to 'en' with low confidence if undetermined.
    """
    text = text.strip()
    if not text:
        return "en", 0.0, None

    # 1. Script-based analysis
    script_lang, script_conf, script_name = _script_analysis(text)

    # 2. Statistical analysis
    stat_lang, stat_conf = _statistical_detection(text)

    # 3. Merge results
    # If script analysis is confident, prefer it for short texts
    if script_lang and script_conf >= 0.85:
        return script_lang, script_conf, script_name

    # If both agree, boost confidence
    if script_lang and stat_lang and script_lang == stat_lang:
        merged_conf = min(1.0, (script_conf + stat_conf) / 2 + 0.1)
        return script_lang, merged_conf, script_name

    # If statistical is confident and in supported set, use it
    if stat_lang and stat_lang in SUPPORTED and stat_conf > 0.7:
        return stat_lang, stat_conf, script_name or "unknown"

    # Fall back to script if available
    if script_lang:
        return script_lang, script_conf, script_name

    # Last resort
    if stat_lang and stat_lang in SUPPORTED:
        return stat_lang, stat_conf, script_name or "unknown"

    return "en", 0.1, "unknown"
