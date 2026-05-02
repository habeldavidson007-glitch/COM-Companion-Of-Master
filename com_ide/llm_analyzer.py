"""
LLM Analyzer Module

This module provides LLM-based analysis for logs and knowledge evolution.
IMPORTANT: LLM is ONLY used for observation and suggestions, NEVER for execution.

Strict Rules:
- LLM cannot execute anything
- LLM cannot modify Signal directly
- All suggestions are non-binding and require user confirmation
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class LLMAnalyzer:
    """
    LLM-based analyzer for log analysis and knowledge evolution.
    
    This is a mock implementation that demonstrates the interface.
    In production, this would connect to an actual LLM API.
    """
    
    def __init__(self, knowledge_base_path: str = "./knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_file = self.knowledge_base_path / "knowledge.json"
        self.suggestions_file = self.knowledge_base_path / "suggestions.jsonl"
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load existing knowledge base."""
        if self.knowledge_file.exists():
            with open(self.knowledge_file, "r", encoding="utf-8") as f:
                self.knowledge_base = json.load(f)
        else:
            self.knowledge_base = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "entries": []
            }
    
    def _save_knowledge_base(self):
        """Save knowledge base to disk."""
        with open(self.knowledge_file, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
    
    def analyze_logs(
        self,
        logs: List[Dict[str, Any]],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze execution logs and provide insights.
        
        Input:
        - logs: Current execution logs
        - history: Past execution history (optional)
        
        Output:
        {
            "summary": "...",
            "root_cause": "...",
            "suggestion": "...",
            "confidence": 0.0-1.0
        }
        
        NOTE: This is a mock implementation. In production, this would
        call an actual LLM API with proper prompts.
        """
        # Mock analysis based on log patterns
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "logs_analyzed": len(logs),
            "summary": "",
            "root_cause": None,
            "suggestion": None,
            "confidence": 0.0,
            "patterns_detected": [],
            "requires_attention": False
        }
        
        # Analyze for errors
        error_count = 0
        success_count = 0
        
        for log in logs:
            if log.get("result", {}).get("success") == False or log.get("error"):
                error_count += 1
                analysis["patterns_detected"].append({
                    "type": "ERROR",
                    "message": log.get("error") or log.get("result", {}).get("error"),
                    "timestamp": log.get("timestamp")
                })
                analysis["requires_attention"] = True
            else:
                success_count += 1
        
        total = error_count + success_count
        
        if total > 0:
            analysis["summary"] = (
                f"Analyzed {total} executions: {success_count} successful, {error_count} failed."
            )
            
            if error_count > 0:
                # Try to identify root cause from error patterns
                error_messages = [p["message"] for p in analysis["patterns_detected"] if p.get("message")]
                if error_messages:
                    common_errors = {}
                    for msg in error_messages:
                        error_str = str(msg)[:100]  # Truncate for grouping
                        common_errors[error_str] = common_errors.get(error_str, 0) + 1
                    
                    most_common = max(common_errors.items(), key=lambda x: x[1])
                    analysis["root_cause"] = f"Most common error ({most_common[1]} occurrences): {most_common[0]}"
                    analysis["confidence"] = min(0.9, 0.5 + (most_common[1] * 0.1))
                    
                    # Generate suggestion based on error type
                    analysis["suggestion"] = self._generate_suggestion_for_error(most_common[0])
                else:
                    analysis["root_cause"] = "Unknown error pattern"
                    analysis["confidence"] = 0.3
            else:
                analysis["summary"] = f"All {success_count} executions completed successfully."
                analysis["confidence"] = 1.0
        else:
            analysis["summary"] = "No executions to analyze."
            analysis["confidence"] = 0.0
        
        return analysis
    
    def _generate_suggestion_for_error(self, error_message: str) -> str:
        """Generate a suggestion based on error message pattern."""
        error_lower = str(error_message).lower()
        
        if "parse error" in error_lower or "expected" in error_lower:
            return (
                "This appears to be a syntax error in E+ code. "
                "Check that: 1) All variables start with @, 2) All expressions are wrapped in parentheses (), "
                "3) All blocks use curly braces {}, 4) Keywords like 'if', 'say', 'input' are used correctly."
            )
        elif "lexer error" in error_lower or "unexpected character" in error_lower:
            return (
                "This appears to be a lexical error. Check for invalid characters in your code. "
                "E+ only supports alphanumeric characters, @, parentheses, braces, and standard operators."
            )
        elif "name" in error_lower or "undefined" in error_lower:
            return (
                "This appears to be a variable reference error. Ensure all variables are defined before use "
                "with the @ prefix (e.g., @myvar = (\"value\"))."
            )
        elif "type" in error_lower or "conversion" in error_lower:
            return (
                "This appears to be a type mismatch error. E+ is dynamically typed but operations must be "
                "compatible (e.g., don't add strings to numbers without explicit conversion)."
            )
        else:
            return (
                "Review the error message and check your E+ code syntax. "
                "Refer to the E+ language specification for correct usage of constructs."
            )
    
    def build_wiki_entry(
        self,
        problem: str,
        cause: str,
        fix: str,
        prevention: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a structured knowledge entry for the wiki.
        
        This is called when a fix is detected and should be stored for future reference.
        """
        entry = {
            "id": f"KB_{len(self.knowledge_base['entries']) + 1:04d}",
            "created_at": datetime.now().isoformat(),
            "problem": problem,
            "cause": cause,
            "fix": fix,
            "prevention": prevention,
            "tags": tags or [],
            "verified": False,
            "usage_count": 0
        }
        
        self.knowledge_base["entries"].append(entry)
        self._save_knowledge_base()
        
        return entry
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant entries."""
        query_lower = query.lower()
        results = []
        
        for entry in self.knowledge_base["entries"]:
            score = 0
            
            # Check if query matches any field
            if query_lower in entry["problem"].lower():
                score += 3
            if query_lower in entry["cause"].lower():
                score += 2
            if query_lower in entry["fix"].lower():
                score += 2
            if query_lower in entry["prevention"].lower():
                score += 1
            for tag in entry.get("tags", []):
                if query_lower in tag.lower():
                    score += 1
            
            if score > 0:
                results.append((score, entry))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results]
    
    def suggest_fix(
        self,
        error_context: Dict[str, Any],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Suggest a fix based on error context.
        
        IMPORTANT: Even if auto_apply is True, this method ONLY returns
        a suggestion. The caller MUST require user confirmation before
        applying any changes.
        
        Returns:
        {
            "suggestion": "...",
            "confidence": 0.0-1.0,
            "requires_confirmation": True,
            "auto_applied": False,
            "knowledge_source": "..."
        }
        """
        suggestion = {
            "timestamp": datetime.now().isoformat(),
            "suggestion": None,
            "confidence": 0.0,
            "requires_confirmation": True,  # ALWAYS requires confirmation
            "auto_applied": False,  # Never auto-apply
            "knowledge_source": None,
            "alternative_fixes": []
        }
        
        # Search knowledge base for similar issues
        error_message = str(error_context.get("error", ""))
        matching_entries = self.search_knowledge(error_message[:100])
        
        if matching_entries:
            best_match = matching_entries[0]
            suggestion["suggestion"] = best_match["fix"]
            suggestion["confidence"] = 0.8
            suggestion["knowledge_source"] = best_match["id"]
            suggestion["alternative_fixes"] = [
                {"source": e["id"], "fix": e["fix"]}
                for e in matching_entries[1:3]
            ]
        else:
            # Fall back to heuristic-based suggestion
            suggestion["suggestion"] = self._generate_suggestion_for_error(error_message)
            suggestion["confidence"] = 0.5
            suggestion["knowledge_source"] = "heuristic"
        
        # Log suggestion for tracking
        self._log_suggestion(suggestion, error_context)
        
        return suggestion
    
    def _log_suggestion(self, suggestion: Dict[str, Any], context: Dict[str, Any]):
        """Log suggestion for audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "suggestion": suggestion,
            "context": context,
            "user_confirmed": False,
            "user_applied": False
        }
        
        with open(self.suggestions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def get_analysis_summary(self, logs: List[Dict[str, Any]]) -> str:
        """Get a human-readable summary of log analysis."""
        analysis = self.analyze_logs(logs)
        
        lines = [
            "=" * 50,
            "LLM LOG ANALYSIS SUMMARY",
            "=" * 50,
            f"Timestamp: {analysis['timestamp']}",
            f"Logs Analyzed: {analysis['logs_analyzed']}",
            "",
            "SUMMARY:",
            analysis["summary"],
            ""
        ]
        
        if analysis["root_cause"]:
            lines.extend([
                "ROOT CAUSE:",
                analysis["root_cause"],
                ""
            ])
        
        if analysis["suggestion"]:
            lines.extend([
                "SUGGESTION:",
                analysis["suggestion"],
                ""
            ])
        
        lines.extend([
            f"Confidence: {analysis['confidence']:.1%}",
            f"Requires Attention: {'Yes' if analysis['requires_attention'] else 'No'}",
            "=" * 50
        ])
        
        return "\n".join(lines)


# Global analyzer instance
_default_analyzer: Optional[LLMAnalyzer] = None


def get_analyzer(knowledge_base_path: str = "./knowledge_base") -> LLMAnalyzer:
    """Get or create the default analyzer instance."""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = LLMAnalyzer(knowledge_base_path)
    return _default_analyzer


def reset_analyzer(knowledge_base_path: str = "./knowledge_base") -> LLMAnalyzer:
    """Reset and create a new analyzer instance."""
    global _default_analyzer
    _default_analyzer = LLMAnalyzer(knowledge_base_path)
    return _default_analyzer
