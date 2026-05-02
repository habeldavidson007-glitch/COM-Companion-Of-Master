#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv-clean
source .venv-clean/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
pip install -e .
python3 scripts/verify_strict5.py
