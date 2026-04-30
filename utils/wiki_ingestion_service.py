from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Iterable, List, Dict, Any
import requests


@dataclass(frozen=True)
class SourceSpec:
    name: str
    url: str


class WikiIngestionService:
    def __init__(self, data_dir: str = "data", min_target_bytes: int = 200 * 1024 * 1024):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.min_target_bytes = min_target_bytes

    def _chunk_text(self, text: str, chunk_size: int = 8000) -> Iterable[str]:
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]

    def _deterministic_file(self, source: SourceSpec, idx: int) -> Path:
        digest = sha1(f"{source.name}|{source.url}|{idx}".encode("utf-8")).hexdigest()[:12]
        safe_name = "".join(c if c.isalnum() else "_" for c in source.name).strip("_").lower() or "source"
        return self.raw_dir / f"wiki_{safe_name}_{idx:05d}_{digest}.md"

    def ingest_sources(self, sources: List[SourceSpec], min_target_bytes: int | None = None, timeout: int = 30) -> Dict[str, Any]:
        target = min_target_bytes if min_target_bytes is not None else self.min_target_bytes
        written_bytes = 0
        errors: List[Dict[str, str]] = []
        files: List[str] = []

        for source in sources:
            try:
                response = requests.get(source.url, timeout=timeout)
                response.raise_for_status()
                text = response.text
                for idx, chunk in enumerate(self._chunk_text(text)):
                    md = self._deterministic_file(source, idx)
                    content = f"# {source.name}\n\nSource: {source.url}\n\n{chunk}\n"
                    md.write_text(content, encoding="utf-8")
                    written_bytes += len(content.encode("utf-8"))
                    files.append(str(md))
                    if written_bytes >= target:
                        return {"success": True, "written_bytes": written_bytes, "target_bytes": target, "files": files, "errors": errors}
            except Exception as exc:
                errors.append({"source": source.url, "error": str(exc)})

        return {"success": written_bytes >= target, "written_bytes": written_bytes, "target_bytes": target, "files": files, "errors": errors}
