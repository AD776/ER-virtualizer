"""Entity extraction utilities built on top of spaCy."""

from __future__ import annotations

from typing import Dict, List, Optional

try:
    import spacy
    from spacy.language import Language
except Exception:  # pragma: no cover - spaCy is heavy and optional during testing
    spacy = None
    Language = None


class SpacyEntityExtractor:
    """Extract entities from free-form text using spaCy."""

    def __init__(self, model: str = "en_core_web_sm", nlp: Optional["Language"] = None):
        self.model = model
        self._nlp = nlp

    def _ensure_model(self) -> "Language":
        if self._nlp is None:
            if spacy is None:
                raise ImportError(
                    "spaCy is required for entity extraction but is not installed."
                )
            self._nlp = spacy.load(self.model)
        return self._nlp

    def extract(self, text: str) -> List[Dict[str, str]]:
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        text = text.strip()
        if not text:
            return []

        nlp = self._ensure_model()
        doc = nlp(text)

        entities: List[Dict[str, str]] = []
        for ent in doc.ents:
            entities.append(
                {
                    "mention": ent.text,
                    "label": ent.text,
                    "qid": "",
                    "type": ent.label_,
                }
            )

        return entities
