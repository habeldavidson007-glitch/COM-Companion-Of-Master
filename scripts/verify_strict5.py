#!/usr/bin/env python3
"""Run GOLDEN_BENCHMARK strict mode 5x and fail if gate is not clean."""
import json
import subprocess
import sys
from pathlib import Path

TARGET_RUNS = 5
rows = []


def dependency_preflight():
    required = ["pydantic", "pandas"]
    missing = []
    for dep in required:
        try:
            __import__(dep)
        except Exception:
            missing.append(dep)
    return missing


missing_deps = dependency_preflight()
if missing_deps:
    print(
        json.dumps(
            {
                "status": "blocked_environment",
                "reason": "missing_python_dependencies",
                "missing_dependencies": missing_deps,
                "next_step": "Install missing deps in a clean environment, then rerun scripts/verify_strict5.py",
            },
            indent=2,
        )
    )
    sys.exit(3)

for i in range(1, TARGET_RUNS + 1):
    proc = subprocess.run([sys.executable, "GOLDEN_BENCHMARK.py", "--strict"], capture_output=True, text=True)
    payload = {}
    if Path("benchmark_results.json").exists():
        payload = json.loads(Path("benchmark_results.json").read_text(encoding="utf-8"))
    row = {
        "run": i,
        "exit_code": proc.returncode,
        "suite_crashes": payload.get("suite_crashes"),
        "strict_pass": payload.get("strict_pass"),
        "dependency_errors": payload.get("dependency_errors"),
    }
    rows.append(row)

print(json.dumps(rows, indent=2))

ok = all(
    r["exit_code"] == 0 and r["suite_crashes"] == 0 and r["strict_pass"] is True
    for r in rows
)
if not ok:
    print("\nFAIL: strict gate not clean across 5 runs.")
    print("Hints:")
    print("- Fix suite crashes until suite_crashes == 0.")
    print("- Ensure strict_pass is true for every run.")
    sys.exit(2)

print("\nPASS: strict gate clean across 5 runs.")
