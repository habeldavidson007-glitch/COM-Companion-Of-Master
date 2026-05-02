#!/usr/bin/env python3
"""Compatibility runner for lowercase command.

Canonical benchmark entrypoint is now `GOLDEN_BENCHMARK.py`.
"""
import subprocess
import sys


def main() -> int:
    args = [sys.executable, "GOLDEN_BENCHMARK.py", *sys.argv[1:]]
    proc = subprocess.run(args)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
