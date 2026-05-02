#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv-clean
source .venv-clean/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e .
python scripts/verify_strict5.py
