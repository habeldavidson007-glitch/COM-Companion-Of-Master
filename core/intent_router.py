"""
Intent Router: Weighted keyword scoring with LLM tie-breaker
Handles ambiguous queries like "make a godot asset spreadsheet".
"""

# Mode definitions with priority weights
# Higher weight = higher priority when keywords overlap
MODES = {
    "GODOT":  {
        "keywords": ["godot", "gdscript", "game", "scene", "node",
                     "physics", "animation", "script", "player", "asset"],
        "weight": 1.0
    },
    "OFFICE": {
        "keywords": ["excel", "pdf", "ppt", "spreadsheet", "report",
                     "dokumen", "laporan", "buat file", "tabel", "save"],
        "weight": 1.5  # Office tools get slight priority for file operations
    },
    "GENERAL": {"keywords": [], "weight": 0}
}

class IntentRouter:
    """
    Stage 1: Weighted keyword scoring (not first-match)
    Stage 2: if scores are tied (within threshold), ask LLM for 1-token classification
    """
    
    TIE_THRESHOLD = 0.3  # If score difference is less than this, use LLM tie-breaker
    ROUTER_PROMPT = """Classify this input into exactly one word: GODOT, OFFICE, or GENERAL.
Input: {query}
Reply with one word only."""

    def __init__(self, client=None):
        self.client = client

    def _score_mode(self, text: str, mode: str) -> float:
        """Calculate weighted score for a mode based on keyword matches."""
        mode_config = MODES[mode]
        keywords = mode_config["keywords"]
        base_weight = mode_config["weight"]
        
        if not keywords:
            return 0.0
        
        matches = sum(1 for k in keywords if k in text)
        # Score = number of matches * base weight
        return matches * base_weight

    def route(self, query: str) -> str:
        scores = {}
        text = query.lower()
        
        # Stage 1: Weighted Keyword Scoring
        for mode in MODES.keys():
            if mode == "GENERAL":
                continue
            scores[mode] = self._score_mode(text, mode)
        
        # Filter to modes with positive scores
        matched_modes = [(mode, score) for mode, score in scores.items() if score > 0]
        
        # No matches → GENERAL
        if not matched_modes:
            return "GENERAL"
        
        # Single match → return it
        if len(matched_modes) == 1:
            return matched_modes[0][0]
        
        # Multiple matches: sort by score descending
        matched_modes.sort(key=lambda x: x[1], reverse=True)
        best_mode, best_score = matched_modes[0]
        second_mode, second_score = matched_modes[1]
        
        # Check if it's a close tie
        score_diff = best_score - second_score
        
        if score_diff <= self.TIE_THRESHOLD:
            # It's a tie - use LLM tie-breaker
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
            
            # Fallback to highest score if LLM fails or unavailable
            return best_mode
        else:
            # Clear winner by score
            return best_mode
