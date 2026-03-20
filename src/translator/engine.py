"""Translation engine.

Implements a glossary-first strategy:
1. Detect domain-specific terms in the source text via the trade glossary.
2. Replace them with placeholders to prevent general-purpose mistranslation.
3. Preserve HS codes, amounts, dates via the normalizer.
4. Translate the remaining text with a general-purpose backend (deep-translator).
5. Reassemble the result with glossary and preserved tokens restored.
"""

from typing import Dict, List, Optional, Tuple

try:
    from deep_translator import GoogleTranslator
    _HAS_DEEP_TRANSLATOR = True
except ImportError:
    _HAS_DEEP_TRANSLATOR = False

from .glossary import TradeGlossary
from .normalizer import TextNormalizer
from .detector import detect_language


# Language code mapping for deep-translator (Google)
_LANG_MAP: Dict[str, str] = {
    "en": "en",
    "ru": "ru",
    "az": "az",
    "tr": "tr",
}

_GLOSSARY_PLACEHOLDER = "GTERM{idx}"


class TranslationEngine:
    """Glossary-aware trade document translator."""

    def __init__(self, glossary: Optional[TradeGlossary] = None, data_dir: Optional[str] = None):
        self.glossary = glossary or TradeGlossary(data_dir=data_dir)
        self._normalizer = TextNormalizer()

    # ------------------------------------------------------------------
    # Core translation
    # ------------------------------------------------------------------

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Tuple[str, List[str]]:
        """Translate *text* from *source_lang* to *target_lang*.

        Returns (translated_text, list_of_glossary_matches).
        """
        if not text or not text.strip():
            return "", []

        if source_lang == target_lang:
            return text, []

        src = source_lang.lower()
        tgt = target_lang.lower()

        # Step 1: Find glossary terms in the source text
        glossary_matches = self.glossary.find_glossary_terms_in_text(text, src, tgt)
        matched_source_terms = [pair[0] for pair in glossary_matches]

        # Step 2: Replace glossary terms with placeholders
        working_text = text
        glossary_placeholders: Dict[str, str] = {}  # placeholder -> target term
        for idx, (src_term, tgt_term) in enumerate(glossary_matches):
            placeholder = _GLOSSARY_PLACEHOLDER.format(idx=idx)
            # Case-insensitive replacement
            import re
            pattern = re.compile(re.escape(src_term), re.IGNORECASE)
            working_text = pattern.sub(placeholder, working_text)
            glossary_placeholders[placeholder] = tgt_term

        # Step 3: Normalizer — protect HS codes, amounts, dates
        working_text = self._normalizer.pre_translate(working_text)

        # Step 4: General translation for remaining text
        working_text = self._general_translate(working_text, src, tgt)

        # Step 5: Restore normalizer placeholders
        working_text = self._normalizer.post_translate(working_text)

        # Step 6: Restore glossary placeholders with target terms
        for placeholder, tgt_term in glossary_placeholders.items():
            working_text = working_text.replace(placeholder, tgt_term)

        return working_text.strip(), matched_source_terms

    def translate_batch(
        self,
        items: List[Tuple[str, str, str]],
    ) -> List[Tuple[str, List[str]]]:
        """Translate a batch of (text, source_lang, target_lang) tuples."""
        return [self.translate(text, src, tgt) for text, src, tgt in items]

    # ------------------------------------------------------------------
    # Auto-detect source language
    # ------------------------------------------------------------------

    def translate_auto(self, text: str, target_lang: str) -> Tuple[str, str, List[str]]:
        """Detect source language, then translate.

        Returns (translated_text, detected_source_lang, glossary_matches).
        """
        detected_lang, _conf, _script = detect_language(text)
        translated, matches = self.translate(text, detected_lang, target_lang)
        return translated, detected_lang, matches

    # ------------------------------------------------------------------
    # General-purpose translation backend
    # ------------------------------------------------------------------

    def _general_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using the general-purpose backend (Google via deep-translator)."""
        if not text.strip():
            return text

        if not _HAS_DEEP_TRANSLATOR:
            # Fallback: return text as-is when deep-translator is not installed
            return text

        src_code = _LANG_MAP.get(source_lang, source_lang)
        tgt_code = _LANG_MAP.get(target_lang, target_lang)

        try:
            translator = GoogleTranslator(source=src_code, target=tgt_code)
            return translator.translate(text)
        except Exception:
            # On any translation failure, return original text
            return text

    # ------------------------------------------------------------------
    # Domain term detection
    # ------------------------------------------------------------------

    def detect_domain_terms(self, text: str, source_lang: str, target_lang: str) -> List[Tuple[str, str]]:
        """Identify trade/customs domain terms in *text*.

        Returns list of (source_term, target_term) found.
        """
        return self.glossary.find_glossary_terms_in_text(text, source_lang, target_lang)

    # ------------------------------------------------------------------
    # Glossary passthrough helpers
    # ------------------------------------------------------------------

    def glossary_lookup(self, term: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Direct glossary lookup."""
        return self.glossary.lookup(term, source_lang, target_lang)
