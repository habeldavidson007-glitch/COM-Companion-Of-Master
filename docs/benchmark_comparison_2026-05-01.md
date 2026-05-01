# GOLDEN_BENCHMARK comparison report (2026-05-01)

## Scope
This report compares:
1. Your provided architecture-level simulated review.
2. An actual local execution of the current benchmark harness (`python benchmark.py`) on `master`.

## Actual run summary (local)
- Command run: `python benchmark.py`
- Environment date: 2026-05-01
- Python: 3.10.19

Observed outcomes:
- Benchmark runner completed and wrote `benchmark_results.json`.
- Passing suites:
  - 02 Signal Parser: 14/14 (100%)
  - 04 Wiki Indexer: 8/8 (100%)
- Partially failing suite:
  - 07 Tool Harness: 6/9 (66.7%)
- Multiple suites crashed due to missing runtime dependency:
  - `ModuleNotFoundError: No module named 'pydantic'` in suites 01, 05, 06, 08, 09, 10.
- Reported overall score from runner: 28/31 (90.3%), but this excludes crashed suites and therefore overstates readiness.

## Direct comparison to your simulated review

### Where your review matches the executed benchmark signal
- **Determinism / enforcement risk is real:** missing strict gate confidence is consistent with the inability to complete schema-dependent suites because required validation stack (`pydantic`) is unavailable in this environment.
- **T-shaped routing still uneven:** Tool harness surfaced alias and parallel-execution issues (`@GDT` alias and parallel signal failure), consistent with your “good structure, weak enforcement” observation.
- **Benchmark automation gap exists:** current benchmark produces a summary even when major suites crash; this aligns with your point that measurement needs stricter reproducibility and pass/fail governance.

### Where your review cannot yet be confirmed from this run
- **2GB RAM law, latency targets, and starvation behavior** are not validated by this specific run because benchmark execution is blocked early by missing dependencies and does not execute full resource stress checks.
- **Context-aware explanation quality** is not meaningfully scored from this run due to suite crashes in core pipeline paths.

## Practical conclusion
Your “Silver but unstable” judgment is directionally consistent with the executable evidence. The highest-confidence finding from the real run is:
- The benchmark harness currently allows an optimistic aggregate score despite hard suite crashes.

That means the most immediate action is not adding more claims, but making benchmark gating stricter:
- Treat any crashed suite as a global benchmark failure.
- Separate “environment dependency missing” from “product logic failure” in the final verdict.
- Promote deterministic validation checks (invalid plan rejection, unknown intent rejection) to mandatory red-line tests.

## Recommended next benchmark hardening steps
1. Add a strict runner mode: fail overall if any suite crashes.
2. Add the five tests you proposed as first-class automated cases:
   - Signal integrity rejection test.
   - Zero re-read/cache reuse test.
   - File prioritization test.
   - Hard RAM limit test.
   - Plan execution consistency test.
3. Emit machine-readable artifact fields for:
   - `suite_crashes`
   - `dependency_errors`
   - `strict_pass` (boolean)
   - `certification_level` only when strict pass is true.
