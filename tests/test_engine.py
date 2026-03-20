"""Tests for the translation engine."""

import os
import sys
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.translator.engine import TranslationEngine
from src.translator.glossary import TradeGlossary


@pytest.fixture
def engine():
    """Engine loaded with the default glossaries."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    return TranslationEngine(data_dir=data_dir)


@pytest.fixture
def glossary():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    return TradeGlossary(data_dir=data_dir)


# ------------------------------------------------------------------
# Basic translation
# ------------------------------------------------------------------

class TestTranslateBasic:
    def test_same_language_returns_original(self, engine):
        result, matches = engine.translate("customs declaration", "en", "en")
        assert result == "customs declaration"
        assert matches == []

    def test_empty_text_returns_empty(self, engine):
        result, matches = engine.translate("", "en", "az")
        assert result == ""
        assert matches == []

    def test_whitespace_only_returns_empty(self, engine):
        result, matches = engine.translate("   ", "en", "az")
        assert result == ""
        assert matches == []


# ------------------------------------------------------------------
# Glossary-first lookup
# ------------------------------------------------------------------

class TestGlossaryTranslation:
    def test_single_glossary_term_en_az(self, engine):
        result, matches = engine.translate("customs declaration", "en", "az")
        assert "gömrük bəyannaməsi" in result.lower()
        assert "customs declaration" in matches

    def test_single_glossary_term_en_ru(self, engine):
        result, matches = engine.translate("bill of lading", "en", "ru")
        assert "коносамент" in result.lower()
        assert "bill of lading" in matches

    def test_glossary_match_case_insensitive(self, engine):
        result, matches = engine.translate("CUSTOMS DECLARATION", "en", "az")
        assert "gömrük bəyannaməsi" in result.lower()

    def test_multiple_glossary_terms_in_text(self, engine):
        text = "The customs declaration and bill of lading are required."
        result, matches = engine.translate(text, "en", "az")
        assert len(matches) >= 2


# ------------------------------------------------------------------
# Domain term detection
# ------------------------------------------------------------------

class TestDomainDetection:
    def test_detect_domain_terms_en_az(self, engine):
        text = "Submit the customs declaration at the bonded warehouse."
        terms = engine.detect_domain_terms(text, "en", "az")
        source_terms = [t[0] for t in terms]
        assert "customs declaration" in source_terms
        assert "bonded warehouse" in source_terms

    def test_detect_no_domain_terms(self, engine):
        text = "The weather is nice today."
        terms = engine.detect_domain_terms(text, "en", "az")
        assert len(terms) == 0


# ------------------------------------------------------------------
# Glossary lookup
# ------------------------------------------------------------------

class TestGlossaryLookup:
    def test_direct_lookup(self, engine):
        result = engine.glossary_lookup("customs broker", "en", "ru")
        assert result == "таможенный брокер"

    def test_lookup_missing_term(self, engine):
        result = engine.glossary_lookup("nonexistent term xyz", "en", "az")
        assert result is None
