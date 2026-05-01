# 🏆 COM IDE: Golden Standard & Benchmark v5.0
## The Compiler-AI Architecture for Godot Development

> **"The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that already thinks better even with small models. The limit is only your imagination."**

---

## 📖 Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Core Philosophy: The Compiler-AI Paradigm](#2-core-philosophy-the-compiler-ai-paradigm)
3. [System Architecture](#3-system-architecture)
4. [The Signal Schema v1.0 (Frozen)](#4-the-signal-schema-v10-frozen)
5. [Division of Labor](#5-division-of-labor)
6. [The 7 Pillars of Excellence (Benchmark)](#6-the-7-pillars-of-excellence-benchmark)
7. [Stress Test Protocols](#7-stress-test-protocols)
8. [Certification Levels](#8-certification-levels)
9. [Repository Structure](#9-repository-structure)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. Executive Summary

COM IDE is **not** another AI chatbot wrapper. It is a **static-analysis + execution engine with LLM-assisted planning**.

### The Moat
While Copilot and Cursor rely on probabilistic text generation, COM IDE relies on **deterministic parsing + structured execution**.
- **Competitors:** `User → LLM → Text → Maybe Tools` (Black Box, Hallucination Prone)
- **COM IDE:** `User → Parse → Plan (LLM) → Execute (Deterministic) → Output` (Traceable, Safe)

### The Constraint as a Feature
Built for **2GB RAM** environments, COM IDE forces architectural discipline that makes it faster and more reliable than bloated cloud-dependent tools.
- **Base Model:** `smollm2:1.7b` (Always on, ~1.2GB)
- **Burst Model:** `qwen2.5-coder:7b` (On-demand, auto-unload)
- **Fallback:** `tinyllama:1.1b` (Emergency mode)

---

## 2. Core Philosophy: The Compiler-AI Paradigm

### LLM Role Definition
The LLM is **NOT** an executor, oracle, or chatbot.
**The LLM is a Compiler Stage (IR Generator).**

| Component | Responsibility | LLM Usage? |
|-----------|----------------|------------|
| **Signal Parser** | Strip noise, extract intent keywords | ❌ No (Regex/Rules) |
| **Intent Router** | Classify intent, route to handler | ❌ No (Rules first) |
| **Wiki Retriever** | Enrich context with project data | ❌ No (TF-IDF/Graph) |
| **LLM (Compiler)** | Generate JSON Execution Plan | ✅ **YES (Once)** |
| **Tool Harness** | Execute plan deterministically | ❌ No (Python) |
| **Formatter** | Render output to user | ❌ No (Template) |

### The Golden Rules
1. **Single Pass Law:** LLM is invoked exactly **ONCE** per request.
2. **Context First:** Wiki retrieval happens **BEFORE** LLM invocation.
3. **Strict Schema:** All LLM outputs must be valid JSON matching `signal_schema.py`.
4. **No Hallucination Policy:** Structural facts (paths, types) come from parsing, never LLM generation.
5. **Dual-Mode Latency:**
   - **Real-time Mode:** <100ms (Heuristics + Cache)
   - **Deep Scan Mode:** 1–3s (Full Graph Analysis)

---

## 3. System Architecture

```mermaid
graph TD
    A[User Input] --> B[Signal Parser (Rule-Based)]
    B --> C{Intent Router}
    C -->|Simple Query| D[Direct Answer (Cache/Wiki)]
    C -->|Complex Intent| E[Wiki Retriever (Context Enrichment)]
    E --> F[LLM: IR Generator]
    F -->|JSON Plan| G[Tool Harness Executor]
    G --> H[Output Formatter]
    H --> I[User Output]
    
    subgraph "RAM Safety Zone (<2GB)"
    J[RAM Monitor] -.->|Kill Idle Models| F
    J -.->|Throttle| G
    end
```

### Data Flow Example: Node Validation
1. **Input:** `"Why does $Player crash?"`
2. **Parse:** Extracts target=`$Player`, file=`player.gd`.
3. **Retrieve:** Wiki finds `MainScene.tscn` has node `PlayerCharacter`, not `Player`.
4. **LLM Plan:**
   ```json
   {
     "action": "VALIDATE_NODE_PATH",
     "found": false,
     "suggestion": "$PlayerCharacter",
     "confidence": 0.98
   }
   ```
5. **Execute:** Harness formats suggestion into user-readable error.
6. **Output:** "`$Player` not found. Did you mean `$PlayerCharacter` in `MainScene.tscn`?"

---

## 4. The Signal Schema v1.0 (Frozen)

**⚠️ CRITICAL:** This schema is frozen. Changing it requires a major version bump and full refactor.

### Root Structure
```typescript
interface SignalPlan {
  version: "1.0";
  intent: IntentType;
  target: TargetObject;
  context: ContextObject;
  constraints: ConstraintObject;
  expected_output: OutputType;
}
```

### Enum Definitions
```typescript
type IntentType = 
  | "VALIDATE_NODE_PATH"
  | "EXPLAIN_ERROR"
  | "SUGGEST_FIX"
  | "REFACTOR_ATOMIC"
  | "QUERY_PROJECT_KNOWLEDGE"
  | "GENERATE_GDSCRIPT";

type OutputType = 
  | "validation_report"
  | "plain_text_explanation"
  | "code_diff"
  | "knowledge_summary";
```

### Example: Node Validation Plan
```json
{
  "version": "1.0",
  "intent": "VALIDATE_NODE_PATH",
  "target": {
    "type": "node_path",
    "value": "$Player",
    "file": "player.gd",
    "line": 42
  },
  "context": {
    "scene_tree_hash": "a1b2c3...",
    "available_nodes": ["PlayerCharacter", "Enemy", "UI"],
    "godot_version": "4.2"
  },
  "constraints": {
    "strict": true,
    "suggest_similar": true,
    "max_suggestions": 3
  },
  "expected_output": "validation_report"
}
```

### Example: Error Explanation Plan
```json
{
  "version": "1.0",
  "intent": "EXPLAIN_ERROR",
  "target": {
    "type": "log_entry",
    "value": "Invalid call to non-existent function 'jump' in base 'KinematicBody2D'",
    "stack_trace": ["player.gd:45", "main.gd:12"]
  },
  "context": {
    "script_content": "func _physics_process... ",
    "node_type": "CharacterBody2D"
  },
  "constraints": {
    "max_tokens": 150,
    "tone": "direct",
    "include_fix": true
  },
  "expected_output": "plain_text_explanation"
}
```

---

## 5. Division of Labor

### 👤 Developer H (Core Architect)
**Focus:** The Brain, Schema, Safety, Routing.
| Module | File | Responsibility |
|--------|------|----------------|
| **Signal Schema** | `core/signal_schema.py` | Define & enforce JSON structures |
| **Intent Router** | `core/intent_router.py` | Rule-first classification logic |
| **RAM Monitor** | `core/ram_monitor.py` | Model hot-swap, OOM prevention |
| **LLM Prompts** | `core/prompts/compiler.py` | "IR Generator" system prompts |
| **Context Compressor** | `core/context_compressor.py` | Token reduction (<512) |
| **Benchmark Harness** | `tests/benchmark_runner.py` | Automated test execution |

### 👤 Developer S (Domain Specialist)
**Focus:** The Hands, Godot Parsing, Validation Logic.
| Module | File | Responsibility |
|--------|------|----------------|
| **Scene Parser** | `tools/godot/scene_parser.py` | `.tscn` parsing, tree building |
| **Script Parser** | `tools/godot/script_parser.py` | `.gd` regex, path extraction |
| **Project Map** | `tools/godot/project_map.py` | Cross-reference validation |
| **Log Watcher** | `tools/godot/log_watcher.py` | Real-time log tailing |
| **Godot Specialist** | `tools/godot/specialist.py` | High-level Godot APIs |
| **Fixture Project** | `tests/fixtures/godot_project/` | Complex test cases |

---

## 6. The 7 Pillars of Excellence (Benchmark)

### Pillar 1: Silent Killer Detection
- **Goal:** Detect broken `$NodePaths`, missing signals, type mismatches **pre-runtime**.
- **Test Suite:** 50 subtle path errors, 20 signal ghosts, 10 resource phantoms.
- **Target:** 100% detection rate, 0 false positives, <200ms latency (Deep Scan).

### Pillar 2: Context-Aware Explanation
- **Goal:** Translate engine errors to human meaning using **project context**.
- **Test Suite:** 20 real-world Godot crashes (RAM, binding, thread).
- **Target:** Explanation references specific lines/nodes; <3 sentences; <3s latency.

### Pillar 3: 2GB RAM Law
- **Goal:** Strict **≤2.0GB peak RAM** while running Godot + COM + VS Code.
- **Stress Test:** 1-hour session with heavy inference; RAM must stay <2.1GB.
- **Target:** Auto-unload burst models after 10min idle; Graceful degradation at 90%.

### Pillar 4: T-Shaped Intelligence
- **Goal:** Generic help for Python/JS, **Godot Super-Intelligence** for scenes.
- **Test Suite:** Mixed language queries (Python generic vs. Godot specific).
- **Target:** Godot answers reference actual project files; Python answers are fast/generic.

### Pillar 5: Deterministic Core (Zero Hallucination)
- **Goal:** **0% hallucination rate** on structural facts.
- **Test Suite:** "Does node X exist?" (100 queries); "List all signals" (50 queries).
- **Target:** 100% accuracy via parsing; LLM never invents node names.

### Pillar 6: Refactor Safety Net
- **Goal:** Identify ALL breaking points before renaming/moving nodes.
- **Test Suite:** Rename central node; Verify ripple effect report.
- **Target:** Atomic refactor plans; 100% coverage of dependent scripts.

### Pillar 7: Flow State Latency
- **Goal:** **<100ms** for validation, **<2s** for explanations.
- **Test Suite:** Real-time typing simulation; Bulk file save.
- **Target:** Dual-mode switching (Real-time vs. Deep Scan) works seamlessly.

---

## 7. Stress Test Protocols

### 🍝 The Spaghetti Scene
- **Setup:** 20-level nested inherited scenes, circular dependencies, 500+ nodes.
- **Task:** Validate all paths, detect cycles, suggest flattening.
- **Pass Criteria:** Completes in <5s; RAM spike <500MB; No stack overflow.

### 🔄 The Version Jump
- **Setup:** Project migrated from Godot 4.2 → 4.3 (breaking API changes).
- **Task:** Identify deprecated nodes, changed signal signatures.
- **Pass Criteria:** Lists all breaking changes; Suggests migration code.

### 📉 The RAM Starvation
- **Setup:** Artificially limit COM to 512MB available RAM.
- **Task:** Continue operating (fallback to tinyllama, disable deep scan).
- **Pass Criteria:** No crash; Degrades gracefully; Recovers when limit lifted.

### 🧠 The Hallucination Trap
- **Setup:** Ask about non-existent nodes (`$NonExistentNode`), fake signals.
- **Task:** Correctly report "Not Found" without inventing alternatives.
- **Pass Criteria:** 100% negative accuracy; No confident lies.

### 🌐 The Multi-Language Maze
- **Setup:** Mixed project (GDScript, C# module, Python build scripts).
- **Task:** Answer questions in all 3 languages appropriately.
- **Pass Criteria:** Godot questions = deep context; Others = generic expert.

---

## 8. Certification Levels

| Level | Requirements | Badge |
|-------|--------------|-------|
| **🥇 Gold** | All 7 Pillars Passed + RAM ≤1.6GB + Latency <80ms | "God-Tier" |
| **🥈 Silver** | All 7 Pillars Passed + RAM ≤1.8GB + Latency <100ms | "Production Ready" (Phase 1 Target) |
| **🥉 Bronze** | 6/7 Pillars Passed + RAM ≤2.0GB | "Beta Stable" |
| **❌ Fail** | Any Pillar <90% OR RAM >2.2GB OR Hallucination Detected | "Unstable" |

---

## 9. Repository Structure

```text
/workspace/
├── core/                   # [Dev H] The Brain
│   ├── signal_schema.py    # Frozen v1.0
│   ├── intent_router.py
│   ├── ram_monitor.py
│   ├── context_compressor.py
│   └── prompts/
├── tools/
│   ├── godot/              # [Dev S] The Hands
│   │   ├── scene_parser.py
│   │   ├── script_parser.py
│   │   ├── project_map.py
│   │   ├── log_watcher.py
│   │   └── specialist.py
│   ├── languages/          # Polyglot Support
│   └── tool_harness.py     # Deterministic Executor
├── tests/
│   ├── fixtures/           # Complex Godot Projects
│   ├── benchmark_runner.py
│   └── human_eval/
├── config.py
└── README.md
```

---

## 10. Implementation Roadmap

### Week 1: Foundation
- **Dev H:** Finalize `signal_schema.py`, implement `intent_router.py` skeleton.
- **Dev S:** Build `scene_parser.py`, create `fixtures/godot_project/` (Spaghetti Scene).
- **Milestone:** Schema frozen; Parser reads `.tscn` successfully.

### Week 2: Knowledge & Validation
- **Dev H:** Wire Wiki Retriever **before** LLM; Implement RAM Monitor.
- **Dev S:** Build `project_map.py`, implement node path validation logic.
- **Milestone:** "Silent Killer" test passes (90% detection).

### Week 3: The Compiler Pipeline
- **Dev H:** Write LLM "IR Generator" prompts; Enforce JSON output.
- **Dev S:** Connect Harness to execute validation plans.
- **Milestone:** End-to-end flow: Input → Plan → Execute → Output.

### Week 4: Stress & Polish
- **Both:** Run full Benchmark Suite; Optimize RAM/Latency.
- **Dev S:** Human Eval scripts; Fixture refinement.
- **Milestone:** Silver Certification achieved.

---

## Appendix: Failure Handling Protocols

1. **Invalid JSON from LLM:**
   - Retry once with stricter prompt.
   - If fail → Fallback to rule-based default response.
   - Log error for prompt tuning.

2. **RAM Threshold Breach (>90%):**
   - Immediately unload burst model (`qwen`).
   - Switch to `tinyllama` fallback.
   - Disable Deep Scan mode until memory recovers.

3. **Parser Failure (Corrupt .tscn):**
   - Isolate corrupt file; skip parsing.
   - Report "Unparseable File" to user.
   - Continue with remaining project.

---

> **"The limit is only your imagination."**
> Built for Godot developers, by Godot developers.
> Local. Private. Evolving.
