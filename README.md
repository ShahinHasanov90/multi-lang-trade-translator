# Multi-Language Trade Translator

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Overview

Translation API optimized for customs and trade terminology. Handles technical trade vocabulary, HS code descriptions, legal customs terms, and regulatory text across **EN/RU/AZ/TR**.

The engine uses a domain-adapted glossary with fallback to general translation, ensuring that specialized trade terms are translated accurately and consistently across all supported language pairs.

## Features

- **Glossary-first translation** -- domain-specific terms are matched before general translation, preserving accuracy for customs and trade vocabulary.
- **Multi-directional lookup** -- translate between any supported language pair (EN, RU, AZ, TR).
- **HS code preservation** -- Harmonized System codes, monetary amounts, dates, and proper nouns are detected and preserved during translation.
- **Language detection** -- script-based (Latin/Cyrillic) and statistical detection tuned for trade documents.
- **Batch translation** -- translate multiple texts in a single API call.
- **Custom glossary management** -- load, save, and extend glossaries at runtime via the API.

## Supported Languages

| Code | Language   |
|------|------------|
| en   | English    |
| ru   | Russian    |
| az   | Azerbaijani|
| tr   | Turkish    |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn src.translator.api:app --reload

# Or use Make
make run
```

## API Endpoints

| Method | Endpoint           | Description                        |
|--------|--------------------|------------------------------------|
| POST   | `/translate`       | Translate a single text            |
| POST   | `/translate/batch` | Translate multiple texts at once   |
| POST   | `/detect`          | Detect the language of a text      |
| GET    | `/glossary`        | List glossary terms for a pair     |
| GET    | `/health`          | Health check                       |

## Example

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "customs declaration", "source_lang": "en", "target_lang": "az"}'
```

Response:

```json
{
  "translated_text": "gomruk beyannamesi",
  "source_lang": "en",
  "target_lang": "az",
  "glossary_matches": ["customs declaration"]
}
```

## Project Structure

```
src/translator/
    __init__.py        # Package init
    engine.py          # Translation engine with glossary-first lookup
    glossary.py        # Trade-specific glossary management
    detector.py        # Language detection for trade documents
    normalizer.py      # Pre/post-translation normalization
    api.py             # FastAPI application
    schemas.py         # Pydantic request/response models
data/
    trade_glossary_en_az.json   # EN-AZ trade glossary (100+ terms)
    trade_glossary_en_ru.json   # EN-RU trade glossary (100+ terms)
tests/
    test_engine.py     # Translation engine tests
    test_glossary.py   # Glossary management tests
    test_detector.py   # Language detection tests
```

## Docker

```bash
docker build -t trade-translator .
docker run -p 8000:8000 trade-translator
```

## Testing

```bash
make test
```

## License

MIT License. See [LICENSE](LICENSE) for details.
