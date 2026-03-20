"""Tests for the language detector module."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.translator.detector import detect_language, _script_analysis


# ------------------------------------------------------------------
# Script analysis
# ------------------------------------------------------------------

class TestScriptAnalysis:
    def test_cyrillic_detected_as_russian(self):
        lang, conf, script = _script_analysis("Таможенная декларация оформлена")
        assert lang == "ru"
        assert script == "cyrillic"
        assert conf > 0.7

    def test_latin_detected(self):
        lang, conf, script = _script_analysis("customs declaration form")
        assert script == "latin"

    def test_azerbaijani_schwa(self):
        """Azerbaijani text with schwa (ə) should be detected as az."""
        lang, conf, script = _script_analysis("Gömrük bəyannaməsi təqdim edildi")
        assert lang == "az"

    def test_empty_text(self):
        lang, conf, script = _script_analysis("")
        assert lang is None
        assert conf == 0.0


# ------------------------------------------------------------------
# Full detection pipeline
# ------------------------------------------------------------------

class TestDetectLanguage:
    def test_english_text(self):
        lang, conf, script = detect_language("The customs declaration was submitted on time.")
        assert lang == "en"
        assert conf > 0.3

    def test_russian_text(self):
        lang, conf, script = detect_language("Таможенная декларация была подана вовремя.")
        assert lang == "ru"
        assert conf > 0.5

    def test_azerbaijani_text(self):
        lang, conf, script = detect_language("Gömrük bəyannaməsi vaxtında təqdim edilmişdir.")
        assert lang == "az"
        assert conf > 0.3

    def test_empty_string_returns_default(self):
        lang, conf, script = detect_language("")
        assert lang == "en"
        assert conf == 0.0

    def test_returns_tuple_of_three(self):
        result = detect_language("hello world")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_confidence_in_range(self):
        _, conf, _ = detect_language("Some text for testing")
        assert 0.0 <= conf <= 1.0
