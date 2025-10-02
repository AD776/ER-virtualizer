#!/usr/bin/env bash
set -euo pipefail

INPUT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      INPUT="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
  echo "Usage: $0 --input <path> --output <path>" >&2
  exit 1
fi

python3 -m src.cli --input "$INPUT" --output "$OUTPUT"
