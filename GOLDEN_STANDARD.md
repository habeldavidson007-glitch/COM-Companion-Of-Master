# 🏆 COM IDE: Golden Standard & Execution Plan v5.0

> **"The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that already thinks better even with small models. The limit is only your imagination."**

---

## 🎯 Executive Summary

**COM IDE** is not a chatbot. It is a **Compiler-AI Hybrid** that combines deterministic static analysis with LLM-powered planning.

**The Revolution:**
- **Old Way:** `User → LLM → Text` (Hallucination-prone, RAM-heavy, non-deterministic)
- **COM Way:** `Parse → Retrieve → LLM(Plan) → Execute` (Zero hallucination on facts, 2GB RAM compliant, fully traceable)

**Target Hardware:** 2GB RAM machines (potato laptops).
**Target Domain:** Polyglot expert (Python, JS, C++, etc.) with **Godot Super-Intelligence**.

---

## 🏗️ Architecture: The Compiler-Lite Pipeline

```
User Input
   ↓
[1] Signal Parser (Rule-Based, NO LLM)
   - Strips noise, extracts intent keywords
   - Latency: <10ms
   ↓
[2] Intent Router (Rule-First, LLM Fallback)
   - 80% resolved via rules (saves RAM)
   - 20% complex queries → LLM for classification
   ↓
[3] Wiki Retriever (Context Enrichment)
   - Fetches project map + docs BEFORE LLM
   - Reduces token count by 60%
   ↓
[4] LLM (SINGLE PASS ONLY)
   - Generates JSON Execution Plan (IR)
   - Model: smollm2:1.7b (default), qwen2.5-coder:7b (on-demand)
   - Constraint: ≤512 tokens context
   ↓
[5] Harness Executor (Deterministic)
   - Executes plan atomically
   - No LLM involved here
   ↓
[6] Output Formatter (Rule-Based)
   - Returns result to user
   - NO summarization step (saves latency/RAM)
```

### Key Constraints
1. **LLM appears ONCE** – Only to generate the execution plan.
2. **Wiki BEFORE LLM** – Context enriches the prompt, doesn't come after.
3. **Strict Signal Schema** – All internal communication is validated JSON.
4. **No Summarization** – Harness output is final.

---

## 📐 Signal Schema v1.0 (Frozen)

Every internal request MUST conform to this schema. Changing this requires full system refactoring.

```json
{
  "intent": "VALIDATE_NODE_PATH",
  "target": {
    "type": "node_path",
    "value": "$Player"
  },
  "context": {
    "file": "player.gd",
    "line": 42,
    "scene": "main.tscn",
    "project_root": "/home/user/game"
  },
  "constraints": {
    "strict": true,
    "suggest_similar": true,
    "max_latency_ms": 100
  },
  "expected_output": "validation_report"
}
```

### Schema Enforcement
- **Invalid JSON?** → Return error immediately, do not retry LLM.
- **Missing fields?** → Reject at router level.
- **Hallucinated target?** → Parser verifies existence before execution.

---

## 🔥 The 7 Pillars of Excellence (Benchmark Summary)

COM IDE must pass these 7 stress tests to be considered "Gold Certified".

| Pillar | Goal | Target Metric |
|--------|------|---------------|
| **1. Silent Killer Detection** | Catch errors pre-runtime | 100% detection, 0 FP, <100ms |
| **2. Context-Aware Explanation** | Plain English error decoding | References specific file/line/node |
| **3. 2GB RAM Law** | Run on potato laptops | Peak ≤2.0GB, auto-unload idle models |
| **4. T-Shaped Intelligence** | Polyglot generalist, Godot god | Project-aware answers for Godot only |
| **5. Deterministic Core** | Zero hallucination on facts | 100% accuracy on structural queries |
| **6. Refactor Safety Net** | Atomic changes with ripple analysis | Human trust ≥9/10 for auto-fix |
| **7. Flow State Latency** | Invisible assistance | <100ms real-time, <2s deep scan |

*See `GOLDEN_BENCHMARK.md` for full test suites, torture chambers, and scoring protocols.*

---

## 📂 Repository Structure (Golden Standard)

```
/workspace/
├── core/                      # THE BRAIN (Developer H)
│   ├── signal_schema.py       # Frozen v1.0 schema validator
│   ├── intent_router.py       # Rule-first routing logic
│   ├── ram_monitor.py         # Memory safety, auto-unload
│   ├── context_compressor.py  # Token reduction (<512)
│   └── prompts/               # Compiler-stage prompts
│
├── tools/                     # THE HANDS (Developer S)
│   ├── godot/                 # Godot Specialist Module
│   │   ├── scene_parser.py    # .tscn parser
│   │   ├── script_parser.py   # .gd extractor
│   │   ├── project_map.py     # Cross-reference engine
│   │   ├── log_watcher.py     # Error explanation pipeline
│   │   └── specialist.py      # High-level Godot API
│   │
│   ├── languages/             # Polyglot Experts (Python, JS, etc.)
│   ├── data_ops/              # Wiki compiler, indexer
│   └── tool_harness.py        # Deterministic executor
│
├── tests/                     # Benchmark Fixtures
│   ├── fixture_project/       # Spaghetti scene, injected errors
│   ├── harness_runner.py      # Automated test suite
│   └── human_eval_scripts/    # Survey forms for devs
│
├── config.py                  # Model configs, RAM limits
├── com_chat.py                # Entry point
└── GOLDEN_STANDARD.md         # This document
```

