"""
Intent Router Module - Rule-first routing with LLM fallback.

CRITICAL: This module classifies user input into specific signal types.
Strategy: Rule-based classifier first (regex for "validate", "explain", "refactor").
If rules fail, use a TINY model (via adaptive_router) to classify intent.

Output: Returns the specific SignalSchema type to use.

Architecture Principle: Fast path for common cases, LLM only when needed.
"""

import re
from typing import Optional, Type, Tuple
import sys

try:
    from config import INSTRUCTOR_MAX_RETRIES
except ImportError:
    INSTRUCTOR_MAX_RETRIES = 3

from .signal_schema import (
    SignalSchema,
    ValidateNodePath,
    ExplainError,
    RefactorSafe,
    SCHEMA_REGISTRY,
)
from .wiki_retriever import WikiRetriever, create_default_retriever
from .adaptive_router import AdaptiveRouter


# Rule-based patterns for common intents
INTENT_PATTERNS = {
    "validate_node_path": [
        r"\b(validate|check|verify|test)\s+(node\s+)?path\b",
        r"\b(path\s+is\s+(wrong|correct|valid))\b",
        r"\bget_node\s*\(",
        r"\$[\w/]+",  # Godot shorthand node path
        r"\bnode\s+path\b",
    ],
    "explain_error": [
        r"\b(error|exception|crash|fail|bug)\b",
        r"\b(null instance|nil|undefined)\b",
        r"\b(what does|why|explain|help)\b.*\b(error|message)\b",
        r"Traceback\s+most\s+recent",
        r"\bGodot\s+Runtime\s+Error\b",
    ],
    "refactor_safe": [
        r"\b(refactor|restructure|reorganize|clean\s+up)\b",
        r"\b(extract|move|rename)\s+(function|method|variable)\b",
        r"\b(make\s+(better|cleaner|safer))\b",
        r"\b(optimize|improve)\s+code\b",
    ],
}


