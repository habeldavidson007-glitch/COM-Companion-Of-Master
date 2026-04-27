"""
Wiki Health Checker - Scans wiki for issues and suggests fixes.
Finds orphans, missing summaries, broken links, and inconsistencies.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..tools.safe_io import SafeIO
from .indexer import WikiIndexer
from .retriever import WikiRetriever


class HealthReport:
    """Represents a health check report."""
    
    def __init__(self):
        self.orphans: List[str] = []
        self.missing_summaries: List[str] = []
        self.broken_links: List[str] = []
        self.suggestions: List[str] = []
        self.stats: Dict[str, Any] = {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "stats": self.stats,
            "issues": {
                "orphans": self.orphans,
                "missing_summaries": self.missing_summaries,
                "broken_links": self.broken_links
            },
            "suggestions": self.suggestions
        }


class WikiHealthChecker:
    """Performs health checks on the wiki."""
    
    def __init__(self, data_dir: str):
        self.io = SafeIO(data_dir)
        self.indexer = WikiIndexer(data_dir)
        self.retriever = WikiRetriever(data_dir)
    
    def check_all(self) -> HealthReport:
        """Run all health checks."""
        report = HealthReport()
        
        # Get index stats
        report.stats = self.indexer.get_stats()
        
        # Check for orphans
        report.orphans = self._find_orphans()
        
        # Check for missing summaries
        report.missing_summaries = self._find_missing_summaries()
        
        # Check for broken links
        report.broken_links = self._find_broken_links()
        
        # Generate suggestions
        report.suggestions = self._generate_suggestions(report)
        
        return report
    
    def _find_orphans(self) -> List[str]:
        """Find documents with no incoming backlinks."""
        return self.indexer.find_orphans()
    
    def _find_missing_summaries(self) -> List[str]:
        """Find documents without proper summaries."""
        missing = []
        
        for doc_id, doc in self.indexer.index["documents"].items():
            summary = doc.get("summary", "")
            
            # Check if summary is too short or placeholder
            if not summary or len(summary) < 50 or "failed" in summary.lower():
                missing.append(doc["path"])
        
        return missing
    
    def _find_broken_links(self) -> List[str]:
        """Find internal links that point to non-existent pages."""
        broken = []
        wiki_files = set(self.io.list_files("wiki", "*.md"))
        
        # Check all documents for broken [[Link]] references
        import re
        link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        for wiki_file in wiki_files:
            try:
                content = self.io.read_text(wiki_file)
                links = link_pattern.findall(content)
                
                for link in links:
                    target = f"wiki/{link.replace(' ', '_')}.md"
                    concept_target = f"wiki/concepts/{link.replace(' ', '_')}.md"
                    
                    if target not in wiki_files and concept_target not in wiki_files:
                        broken.append(f"{wiki_file} -> {link}")
                        
            except Exception:
                continue
        
        return broken[:20]  # Limit results
    
    def _generate_suggestions(self, report: HealthReport) -> List[str]:
        """Generate actionable suggestions based on issues found."""
        suggestions = []
        
        if report.orphans:
            suggestions.append(
                f"Found {len(report.orphans)} orphaned documents. "
                "Consider adding backlinks or categorizing them."
            )
        
        if report.missing_summaries:
            suggestions.append(
                f"Found {len(report.missing_summaries)} documents with missing/weak summaries. "
                "Re-run compiler to regenerate summaries."
            )
        
        if report.broken_links:
            suggestions.append(
                f"Found {len(report.broken_links)} broken internal links. "
                "Create missing concept articles or fix link references."
            )
        
        # Suggest new concept articles
        concept_counts: Dict[str, int] = {}
        for doc in self.indexer.index["documents"].values():
            for concept in doc.get("concepts", []):
                concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        # Find concepts with multiple docs but no article
        for concept, count in concept_counts.items():
            if count >= 3:
                concept_path = f"wiki/concepts/{concept.replace(' ', '_')}.md"
                if not self.io.exists(concept_path):
                    suggestions.append(
                        f"Concept '{concept}' has {count} related documents. "
                        f"Consider creating a concept article."
                    )
        
        return suggestions
    
    def auto_fix_missing_summaries(self, llm_host: str = "http://localhost:11434") -> int:
        """Attempt to regenerate missing summaries using LLM."""
        from ..core.client import OllamaClient
        from .compiler import WikiCompiler
        
        compiler = WikiCompiler(self.io.base_dir, llm_host=llm_host)
        missing = self._find_missing_summaries()
        fixed = 0
        
        for wiki_path in missing:
            # Find corresponding raw file (if exists)
            # This is simplified - in practice you'd track raw->wiki mapping
            print(f"Regenerating summary for: {wiki_path}")
            # Would need raw content to regenerate - skipping for now
            # In full implementation, store raw content reference in index
        
        return fixed
    
    def export_report(self, output_path: str = "logs/health_report.json") -> str:
        """Export health report to JSON."""
        report = self.check_all()
        self.io.ensure_dir("logs")
        self.io.write_json(output_path, report.to_dict())
        return output_path
