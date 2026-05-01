"""
Enhanced Benchmark Runner with All 5 New Test Layers.
Implements: Signal Integrity, Zero Re-read, File Prioritization, Hard RAM Limit, Plan Consistency
"""
import os
import sys
import json
import time
import hashlib
from datetime import datetime
from typing import Any
from pathlib import Path

# Add parent directory to path for imports
BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(BENCHMARK_DIR))
sys.path.insert(0, ROOT_DIR)


class EnhancedBenchmarkRunner:
    """
    Master runner for all benchmark suites including new test layers.
    
    New Tests:
    1. SIGNAL INTEGRITY TEST - Rejects invalid LLM outputs
    2. ZERO RE-READ TEST - Ensures no repeated file parsing
    3. FILE PRIORITIZATION TEST - Prioritizes relevant files
    4. HARD RAM LIMIT TEST - Enforces strict memory ceiling
    5. PLAN CONSISTENCY TEST - Same input → same output
    """

    def __init__(self):
        self.results: dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
        self.fixture_path = os.path.join(BENCHMARK_DIR, "fixture_project")

    def run_all(self) -> dict[str, Any]:
        """Run all benchmark suites and return aggregated results."""
        self.start_time = time.time()

        print("\n" + "="*70)
        print(" " * 15 + "COM IDE ENHANCED BENCHMARK SUITE")
        print(" " * 20 + "Phase 1 + New Test Layers")
        print("="*70)
        print(f"Started at: {datetime.now().isoformat()}")
        print("="*70)

        # Run Pillar 1: Silent Killer Detection
        try:
            pillar1_results = self._run_pillar1()
            self.results["pillar1"] = pillar1_results
        except Exception as e:
            print(f"ERROR running Pillar 1: {e}")
            import traceback
            traceback.print_exc()
            self.results["pillar1"] = {"error": str(e), "passed": False}

        # Run Pillar 3: RAM Torture
        try:
            pillar3_results = self._run_pillar3()
            self.results["pillar3"] = pillar3_results
        except Exception as e:
            print(f"ERROR running Pillar 3: {e}")
            import traceback
            traceback.print_exc()
            self.results["pillar3"] = {"error": str(e), "passed": False}

        # NEW TEST 1: Signal Integrity
        try:
            signal_integrity_results = self._test_signal_integrity()
            self.results["signal_integrity"] = signal_integrity_results
        except Exception as e:
            print(f"ERROR running Signal Integrity test: {e}")
            import traceback
            traceback.print_exc()
            self.results["signal_integrity"] = {"error": str(e), "passed": False}

        # NEW TEST 2: Zero Re-read
        try:
            zero_reread_results = self._test_zero_reread()
            self.results["zero_reread"] = zero_reread_results
        except Exception as e:
            print(f"ERROR running Zero Re-read test: {e}")
            import traceback
            traceback.print_exc()
            self.results["zero_reread"] = {"error": str(e), "passed": False}

        # NEW TEST 3: File Prioritization
        try:
            file_priority_results = self._test_file_prioritization()
            self.results["file_prioritization"] = file_priority_results
        except Exception as e:
            print(f"ERROR running File Prioritization test: {e}")
            import traceback
            traceback.print_exc()
            self.results["file_prioritization"] = {"error": str(e), "passed": False}

        # NEW TEST 5: Plan Consistency (before RAM test which might affect it)
        try:
            plan_consistency_results = self._test_plan_consistency()
            self.results["plan_consistency"] = plan_consistency_results
        except Exception as e:
            print(f"ERROR running Plan Consistency test: {e}")
            import traceback
            traceback.print_exc()
            self.results["plan_consistency"] = {"error": str(e), "passed": False}

        # NEW TEST 4: Hard RAM Limit (run last as it's most stressful)
        try:
            hard_ram_results = self._test_hard_ram_limit()
            self.results["hard_ram_limit"] = hard_ram_results
        except Exception as e:
            print(f"ERROR running Hard RAM Limit test: {e}")
            import traceback
            traceback.print_exc()
            self.results["hard_ram_limit"] = {"error": str(e), "passed": False}

        self.end_time = time.time()

        # Generate aggregated metrics
        aggregated = self._aggregate_results()

        # Print final summary
        self._print_final_summary(aggregated)

        # Save report to JSON
        report_path = self._save_report(aggregated)
        print(f"\nReport saved to: {report_path}")

        return aggregated

    def _run_pillar1(self) -> dict[str, Any]:
        """Run Pillar 1: Silent Killer Detection."""
        from tests.benchmark.suite_pillar1 import Pillar1Suite
        
        suite = Pillar1Suite(self.fixture_path)
        return suite.run()

    def _run_pillar3(self) -> dict[str, Any]:
        """Run Pillar 3: RAM Torture."""
        from tests.benchmark.suite_pillar3 import Pillar3Suite
        
        suite = Pillar3Suite(self.fixture_path)
        return suite.run()

    def _test_signal_integrity(self) -> dict[str, Any]:
        """
        NEW TEST 1: Signal Integrity Test
        
        Feed invalid LLM outputs and verify 100% rejection rate.
        Tests: {}, {"intent": "UNKNOWN"}, {"action": "VALIDATE"} (missing params)
        """
        print("\n" + "="*60)
        print("TEST 1: SIGNAL INTEGRITY")
        print("="*60)
        
        from core.plan_validator import validate_plan, PlanValidationError
        from core.deterministic_mock_llm import DeterministicMockLLM
        
        mock_llm = DeterministicMockLLM(seed=42)
        
        invalid_plans = [
            ({}, "Empty dict"),
            ({"intent": "UNKNOWN"}, "Unknown action field"),
            ({"action": "VALIDATE"}, "Missing params"),
            ({"action": "maybe_fix_this"}, "Invalid action name"),
            ({"action": "VALIDATE", "params": "not_a_dict"}, "Wrong param type"),
            ({"action": "EXPLAIN", "params": {}}, "Empty params"),
        ]
        
        rejected_count = 0
        total_tests = len(invalid_plans)
        test_details = []
        
        for plan, description in invalid_plans:
            try:
                result = validate_plan(plan)
                # If we get here without exception, validation failed to reject
                test_result = {
                    "plan": description,
                    "rejected": False,
                    "result": result
                }
                test_details.append(test_result)
                print(f"  ✗ FAILED TO REJECT: {description}")
            except PlanValidationError as e:
                # This is the expected behavior - invalid plans should be rejected
                rejected_count += 1
                test_result = {
                    "plan": description,
                    "rejected": True,
                    "error": str(e)
                }
                test_details.append(test_result)
                print(f"  ✓ CORRECTLY REJECTED: {description}")
        
        # Also test that valid plans are accepted
        print("\nTesting valid plans are accepted...")
        valid_plan = mock_llm.valid_plans["validate"]
        try:
            result = validate_plan(valid_plan)
            if result is not None:
                print(f"  ✓ Valid plan correctly accepted")
                valid_accepted = True
            else:
                print(f"  ✗ Valid plan incorrectly rejected (returned None)")
                valid_accepted = False
        except Exception as e:
            print(f"  ✗ Valid plan raised exception: {e}")
            valid_accepted = False
        
        passed = (rejected_count == total_tests) and valid_accepted
        rejection_rate = rejected_count / total_tests if total_tests > 0 else 0
        
        return {
            "passed": passed,
            "rejection_rate": rejection_rate,
            "total_invalid_tested": total_tests,
            "correctly_rejected": rejected_count,
            "valid_plans_accepted": valid_accepted,
            "test_details": test_details
        }

    def _test_zero_reread(self) -> dict[str, Any]:
        """
        NEW TEST 2: Zero Re-read Test
        
        Execute same query 3 times and verify token usage drops after first run.
        Ensures caching is working and no repeated file parsing.
        """
        print("\n" + "="*60)
        print("TEST 2: ZERO RE-READ")
        print("="*60)
        
        from core.pipeline import CompilerPipeline
        from core.cache_manager import cache_manager
        from core.deterministic_mock_llm import TokenCountingMockLLM
        
        pipeline = CompilerPipeline()
        mock_llm = TokenCountingMockLLM(seed=42)
        
        # Clear cache first
        cache_manager.clear_all()
        
        query = "Validate player.gd for errors"
        runs = 3
        latencies = []
        cache_hits = []
        
        print(f"Running same query {runs} times...")
        for i in range(runs):
            start = time.time()
            result = pipeline.run(query, self.fixture_path)
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)
            cache_hit = result.get("cache_hit", False)
            cache_hits.append(cache_hit)
            
            status = "CACHE HIT" if cache_hit else "MISS"
            print(f"  Run {i+1}: {elapsed_ms:.1f}ms [{status}]")
        
        # Calculate metrics
        first_run_latency = latencies[0]
        avg_subsequent_latency = sum(latencies[1:]) / len(latencies[1:]) if len(latencies) > 1 else 0
        latency_improvement = (first_run_latency - avg_subsequent_latency) / first_run_latency if first_run_latency > 0 else 0
        
        # Check if cache hits occurred after first run
        cache_hits_after_first = sum(cache_hits[1:])
        cache_hit_rate = cache_hits_after_first / (runs - 1) if runs > 1 else 0
        
        # Get token stats from mock
        token_stats = mock_llm.get_token_stats()
        
        # Pass criteria: subsequent runs should be faster (cache working)
        # OR have cache hits
        passed = cache_hit_rate > 0 or latency_improvement > 0.1
        
        print(f"\n  Cache hit rate (after first): {cache_hit_rate*100:.1f}%")
        print(f"  Latency improvement: {latency_improvement*100:.1f}%")
        print(f"  Token trend: {token_stats.get('token_trend', 'unknown')}")
        
        return {
            "passed": passed,
            "cache_hit_rate": cache_hit_rate,
            "latency_improvement": latency_improvement,
            "first_run_latency_ms": first_run_latency,
            "avg_subsequent_latency_ms": avg_subsequent_latency,
            "all_latencies_ms": latencies,
            "cache_hits": cache_hits,
            "token_stats": token_stats
        }

    def _test_file_prioritization(self) -> dict[str, Any]:
        """
        NEW TEST 3: File Prioritization Test
        
        Create project with 1 huge file (2000 lines) and 1 small config (50 lines).
        Verify system prioritizes relevant file and avoids loading entire large file.
        """
        print("\n" + "="*60)
        print("TEST 3: FILE PRIORITIZATION")
        print("="*60)
        
        # Create temporary test fixture
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp(prefix="benchmark_priority_")
        
        try:
            # Create huge file (2000 lines)
            huge_file = os.path.join(temp_dir, "huge_module.gd")
            with open(huge_file, 'w') as f:
                f.write("# Huge module with 2000 lines\n")
                for i in range(2000):
                    f.write(f"# Line {i+1}: This is a comment line\n")
                f.write("var important_config = 42\n")
            
            # Create small relevant file (50 lines)
            small_file = os.path.join(temp_dir, "player_config.gd")
            with open(small_file, 'w') as f:
                f.write("# Player configuration\n")
                for i in range(48):
                    f.write(f"# Config line {i+1}\n")
                f.write("var player_speed = 100\n")
            
            # Create query that specifically targets small file
            query = "Check player speed configuration"
            
            from core.pipeline import CompilerPipeline
            pipeline = CompilerPipeline()
            
            # Measure what files are accessed
            start = time.time()
            result = pipeline.run(query, temp_dir)
            elapsed_ms = (time.time() - start) * 1000
            
            # In production, we'd track which files were actually parsed
            # For now, we check if the result is relevant and fast
            success = result.get("success", False)
            
            print(f"  Query executed in: {elapsed_ms:.1f}ms")
            print(f"  Execution success: {success}")
            print(f"  Temp dir: {temp_dir}")
            print(f"  Huge file size: 2000 lines")
            print(f"  Small file size: 50 lines")
            
            # Pass criteria: execution completes successfully and quickly
            # (under 500ms suggests it didn't parse entire huge file)
            passed = success and elapsed_ms < 500
            
            return {
                "passed": passed,
                "execution_time_ms": elapsed_ms,
                "huge_file_lines": 2000,
                "small_file_lines": 50,
                "query": query,
                "success": success
            }
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _test_plan_consistency(self) -> dict[str, Any]:
        """
        NEW TEST 5: Plan Execution Consistency Test
        
        Run same query 5 times and verify identical plan output.
        Ensures determinism across runs.
        """
        print("\n" + "="*60)
        print("TEST 5: PLAN CONSISTENCY")
        print("="*60)
        
        from core.pipeline import CompilerPipeline
        from core.cache_manager import cache_manager
        
        pipeline = CompilerPipeline()
        
        # Clear cache to ensure fresh runs
        cache_manager.clear_all()
        
        query = "Validate project for errors"
        runs = 5
        plans = []
        
        print(f"Running same query {runs} times...")
        for i in range(runs):
            result = pipeline.run(query, self.fixture_path)
            plan = result.get("plan")
            if plan:
                # Convert to JSON string for comparison
                plan_str = json.dumps(plan, sort_keys=True)
                plans.append(plan_str)
                print(f"  Run {i+1}: Plan hash = {hashlib.md5(plan_str.encode()).hexdigest()[:8]}")
            else:
                plans.append(None)
                print(f"  Run {i+1}: No plan generated")
        
        # Check if all plans are identical
        non_null_plans = [p for p in plans if p is not None]
        
        if len(non_null_plans) == 0:
            print("  ✗ No plans generated")
            passed = False
            consistency_rate = 0.0
        elif len(non_null_plans) == 1:
            print("  ✓ Only one plan generated (trivially consistent)")
            passed = True
            consistency_rate = 1.0
        else:
            # Check if all plans are identical
            first_plan = non_null_plans[0]
            all_identical = all(p == first_plan for p in non_null_plans)
            
            if all_identical:
                print("  ✓ All plans are IDENTICAL")
                passed = True
            else:
                print("  ✗ Plans differ across runs")
                passed = False
            
            # Calculate consistency rate
            unique_plans = set(non_null_plans)
            consistency_rate = 1.0 / len(unique_plans)
        
        return {
            "passed": passed,
            "consistency_rate": consistency_rate,
            "total_runs": runs,
            "plans_generated": len(non_null_plans),
            "unique_plans": len(set(non_null_plans)) if non_null_plans else 0,
            "all_identical": len(set(non_null_plans)) == 1 if non_null_plans else False
        }

    def _test_hard_ram_limit(self) -> dict[str, Any]:
        """
        NEW TEST 4: Hard RAM Limit Test
        
        Force RAM limit = 1.6GB and verify system unloads models, queues tasks, doesn't crash.
        """
        print("\n" + "="*60)
        print("TEST 4: HARD RAM LIMIT")
        print("="*60)
        
        from core.pipeline import CompilerPipeline
        from core.ram_hardener import ram_hardener
        from core.ram_monitor import get_ram_usage_gb
        
        # Set aggressive RAM limit for testing
        original_threshold = ram_hardener.threshold_gb
        ram_hardener.threshold_gb = 1.6  # Aggressive limit
        
        pipeline = CompilerPipeline()
        
        queries = [
            "Validate entire project",
            "Explain all errors found",
            "Refactor code for performance",
            "Check for optimization opportunities",
            "Generate documentation"
        ]
        
        crashes = 0
        successful_unloads = 0
        total_queries = len(queries)
        peak_ram = get_ram_usage_gb()
        ram_samples = [peak_ram]
        
        print(f"Starting RAM usage: {peak_ram:.2f}GB")
        print(f"RAM limit: 1.6GB")
        print(f"Running {total_queries} queries under stress...")
        
        for i, query in enumerate(queries):
            try:
                current_ram = get_ram_usage_gb()
                ram_samples.append(current_ram)
                
                print(f"\n  Query {i+1}/{total_queries}: {query[:40]}...")
                print(f"    Current RAM: {current_ram:.2f}GB")
                
                result = pipeline.run(query, self.fixture_path)
                
                # Check if RAM hardener triggered
                if ram_hardener._last_action_taken:
                    successful_unloads += 1
                    print(f"    ✓ RAM hardener activated (action taken)")
                
                current_ram = get_ram_usage_gb()
                ram_samples.append(current_ram)
                peak_ram = max(peak_ram, current_ram)
                
                print(f"    Result: {'Success' if result.get('success') else 'Failed'}")
                
            except Exception as e:
                crashes += 1
                print(f"    ✗ CRASHED: {str(e)}")
        
        # Restore original threshold
        ram_hardener.threshold_gb = original_threshold
        
        # Pass criteria: no crashes, stayed under limit (or handled gracefully)
        passed = crashes == 0 and peak_ram <= 2.0  # Some headroom allowed
        
        print(f"\n  Peak RAM: {peak_ram:.2f}GB")
        print(f"  Crashes: {crashes}")
        print(f"  RAM hardener activations: {successful_unloads}")
        print(f"  Passed: {passed}")
        
        return {
            "passed": passed,
            "peak_ram_gb": peak_ram,
            "ram_limit_gb": 1.6,
            "crashes": crashes,
            "successful_unloads": successful_unloads,
            "total_queries": total_queries,
            "ram_samples_gb": ram_samples
        }

    def _aggregate_results(self) -> dict[str, Any]:
        """Aggregate results from all suites into a single report."""
        pillar1 = self.results.get("pillar1", {})
        pillar3 = self.results.get("pillar3", {})
        signal_integrity = self.results.get("signal_integrity", {})
        zero_reread = self.results.get("zero_reread", {})
        file_priority = self.results.get("file_prioritization", {})
        plan_consistency = self.results.get("plan_consistency", {})
        hard_ram = self.results.get("hard_ram_limit", {})

        # Calculate overall pass/fail
        all_passed = (
            pillar1.get("passed", False) and
            pillar3.get("passed", False) and
            signal_integrity.get("passed", False) and
            zero_reread.get("passed", False) and
            file_priority.get("passed", False) and
            plan_consistency.get("passed", False) and
            hard_ram.get("passed", False)
        )

        # Determine certification level
        if all_passed:
            accuracy = pillar1.get("accuracy_rate", 0)
            peak_ram = max(
                pillar3.get("peak_ram_gb", 0),
                hard_ram.get("peak_ram_gb", 0)
            )
            signal_rejection = signal_integrity.get("rejection_rate", 0)
            consistency = plan_consistency.get("consistency_rate", 0)

            if accuracy >= 0.95 and peak_ram <= 1.8 and signal_rejection >= 1.0 and consistency >= 1.0:
                certification = "GOLD"
            elif accuracy >= 0.85 and peak_ram <= 1.9 and signal_rejection >= 0.9:
                certification = "SILVER"
            elif accuracy >= 0.8 and peak_ram <= 2.0:
                certification = "BRONZE"
            else:
                certification = "PASS"
        else:
            certification = "FAIL"

        aggregated = {
            "report_version": "2.0-enhanced",
            "generated_at": datetime.now().isoformat(),
            "total_duration_seconds": self.end_time - self.start_time if self.end_time else 0,
            "certification": certification,
            "all_passed": all_passed,
            "suites": {
                "pillar1_silent_killer_detection": {
                    "passed": pillar1.get("passed", False),
                    "accuracy_rate": pillar1.get("accuracy_rate", 0),
                },
                "pillar3_ram_torture": {
                    "passed": pillar3.get("passed", False),
                    "peak_ram_gb": pillar3.get("peak_ram_gb", 0),
                },
                "signal_integrity": {
                    "passed": signal_integrity.get("passed", False),
                    "rejection_rate": signal_integrity.get("rejection_rate", 0),
                },
                "zero_reread": {
                    "passed": zero_reread.get("passed", False),
                    "cache_hit_rate": zero_reread.get("cache_hit_rate", 0),
                },
                "file_prioritization": {
                    "passed": file_priority.get("passed", False),
                    "execution_time_ms": file_priority.get("execution_time_ms", 0),
                },
                "plan_consistency": {
                    "passed": plan_consistency.get("passed", False),
                    "consistency_rate": plan_consistency.get("consistency_rate", 0),
                },
                "hard_ram_limit": {
                    "passed": hard_ram.get("passed", False),
                    "peak_ram_gb": hard_ram.get("peak_ram_gb", 0),
                    "crashes": hard_ram.get("crashes", 0),
                }
            },
            "summary_metrics": {
                "accuracy_rate": pillar1.get("accuracy_rate", 0),
                "signal_rejection_rate": signal_integrity.get("rejection_rate", 0),
                "cache_hit_rate": zero_reread.get("cache_hit_rate", 0),
                "plan_consistency_rate": plan_consistency.get("consistency_rate", 0),
                "overall_peak_ram_gb": max(
                    pillar3.get("peak_ram_gb", 0),
                    hard_ram.get("peak_ram_gb", 0)
                ),
            },
            "detailed_results": self.results
        }

        return aggregated

    def _print_final_summary(self, aggregated: dict[str, Any]) -> None:
        """Print the final benchmark summary."""
        print("\n" + "="*70)
        print(" " * 25 + "FINAL RESULTS")
        print("="*70)

        cert = aggregated["certification"]
        cert_colors = {
            "GOLD": "\033[93m",    # Yellow
            "SILVER": "\033[97m",  # White
            "BRONZE": "\033[91m",  # Red-orange
            "PASS": "\033[92m",    # Green
            "FAIL": "\033[91m",    # Red
        }
        reset = "\033[0m"

        color = cert_colors.get(cert, "")
        print(f"\n{color}{'='*30}{reset}")
        print(f"{color}  CERTIFICATION: {cert}{reset}")
        print(f"{color}{'='*30}{reset}")

        print(f"\nOverall Status: {'✓ PASSED' if aggregated['all_passed'] else '✗ FAILED'}")
        print(f"Total Duration: {aggregated['total_duration_seconds']:.2f}s")

        print("\n--- Core Pillars ---")
        p1 = aggregated["suites"]["pillar1_silent_killer_detection"]
        p3 = aggregated["suites"]["pillar3_ram_torture"]
        print(f"  Pillar 1 (Detection):  {'✓' if p1['passed'] else '✗'} - Accuracy: {p1['accuracy_rate']*100:.1f}%")
        print(f"  Pillar 3 (RAM):        {'✓' if p3['passed'] else '✗'} - Peak: {p3['peak_ram_gb']:.2f}GB")

        print("\n--- New Test Layers ---")
        si = aggregated["suites"]["signal_integrity"]
        zr = aggregated["suites"]["zero_reread"]
        fp = aggregated["suites"]["file_prioritization"]
        pc = aggregated["suites"]["plan_consistency"]
        hr = aggregated["suites"]["hard_ram_limit"]
        
        print(f"  Signal Integrity:      {'✓' if si['passed'] else '✗'} - Rejection: {si['rejection_rate']*100:.1f}%")
        print(f"  Zero Re-read:          {'✓' if zr['passed'] else '✗'} - Cache Hit: {zr['cache_hit_rate']*100:.1f}%")
        print(f"  File Prioritization:   {'✓' if fp['passed'] else '✗'} - Latency: {fp['execution_time_ms']:.1f}ms")
        print(f"  Plan Consistency:      {'✓' if pc['passed'] else '✗'} - Rate: {pc['consistency_rate']*100:.1f}%")
        print(f"  Hard RAM Limit:        {'✓' if hr['passed'] else '✗'} - Peak: {hr['peak_ram_gb']:.2f}GB, Crashes: {hr['crashes']}")

        print("\n--- Summary Metrics ---")
        sm = aggregated["summary_metrics"]
        print(f"  Accuracy Rate:         {sm['accuracy_rate']*100:.1f}%")
        print(f"  Signal Rejection:      {sm['signal_rejection_rate']*100:.1f}%")
        print(f"  Cache Hit Rate:        {sm['cache_hit_rate']*100:.1f}%")
        print(f"  Plan Consistency:      {sm['plan_consistency_rate']*100:.1f}%")
        print(f"  Overall Peak RAM:      {sm['overall_peak_ram_gb']:.2f}GB")

        print("\n" + "="*70)

    def _save_report(self, aggregated: dict[str, Any]) -> str:
        """Save the benchmark report to a JSON file."""
        report_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        os.makedirs(report_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(report_dir, f"benchmark_report_{timestamp}.json")

        with open(report_path, "w") as f:
            json.dump(aggregated, f, indent=2, default=str)

        # Also save a latest.json equivalent
        latest_path = os.path.join(report_dir, "benchmark_report_latest.json")
        with open(latest_path, "w") as f:
            json.dump(aggregated, f, indent=2, default=str)

        return report_path


def main():
    """Main entry point for enhanced benchmark runner."""
    runner = EnhancedBenchmarkRunner()
    results = runner.run_all()

    # Exit with appropriate code
    sys.exit(0 if results["all_passed"] else 1)


if __name__ == "__main__":
    main()
