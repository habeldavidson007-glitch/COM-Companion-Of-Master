"""
Intent Router: Two-stage classification (Keyword + LLM Tie-Breaker) with Wiki Integration
Handles ambiguous queries like "make a godot asset spreadsheet".
Routes signals to appropriate expert modules and harnesses.
"""

MODES = {
    "GODOT":  ["godot", "gdscript", "game", "scene", "node",
               "physics", "animation", "script", "player", "asset"],
    "OFFICE": ["excel", "pdf", "ppt", "spreadsheet", "report",
               "dokumen", "laporan", "buat file", "tabel", "save"],
    "CPP":    ["c++", "cpp", "cplusplus", "header", "cmake", 
               "smart pointer", "template", "std::"],
    "PYTHON": ["python", "py", "script", "pip", "package", "module"],
    "JAVASCRIPT": ["javascript", "js", "typescript", "ts", "react", 
                   "node", "npm", "browser", "dom", "async"],
    "JSON":   ["json", "schema", "parse json", "validate json", "api response"],
    "DESKTOP":["file", "folder", "browser", "clipboard", "screenshot",
               "open", "create", "delete", "copy", "move"],
    "WIKI":   ["wiki", "knowledge", "document", "explain", "concept",
               "what is", "how to", "tutorial", "guide"],
    "GENERAL": []
}

# Signal prefixes for routing to harnesses
SIGNAL_PREFIXES = {
    "GODOT": "@GODOT:",
    "OFFICE": "@OFFICE:",
    "CPP": "@CPP:",
    "PYTHON": "@PYTHON:",
    "JAVASCRIPT": "@JS:",
    "JSON": "@JSON:",
    "DESKTOP": "@DESK:",
    "WIKI": "@WIKI:"
}


class IntentRouter:
    """
    Two-stage classification with Wiki integration:
    Stage 1: Keyword fast-path
    Stage 2: If ambiguous (2+ modes match), ask LLM for 1-token classification
    Stage 3: Route to appropriate harness/expert with signal format
    """
    
    AMBIGUOUS_THRESHOLD = 2
    ROUTER_PROMPT = """Classify this input into exactly one word: GODOT, OFFICE, CPP, PYTHON, JAVASCRIPT, JSON, DESKTOP, WIKI, or GENERAL.
Input: {query}
Reply with one word only."""

    def __init__(self, client=None, wiki_indexer=None):
        self.client = client
        self.wiki_indexer = wiki_indexer
        self.signal_history = []
    
    def route(self, query: str) -> dict:
        """
        Route query to appropriate harness/expert.
        Returns dict with mode, signal, and confidence.
        """
        matches = []
        text = query.lower()
        
        # Stage 1: Keyword Matching
        for mode, keywords in MODES.items():
            if mode == "GENERAL":
                continue
            if any(k in text for k in keywords):
                matches.append(mode)
        
        # Clear cases
        if len(matches) == 1:
            mode = matches[0]
            confidence = "high"
        elif len(matches) == 0:
            mode = "GENERAL"
            confidence = "low"
        else:
            # Ambiguous case: Use LLM tie-breaker
            if self.client:
                try:
                    result = self.client.generate(
                        [{"role": "user", 
                          "content": self.ROUTER_PROMPT.format(query=query)}],
                        max_tokens=4,
                        temperature=0.0
                    ).strip().upper()
                    
                    if result in MODES.keys():
                        mode = result
                        confidence = "medium"
                    else:
                        mode = matches[0]
                        confidence = "fallback"
                except Exception:
                    mode = matches[0]
                    confidence = "fallback"
            else:
                mode = matches[0]
                confidence = "fallback"
        
        # Generate signal
        signal_prefix = SIGNAL_PREFIXES.get(mode, "@GENERAL:")
        signal = f"{signal_prefix}{query}"
        
        # Store in history
        self.signal_history.append({
            "query": query,
            "mode": mode,
            "signal": signal,
            "confidence": confidence
        })
        
        return {
            "mode": mode,
            "signal": signal,
            "confidence": confidence,
            "matches": matches if len(matches) > 1 else []
        }
    
    def route_with_wiki(self, query: str) -> dict:
        """
        Enhanced routing with wiki lookup for knowledge-based queries.
        """
        # First check if it's a wiki query
        wiki_keywords = ["what is", "explain", "concept", "define", "meaning", "how does"]
        is_wiki_query = any(kw in query.lower() for kw in wiki_keywords)
        
        if is_wiki_query and self.wiki_indexer:
            # Search wiki first
            wiki_results = self.wiki_indexer.search(query, top_k=3)
            
            if wiki_results and len(wiki_results) > 0:
                return {
                    "mode": "WIKI",
                    "signal": f"@WIKI:{query}",
                    "confidence": "high",
                    "wiki_results": wiki_results,
                    "action": "retrieve_and_synthesize"
                }
        
        # Fall back to standard routing
        return self.route(query)
    
    def parse_signal(self, signal: str) -> dict:
        """
        Parse a COM signal string into structured format.
        Example: "@DESK:open_browser:https://example.com"
        """
        if not signal.startswith("@"):
            return {"error": "Invalid signal format", "signal": signal}
        
        parts = signal.split(":", 2)
        
        if len(parts) < 2:
            return {"error": "Incomplete signal", "signal": signal}
        
        harness = parts[0][1:]  # Remove @ prefix
        action_or_payload = parts[1] if len(parts) > 1 else ""
        payload = parts[2] if len(parts) > 2 else ""
        
        return {
            "harness": harness,
            "action": action_or_payload,
            "payload": payload,
            "full_signal": signal
        }
    
    def get_routing_stats(self) -> dict:
        """Get statistics about routing decisions."""
        if not self.signal_history:
            return {"total": 0, "message": "No signals routed yet"}
        
        mode_counts = {}
        confidence_counts = {}
        
        for entry in self.signal_history:
            mode = entry["mode"]
            confidence = entry["confidence"]
            
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        return {
            "total": len(self.signal_history),
            "by_mode": mode_counts,
            "by_confidence": confidence_counts,
            "recent_signals": self.signal_history[-10:]
        }
