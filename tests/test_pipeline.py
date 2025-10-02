import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from src.pipeline import Pipeline
except ModuleNotFoundError as exc:  # pragma: no cover - ensures useful failure message early
    raise AssertionError(
        "Expected `src.pipeline` module exposing a `Pipeline` class implementing the knowledge graph "
        "generation pipeline described in requirements.md."
    ) from exc


_SAMPLE_TEXT = (
    "Alan Turing was a pioneering mathematician and computer scientist from the United Kingdom."
)


class StubEntityExtractor:
    def extract(self, text: str):
        # The pipeline should pass the raw text through to the extractor.
        assert "Alan Turing" in text
        return [
            {
                "mention": "Alan Turing",
                "label": "Alan Turing",
                "qid": "Q7251",
                "type": "human",
            },
            {
                "mention": "United Kingdom",
                "label": "United Kingdom",
                "qid": "Q145",
                "type": "country",
            },
        ]


class StubKGClient:
    def get_relationships(self, subject_qid: str, object_qid: str):
        if (subject_qid, object_qid) == ("Q7251", "Q145"):
            return [
                {
                    "pid": "P27",
                    "labels": [
                        "country of citizenship",
                        "citizenship",
                    ],
                }
            ]
        return []


class EmptyKGClient:
    def get_relationships(self, subject_qid: str, object_qid: str):
        return []


@pytest.fixture()
def pipeline():
    return Pipeline(
        entity_extractor=StubEntityExtractor(),
        kg_client=StubKGClient(),
    )


def test_generate_triplets_chooses_shortest_relationship_label(pipeline):
    triplets = pipeline.generate_triplets(_SAMPLE_TEXT)

    assert len(triplets) == 1
    record = triplets[0]

    expected = {
        "subject": "Alan Turing",
        "subject_qid": "Q7251",
        "subject_type": "human",
        "predicate": "citizenship",
        "predicate_pid": "P27",
        "object": "United Kingdom",
        "object_qid": "Q145",
        "object_type": "country",
    }

    assert record == expected


def test_generate_triplets_handles_missing_relationships():
    pipeline = Pipeline(
        entity_extractor=StubEntityExtractor(),
        kg_client=EmptyKGClient(),
    )

    triplets = pipeline.generate_triplets(_SAMPLE_TEXT)

    assert triplets == []
