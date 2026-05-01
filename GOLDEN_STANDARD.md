# 🏆 COM IDE: Golden Standard & Execution Plan

**Version:** 1.0 (Phase 1 - Compiler-Lite Architecture)  
**Target Hardware:** 2GB RAM Minimum (Optimized for Low-End)  
**Philosophy:** Polyglot Expert + Godot Specialist  
**Status:** Active Development  

---

## 🚀 Executive Summary

COM IDE is not just another coding assistant. It is a **signal-driven execution engine** where the LLM acts as a **compiler stage**, not an oracle. 

### The Core Shift
- **Old Paradigm:** User → LLM → Answer (Black box, high RAM, hallucinations)
- **New Paradigm (Compiler-Lite):** User → Signal Parser → Wiki → LLM(Plan) → Harness → Output (Deterministic, low RAM, verifiable)

### Why This Works on 2GB RAM
1. **LLM appears exactly ONCE** in the pipeline (generates a small JSON plan).
2. **Rule-based parsing first** strips noise before tokens are counted.
3. **Wiki retrieval happens BEFORE LLM** to inject context, reducing guesswork.
4. **No summarization step**—the harness output is the final answer.
5. **Model Hot-Swapping:** `smollm2:1.7b` (1.2GB) stays loaded; `qwen2.5-coder:7b` loads on-demand and unloads after 10 mins.

---

## 🏛️ Architecture: The "Compiler-Lite" Pipeline

The system behaves like a compiler, not a chatbot. Every user input is compiled into an **Execution Plan** (JSON), executed deterministically, and returned.

```
User Input
   ↓
[1] Signal Parser (Rule-Based, No LLM)
   ↓
[2] Intent Router (Rule-First, LLM Fallback)
   ↓
[3] Wiki Retriever (Enrich Context)
   ↓
[4] LLM Stage (Generate JSON Plan ONLY)
   ↓
[5] Tool Harness (Execute Plan Deterministically)
   ↓
[6] Core Formatter (Render Output)
   ↓
Final Output
```

### Stage Breakdown

| Stage | Component | Responsibility | LLM Used? |
|-------|-----------|----------------|-----------|
| **1. Lexer** | `SignalParser` | Extract entities ($NodePath, signals), strip noise, normalize intent. | ❌ No |
| **2. Parser** | `IntentRouter` | Map intent to action (`VALIDATE`, `EXPLAIN`, `SEARCH`). Use rules first; LLM only for ambiguity. | ⚠️ Rarely |
| **3. Semantic** | `WikiRetriever` | Fetch relevant docs/project context *before* LLM sees the prompt. | ❌ No |
| **4. IR Gen** | `LLM Engine` | **Single Pass:** Generate structured JSON plan `{ "action": "...", "params": {} }`. | ✅ Yes (Once) |
| **5. Exec** | `ToolHarness` | Execute the JSON plan. No thinking, just doing. | ❌ No |
| **6. Format** | `CoreFormatter` | Render harness output to human-readable text. | ❌ No |

---

## 👥 Division of Labor (Professional Split)

Work is split by **Architecture/Core** vs. **Domain/Tools**. This minimizes merge conflicts and maximizes parallel velocity.

### 👨‍💻 Developer H (You) — Core Architect
**Focus:** The "Brain". Signal processing, RAM safety, LLM orchestration, and the execution backbone.  
**Goal:** Ensure the pipeline is deterministic, fits in 2GB RAM, and routes correctly.

| Module | File Path | Key Tasks |
|--------|-----------|-----------|
| **Signal Schema** | `core/signal_schema.py` | Define strict JSON schema for Execution Plans. Validate all LLM outputs against this. |
| **Intent Router** | `core/intent_router.py` | Implement rule-first routing. Add LLM fallback *only* for ambiguous intents. |
| **RAM Monitor** | `core/ram_monitor.py` | Implement memory tracking. Auto-unload large models when >90% threshold hit. |
| **LLM Prompts** | `core/prompts/` | Craft "Compiler Prompts" that force JSON output. No conversational fluff. |
| **Tool Harness** | `tools/tool_harness.py` | Ensure `@GDT` alias is fixed. Verify it accepts JSON plans, not raw text. |
| **Context Compressor** | `core/context_compressor.py` | Aggressively trim context window to <512 tokens before sending to LLM. |

