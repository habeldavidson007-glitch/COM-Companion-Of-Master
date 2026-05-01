# COM IDE Roadmap: From Compiler Core to Godot Super-Intelligence

> **"The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that's already thinks better even with small model, the limit only your imagination."**

## Executive Summary

**COM IDE** is not a chatbot wrapper. It is a **Compiler-AI Hybrid** that treats the LLM as a single compilation stage (IR Generator) within a deterministic pipeline. This architecture allows it to run on **2GB RAM** while delivering **zero-hallucination** structural analysis for Godot, surpassing generic AI assistants that rely on probabilistic guessing.

### The Core Philosophy: "Compiler-Lite"
1.  **LLM Appears Exactly Once**: To generate a structured JSON execution plan. No chatting, no summarizing.
2.  **Parse → Retrieve → Plan → Execute**: Context is enriched *before* the LLM sees it.
3.  **Deterministic Execution**: The Tool Harness executes the plan. If the plan is invalid, the system fails safely; it never hallucinates.
4.  **T-Shaped Intelligence**: General polyglot support (Python, JS, C++) with **Godot Super-Intelligence** (deep scene tree awareness, pre-runtime validation).

---

## 🏗 Architecture Overview

```mermaid
graph TD
    A[User Input] --> B[Signal Parser (Rule-Based)]
    B --> C{Intent Router}
    C -->|Simple| D[Direct Harness Execution]
    C -->|Complex| E[Wiki Retriever (Context Enrichment)]
    E --> F[LLM Stage (Single Pass)]
    F -->|Generates JSON Plan| G[Tool Harness Executor]
    G --> H[Final Output]
    
    style F fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#bbf,stroke:#333,stroke-width:2px
```

### Key Constraints
- **RAM Law**: Peak usage ≤ 2.0GB (Adaptive model selection via liteLLM).
  - *Logic*: `Max_Model_RAM = Available_RAM - 1.5GB`
  - *Chain*: `Qwen-7B` (if >5.5GB free) → `Llama-3B` (if >3.5GB free) → `Smol-1.7B` (fallback).
- **Latency Modes**: 
  - *Real-time*: <100ms (Heuristic/Cache)
  - *Deep Scan*: <3s (Full Graph + LLM)
- **Accuracy**: 100% on structural facts (Node paths, signals). 0% hallucination tolerance.

---

## 👥 Team Structure & Division of Labor

| Role | Responsibility | Key Deliverables |
| :--- | :--- | :--- |
| **Developer H (Core Architect)** | **The Brain**: Signal Schema, Intent Routing, RAM Safety, LLM Prompts | `signal_schema.py`, `intent_router.py`, `ram_monitor.py`, `prompts/` |
| **Developer S (Domain Specialist)** | **The Hands**: Godot Parsers, Project Map, Log Watching, Validation Logic | `scene_parser.py`, `script_parser.py`, `project_map.py`, `log_watcher.py` |

---

## 🗓 Phase 1: The Compiler Core (Project Scanner + Error Explainer)
**Goal**: A terminal-based tool that parses Godot projects, validates node paths pre-runtime, and explains errors in plain English.  
**Duration**: 4 Weeks  
**RAM Target**: ≤ 1.8GB Base / ≤ 2.0GB Burst  
**Benchmark Target**: Silver (All 7 Pillars Pass)

### Sprint 1: Foundation & Schema (Week 1)
*Focus: Defining the language of the compiler and building the eyes.*

| Task ID | Owner | Task Description | Success Criteria (Benchmark) |
| :--- | :--- | :--- | :--- |
| **1.1** | **Dev H** | **Freeze Signal Schema v1.0**. Define strict JSON structure for all intents (`VALIDATE_NODE`, `EXPLAIN_ERROR`). | Schema validates 100% of test cases; 0 ambiguous fields. |
| **1.2** | **Dev H** | Implement `core/signal_parser.py`. Regex/Rule-based extractor to strip noise before LLM. | Parses raw input to schema in <10ms. |
| **1.3** | **Dev S** | Build `tools/godot/scene_parser.py`. Parse `.tscn` into in-memory node tree (name, type, path). | Parses 50-level nested scene in <50ms. 100% node accuracy. |
| **1.4** | **Dev S** | Build `tools/godot/script_parser.py`. Extract `$NodePath`, `@onready`, `connect` from `.gd` files. | Detects 100% of path references in test script. |

### Sprint 2: Knowledge & Validation (Week 2)
*Focus: Connecting the eyes to the brain and checking facts.*

