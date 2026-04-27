"""
WikiTool: COM integration for knowledge base operations.
Provides @WIKI signal support for:
- @WIKI:INGEST:filename - Ingest a document
- @WIKI:COMPILE:concept - Compile a wiki article
- @WIKI:SEARCH:query - Search the wiki
- @WIKI:HEALTH - Run health checks

Low-RAM optimized, incremental updates.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

from tools.base import BaseTool
from tools.knowledge_ops.wiki_compiler import WikiCompiler


class WikiTool(BaseTool):
    """Knowledge base management tool for COM."""
    
    def __init__(self):
        super().__init__()
        self.compiler = WikiCompiler()
    
    def execute(self, payload: str) -> str:
        """
        Execute wiki operation based on payload.
        Payload format: OPERATION:argument
        """
        if not payload or ':' not in payload:
            return "Usage: @WIKI:OPERATION:argument\nOperations: INGEST, COMPILE, SEARCH, HEALTH"
        
        parts = payload.split(':', 1)
        operation = parts[0].upper()
        argument = parts[1] if len(parts) > 1 else ""
        
        try:
            if operation == "INGEST":
                return self._ingest(argument)
            elif operation == "COMPILE":
                return self._compile(argument)
            elif operation == "SEARCH":
                return self._search(argument)
            elif operation == "HEALTH":
                return self._health_check()
            elif operation == "STATS":
                return self._stats()
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            return f"Wiki error: {str(e)}"
    
    def _ingest(self, filepath: str) -> str:
        """Ingest a document into the wiki."""
        result = self.compiler.ingest_document(filepath)
        if result:
            concepts = ", ".join(result.get("concepts", [])[:5])
            return (
                f"✅ Document ingested successfully.\n"
                f"📄 File: {Path(result['path']).name}\n"
                f"📝 Summary: {result['summary'][:200]}...\n"
                f"🏷️ Concepts: {concepts}\n"
                f"📊 Word count: {result.get('word_count', 0)}"
            )
        return "❌ Failed to ingest document. Check file path and encoding."
    
    def _compile(self, concept: str) -> str:
        """Compile a wiki article for a concept."""
        article_path = self.compiler.compile_wiki_article(concept)
        if article_path:
            return (
                f"✅ Wiki article compiled successfully.\n"
                f"📄 Concept: {concept}\n"
                f"💾 Saved to: {article_path}\n"
                f"💡 Open with: cat {article_path}"
            )
        return f"❌ Concept '{concept}' not found in index. Try ingesting related documents first."
    
    def _search(self, query: str) -> str:
        """Search the wiki index for matching documents/concepts."""
        results = []
        query_lower = query.lower()
        
        # Search in documents
        for doc_id, doc in self.compiler.index["documents"].items():
            if (query_lower in doc.get("summary", "").lower() or 
                query_lower in doc_id.lower() or
                any(query_lower in c.lower() for c in doc.get("concepts", []))):
                results.append({
                    "type": "document",
                    "id": doc_id,
                    "summary": doc.get("summary", "")[:150],
                    "concepts": doc.get("concepts", [])[:3]
                })
        
        # Search in concepts
        for concept, docs in self.compiler.index["concepts"].items():
            if query_lower in concept.lower():
                results.append({
                    "type": "concept",
                    "id": concept,
                    "doc_count": len(docs),
                    "sample_docs": docs[:3]
                })
        
        if not results:
            return f"❌ No results found for '{query}'"
        
        # Format results
        output = f"🔍 Search results for '{query}':\n\n"
        for i, r in enumerate(results[:10], 1):  # Limit to top 10
            if r["type"] == "document":
                output += f"{i}. 📄 {r['id']}\n"
                output += f"   {r['summary']}...\n"
                output += f"   Tags: {', '.join(r['concepts'])}\n\n"
            else:
                output += f"{i}. 🏷️ Concept: {r['id']}\n"
                output += f"   Related docs: {r['doc_count']}\n"
                output += f"   Sample: {', '.join(r['sample_docs'])}\n\n"
        
        return output
    
    def _health_check(self) -> str:
        """Run wiki health checks."""
        issues = self.compiler.run_health_check()
        
        total_issues = (
            len(issues["orphaned_concepts"]) +
            len(issues["missing_summaries"]) +
            len(issues["broken_links"])
        )
        
        if total_issues == 0:
            return "✅ Wiki health check passed. No issues found."
        
        output = f"⚠️ Wiki health check found {total_issues} issues:\n\n"
        
        if issues["orphaned_concepts"]:
            output += f"🔸 Orphaned concepts ({len(issues['orphaned_concepts'])}): "
            output += ", ".join(issues["orphaned_concepts"][:5])
            output += "\n"
        
        if issues["missing_summaries"]:
            output += f"🔸 Missing summaries ({len(issues['missing_summaries'])}): "
            output += ", ".join(issues["missing_summaries"][:5])
            output += "\n"
        
        if issues["broken_links"]:
            output += f"🔸 Broken links ({len(issues['broken_links'])}): "
            output += ", ".join(issues["broken_links"][:5])
            output += "\n"
        
        output += "\n💡 Run @WIKI:HEALTH:FIX to auto-repair (future feature)"
        return output
    
    def _stats(self) -> str:
        """Get wiki statistics."""
        stats = self.compiler.get_statistics()
        
        return (
            f"📊 Wiki Statistics:\n"
            f"📄 Total documents: {stats['total_documents']}\n"
            f"🏷️ Total concepts: {stats['total_concepts']}\n"
            f"📝 Total words: {stats['total_words']:,}\n"
            f"📈 Avg document length: {stats['avg_doc_length']} words\n"
            f"🕒 Last updated: {stats['last_updated'] or 'Never'}"
        )


# Register tool
if __name__ == "__main__":
    # Test execution
    tool = WikiTool()
    print(tool.execute("STATS:"))
