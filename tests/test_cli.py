import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from src.cli import run
except ModuleNotFoundError as exc:  # pragma: no cover - ensures useful failure message early
    raise AssertionError(
        "Expected `src.cli` module exposing a `run` function that orchestrates the triplet generation "
        "workflow described in requirements.md."
    ) from exc


def test_run_writes_expected_json_lines(tmp_path: Path):
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"

    sample_text = (
        "Alan Turing was a pioneering mathematician and computer scientist from the United Kingdom."
    )
    input_path.write_text(sample_text, encoding="utf-8")

    class StubPipeline:
        def __init__(self):
            self.observed = None

        def generate_triplets(self, text: str):
            self.observed = text
            return [
                {
                    "subject": "Alan Turing",
                    "subject_qid": "Q7251",
                    "subject_type": "human",
                    "predicate": "citizenship",
                    "predicate_pid": "P27",
                    "object": "United Kingdom",
                    "object_qid": "Q145",
                    "object_type": "country",
                }
            ]

    pipeline = StubPipeline()

    run(str(input_path), str(output_path), pipeline=pipeline)

    assert output_path.exists(), "CLI run should create the specified output file."
    assert pipeline.observed == sample_text

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    # The specification requires single-quoted JSON-like strings.
    assert lines[0].startswith("{'") and lines[0].endswith("'}"), "Output must use single quotes."

    parsed = ast.literal_eval(lines[0])
    expected_keys = {
        "subject",
        "subject_qid",
        "predicate",
        "predicate_pid",
        "object",
        "object_qid",
    }
    assert set(parsed.keys()) == expected_keys
    assert parsed["subject"] == "Alan Turing"
    assert parsed["object"] == "United Kingdom"
    assert parsed["predicate"] == "citizenship"
    assert "subject_type" not in parsed
    assert "object_type" not in parsed
