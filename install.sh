#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
