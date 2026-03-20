"""FastAPI application for the Multi-Language Trade Translator."""

from fastapi import FastAPI, HTTPException, Query

from . import __version__
from .engine import TranslationEngine
from .detector import detect_language
from .schemas import (
    SUPPORTED_LANGUAGES,
    TranslateRequest,
    TranslateResponse,
    BatchTranslateRequest,
    BatchTranslateResponse,
    DetectRequest,
    DetectResponse,
    GlossaryEntry,
    GlossaryResponse,
    HealthResponse,
)

app = FastAPI(
    title="Multi-Language Trade Translator",
    description="Translation API optimized for customs and trade terminology.",
    version=__version__,
)

# Shared engine instance
_engine = TranslationEngine()


def _validate_lang(lang: str, field: str) -> None:
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported {field}: '{lang}'. Supported: {SUPPORTED_LANGUAGES}",
        )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    """Translate a single text with glossary-first strategy."""
    _validate_lang(req.source_lang, "source_lang")
    _validate_lang(req.target_lang, "target_lang")

    translated, glossary_matches = _engine.translate(
        req.text, req.source_lang, req.target_lang
    )
    return TranslateResponse(
        translated_text=translated,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
        glossary_matches=glossary_matches,
    )


@app.post("/translate/batch", response_model=BatchTranslateResponse)
def translate_batch(req: BatchTranslateRequest):
    """Translate multiple texts in one call."""
    results = []
    for item in req.items:
        _validate_lang(item.source_lang, "source_lang")
        _validate_lang(item.target_lang, "target_lang")

        translated, glossary_matches = _engine.translate(
            item.text, item.source_lang, item.target_lang
        )
        results.append(
            TranslateResponse(
                translated_text=translated,
                source_lang=item.source_lang,
                target_lang=item.target_lang,
                glossary_matches=glossary_matches,
            )
        )
    return BatchTranslateResponse(results=results)


@app.post("/detect", response_model=DetectResponse)
def detect(req: DetectRequest):
    """Detect the language of a text."""
    lang, confidence, script = detect_language(req.text)
    return DetectResponse(language=lang, confidence=confidence, script=script)


@app.get("/glossary", response_model=GlossaryResponse)
def glossary(
    source_lang: str = Query(default="en", description="Source language code"),
    target_lang: str = Query(default="az", description="Target language code"),
    term: str = Query(default=None, description="Filter by substring"),
):
    """List glossary entries for a language pair."""
    _validate_lang(source_lang, "source_lang")
    _validate_lang(target_lang, "target_lang")

    if term:
        pairs = _engine.glossary.search(term, source_lang, target_lang)
        entries = [GlossaryEntry(source_term=s, target_term=t) for s, t in pairs]
    else:
        all_terms = _engine.glossary.get_all(source_lang, target_lang)
        entries = [
            GlossaryEntry(source_term=s, target_term=t) for s, t in all_terms.items()
        ]
    return GlossaryResponse(
        source_lang=source_lang,
        target_lang=target_lang,
        entries=entries,
        total=len(entries),
    )


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return HealthResponse(version=__version__)
