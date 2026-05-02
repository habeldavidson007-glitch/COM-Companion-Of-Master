#!/usr/bin/env python3
"""Canonical GOLDEN_BENCHMARK entrypoint for COM IDE benchmark suite."""
import subprocess
import sys


def main() -> int:
    args = [sys.executable, "benchmark.py", *sys.argv[1:]]
    return subprocess.run(args).returncode


if __name__ == "__main__":
    raise SystemExit(main())
