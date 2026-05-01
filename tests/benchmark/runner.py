"""
Master Benchmark Runner for COM IDE.
Runs all benchmark suites and generates a comprehensive report.
"""
import os
import sys
import json
import time
from datetime import datetime
from typing import Any

# Add parent directory to path for imports
BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(BENCHMARK_DIR))
sys.path.insert(0, ROOT_DIR)

class BenchmarkRunner:
    """Master runner for all benchmark suites."""
    
    def __init__(self):
        self.results: dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
        
    def run_all(self) -> dict[str, Any]:
        """Run all benchmark suites and return aggregated results."""
        self.start_time = time.time()
        
        print("\n" + "="*70)
        print(" " * 20 + "COM IDE BENCHMARK SUITE")
        print(" " * 25 + "Phase 1 Validation")
        print("="*70)
        print(f"Started at: {datetime.now().isoformat()}")
        print("="*70)
        
        # Run Pillar 1: Silent Killer Detection
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("suite_pillar1", os.path.join(BENCHMARK_DIR, "suite_pillar1.py"))
            suite_pillar1 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(suite_pillar1)
            print("\n>>> Running Pillar 1 Suite...")
            pillar1_results = suite_pillar1.run_pillar1_benchmark()
            self.results["pillar1"] = pillar1_results
        except Exception as e:
            print(f"ERROR running Pillar 1: {e}")
            import traceback
            traceback.print_exc()
            self.results["pillar1"] = {"error": str(e), "passed": False}
        
        # Run Pillar 3: RAM Torture
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("suite_pillar3", os.path.join(BENCHMARK_DIR, "suite_pillar3.py"))
            suite_pillar3 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(suite_pillar3)
            print("\n>>> Running Pillar 3 Suite...")
            pillar3_results = suite_pillar3.run_pillar3_benchmark()
            self.results["pillar3"] = pillar3_results
        except Exception as e:
            print(f"ERROR running Pillar 3: {e}")
            import traceback
            traceback.print_exc()
            self.results["pillar3"] = {"error": str(e), "passed": False}
        
        self.end_time = time.time()
        
        # Generate aggregated metrics
        aggregated = self._aggregate_results()
        
        # Print final summary
        self._print_final_summary(aggregated)
        
        # Save report to JSON
        report_path = self._save_report(aggregated)
        print(f"\nReport saved to: {report_path}")
        
        return aggregated
    
    def _aggregate_results(self) -> dict[str, Any]:
        """Aggregate results from all suites into a single report."""
        pillar1 = self.results.get("pillar1", {})
        pillar3 = self.results.get("pillar3", {})
        
        # Calculate overall metrics
        all_passed = (
            pillar1.get("passed", False) and 
            pillar3.get("passed", False)
        )
        
        # Determine certification level
        if all_passed:
            accuracy = pillar1.get("accuracy_rate", 0)
            peak_ram = pillar3.get("peak_ram_gb", 999)
            
            if accuracy >= 0.95 and peak_ram <= 1.8:
                certification = "GOLD"
            elif accuracy >= 0.85 and peak_ram <= 1.9:
                certification = "SILVER"
            elif accuracy >= 0.8 and peak_ram <= 2.0:
                certification = "BRONZE"
            else:
                certification = "PASS"
        else:
            certification = "FAIL"
        
        aggregated = {
            "report_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_duration_seconds": self.end_time - self.start_time if self.end_time else 0,
            "certification": certification,
            "all_passed": all_passed,
            "suites": {
                "pillar1_silent_killer_detection": {
                    "passed": pillar1.get("passed", False),
                    "accuracy_rate": pillar1.get("accuracy_rate", 0),
                    "false_positive_rate": pillar1.get("false_positive_rate", 0),
                    "avg_latency_ms": pillar1.get("avg_latency_ms", 0),
                    "cache_hit_rate": pillar1.get("cache_hit_rate", 0),
                },
                "pillar3_ram_torture": {
                    "passed": pillar3.get("passed", False),
                    "peak_ram_gb": pillar3.get("peak_ram_gb", 0),
                    "success_rate": pillar3.get("success_rate", 0),
                    "crashes": pillar3.get("crashes", 0),
                    "model_switches": pillar3.get("model_switches", 0),
                }
            },
            "summary_metrics": {
                "accuracy_rate": pillar1.get("accuracy_rate", 0),
                "false_positive_rate": pillar1.get("false_positive_rate", 0),
                "peak_ram_gb": pillar3.get("peak_ram_gb", 0),
                "avg_latency_ms": (
                    pillar1.get("avg_latency_ms", 0) + pillar3.get("avg_latency_ms", 0)
                ) / 2,
                "cache_hit_rate": pillar1.get("cache_hit_rate", 0),
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
        
        print("\n--- Pillar 1: Silent Killer Detection ---")
        p1 = aggregated["suites"]["pillar1_silent_killer_detection"]
        print(f"  Passed:       {'✓' if p1['passed'] else '✗'}")
        print(f"  Accuracy:     {p1['accuracy_rate']*100:.1f}%")
        print(f"  False Pos:    {p1['false_positive_rate']*100:.1f}%")
        print(f"  Avg Latency:  {p1['avg_latency_ms']:.1f}ms")
        print(f"  Cache Hit:    {p1['cache_hit_rate']*100:.1f}%")
        
        print("\n--- Pillar 3: RAM Torture ---")
        p3 = aggregated["suites"]["pillar3_ram_torture"]
        print(f"  Passed:       {'✓' if p3['passed'] else '✗'}")
        print(f"  Peak RAM:     {p3['peak_ram_gb']:.2f}GB")
        print(f"  Success Rate: {p3['success_rate']*100:.1f}%")
        print(f"  Crashes:      {p3['crashes']}")
        print(f"  Model Switch: {p3['model_switches']}")
        
        print("\n--- Summary Metrics ---")
        sm = aggregated["summary_metrics"]
        print(f"  Accuracy Rate:     {sm['accuracy_rate']*100:.1f}%")
        print(f"  False Positive:    {sm['false_positive_rate']*100:.1f}%")
        print(f"  Peak RAM:          {sm['peak_ram_gb']:.2f}GB")
        print(f"  Avg Latency:       {sm['avg_latency_ms']:.1f}ms")
        print(f"  Cache Hit Rate:    {sm['cache_hit_rate']*100:.1f}%")
        
        print("\n" + "="*70)
    
    def _save_report(self, aggregated: dict[str, Any]) -> str:
        """Save the benchmark report to a JSON file."""
        report_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(report_dir, f"benchmark_report_{timestamp}.json")
        
        with open(report_path, "w") as f:
            json.dump(aggregated, f, indent=2, default=str)
        
        # Also save a latest.json symlink equivalent
        latest_path = os.path.join(report_dir, "benchmark_report_latest.json")
        with open(latest_path, "w") as f:
            json.dump(aggregated, f, indent=2, default=str)
        
        return report_path


def main():
    """Main entry point for benchmark runner."""
    runner = BenchmarkRunner()
    results = runner.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if results["all_passed"] else 1)


if __name__ == "__main__":
    main()
