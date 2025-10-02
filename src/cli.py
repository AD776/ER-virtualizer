"""Command-line entry points for the project pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .entities import SpacyEntityExtractor
from .pipeline import Pipeline
from .wikidata import WikidataClient

_REQUIRED_OUTPUT_KEYS = (
    "subject",
    "subject_qid",
    "predicate",
    "predicate_pid",
    "object",
    "object_qid",
)


def build_pipeline() -> Pipeline:
    """Construct the default pipeline with real extractor and KG client."""

    extractor = SpacyEntityExtractor()
    kg_client = WikidataClient()
    return Pipeline(entity_extractor=extractor, kg_client=kg_client)


def run(input_path: str, output_path: str, pipeline: Optional[Pipeline] = None) -> None:
    """Execute the pipeline with the provided input and persist JSON-line output."""

    text = Path(input_path).read_text(encoding="utf-8")

    pipeline = pipeline or build_pipeline()
    triplets = pipeline.generate_triplets(text)

    records = [_normalise_record(record) for record in triplets]
    # Ensure the parent folder exists to avoid surprising IOErrors.
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    Path(output_path).write_text("\n".join(records), encoding="utf-8")


def _normalise_record(record: Mapping[str, object]) -> str:
    """Ensure values are stringified and serialised with single quotes via repr.

    The submission format requires single-quoted JSON-like dictionaries containing
    only the canonical keys described in requirements.md. Any additional metadata
    present on the pipeline records is ignored for the serialized output.
    """

    filtered = {key: str(record.get(key, "")) for key in _REQUIRED_OUTPUT_KEYS}
    return repr(filtered)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Wikidata triplets from text input.")
    parser.add_argument("--input", required=True, help="Path to the UTF-8 encoded text file to analyse")
    parser.add_argument(
        "--output", required=True, help="Destination path for the generated single-quoted JSON lines"
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    run(args.input, args.output)


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    main()
