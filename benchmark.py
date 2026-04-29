"""
COM v5 — Signal-Trace Architecture Benchmark Suite
Mirrors the exact 10-suite, 96-assertion methodology used in Claude's benchmark.
Run from the COM repo root: python benchmark.py
"""

import sys
import os
import time
import json
import inspect
import asyncio
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

GREEN  = "[32m"
RED    = "[31m"
YELLOW = "[33m"
CYAN   = "[36m"
BOLD   = "[1m"
RESET  = "[0m"
DIM    = "[2m"

def ok(msg):   return f"{GREEN}PASS{RESET}  {msg}"
def fail(msg): return f"{RED}FAIL{RESET}  {msg}"
def warn(msg): return f"{YELLOW}WARN{RESET}  {msg}"
def info(msg): return f"{CYAN}INFO{RESET}  {msg}"

@dataclass
class SuiteResult:
    name: str
    passed: int = 0
    total: int  = 0
    notes: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    @property
    def pct(self): return (self.passed / self.total * 100) if self.total else 0

    def record(self, label: str, result: bool, detail: str = ""):
        self.total += 1
        if result:
            self.passed += 1
            print(f"    {ok(label)}")
        else:
            self.failures.append(label + (f" — {detail}" if detail else ""))
            print(f"    {fail(label)}" + (f"  {DIM}({detail}){RESET}" if detail else ""))

    def note(self, msg: str):
        self.notes.append(msg)
        print(f"    {info(msg)}")

ALL: List[SuiteResult] = []

def suite(fn):
    def wrapper():
        name = fn.__name__.replace("test_", "").replace("_", " ").title()
        print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
        print(f"{BOLD}  {name}{RESET}")
        print(f"{CYAN}{'─'*60}{RESET}")
        sr = SuiteResult(name=name)
        fn(sr)
        score_color = GREEN if sr.pct >= 90 else (YELLOW if sr.pct >= 70 else RED)
        print(f"\n  Score: {score_color}{BOLD}{sr.passed}/{sr.total} = {sr.pct:.1f}%{RESET}")
        ALL.append(sr)
    return wrapper
