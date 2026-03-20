"""Tests for the trade glossary module."""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.translator.glossary import TradeGlossary


@pytest.fixture
def glossary():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    return TradeGlossary(data_dir=data_dir)


# ------------------------------------------------------------------
# Loading
# ------------------------------------------------------------------

class TestGlossaryLoading:
    def test_loads_en_az(self, glossary):
        assert glossary.term_count("en", "az") >= 100

    def test_loads_en_ru(self, glossary):
        assert glossary.term_count("en", "ru") >= 100

    def test_reverse_direction_created(self, glossary):
        """Loading en->az should also create az->en."""
        assert glossary.term_count("az", "en") >= 100

    def test_available_pairs(self, glossary):
        pairs = glossary.available_pairs()
        assert ("en", "az") in pairs
        assert ("az", "en") in pairs
        assert ("en", "ru") in pairs
        assert ("ru", "en") in pairs


# ------------------------------------------------------------------
# Lookup
# ------------------------------------------------------------------

class TestGlossaryLookup:
    def test_exact_lookup_en_az(self, glossary):
        result = glossary.lookup("customs declaration", "en", "az")
        assert result == "gömrük bəyannaməsi"

    def test_exact_lookup_reverse_az_en(self, glossary):
        result = glossary.lookup("gömrük bəyannaməsi", "az", "en")
        assert result == "customs declaration"

    def test_lookup_case_insensitive(self, glossary):
        result = glossary.lookup("CUSTOMS DECLARATION", "en", "az")
        assert result is not None

    def test_lookup_missing_term(self, glossary):
        result = glossary.lookup("nonexistent term xyz", "en", "az")
        assert result is None

    def test_search_substring(self, glossary):
        results = glossary.search("customs", "en", "az")
        assert len(results) > 3  # customs declaration, customs broker, customs duty, etc.

    def test_find_terms_in_text(self, glossary):
        text = "The customs declaration for the bonded warehouse shipment."
        matches = glossary.find_glossary_terms_in_text(text, "en", "az")
        source_terms = [m[0] for m in matches]
        assert "customs declaration" in source_terms
        assert "bonded warehouse" in source_terms


# ------------------------------------------------------------------
# Add / remove
# ------------------------------------------------------------------

class TestGlossaryMutation:
    def test_add_term(self, glossary):
        glossary.add_term("test term", "test söz", "en", "az")
        assert glossary.lookup("test term", "en", "az") == "test söz"
        assert glossary.lookup("test söz", "az", "en") == "test term"

    def test_remove_term(self, glossary):
        glossary.add_term("removable", "silinən", "en", "az")
        assert glossary.remove_term("removable", "en", "az") is True
        assert glossary.lookup("removable", "en", "az") is None

    def test_remove_nonexistent_returns_false(self, glossary):
        assert glossary.remove_term("doesnotexist", "en", "az") is False


# ------------------------------------------------------------------
# Save / Load round-trip
# ------------------------------------------------------------------

class TestGlossarySaveLoad:
    def test_save_and_reload(self, glossary):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name

        try:
            glossary.save_glossary("en", "az", tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert len(data) >= 100
            assert "customs declaration" in data
        finally:
            os.unlink(tmp_path)
