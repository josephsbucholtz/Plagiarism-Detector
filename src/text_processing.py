from __future__ import annotations

import string
from functools import lru_cache
from pathlib import Path

try:
    import spacy
except ImportError:  # pragma: no cover - fallback for environments without spaCy
    spacy = None


PUNCTUATION_TRANSLATOR = str.maketrans("", "", string.punctuation)


def read_text(file_path: str | Path) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def basic_normalize(text: str) -> str:
    cleaned = text.replace("\n", " ").translate(PUNCTUATION_TRANSLATOR).lower()
    return " ".join(cleaned.split())


@lru_cache(maxsize=1)
def _load_language_model():
    if spacy is None:
        raise RuntimeError("spaCy is not installed. Run `pip install -r requirements.txt` first.")
    return spacy.load("en_core_web_sm")


def lemmatize_text(text: str) -> str:
    language_model = _load_language_model()
    doc = language_model(text)
    return " ".join(token.lemma_ for token in doc if not token.is_space)


def normalize_text(text: str, use_lemma: bool = True) -> str:
    normalized = basic_normalize(text)
    if not normalized or not use_lemma:
        return normalized

    try:
        return lemmatize_text(normalized)
    except Exception:
        # Fall back to the basic normalized text if the model is unavailable.
        return normalized


def clean_document_data(input_file: str | Path, use_lemma: bool = False) -> str:
    raw_text = read_text(input_file)
    return normalize_text(raw_text, use_lemma=use_lemma)


def shingles(text: str, k: int = 3) -> set[str]:
    word_list = text.split()
    if len(word_list) < k:
        return set()
    return {" ".join(word_list[index:index + k]) for index in range(len(word_list) - k + 1)}