**Critical Success Factor:** If the LLM ever outputs raw text instead of JSON, or if RAM spikes >2.5GB during idle, the Core is failing.

---

### 👨‍🔧 Developer S (Friend) — Domain Specialist
**Focus:** The "Hands". Godot-specific parsing, project analysis, log monitoring, and domain logic.  
**Goal:** Build the deepest possible understanding of Godot projects without needing LLM for basic facts.

| Module | File Path | Key Tasks |
|--------|-----------|-----------|
| **Scene Parser** | `tools/godot/scene_parser.py` | Parse `.tscn` files into a node tree dict. Handle inheritance and nested scenes. |
| **Script Parser** | `tools/godot/script_parser.py` | Regex-based extraction of `$NodePath`, `@onready`, and signal connections from `.gd`. |
| **Project Map** | `tools/godot/project_map.py` | Merge scene + script data. Implement `validate_node_paths()` with similarity suggestions. |
| **Log Watcher** | `tools/godot/log_watcher.py` | Tail Godot's `output.log`. Pre-process errors before sending to Core. |
| **Godot Specialist** | `tools/godot/specialist.py` | The bridge: Takes Core's JSON plan and executes Godot-specific logic. |
| **Test Suite** | `tools/godot/test_phase1.py` | Unit tests for parsers using real Godot project fixtures. |

**Critical Success Factor:** If the parser misses a renamed node, or if the log watcher fails to detect a crash, the Specialist is failing. **No LLM calls allowed in parsers**—they must be 100% regex/string logic for speed and RAM.

---

## 🗓️ Phase 1 Execution Plan (4 Weeks)

**Goal:** A terminal-based tool that scans a Godot project, validates node paths, and explains crashes in plain English. **NO UI YET.**

### Week 1: Foundation (Parsing & Schema)
- **Dev H:** 
  - [ ] Draft `core/signal_schema.py` (JSON structure for plans).
  - [ ] Create `core/prompts/compiler_prompt.txt` (forces JSON output).
  - [ ] Fix `@GDT` alias in `tool_harness.py`.
- **Dev S:** 
  - [ ] Build `scene_parser.py` (test on 5 complex `.tscn` files).
  - [ ] Build `script_parser.py` (extract all `$` paths).
  - [ ] Create `tools/godot/fixtures/` with test projects.
- **Joint:** Mid-week sync to align Schema ↔ Parser output.

### Week 2: Knowledge & Validation
- **Dev H:** 
  - [ ] Refactor `IntentRouter` to use Rule-First logic.
  - [ ] Implement `WikiRetriever` pre-fetching (context before LLM).
  - [ ] Fix Wiki truncation bug in `wiki_compiler.py`.
- **Dev S:** 
  - [ ] Build `project_map.py` (merge scene + script).
  - [ ] Implement `validate_node_paths()` with fuzzy matching.
  - [ ] Write 10 unit tests for validation edge cases.
- **Joint:** End-to-end test: Run validator on a broken project.

### Week 3: RAM Safety & Execution
- **Dev H:** 
  - [ ] Implement `ram_monitor.py` with auto-unload.
  - [ ] Optimize context compressor (hard limit 512 tokens).
  - [ ] Wire `log_watcher` → `LLM` → `Harness` pipeline.
- **Dev S:** 
  - [ ] Build `log_watcher.py` (async file tailing).
  - [ ] Create `specialist.py` to execute validation plans.
  - [ ] Tune error explanation prompts for `smollm2:1.7b`.
- **Joint:** Stress test: Run for 1 hour, monitor RAM usage.

### Week 4: Polish & Demo
- **Dev H:** 
  - [ ] Finalize error formatting (clear, actionable output).
  - [ ] Document the Signal Schema for future phases.
  - [ ] Record terminal demo video.
- **Dev S:** 
  - [ ] Test on 3 real-world Godot projects (GitHub repos).
  - [ ] Fix top 5 false positives from validation.
  - [ ] Write `README.md` for the Godot module.
- **Joint:** **Phase 1 Freeze.** No new features. Only bug fixes.

---

## 🧹 Repository Hygiene (Golden Standard Structure)

A clean repo is a fast repo. We strictly separate concerns.

