"""Project Intelligence Layer (PIL).

Provides a lightweight, deterministic index so the assistant can prioritize
small/high-signal files before opening large modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import re


@dataclass(frozen=True)
class FileProfile:
    path: str
    lines: int
    size_bytes: int
    extension: str
    symbols: List[str]
    importance: str


class ProjectIntelligence:
    """Deterministic file index + relevance query layer."""

    def __init__(self, root_dir: str):
        self.root = Path(root_dir).resolve()
        self.file_index: Dict[str, FileProfile] = {}

    def index_project(self, max_file_bytes: int = 512_000) -> int:
        """Index project files once and cache metadata in memory.

        Large binary files are skipped. Returns indexed file count.
        """
        self.file_index.clear()

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if ".git" in path.parts:
                continue
            if path.stat().st_size > max_file_bytes:
                continue

            rel = str(path.relative_to(self.root))
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            lines = content.count("\n") + (1 if content else 0)
            symbols = self._extract_symbols(path.suffix, content)
            importance = self._classify_importance(path.suffix, lines, symbols)

            self.file_index[rel] = FileProfile(
                path=rel,
                lines=lines,
                size_bytes=path.stat().st_size,
                extension=path.suffix,
                symbols=symbols,
                importance=importance,
            )

        return len(self.file_index)

    def query_relevant_files(self, query: str, limit: int = 8) -> List[FileProfile]:
        """Return the most relevant files without opening files repeatedly."""
        tokens = {t for t in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", query.lower()) if len(t) > 2}

        ranked = []
        for profile in self.file_index.values():
            symbol_hits = sum(1 for s in profile.symbols if s.lower() in tokens)
            name_hits = sum(1 for t in tokens if t in profile.path.lower())
            importance_bonus = 2 if profile.importance == "high" else 1 if profile.importance == "medium" else 0
            small_file_bonus = 1 if profile.lines <= 120 else 0
            score = (symbol_hits * 3) + (name_hits * 2) + importance_bonus + small_file_bonus
            if score > 0:
                ranked.append((score, profile))

        ranked.sort(key=lambda pair: (-pair[0], pair[1].lines, pair[1].path))
        return [p for _, p in ranked[:limit]]

    def _extract_symbols(self, suffix: str, content: str) -> List[str]:
        if suffix == ".py":
            return re.findall(r"(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", content)
        if suffix == ".gd":
            return re.findall(r"(?:func|class_name|signal)\s+([A-Za-z_][A-Za-z0-9_]*)", content)
        if suffix in {".tscn", ".cfg", ".toml", ".yaml", ".yml", ".json"}:
            return re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", content)[:40]
        return []

    def _classify_importance(self, suffix: str, lines: int, symbols: List[str]) -> str:
        if suffix in {".tscn", ".gd", ".py"}:
            return "high"
        if suffix in {".toml", ".json", ".cfg", ".yaml", ".yml"}:
            return "medium"
        if symbols and lines <= 300:
            return "medium"
        return "low"
