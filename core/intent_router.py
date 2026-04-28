"""
Intent Router: Two-stage classification (Keyword + LLM Tie-Breaker)
Handles ambiguous queries like "make a godot asset spreadsheet".
"""

MODES = {
    "GODOT":  ["godot", "gdscript", "game", "scene", "node",
               "physics", "animation", "script", "player", "asset"],
    "OFFICE": ["excel", "pdf", "ppt", "spreadsheet", "report",
               "dokumen", "laporan", "buat file", "tabel", "save"],
    "GENERAL": []
}

class IntentRouter:
    """
    Stage 1: keyword fast-path
    Stage 2: if ambiguous (2+ modes match), ask LLM for 1-token classification
    """
    
    AMBIGUOUS_THRESHOLD = 2
    ROUTER_PROMPT = """Classify this input into exactly one word: GODOT, OFFICE, or GENERAL.
Input: {query}
Reply with one word only."""

    def __init__(self, client=None):
        self.client = client

    def route(self, query: str) -> str:
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
            return matches[0]
        elif len(matches) == 0:
            return "GENERAL"
        
        # Ambiguous case: Use LLM tie-breaker
        else:
            if self.client:
                try:
                    result = self.client.generate(
                        [{"role": "user", 
                          "content": self.ROUTER_PROMPT.format(query=query)}],
                        max_tokens=4,
                        temperature=0.0
                    ).strip().upper()
                    
                    if result in ("GODOT", "OFFICE", "GENERAL"):
                        return result
                except Exception:
                    pass
            
            # Fallback to first match if LLM fails or unavailable
            return matches[0]
