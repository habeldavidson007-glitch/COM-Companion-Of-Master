# Clean Environment Strict Gate

Use this when preparing to merge into `master`.

## Goal
Require all conditions:
- `suite_crashes = 0`
- `strict_pass = true`
- pass on 5 consecutive `golden_benchmark.py --strict` runs

## One-command flow
```bash
bash scripts/prepare_clean_env.sh
```

## What it does
1. Creates isolated virtualenv `.venv-clean`.
2. Upgrades installer tooling (`pip`, `setuptools`, `wheel`).
3. Installs project in editable mode (`pip install -e .`).
4. Runs `scripts/verify_strict5.py` to enforce strict 5x gate.

## CI/Review contract
Do not merge if `scripts/verify_strict5.py` exits non-zero.

## Exit codes
- `0`: strict gate clean (5/5 passes, zero crashes).
- `2`: benchmark executed but strict criteria failed.
- `3`: blocked environment (missing required Python deps such as `pydantic`/`pandas`).