| Task ID | Owner | Task Description | Success Criteria (Benchmark) |
| :--- | :--- | :--- | :--- |
| **2.1** | **Dev S** | Build `tools/godot/project_map.py`. Cross-reference scene tree + script refs. | Identifies broken paths instantly. |
| **2.2** | **Dev S** | Implement `validate_node_paths()`. Return `ValidationError` with suggestions (Levenshtein distance). | **Pillar 1 Pass**: 100% detection, 0 false positives. |
| **2.3** | **Dev H** | Integrate `WikiRetriever`. Ensure full-content indexing (no truncation bug). Load Godot docs. | Retrieval happens *before* LLM call. |
| **2.4** | **Dev H** | Write `core/prompts/compiler_prompt.txt`. Instruct LLM to output *only* JSON plans. | LLM outputs valid JSON 100% of time (no chatter). |

### Sprint 3: RAM Safety & Execution (Week 3)
*Focus: Hardening the system for 2GB constraint.*

| Task ID | Owner | Task Description | Success Criteria (Benchmark) |
| :--- | :--- | :--- | :--- |
| **3.1** | **Dev H** | Build `core/ram_monitor.py`. Auto-unload large models if RAM > 90%. | **Pillar 3 Pass**: Peak RAM ≤ 2.0GB under stress. |
| **3.2** | **Dev H** | Refactor `tool_harness.py`. Add `GDT` alias fix. Ensure it executes JSON plans strictly. | Executes `VALIDATE_NODE` plan deterministically. |
| **3.3** | **Dev S** | Build `tools/godot/log_watcher.py`. Async file watcher for Godot output logs. | Detects new log line in <200ms. |
| **3.4** | **Both** | **Wiring**: Connect Log Watcher → Parser → LLM → Harness. | End-to-end latency < 2s for error explanation. |

### Sprint 4: Polish & Torture Testing (Week 4)
*Focus: Proving superiority via the Golden Benchmark.*

| Task ID | Owner | Task Description | Success Criteria (Benchmark) |
| :--- | :--- | :--- | :--- |
| **4.1** | **Dev S** | Create "Spaghetti Scene" fixture (20-level nesting, circular refs). | Parser handles it without crash/recursion error. |
| **4.2** | **Dev H** | Run "Hallucination Trap" test. Ask about non-existent nodes. | System replies "Not found" 100/100 times. |
| **4.3** | **Both** | **Dual-Mode Tuning**: Optimize Real-time (<100ms) vs Deep Scan (<3s). | Mode switch works seamlessly based on query complexity. |
| **4.4** | **Both** | **Demo Recording**: 60-second video showing pre-runtime error catch. | Demo shows value prop clearly. |

**Phase 1 Deliverable**: A CLI tool (`com-cli`) that you run in a Godot project folder. It outputs a report of broken node paths and explains any recent crashes.

---

## 🗓 Phase 2: Context-Aware Q&A + Memory (The Knowledge Layer)
**Goal**: Persistent project memory and deep Q&A. COM remembers your project between sessions.  
**Duration**: 6 Weeks  
**RAM Target**: ≤ 2.0GB (Aggressive caching)

### Sprint 1: Indexing & Persistence
- **Dev H**: Implement `core/memory_manager.py`. Sliding window context + salience filter. Save/Load project state to disk.
- **Dev S**: Extend `project_map.py` to serialize/deserialize the full graph to JSON/SQLite.
- **Benchmark**: Session restart retains 100% of node/signal knowledge.

### Sprint 2: Project-Aware RAG
- **Dev H**: Upgrade `WikiRetriever` to hybrid search (TF-IDF + Graph Traversal). Prioritize *project* files over general docs.
- **Dev S**: Tag scripts with metadata (e.g., "PlayerController", "EnemyAI") for semantic search.
- **Benchmark**: Question "Where is player jump logic?" returns exact file/line.

### Sprint 3: Suggest Fix Mode
- **Dev H**: Prompt engineering for "Refactor Plan" generation. LLM outputs `APPLY_PATCH` JSON.
- **Dev S**: Build `tools/godot/patch_applier.py`. Safe atomic writes with rollback capability.
- **Benchmark**: **Pillar 6 Pass**: Refactor safety net verifies 0 broken dependencies after apply.

### Sprint 4: Stress & Optimization
- **Both**: "RAM Starvation" test. Run COM + Godot + Chrome on 2GB machine.
- **Benchmark**: System degrades gracefully (falls back to Smol-1.7B via liteLLM) rather than crashing.

**Phase 2 Deliverable**: COM Chat (Terminal/Basic GUI) that answers "Why does my player fall?" using *your* collision shape data, not generic advice.

---

## 🗓 Phase 3: VS Code Extension (Distribution)
**Goal**: Bring the Compiler Core to the editor where developers live.  
**Duration**: 8 Weeks  
**Key Tech**: Python Server + TS Extension (IPC)

