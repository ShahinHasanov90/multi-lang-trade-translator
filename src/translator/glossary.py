"""Trade-specific glossary management.

Provides loading, saving, term matching, and multi-directional lookup
for domain-specific trade and customs terminology.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Default data directory (relative to project root)
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class TradeGlossary:
    """Manages bilingual trade glossaries with multi-directional lookup."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        # Structure: {("en","az"): {"customs declaration": "gomruk beyannamesi", ...}}
        self._glossaries: Dict[Tuple[str, str], Dict[str, str]] = {}
        self._load_all()

    # ------------------------------------------------------------------
    # Loading / saving
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        """Scan data_dir for glossary JSON files and load them."""
        if not self.data_dir.exists():
            return
        for fpath in sorted(self.data_dir.glob("trade_glossary_*.json")):
            self._load_file(fpath)

    def _load_file(self, fpath: Path) -> None:
        """Load a single glossary file.

        Expected filename pattern: trade_glossary_{src}_{tgt}.json
        Expected content: {"term_src": "term_tgt", ...}
        """
        stem = fpath.stem  # e.g. trade_glossary_en_az
        parts = stem.replace("trade_glossary_", "").split("_")
        if len(parts) != 2:
            return
        src, tgt = parts
        with open(fpath, "r", encoding="utf-8") as f:
            data: Dict[str, str] = json.load(f)
        # Store forward direction
        self._glossaries[(src, tgt)] = {k.lower(): v.lower() for k, v in data.items()}
        # Store reverse direction
        self._glossaries[(tgt, src)] = {v.lower(): k.lower() for k, v in data.items()}

    def load_glossary(self, file_path: str) -> int:
        """Load an additional glossary file at runtime. Returns term count."""
        fpath = Path(file_path)
        if not fpath.exists():
            raise FileNotFoundError(f"Glossary file not found: {file_path}")
        self._load_file(fpath)
        return sum(len(v) for v in self._glossaries.values()) // 2  # each pair counted twice

    def save_glossary(self, source_lang: str, target_lang: str, file_path: str) -> None:
        """Save the glossary for a language pair to a JSON file."""
        key = (source_lang.lower(), target_lang.lower())
        entries = self._glossaries.get(key, {})
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def lookup(self, term: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Exact lookup for a term in the glossary. Returns None if not found."""
        key = (source_lang.lower(), target_lang.lower())
        glossary = self._glossaries.get(key, {})
        return glossary.get(term.lower())

    def search(self, substring: str, source_lang: str, target_lang: str) -> List[Tuple[str, str]]:
        """Search for terms containing *substring*. Returns list of (src, tgt) pairs."""
        key = (source_lang.lower(), target_lang.lower())
        glossary = self._glossaries.get(key, {})
        needle = substring.lower()
        return [(s, t) for s, t in glossary.items() if needle in s or needle in t]

    def get_all(self, source_lang: str, target_lang: str) -> Dict[str, str]:
        """Return the full glossary dict for a language pair."""
        key = (source_lang.lower(), target_lang.lower())
        return dict(self._glossaries.get(key, {}))

    def add_term(self, source_term: str, target_term: str, source_lang: str, target_lang: str) -> None:
        """Add a term pair to the in-memory glossary (both directions)."""
        fwd = (source_lang.lower(), target_lang.lower())
        rev = (target_lang.lower(), source_lang.lower())
        self._glossaries.setdefault(fwd, {})[source_term.lower()] = target_term.lower()
        self._glossaries.setdefault(rev, {})[target_term.lower()] = source_term.lower()

    def remove_term(self, source_term: str, source_lang: str, target_lang: str) -> bool:
        """Remove a term pair. Returns True if found and removed."""
        fwd = (source_lang.lower(), target_lang.lower())
        rev = (target_lang.lower(), source_lang.lower())
        glossary_fwd = self._glossaries.get(fwd, {})
        target_term = glossary_fwd.pop(source_term.lower(), None)
        if target_term is None:
            return False
        self._glossaries.get(rev, {}).pop(target_term, None)
        return True

    # ------------------------------------------------------------------
    # Multi-directional helpers
    # ------------------------------------------------------------------

    def available_pairs(self) -> List[Tuple[str, str]]:
        """Return list of available language pairs."""
        return list(self._glossaries.keys())

    def term_count(self, source_lang: str, target_lang: str) -> int:
        """Number of terms for a given pair."""
        key = (source_lang.lower(), target_lang.lower())
        return len(self._glossaries.get(key, {}))

    def find_glossary_terms_in_text(self, text: str, source_lang: str, target_lang: str) -> List[Tuple[str, str]]:
        """Find all glossary terms that appear in *text*.

        Returns list of (source_term, target_term) sorted longest-first
        to support greedy replacement.
        """
        key = (source_lang.lower(), target_lang.lower())
        glossary = self._glossaries.get(key, {})
        text_lower = text.lower()
        matches = []
        for src_term, tgt_term in glossary.items():
            if src_term in text_lower:
                matches.append((src_term, tgt_term))
        # Sort longest first for greedy replacement
        matches.sort(key=lambda pair: len(pair[0]), reverse=True)
        return matches