```text
/workspace/
├── core/                      # THE BRAIN (Dev H)
│   ├── signal_schema.py       # Strict JSON definition
│   ├── intent_router.py       # Rule-first routing
│   ├── ram_monitor.py         # Memory safety
│   ├── context_compressor.py  # Token trimming
│   └── prompts/               # Compiler-style prompts
│
├── tools/                     # THE HANDS (Dev S + Others)
│   ├── godot/                 # ★ GODOT SPECIALIST (Phase 1 Focus)
│   │   ├── scene_parser.py
│   │   ├── script_parser.py
│   │   ├── project_map.py
│   │   ├── log_watcher.py
│   │   ├── specialist.py      # Executes JSON plans
│   │   └── test_phase1.py
│   │
│   ├── languages/             # Polyglot experts (Python, JS, etc.)
│   ├── data_ops/              # Wiki compiler, indexer
│   └── tool_harness.py        # Universal executor
│
├── config.py                  # Model configs (smollm2, qwen)
├── com_chat.py                # Main entry point
├── GOLDEN_STANDARD.md         # This document
└── .gitignore                 # Strict exclusion rules
```

### 🗑️ What Must Be Deleted (Immediately)
1. **Legacy Benchmarks:** `benchmark and test review/`, `benchmark_results.json`.
2. **Node.js Artifacts:** `node_modules/`, `package.json` (accidental commits).
3. **Unused Office Tools:** Move `tools/excel/`, `tools/ppt/` to `tools/_deferred/`.
4. **Language Bloat:** If a language isn't Python, JS, C++, or GDScript, move to `_deferred`.
5. **All `__pycache__/` and `.pyc` files.**
6. **Old Game Dev Scripts:** Delete and rewrite fresh in `tools/godot/`.

---

## ⚠️ Critical Constraints & Rules

### 1. The 2GB RAM Law
- **Base Load:** `smollm2:1.7b` (~1.2GB) + OS + Python overhead = ~1.8GB.
- **Burst Load:** `qwen2.5-coder:7b` loads only for complex code gen, unloads after 10 mins idle.
- **Hard Limit:** If RAM > 90%, immediately unload `qwen` and switch to `tinyllama:1.1b` fallback.
- **No Buffering:** Stream tokens directly to output. Do not store full responses in memory.

### 2. The "One LLM Pass" Rule
- **Forbidden:** Using LLM to parse input AND generate output.
- **Required:** Parse input with Regex/Rules → LLM generates Plan → Harness executes.
- **Exception:** None. If you need a second LLM call, your prompt or schema is wrong.

### 3. The "No UI" Rule (Phase 1)
- **Focus:** Terminal output only.
- **Why:** UI frameworks (Tkinter, Qt) add complexity and RAM overhead.
- **Goal:** Perfect the logic first. UI is Week 5+.

### 4. The "Godot First" Principle
- COM is a polyglot expert, but **Godot is the superpower**.
- General coding help (Python, JS) uses standard patterns.
- Godot help uses the **Specialist Module** with deep project awareness.
- **Differentiation:** No other tool validates `$NodePath` before runtime.

---

## 🔮 Future Phases (Vision)

- **Phase 2:** Context-Aware Q&A + Memory (Project indexing, session persistence).
- **Phase 3:** VS Code Extension (Distribution, inline validation).
- **Phase 4:** E+ Language Translator (Live E+ → GDScript compilation).
- **Phase 5:** Standalone COM IDE (Full editor surface).

---

## 🤝 Joint Responsibilities

Both developers share these duties:
1. **Testing:** Every PR must include tests. No tests = no merge.
2. **Documentation:** Update this file if architecture changes.
3. **RAM Audits:** Weekly check of memory usage during peak load.
4. **Code Reviews:** Dev H reviews Godot tools for RAM efficiency; Dev S reviews Core for Godot accuracy.

---

## 🚦 Immediate Next Steps (Day 1)

1. **Dev H:** 
   - Create `core/signal_schema.py` with draft JSON.
   - Push to branch `feature/signal-schema`.
2. **Dev S:** 
   - Create `tools/godot/` directory.
   - Start `scene_parser.py` with a simple `.tscn` fixture.
   - Push to branch `feature/scene-parser`.
3. **Both:** 
   - Schedule 30-min sync tomorrow to finalize the Signal Schema.
   - Agree on the exact JSON structure for `VALIDATE_NODE_PATH`.

**Let's build the compiler.** 🛠️
