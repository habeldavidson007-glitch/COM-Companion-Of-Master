"""
Deterministic LLM Mocks for End-to-End Testing.
Provides reproducible, schema-compliant mock responses for benchmark testing.
"""
import json
import random
from typing import Any, Optional


class DeterministicMockLLM:
    """
    Deterministic mock LLM that returns pre-defined responses based on input patterns.
    Ensures 100% reproducibility for benchmark testing.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.call_count = 0
        self.response_history: list[dict] = []
        
        # Pre-defined valid plans for different query types (matching actual schema registry)
        self.valid_plans = {
            "validate": {
                "action": "validate_node_path",
                "params": {
                    "node_path": "$Player"
                },
                "context": "Validating Godot script for errors",
                "constraints": ["no_file_modification", "read_only"]
            },
            "explain": {
                "action": "explain_error",
                "params": {
                    "error_type": "signal_typo",
                    "file_path": "player.gd",
                    "line_number": 15
                },
                "context": "Explaining detected error with project-aware context",
                "constraints": ["use_project_map", "no_generic_answer"]
            },
            "refactor": {
                "action": "refactor_safe",
                "params": {
                    "target_path": "utils.gd",
                    "changes": [{"type": "rename", "old": "speedd", "new": "speed"}],
                    "impact_scope": ["player.gd"]
                },
                "context": "Safe refactoring with impact analysis",
                "constraints": ["atomic_execution", "rollback_available"]
            },
            "detect": {
                "action": "validate_node_path",
                "params": {
                    "node_path": "$"
                },
                "context": "Full project error detection scan",
                "constraints": ["complete_scan", "no_false_positives"]
            }
        }
        
        # Invalid plans for signal integrity testing
        self.invalid_plans = [
            {},  # Empty dict
            {"intent": "UNKNOWN"},  # Unknown action
            {"action": "VALIDATE"},  # Missing params
            {"action": "maybe_fix_this"},  # Invalid action
            {"action": "VALIDATE", "params": "not_a_dict"},  # Wrong type
            {"action": "EXPLAIN", "params": {}},  # Empty params
            "not_json_at_all",  # Not JSON
            None,  # Null response
        ]
    
    def complete(self, messages: list[dict], temperature: float = 0.2, 
                 max_tokens: int = 512, **kwargs) -> str:
        """
        Generate a deterministic mock response based on input content.
        
        Args:
            messages: List of message dicts with role/content
            temperature: Ignored (always deterministic)
            max_tokens: Ignored
            **kwargs: Additional parameters
            
        Returns:
            JSON string response conforming to schema (or invalid for testing)
        """
        self.call_count += 1
        
        # Extract user input
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "").lower()
                break
        
        # Determine response type based on keywords
        response_key = self._classify_query(user_content)
        
        # Check if we should return invalid response (for signal integrity tests)
        if "invalid" in user_content or "break" in user_content or "fail" in user_content:
            # Return progressively worse invalid responses
            idx = self.call_count % len(self.invalid_plans)
            invalid_response = self.invalid_plans[idx]
            if isinstance(invalid_response, str):
                return invalid_response
            elif invalid_response is None:
                return ""
            else:
                return json.dumps(invalid_response)
        
        # Return valid plan
        plan = self.valid_plans.get(response_key, self.valid_plans["validate"])
        
        # Store for history tracking
        self.response_history.append({
            "call_index": self.call_count,
            "query": user_content[:100],
            "response_type": response_key,
            "plan": plan.copy()
        })
        
        return json.dumps(plan)
    
    def _classify_query(self, query: str) -> str:
        """Classify query to select appropriate mock response."""
        if any(word in query for word in ["validate", "check", "verify"]):
            return "validate"
        elif any(word in query for word in ["explain", "why", "what"]):
            return "explain"
        elif any(word in query for word in ["refactor", "fix", "change", "update"]):
            return "refactor"
        elif any(word in query for word in ["detect", "find", "scan", "error"]):
            return "detect"
        else:
            return "validate"
    
    def get_stats(self) -> dict[str, Any]:
        """Get mock LLM usage statistics."""
        return {
            "total_calls": self.call_count,
            "unique_queries": len(set(r["query"] for r in self.response_history)),
            "response_distribution": self._get_response_distribution()
        }
    
    def _get_response_distribution(self) -> dict[str, int]:
        """Get count of each response type returned."""
        dist = {}
        for record in self.response_history:
            key = record["response_type"]
            dist[key] = dist.get(key, 0) + 1
        return dist
    
    def reset(self):
        """Reset mock state for fresh test run."""
        self.call_count = 0
        self.response_history.clear()
        random.seed(self.seed)


class TokenCountingMockLLM(DeterministicMockLLM):
    """
    Extended mock that tracks token usage for ZERO RE-READ TEST.
    Ensures no repeated file parsing or context loading.
    """
    
    def __init__(self, seed: int = 42):
        super().__init__(seed)
        self.token_counts: list[int] = []
        self.context_hashes: set[str] = set()
        self.repeated_contexts = 0
    
    def complete(self, messages: list[dict], temperature: float = 0.2,
                 max_tokens: int = 512, **kwargs) -> str:
        """Generate response and track token usage."""
        response = super().complete(messages, temperature, max_tokens, **kwargs)
        
        # Estimate token count (rough approximation: 4 chars ≈ 1 token)
        token_count = len(response) // 4
        self.token_counts.append(token_count)
        
        # Track context to detect re-reading
        context_hash = hash(str(messages))
        if context_hash in self.context_hashes:
            self.repeated_contexts += 1
        else:
            self.context_hashes.add(context_hash)
        
        return response
    
    def get_token_stats(self) -> dict[str, Any]:
        """Get token usage statistics."""
        if not self.token_counts:
            return {"total_tokens": 0, "avg_tokens": 0, "repeated_contexts": 0}
        
        return {
            "total_tokens": sum(self.token_counts),
            "avg_tokens": sum(self.token_counts) / len(self.token_counts),
            "min_tokens": min(self.token_counts),
            "max_tokens": max(self.token_counts),
            "call_count": len(self.token_counts),
            "repeated_contexts": self.repeated_contexts,
            "token_trend": "decreasing" if self._is_decreasing() else "stable"
        }
    
    def _is_decreasing(self) -> bool:
        """Check if token usage is decreasing (indicates caching working)."""
        if len(self.token_counts) < 3:
            return False
        # Compare first half avg vs second half avg
        mid = len(self.token_counts) // 2
        first_half_avg = sum(self.token_counts[:mid]) / mid
        second_half_avg = sum(self.token_counts[mid:]) / (len(self.token_counts) - mid)
        return second_half_avg < first_half_avg * 0.9  # 10% reduction threshold


# Global mock instance for easy import
mock_llm = DeterministicMockLLM()
token_mock_llm = TokenCountingMockLLM()


def create_mock_llm(mode: str = "deterministic") -> DeterministicMockLLM:
    """Factory function to create mock LLM instances."""
    if mode == "token_tracking":
        return TokenCountingMockLLM()
    return DeterministicMockLLM()
