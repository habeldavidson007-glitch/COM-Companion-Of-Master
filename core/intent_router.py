"""
Intent Router: Hierarchical Specificity Scoring with LLM tie-breaker
Handles ambiguous queries like "make a godot asset spreadsheet".
"""

# Mode definitions with priority weights and specificity multipliers
# Higher weight = higher priority when keywords overlap
# Specificity multiplier boosts scores for exact phrase matches
MODES = {
    "GODOT":  {
        "keywords": ["godot", "gdscript", "game", "scene", "node",
                     "physics", "animation", "script", "player", "asset"],
        "weight": 1.0,
        "specificity_multiplier": 2.0,  # Boost for exact phrases like "godot game"
        "phrases": ["godot game", "gdscript script", "game scene", "physics body"]
    },
    "OFFICE": {
        "keywords": ["excel", "pdf", "ppt", "pptx", "spreadsheet", "report",
                     "dokumen", "laporan", "buat file", "tabel", "save",
                     "write a", "create a", "make a", "generate"],
        "weight": 1.5,  # Office tools get slight priority for file operations
        "specificity_multiplier": 2.5,
        "phrases": ["excel spreadsheet", "pdf report", "ppt presentation", "create a pdf", "make a ppt"]
    },
    "PYTHON": {
        "keywords": ["python", "py", "pip", "venv", "virtualenv", "package",
                     "module", "import", "pep8", "flask", "django", "fastapi"],
        "weight": 1.2,
        "specificity_multiplier": 2.0,
        "phrases": ["python script", "python module", "pip install", "virtual environment"]
    },
    "CPP": {
        "keywords": ["c++", "cpp", "header", "namespace", "std::", "compile",
                     "linker", "cmake", "makefile", "pointer", "reference"],
        "weight": 1.2,
        "specificity_multiplier": 2.0,
        "phrases": ["c++ code", "cpp header", "compile error", "cmake build"]
    },
    "WEB": {
        "keywords": ["html", "css", "javascript", "react", "vue", "angular",
                     "nodejs", "express", "api", "rest", "http", "dom"],
        "weight": 1.2,
        "specificity_multiplier": 2.0,
        "phrases": ["html page", "css style", "javascript function", "react component"]
    },
    "WIKI": {
        "keywords": ["wiki", "knowledge", "research", "article", "document", "ingest",
                     "compile", "summarize", "concept", "backlink", "index", "reference",
                     "learn", "study", "paper", "note", "archive"],
        "weight": 1.3,  # Slightly higher than language tools for knowledge tasks
        "specificity_multiplier": 2.5,
        "phrases": ["wiki article", "knowledge base", "research paper", "compile wiki", "ingest document"]
    },
    "GENERAL": {"keywords": [], "weight": 0, "specificity_multiplier": 1.0, "phrases": []}
}

class IntentRouter:
    """
    Stage 1: Weighted keyword scoring (not first-match)
    Stage 2: if scores are tied (within threshold), ask LLM for 1-token classification
    """
    
    TIE_THRESHOLD = 1.5  # If score difference is less than this, use LLM tie-breaker (raised from 0.3)
    ROUTER_PROMPT = """Classify this input into exactly one word: GODOT, OFFICE, PYTHON, CPP, WEB, or GENERAL.
Input: {query}
Reply with one word only."""

    def __init__(self, client=None):
        self.client = client

    def _score_mode(self, text: str, mode: str) -> float:
        """Calculate weighted score for a mode based on keyword matches and phrase specificity."""
        mode_config = MODES[mode]
        keywords = mode_config["keywords"]
        base_weight = mode_config["weight"]
        specificity_multiplier = mode_config.get("specificity_multiplier", 1.0)
        phrases = mode_config.get("phrases", [])
        
        if not keywords:
            return 0.0
        
        # Base score from individual keyword matches
        keyword_matches = sum(1 for k in keywords if k in text)
        base_score = keyword_matches * base_weight
        
        # Bonus for exact phrase matches (hierarchical specificity)
        phrase_bonus = 0.0
        for phrase in phrases:
            if phrase in text:
                phrase_bonus += specificity_multiplier
        
        # Final score = base score + phrase bonus
        return base_score + phrase_bonus

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
                    
                    if result in ("GODOT", "OFFICE", "PYTHON", "CPP", "WEB", "GENERAL"):
                        return result
                except Exception:
                    pass
            
            # Fallback to highest score if LLM fails or unavailable
            return best_mode
        else:
            # Clear winner by score
            return best_mode