class IntentRouter:
    """
    Routes user input to appropriate schema type.
    
    Uses rule-based classification first for speed and determinism.
    Falls back to LLM-based classification only when rules are inconclusive.
    
    Attributes:
        retriever: WikiRetriever for context enrichment.
        router: AdaptiveRouter for LLM fallback classification.
    
    Example:
        >>> router = IntentRouter()
        >>> schema_class, confidence = router.classify("Check if my node path is valid")
        >>> print(schema_class)
        <class 'ValidateNodePath'>
    """
    
    def __init__(
        self,
        client=None,
        retriever: Optional[WikiRetriever] = None,
        adaptive_router: Optional[AdaptiveRouter] = None
    ):
        """
        Initialize the intent router.
        
        Args:
            client: Backward-compatible placeholder (unused).
            retriever: Optional WikiRetriever instance.
            adaptive_router: Optional AdaptiveRouter for LLM fallback.
        """
        self.retriever = retriever or create_default_retriever()
        self.adaptive_router = adaptive_router or AdaptiveRouter()
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> dict:
        """
        Pre-compile regex patterns for efficiency.
        
        Returns:
            Dict mapping intent names to compiled regex patterns.
        """
        compiled = {}
        for intent, patterns in INTENT_PATTERNS.items():
            compiled[intent] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled
    
    def classify(
        self,
        user_input: str
    ) -> Tuple[Optional[Type[SignalSchema]], float, str]:
        """
        Classify user input into a schema type.
        
        Args:
            user_input: User's natural language input.
        
        Returns:
            Tuple of (schema_class, confidence, matched_rule).
            - schema_class: The SignalSchema subclass to use.
            - confidence: Confidence score (0.0 to 1.0).
            - matched_rule: Description of what matched ("rule:*" or "llm").
        
        Logic:
            1. Try rule-based matching first.
            2. If multiple rules match, pick highest confidence.
            3. If no rules match, use LLM fallback.
            4. Return None if classification fails.
        """
        # Try rule-based classification first
        schema_class, confidence, rule = self._classify_by_rules(user_input)
        
        if schema_class is not None and confidence >= 0.7:
            # High confidence rule match - use it
            return schema_class, confidence, f"rule:{rule}"
        
        # Fall back to LLM classification
        schema_class, confidence = self._classify_by_llm(user_input)
        return schema_class, confidence, "llm"
    
    def _classify_by_rules(
        self,
        user_input: str
    ) -> Tuple[Optional[Type[SignalSchema]], float, str]:
        """
        Classify using rule-based pattern matching.
        
        Args:
            user_input: User input text.
        
        Returns:
            Tuple of (schema_class, confidence, matched_pattern_name).
        """
        matches = []
        
        for intent, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(user_input)
                if match:
                    # Calculate confidence based on match quality
                    match_text = match.group()
                    confidence = len(match_text) / len(user_input)
                    confidence = min(1.0, confidence * 1.5)  # Boost slightly
                    matches.append((intent, confidence, pattern.pattern))
        
        if not matches:
            return None, 0.0, ""
        
        # Pick best match
        matches.sort(key=lambda x: x[1], reverse=True)
        best_intent, confidence, pattern = matches[0]
        
        schema_class = SCHEMA_REGISTRY.get(best_intent)
        return schema_class, confidence, pattern[:50]
    
    def _classify_by_llm(
        self,
        user_input: str
    ) -> Tuple[Optional[Type[SignalSchema]], float]:
        """
        Classify using LLM fallback.
        
        Args:
            user_input: User input text.
        
        Returns:
            Tuple of (schema_class, confidence).
        
        Note:
            Uses a tiny model via adaptive_router to minimize RAM usage.
        """
        classification_prompt = f"""Classify this user request into one of these categories:
1. validate_node_path - Checking if a Godot node path exists or is correct
2. explain_error - Understanding an error message or bug
3. refactor_safe - Improving or restructuring code safely

User request: "{user_input}"

Output ONLY the category name (e.g., "validate_node_path")."""

        try:
            messages = [{"role": "user", "content": classification_prompt}]
            response = self.adaptive_router.complete(
                messages,
                temperature=0.0,  # Deterministic for classification
                max_tokens=20
            )
            
            # Parse response
            if hasattr(response, "choices") and response.choices:
                content = response.choices[0].message.content.strip().lower()
                
                # Map response to schema
                for intent, schema_class in SCHEMA_REGISTRY.items():
                    if intent in content:
                        return schema_class, 0.6  # Lower confidence for LLM
            
            # Default fallback
            return ExplainError, 0.3  # Assume error explanation if unclear
            
        except Exception as e:
            print(f"LLM classification failed: {e}", file=sys.stderr)
            return None, 0.0
    
    def route(
        self,
        user_input: str,
        context: Optional[str] = None
    ) -> Optional[SignalSchema]:
        """
        Full routing pipeline: classify + enrich + create schema.
        
        Args:
            user_input: User's natural language input.
            context: Optional additional context.
        
        Returns:
            SignalSchema instance ready for LLM processing.
            None if classification fails.
        
        Pipeline:
            1. Classify intent
            2. Retrieve relevant wiki snippets
            3. Create schema with enriched context
        """
        # Step 1: Classify
        schema_class, confidence, source = self.classify(user_input)
        
        if schema_class is None:
            return None
        
        # Step 2: Enrich with wiki context
        wiki_snippets = self.retriever.get_snippets(user_input, k=3)
        wiki_context = "\n".join(wiki_snippets) if wiki_snippets else ""
        
        # Step 3: Create schema instance
        full_context = f"{context}\n\nWiki:\n{wiki_context}" if context else wiki_context
        
        schema = schema_class(
            params={"raw_input": user_input},
            context=full_context[:1000],  # Limit context size
            constraints=["Use wiki facts, do not hallucinate"]
        )
        
        return schema


# Convenience function
def route_intent(
    user_input: str,
    context: Optional[str] = None
) -> Optional[SignalSchema]:
    """
    Convenience function for intent routing.
    
    Creates a temporary router and routes the input.
    For repeated use, instantiate IntentRouter directly.
    
    Args:
        user_input: User input text.
        context: Optional additional context.
    
    Returns:
        SignalSchema instance or None.
    """
    router = IntentRouter()
    return router.route(user_input, context)


if __name__ == "__main__":
    # Test the intent router
    print("=" * 50)
    print("Intent Router Test")
    print("=" * 50)
    
    router = IntentRouter()
    
    test_cases = [
        "Check if the node path root/Player is valid",
        "I'm getting an error: Attempt to call on null instance",
        "Refactor this code to be cleaner",
        "What does get_node do?",
        "Help me understand this crash",
    ]
    
    for test_input in test_cases:
        print(f"\nInput: '{test_input}'")
        schema_class, confidence, source = router.classify(test_input)
        print(f"  Schema: {schema_class.__name__ if schema_class else 'None'}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Source: {source}")
    
    print("\n" + "=" * 50)
