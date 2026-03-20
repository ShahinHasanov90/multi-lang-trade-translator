"""Pydantic models for request and response validation."""

from typing import List, Optional

from pydantic import BaseModel, Field


SUPPORTED_LANGUAGES = ("en", "ru", "az", "tr")


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

class TranslateRequest(BaseModel):
    """Single translation request."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to translate")
    source_lang: str = Field(..., description="Source language code (en, ru, az, tr)")
    target_lang: str = Field(..., description="Target language code (en, ru, az, tr)")


class TranslateResponse(BaseModel):
    """Single translation response."""

    translated_text: str
    source_lang: str
    target_lang: str
    glossary_matches: List[str] = Field(default_factory=list)


class BatchTranslateRequest(BaseModel):
    """Batch translation request."""

    items: List[TranslateRequest] = Field(..., min_length=1, max_length=50)


class BatchTranslateResponse(BaseModel):
    """Batch translation response."""

    results: List[TranslateResponse]


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

class DetectRequest(BaseModel):
    """Language detection request."""

    text: str = Field(..., min_length=1, max_length=5000)


class DetectResponse(BaseModel):
    """Language detection response."""

    language: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    script: Optional[str] = None


# ---------------------------------------------------------------------------
# Glossary
# ---------------------------------------------------------------------------

class GlossaryQuery(BaseModel):
    """Query parameters for glossary lookup."""

    source_lang: str = Field(default="en")
    target_lang: str = Field(default="az")
    term: Optional[str] = Field(default=None, description="Filter by term (substring match)")


class GlossaryEntry(BaseModel):
    """A single glossary term pair."""

    source_term: str
    target_term: str


class GlossaryResponse(BaseModel):
    """Glossary lookup response."""

    source_lang: str
    target_lang: str
    entries: List[GlossaryEntry]
    total: int


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str
    supported_languages: List[str] = list(SUPPORTED_LANGUAGES)
