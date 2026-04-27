"""
WikiCompiler: Incremental knowledge base builder.
Converts raw documents (MD, TXT, PDF) into a structured wiki with:
- Summaries
- Concept extraction
- Backlinks
- Consistency checks

Designed for low-RAM, incremental updates, and LLM-assisted maintenance.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

class WikiCompiler:
    def __init__(self, raw_dir: str = "data/raw", wiki_dir: str = "data/wiki"):
        self.raw_dir = Path(raw_dir)
        self.wiki_dir = Path(wiki_dir)
        self.concepts_dir = self.wiki_dir / "concepts"
        self.summaries_dir = self.wiki_dir / "summaries"
        self.index_file = self.wiki_dir / "wiki_index.json"
        
        # Ensure directories exist
        for d in [self.raw_dir, self.wiki_dir, self.concepts_dir, self.summaries_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load or create wiki index."""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "documents": {},
            "concepts": {},
            "backlinks": {},
            "last_updated": None
        }
    
    def _save_index(self):
        """Persist index to disk."""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
    
    def _file_hash(self, filepath: Path) -> str:
        """Generate hash for change detection."""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def ingest_document(self, filepath: str, force: bool = False) -> Optional[Dict]:
        """
        Ingest a raw document into the wiki system.
        Returns summary metadata if successful.
        """
        path = Path(filepath)
        if not path.exists():
            # Try in raw_dir
            path = self.raw_dir / filepath
            if not path.exists():
                return None
        
        file_hash = self._file_hash(path)
        doc_id = str(path.relative_to(self.raw_dir.parent)) if path.is_relative_to(self.raw_dir.parent) else path.name
        
        # Skip if unchanged
        if doc_id in self.index["documents"] and not force:
            if self.index["documents"][doc_id].get("hash") == file_hash:
                return self.index["documents"][doc_id]
        
        # Read content
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback for binary files (PDFs would need pdfplumber)
            return None
        
        # Generate summary (LLM call placeholder)
        summary = self._generate_summary(content, path.name)
        
        # Extract concepts (simple keyword extraction for now)
        concepts = self._extract_concepts(content)
        
        # Update index
        doc_entry = {
            "path": str(path),
            "hash": file_hash,
            "summary": summary,
            "concepts": concepts,
            "ingested_at": datetime.now().isoformat(),
            "word_count": len(content.split())
        }
        
        self.index["documents"][doc_id] = doc_entry
        
        # Update concept index
        for concept in concepts:
            if concept not in self.index["concepts"]:
                self.index["concepts"][concept] = []
            if doc_id not in self.index["concepts"][concept]:
                self.index["concepts"][concept].append(doc_id)
        
        # Update backlinks
        self._update_backlinks(doc_id, content)
        
        self._save_index()
        return doc_entry
    
    def _generate_summary(self, content: str, filename: str) -> str:
        """
        Generate a concise summary of the document.
        In production, this calls the LLM with a specific prompt.
        For now, uses extractive summarization (first 3 sentences + keywords).
        """
        # Simple extractive summary (replace with LLM call)
        sentences = re.split(r'(?<=[.!?])\s+', content.replace('\n', ' '))
        summary_sentences = sentences[:min(3, len(sentences))]
        return " ".join(summary_sentences)[:500] + "..."
    
    def _extract_concepts(self, content: str) -> List[str]:
        """
        Extract key concepts from content.
        Uses simple frequency analysis + capitalization heuristics.
        Replace with LLM-based extraction for better accuracy.
        """
        # Find capitalized phrases (potential concepts)
        candidates = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        
        # Frequency count
        freq = {}
        for c in candidates:
            if len(c) > 3:  # Filter short words
                freq[c] = freq.get(c, 0) + 1
        
        # Top 10 concepts
        sorted_concepts = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [c[0] for c in sorted_concepts[:10]]
    
    def _update_backlinks(self, doc_id: str, content: str):
        """Update backlink graph based on concept mentions."""
        # Remove old backlinks for this doc
        for concept, docs in self.index["backlinks"].items():
            if doc_id in docs:
                docs.remove(doc_id)
        
        # Find concept mentions in content
        for concept in self.index["concepts"].keys():
            if re.search(r'\b' + re.escape(concept) + r'\b', content, re.IGNORECASE):
                if concept not in self.index["backlinks"]:
                    self.index["backlinks"][concept] = []
                if doc_id not in self.index["backlinks"][concept]:
                    self.index["backlinks"][concept].append(doc_id)
    
    def compile_wiki_article(self, concept: str) -> Optional[str]:
        """
        Compile a wiki article for a given concept.
        Aggregates all documents mentioning this concept.
        """
        if concept not in self.index["concepts"]:
            return None
        
        related_docs = self.index["concepts"][concept]
        article_path = self.concepts_dir / f"{concept.replace(' ', '_')}.md"
        
        # Build article content
        content = f"# {concept}\n\n"
        content += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        content += f"**Related Documents:** {len(related_docs)}\n\n"
        content += "---\n\n"
        
        for doc_id in related_docs[:10]:  # Limit to top 10
            if doc_id in self.index["documents"]:
                doc = self.index["documents"][doc_id]
                content += f"## From: {Path(doc['path']).name}\n\n"
                content += f"{doc['summary']}\n\n"
                content += f"*Concepts: {', '.join(doc['concepts'][:5])}*\n\n"
                content += "---\n\n"
        
        # Write article
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(article_path)
    
    def run_health_check(self) -> Dict:
        """
        Run integrity checks on the wiki.
        Returns issues found.
        """
        issues = {
            "orphaned_concepts": [],
            "missing_summaries": [],
            "broken_links": [],
            "duplicate_content": []
        }
        
        # Check for orphaned concepts (no documents)
        for concept, docs in self.index["concepts"].items():
            if not docs:
                issues["orphaned_concepts"].append(concept)
        
        # Check for documents without summaries
        for doc_id, doc in self.index["documents"].items():
            if not doc.get("summary"):
                issues["missing_summaries"].append(doc_id)
        
        # Check for broken file paths
        for doc_id, doc in self.index["documents"].items():
            if not Path(doc["path"]).exists():
                issues["broken_links"].append(doc_id)
        
        return issues
    
    def get_statistics(self) -> Dict:
        """Return wiki statistics."""
        total_words = sum(d.get("word_count", 0) for d in self.index["documents"].values())
        return {
            "total_documents": len(self.index["documents"]),
            "total_concepts": len(self.index["concepts"]),
            "total_words": total_words,
            "last_updated": self.index.get("last_updated"),
            "avg_doc_length": total_words // max(1, len(self.index["documents"]))
        }


# CLI interface for direct usage
if __name__ == "__main__":
    import sys
    
    compiler = WikiCompiler()
    
    if len(sys.argv) < 2:
        print("Usage: python wiki_compiler.py [ingest|compile|health|stats] [args]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "ingest":
        if len(sys.argv) < 3:
            print("Provide a file path")
            sys.exit(1)
        result = compiler.ingest_document(sys.argv[2])
        print(json.dumps(result, indent=2) if result else "Failed to ingest")
    
    elif command == "compile":
        if len(sys.argv) < 3:
            print("Provide a concept name")
            sys.exit(1)
        path = compiler.compile_wiki_article(sys.argv[2])
        print(f"Article compiled: {path}" if path else "Concept not found")
    
    elif command == "health":
        issues = compiler.run_health_check()
        print(json.dumps(issues, indent=2))
    
    elif command == "stats":
        stats = compiler.get_statistics()
        print(json.dumps(stats, indent=2))
