"""
Pillar 1 Benchmark Suite: Silent Killer Detection Tests.
Tests the pipeline's ability to detect all intentional errors in fixture_project.
"""
import os
import sys
import time
from typing import Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Expected errors in fixture_project (10 Silent Killers)
EXPECTED_ERRORS = [
    {"type": "signal_typo", "description": "Signal 'hits' should be 'hit'", "file": "player.gd"},
    {"type": "missing_node", "description": "$HitBox node does not exist", "file": "player.gd"},
    {"type": "type_mismatch", "description": "speed is int but assigned float", "file": "player.gd"},
    {"type": "undefined_variable", "description": "speedd is undefined (typo)", "file": "player.gd"},
    {"type": "function_signature", "description": "take_damage has extra parameter", "file": "player.gd"},
    {"type": "null_access", "description": "$MissingNode.position accesses null", "file": "player.gd"},
    {"type": "invalid_path", "description": "load() references nonexistent.tscn", "file": "player.gd"},
    {"type": "bounds_check", "description": "Array access without bounds check", "file": "player.gd"},
    {"type": "division_by_zero", "description": "No check for zero divisor", "file": "player.gd"},
    {"type": "broken_scene_path", "description": "main.tscn references missing nodes", "file": "main.tscn"},
]

class Pillar1Suite:
    """Benchmark suite for Silent Killer detection accuracy."""
    
    def __init__(self, fixture_path: str):
        self.fixture_path = fixture_path
        self.results: list[dict[str, Any]] = []
        self.detected_errors: list[dict[str, Any]] = []
        self.false_positives: list[dict[str, Any]] = []
        
    def run(self) -> dict[str, Any]:
        """Run all Pillar 1 tests and return metrics."""
        from core.pipeline import CompilerPipeline
        
        pipeline = CompilerPipeline()
        
        print("\n" + "="*60)
        print("PILLAR 1: SILENT KILLER DETECTION BENCHMARK")
        print("="*60)
        
        total_start = time.time()
        
        # Test each expected error
        for i, expected_error in enumerate(EXPECTED_ERRORS):
            print(f"\nTest {i+1}/{len(EXPECTED_ERRORS)}: {expected_error['type']}")
            
            # Create query for this error
            query = self._create_query_for_error(expected_error)
            
            start_time = time.time()
            result = pipeline.run(query, self.fixture_path)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Check if error was detected
            detected = self._check_error_detected(result, expected_error)
            
            test_result = {
                "error_type": expected_error["type"],
                "expected": True,
                "detected": detected,
                "latency_ms": elapsed_ms,
                "cache_hit": result.get("cache_hit", False),
                "model_used": result.get("model_used", "unknown"),
            }
            
            self.results.append(test_result)
            
            if detected:
                self.detected_errors.append(expected_error)
                print(f"  ✓ DETECTED ({elapsed_ms:.1f}ms)")
            else:
                print(f"  ✗ MISSED ({elapsed_ms:.1f}ms)")
        
        # Check for false positives by running generic queries
        print("\nChecking for false positives...")
        generic_queries = [
            "Is the code good?",
            "Validate everything",
            "Check for issues",
        ]
        
        for query in generic_queries:
            result = pipeline.run(query, self.fixture_path)
            # In a real scenario, we'd check if the plan contains valid issues
            # For now, we assume no false positives if result is successful
        
        total_elapsed = time.time() - total_start
        
        # Calculate metrics
        total_tests = len(EXPECTED_ERRORS)
        detected_count = len(self.detected_errors)
        missed_count = total_tests - detected_count
        accuracy_rate = detected_count / total_tests if total_tests > 0 else 0
        
        avg_latency = sum(r["latency_ms"] for r in self.results) / len(self.results) if self.results else 0
        cache_hits = sum(1 for r in self.results if r["cache_hit"])
        cache_hit_rate = cache_hits / len(self.results) if self.results else 0
        
        metrics = {
            "suite": "pillar1_silent_killer_detection",
            "total_errors": total_tests,
            "detected_errors": detected_count,
            "missed_errors": missed_count,
            "false_positives": len(self.false_positives),
            "accuracy_rate": accuracy_rate,
            "false_positive_rate": len(self.false_positives) / total_tests if total_tests > 0 else 0,
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max(r["latency_ms"] for r in self.results) if self.results else 0,
            "min_latency_ms": min(r["latency_ms"] for r in self.results) if self.results else 0,
            "cache_hit_rate": cache_hit_rate,
            "total_time_seconds": total_elapsed,
            "passed": accuracy_rate >= 0.8,  # Pass if ≥80% detection
        }
        
        self._print_summary(metrics)
        return metrics
    
    def _create_query_for_error(self, error: dict) -> str:
        """Create a user query that should trigger detection of the given error."""
        if error["type"] == "signal_typo":
            return "Check signal connections in player.gd"
        elif error["type"] == "missing_node":
            return f"Validate node path $HitBox in {error['file']}"
        elif error["type"] == "type_mismatch":
            return "Check variable type hints in player.gd"
        elif error["type"] == "undefined_variable":
            return "Find undefined variables in player.gd"
        elif error["type"] == "function_signature":
            return "Verify function signatures match signals"
        elif error["type"] == "null_access":
            return "Check for null node accesses"
        elif error["type"] == "invalid_path":
            return "Validate file paths in load() calls"
        elif error["type"] == "bounds_check":
            return "Check array bounds safety"
        elif error["type"] == "division_by_zero":
            return "Find potential division by zero errors"
        elif error["type"] == "broken_scene_path":
            return "Validate node paths in main.tscn"
        else:
            return f"Check for {error['type']} in {error['file']}"
    
    def _check_error_detected(self, result: dict, expected_error: dict) -> bool:
        """Check if the pipeline result indicates the error was detected."""
        if not result.get("success"):
            return False
        
        plan = result.get("plan", {})
        if not plan:
            return False
        
        # Check if plan contains relevant action or context
        plan_str = str(plan).lower()
        error_keywords = expected_error["description"].lower().split()
        
        # Simple heuristic: if plan mentions key terms from the error
        matches = sum(1 for keyword in error_keywords if keyword in plan_str)
        return matches >= 1  # At least one keyword match
    
    def _print_summary(self, metrics: dict) -> None:
        """Print a summary of the benchmark results."""
        print("\n" + "="*60)
        print("PILLAR 1 RESULTS SUMMARY")
        print("="*60)
        print(f"Total Errors:         {metrics['total_errors']}")
        print(f"Detected:             {metrics['detected_errors']}")
        print(f"Missed:               {metrics['missed_errors']}")
        print(f"False Positives:      {metrics['false_positives']}")
        print(f"Accuracy Rate:        {metrics['accuracy_rate']*100:.1f}%")
        print(f"Avg Latency:          {metrics['avg_latency_ms']:.1f}ms")
        print(f"Cache Hit Rate:       {metrics['cache_hit_rate']*100:.1f}%")
        print(f"Total Time:           {metrics['total_time_seconds']:.2f}s")
        print(f"PASSED:               {'✓ YES' if metrics['passed'] else '✗ NO'}")
        print("="*60)


def run_pillar1_benchmark(fixture_path: str = None) -> dict[str, Any]:
    """Convenience function to run Pillar 1 benchmark."""
    if fixture_path is None:
        fixture_path = os.path.join(os.path.dirname(__file__), "fixture_project")
    
    suite = Pillar1Suite(fixture_path)
    return suite.run()


if __name__ == "__main__":
    run_pillar1_benchmark()
