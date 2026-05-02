#!/usr/bin/env python3
"""GOLDEN_BENCHMARK runner entrypoint.

Canonical benchmark command for CI/local verification.
"""
import subprocess
import sys


def main() -> int:
    args = [sys.executable, "benchmark.py", *sys.argv[1:]]
    proc = subprocess.run(args)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
