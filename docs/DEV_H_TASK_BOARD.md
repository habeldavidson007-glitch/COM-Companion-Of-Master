# Dev H Task Board (No Dev S Overlap)

## Scope Guard (must pass before any task)
- ✅ Allowed: `core/context_compressor.py`, `core/project_intelligence.py`, `core/com_core.py`, `core/session_logger.py`, `tests/test_phase2_token_budget.py`, `tests/test_project_intelligence.py`, `tests/benchmark/runner.py`, `docs/*`.
- ❌ Not allowed (Dev S ownership): parser logic, harness execution semantics, validator policy/rule semantics.

---

## Board Overview

### H1 — Strict Benchmark Gating (Dev H infra)
**Goal:** if any suite crashes, certification cannot be reported as pass.

**File targets:**
- `tests/benchmark/runner.py`
- `benchmark.py`

**Implementation tasks:**
1. Add `--strict` mode.
2. In strict mode, any `suite_crashed > 0` sets `strict_pass=false` and non-zero exit code.
3. Keep old aggregate score, but label as `non_strict_score`.

**Acceptance tests:**
- `python benchmark.py --strict` returns non-zero when one suite crashes.
- Output JSON includes: `strict_pass`, `suite_crashes`, `dependency_errors`, `non_strict_score`.

---

### H2 — Multi-context Token Budget Telemetry
**Goal:** prove token controls are enforced deterministically.

**File targets:**
- `core/context_compressor.py`
- `core/session_logger.py`
- `tests/test_phase2_token_budget.py`

**Implementation tasks:**
1. Extend compressor telemetry return path with:
   - `input_tokens_total`
   - `output_tokens_total`
   - `compression_ratio`
   - `budget_enforced`.
2. Log telemetry per request.
3. Add edge-budget tests (tiny budget, floor collisions, deterministic tie breaks).

**Acceptance tests:**
- `pytest -q tests/test_phase2_token_budget.py`
- Assert deterministic output across repeated runs.
- Assert aggregate output token count `<= max_total_tokens`.

---

### H3 — Project Intelligence Wiring (pre-LLM only)
**Goal:** context comes from indexed facts first, not blind file reads.

**File targets:**
- `core/project_intelligence.py`
- `core/com_core.py`
- `tests/test_project_intelligence.py`

**Implementation tasks:**
1. Add optional `ProjectIntelligence` init in COMCore.
2. For relevant intents, query index and add distilled file facts to prompt context.
3. Add cache-hit counter for indexed retrieval vs raw scan fallback.

**Acceptance tests:**
- `pytest -q tests/test_project_intelligence.py`
- New test: repeated same query increases index-hit path and does not trigger re-index.

---

### H4 — Low-RAM Profile Switch (Phase 3 prep, Dev H-only)
**Goal:** stable operation on 2.5GB available RAM machines.

**File targets:**
- `core/com_core.py`
- `core/ram_monitor.py`
- `core/context_compressor.py`

**Implementation tasks:**
1. Add `LOW_RAM_PROFILE` config flag.
2. Enforce lower `num_ctx`, lower max tokens, and stricter compressor budget under profile.
3. Add warning logs when fallback profile is activated.

**Acceptance tests:**
- Unit test that profile changes runtime limits deterministically.
- Smoke check with profile enabled does not exceed configured budget controls.

---

## Harness “/btw” Side-Question Policy (Dev H UX optimization)
Use self-check prompts from harness only when uncertainty/time-risk is high.

### Trigger conditions
- `route_confidence < 0.55`, or
- elapsed time exceeds 70% of SLA target, or
- expected test pass probability `< 0.80`, or
- deterministic check mismatch detected.

### Message format
Harness appends one short `/btw` line (max 16 words), then continues work:
- `/btw Is this the right way? Running a fast double-check.`
- `/btw This path looks slow; trying a faster route now.`
- `/btw Is this the right solution? Verifying before finalize.`

### Guardrails
- At most 1 `/btw` message per phase step.
- Never ask if confidence ≥ 0.8 and latency risk low.
- Must include follow-up action in same turn (double-check, fallback, or alternate route).

### Probability fields to compute
- `route_confidence` (0..1)
- `latency_risk` (0..1)
- `test_pass_probability` (0..1)
- `final_confidence = weighted(route_confidence, 1-latency_risk, test_pass_probability)`

**Acceptance tests:**
- When any trigger hits threshold, harness emits exactly one `/btw` and runs second check.
- When confidence is high, harness emits no `/btw`.
- Token overhead remains bounded: `/btw` payload < 20 tokens average.

---

## Definition of Done (Dev H)
1. All H1–H4 acceptance tests pass.
2. No file changes in Dev S-owned parser/validator/harness semantics.
3. Benchmark output clearly separates strict vs non-strict pass.
4. `/btw` policy is deterministic, bounded, and test-covered.