### Sprint 1: Extension Skeleton
- **Dev H**: Build Python language server (`com-server`) exposing the Pipeline via TCP/STDIO.
- **Dev S**: Create VS Code extension scaffold. Register commands.

### Sprint 2: Inline Validation (The Killer Feature)
- **Dev S**: Implement Decorations API. Red underline on `$BadPath` detected by `project_map`.
- **Dev H**: Optimize `scene_parser` for incremental updates (watch file change, re-parse only delta).
- **Benchmark**: **Pillar 7 Pass**: Latency <100ms from save to underline.

### Sprint 3: IntelliSense + Hover
- **Dev S**: Completion Items provider. Suggest *actual* node names from scene tree.
- **Dev H**: Hover Provider. Show `Wiki` + `Project Context` on hover.
- **Benchmark**: Completions include 100% of valid scene nodes.

### Sprint 4: Marketplace Launch
- **Both**: Packaging, Documentation, Free/Paid Tier logic (Stripe integration for "Unlimited Explanations").
- **Deliverable**: Public release on VS Code Marketplace.

---

## 🗓 Phase 4: E+ Language & Standalone IDE (The Endgame)
**Goal**: A new high-level language that compiles to GDScript, running in a custom shell.  
**Duration**: 12 Weeks  

### Sprint 1: E+ Grammar Definition
- **Dev H**: Define E+ syntax (near-English). `@when player jumps -> ...`
- **Dev S**: Build Rule-Based Translator (E+ → GDScript). Deterministic mapping for 80% of cases.

### Sprint 2: LLM Fallback for Complex Logic
- **Dev H**: Train/Prompt LLM to handle ambiguous E+ constructs.
- **Benchmark**: 95% of common patterns translated without LLM.

### Sprint 3: Standalone Shell (Qt/Electron)
- **Dev S**: Build UI wrapper. Integrated terminal, scene viewer, file tree.
- **Dev H**: Embed the entire Compiler Pipeline into the app bundle.

### Sprint 4: Plugin System
- **Both**: API for community tools (Blender export, Aseprite import).
- **Deliverable**: Full IDE replacing the need for external editors for logic.

---

## 🏆 The God-Tier Benchmark System

We do not ship unless we pass these tests. These define our superiority over Copilot/ChatGPT.

### Pillar 1: Silent Killer Detection
- **Test**: Inject 50 broken `$NodePaths` into a clean project.
- **Pass**: 100% detected pre-runtime. 0 False Positives.
- **Latency**: <200ms (Deep Scan).

### Pillar 2: Context-Aware Explanation  
- **Test**: Feed 20 cryptic Godot engine errors.
- **Pass**: Explanation references specific user file/line/node. No generic "Check your code" fluff.
- **Model**: Adaptive via liteLLM (Must work on smallest available model).

### Pillar 3: 2GB RAM Law
- **Test**: Run COM + Godot + Chrome on 2GB VM for 1 hour.
- **Pass**: RAM never exceeds 2.0GB. OOM killer never triggers.
- **Mechanism**: Adaptive routing unloads larger models when RAM < 90%.

### Pillar 4: T-Shaped Intelligence
- **Test**: Ask Python question (Generic) vs Godot question (Specific).
- **Pass**: Godot answer cites `main.tscn` structure. Python answer is standard best-practice.

### Pillar 5: Deterministic Core (Zero Hallucination)
- **Test**: Ask "Does node $NonExistent exist?"
- **Pass**: "No" (100% certainty). Never "Maybe, try adding it."
- **Source**: Parsed graph, not LLM probability.

### Pillar 6: Refactor Safety Net
- **Test**: Rename `Player` to `Hero`.
- **Pass**: COM lists *every* script/line that needs updating. Applies changes atomically.
- **Safety**: Rollback works if any patch fails.

### Pillar 7: Flow State Latency
- **Test**: Type invalid path, save.
- **Pass**: Error visible in <100ms (Real-time mode).
- **Pass**: Complex analysis finishes in <3s (Deep Scan mode).

---

## 🚀 Immediate Next Steps (Day 1)

1.  **Dev H**: Initialize `core/signal_schema.py`. Copy the v1.0 JSON structure from `GOLDEN_STANDARD.md`.
2.  **Dev S**: Initialize `tools/godot/` directory. Create empty `scene_parser.py` and `script_parser.py`.
3.  **Both**: 30-minute Sync Call.
    - Review Signal Schema v1.0 together.
    - Agree on the JSON field names (`intent`, `target`, `context`).
    - **Lock it.** No changes allowed after this call without mutual consent.

**Let's build the compiler.**
