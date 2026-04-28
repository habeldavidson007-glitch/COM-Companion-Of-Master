"""
Wiki Indexer - Maintains the knowledge base index without LLM.
Tracks backlinks, concept graphs, and document metadata.

FIXED: Backlink key mismatch - now uses consistent doc_id format for save/retrieve
"""
import json
from typing import Dict, List, Set, Any
from pathlib import Path
from datetime import datetime

from tools.safe_io import SafeIO


class WikiIndexer:
    """Maintains wiki index structure and metadata."""

    def __init__(self, data_dir: str):
        self.io = SafeIO(data_dir)
        self.index_path = "wiki/_index.json"
        self.index: Dict[str, Any] = {
            "documents": {},
            "concepts": {},
            "backlinks": {},
            "last_updated": None
        }
        self._load_index()

    def _load_index(self) -> None:
        """Load existing index or initialize empty."""
        if self.io.exists(self.index_path):
            try:
                self.index = self.io.read_json(self.index_path)
            except Exception:
                pass  # Start fresh if corrupted

    def _save_index(self) -> None:
        """Persist index to disk."""
        self.index["last_updated"] = datetime.now().isoformat()
        self.io.write_json(self.index_path, self.index)
    
    def save_index(self) -> None:
        """Public method to save index (alias for _save_index)."""
        self._save_index()

    def _to_doc_id(self, path: str) -> str:
        """Convert a file path to a consistent document ID."""
        return path.replace("/", "_").replace(".md", "")

    def add_document(
        self,
        path: str,
        title: str,
        summary: str,
        concepts: List[str],
        word_count: int
    ) -> None:
        """Add or update a document in the index."""
        doc_id = self._to_doc_id(path)

        self.index["documents"][doc_id] = {
            "path": path,
            "title": title,
            "summary": summary,
            "concepts": concepts,
            "word_count": word_count,
            "created": datetime.now().isoformat()
        }

        # Update concept mappings
        for concept in concepts:
            if concept not in self.index["concepts"]:
                self.index["concepts"][concept] = []
            if doc_id not in self.index["concepts"][concept]:
                self.index["concepts"][concept].append(doc_id)

        self._save_index()

    def add_backlink(self, source: str, target: str) -> None:
        """
        Record a backlink from source to target.
        FIXED: Now uses consistent doc_id format for both source and target.
        """
        # Convert both paths to doc_id format for consistency
        source_id = self._to_doc_id(source)
        target_id = self._to_doc_id(target)
        
        if target_id not in self.index["backlinks"]:
            self.index["backlinks"][target_id] = []

        if source_id not in self.index["backlinks"][target_id]:
            self.index["backlinks"][target_id].append(source_id)

        self._save_index()

    def get_concept_documents(self, concept: str) -> List[Dict]:
        """Get all documents related to a concept."""
        doc_ids = self.index["concepts"].get(concept, [])
        return [
            self.index["documents"][doc_id]
            for doc_id in doc_ids
            if doc_id in self.index["documents"]
        ]

    def get_backlinks(self, path: str) -> List[str]:
        """
        Get all documents that link to this path.
        FIXED: Uses same doc_id conversion as add_backlink for key matching.
        """
        doc_id = self._to_doc_id(path)
        return self.index["backlinks"].get(doc_id, [])

    def find_orphans(self) -> List[str]:
        """Find documents with no backlinks (except index itself)."""
        orphans = []
        for doc_id, doc in self.index["documents"].items():
            if doc_id not in self.index["backlinks"] or not self.index["backlinks"][doc_id]:
                # Check if it's not a root concept article
                if not doc["path"].startswith("concepts/"):
                    orphans.append(doc["path"])
        return orphans

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_documents": len(self.index["documents"]),
            "total_concepts": len(self.index["concepts"]),
            "total_backlinks": sum(len(v) for v in self.index["backlinks"].values()),
            "last_updated": self.index["last_updated"]
        }