### Cleanup List (Delete Immediately)
- `node_modules/`, `package.json` (accidental Node.js artifacts)
- `benchmark and test review/`, `benchmark_results.json` (legacy)
- `tools/languages/` (if unused, defer to Phase 2)
- All `__pycache__/` directories
- Any `.xlsx` test files

---

## 👥 Division of Labor (Professional Split)

### Developer H (You) – Core Architect
**Focus:** The Brain, Memory Safety, Schema Integrity.

| Task | File | Priority |
|------|------|----------|
| **Signal Schema v1.0** | `core/signal_schema.py` | 🔴 CRITICAL (Day 1) |
| **Intent Router** | `core/intent_router.py` | 🔴 CRITICAL (Day 2-3) |
| **RAM Monitor** | `core/ram_monitor.py` | 🟠 HIGH (Day 4) |
| **Context Compressor** | `core/context_compressor.py` | 🟠 HIGH (Day 5) |
| **LLM Prompts** | `core/prompts/compiler_prompt.txt` | 🟠 HIGH (Day 5) |
| **Bug Fix: @GDT Alias** | `tools/tool_harness.py` | 🟠 HIGH (Immediate) |
| **Bug Fix: Wiki Truncation** | `tools/data_ops/wiki_compiler.py` | 🟠 HIGH (Immediate) |
| **Test Harness** | `tests/harness_runner.py` | 🟡 MED (Week 2) |

**Success Metric:** Schema validation passes 100%, RAM stays <1.2GB base.

---

### Developer S (Friend) – Domain Specialist
**Focus:** Godot Parsing, Project Mapping, Error Detection.

| Task | File | Priority |
|------|------|----------|
| **Scene Parser** | `tools/godot/scene_parser.py` | 🔴 CRITICAL (Day 1-2) |
| **Script Parser** | `tools/godot/script_parser.py` | 🔴 CRITICAL (Day 2-3) |
| **Project Map** | `tools/godot/project_map.py` | 🔴 CRITICAL (Day 4) |
| **Log Watcher** | `tools/godot/log_watcher.py` | 🟠 HIGH (Day 5-6) |
| **Godot Specialist** | `tools/godot/specialist.py` | 🟠 HIGH (Week 2) |
| **Unit Tests** | `tools/godot/test_*.py` | 🟡 MED (Ongoing) |
| **Fixture Project** | `tests/fixture_project/` | 🟡 MED (Week 2) |

**Success Metric:** Node path validation 100% accurate, <100ms latency.

---

## 📅 4-Week Phase 1 Sprint Plan

### Week 1: Foundation (Schema + Parsers)
- **Dev H:** Freeze `signal_schema.py`, implement `intent_router.py`.
- **Dev S:** Build `scene_parser.py`, `script_parser.py`.
- **Milestone:** Can parse a .tscn and .gd file, output valid JSON plan.

### Week 2: Knowledge & Validation (Wiki + Node Checks)
- **Dev H:** Wire `WikiRetriever` BEFORE LLM, fix truncation bug.
- **Dev S:** Build `project_map.py`, implement node path validation.
- **Milestone:** Detects `$Player` → `$PlayerCharacter` rename correctly.

### Week 3: RAM Safety & Execution (Monitor + Pipeline)
- **Dev H:** Implement `ram_monitor.py`, model hot-swap logic.
- **Dev S:** Build `log_watcher.py`, wire error explanation pipeline.
- **Milestone:** Full pipeline runs, RAM peaks <2.0GB, qwen unloads after 10min.

### Week 4: Polish & Demo (Testing + Recording)
- **Both:** Run benchmark suite, fix top 5 failures.
- **Both:** Record 60-second demo video (finds bug, explains fix).
- **Milestone:** Silver Certification achieved.

---

## ⚠️ Critical Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Schema Drift** | High (breaks all modules) | Freeze v1.0 Day 1, no changes without full review |
| **RAM Blowout** | High (crashes on target HW) | Aggressive idle timeout (10min), streaming responses |
| **Latency Creep** | Med (breaks flow state) | Dual-mode: Real-time (<100ms) vs Deep Scan (<2s) |
| **Hallucination** | Critical (destroys trust) | Parser verifies ALL structural facts before LLM sees them |
| **Scope Creep** | High (misses Phase 1) | NO UI until Week 5, NO general chat, Godot focus only |

---

## 🚀 The Ultimate Vision

COM IDE is building the **first compiler that understands intent**.

- **Today:** Godot node validation + error explanation on 2GB RAM.
- **Tomorrow:** E+ Language Layer (English → GDScript compiler).
- **Future:** Full standalone IDE with AI woven into every layer.

**The Promise:**
> We don't just write code faster. We write code that **cannot fail silently**.

Let's build the compiler. 🛠️
