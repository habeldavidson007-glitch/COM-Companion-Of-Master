# 🚀 COM IDE: Godot AI Companion

> **"The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that already thinks better even with small models. The limit is only your imagination."**

**COM IDE** is a **Compiler-AI Hybrid** that combines deterministic static analysis with LLM-powered planning. It is not a chatbot—it is a development companion that knows your project better than you do, runs on 2GB RAM, and never lies about your code structure.

---

## 🎯 Quick Start

```bash
# Install dependencies
pip install -e .

# Run COM IDE (terminal mode)
python com_chat.py --project /path/to/godot/project

# Run benchmark suite
python tests/harness_runner.py
```

---

## 🔥 Why COM IDE?

| Feature | Traditional AI IDE | COM IDE |
|---------|-------------------|---------|
| **Architecture** | `User → LLM → Text` | `Parse → Retrieve → Plan → Execute` |
| **Hallucination** | Common (guesses facts) | **Zero** (parser verifies everything) |
| **RAM Usage** | 4-8GB minimum | **<2GB** (model hot-swap) |
| **Project Awareness** | None (generic answers) | **Deep** (knows your scene tree) |
| **Latency** | 3-10s per query | **<100ms** real-time validation |
| **Offline** | No (cloud API) | **Yes** (local Ollama inference) |

---

## 🏗️ Architecture: Compiler-Lite Pipeline

```
User Input
   ↓
[1] Signal Parser (Rule-Based, NO LLM)
   ↓
[2] Intent Router (Rule-First, LLM Fallback)
   ↓
[3] Wiki Retriever (Context BEFORE LLM)
   ↓
[4] LLM (SINGLE PASS → JSON Plan)
   ↓
[5] Harness Executor (Deterministic)
   ↓
[6] Output Formatter (No summarization)
```

**Key Innovation:** LLM appears **exactly ONCE** to generate an execution plan. All structural facts come from parsing, not probability.

---

## 📦 Phase 1 Features (Current)

| Feature | Status | Description |
|---------|--------|-------------|
| **Node Path Validation** | ✅ Ready | Catches `$Player` → `$PlayerCharacter` renames pre-runtime |
| **Error Explanation** | ✅ Ready | Translates Godot crashes to plain English |
| **Project Map** | ✅ Ready | Builds in-memory scene tree from .tscn/.gd files |
| **Log Watcher** | ✅ Ready | Monitors Godot output.log in real-time |
| **RAM Monitor** | ✅ Ready | Auto-unloads models after 10min idle |
| **Signal Schema v1.0** | ✅ Frozen | Strict JSON protocol for all internal comms |
| **VS Code Extension** | 🚧 Phase 3 | Coming soon |
| **E+ Language** | 🚧 Phase 4 | English → GDScript compiler |

---

## 🏆 Benchmark Standards

COM IDE must pass the **7 Pillars of Excellence** to be certified:

1. **Silent Killer Detection** – 100% pre-runtime error catch rate
2. **Context-Aware Explanation** – References specific file/line/node
3. **2GB RAM Law** – Peak memory ≤2.0GB with Godot + VS Code running
4. **T-Shaped Intelligence** – Polyglot generalist, Godot god
5. **Deterministic Core** – Zero hallucination on structural facts
6. **Refactor Safety Net** – Atomic changes with ripple analysis
7. **Flow State Latency** – <100ms validation, <2s deep scan

*See `GOLDEN_BENCHMARK.md` for full test suites and torture chambers.*

---

## 👥 Team Structure

### Developer H (Core Architect)
- **Focus:** Signal schema, intent routing, RAM safety, LLM prompts
- **Files:** `core/signal_schema.py`, `core/intent_router.py`, `core/ram_monitor.py`
- **Goal:** Keep base RAM <1.2GB, schema validation 100%

### Developer S (Domain Specialist)
- **Focus:** Godot parsing, project mapping, error detection
- **Files:** `tools/godot/scene_parser.py`, `tools/godot/script_parser.py`, `tools/godot/project_map.py`
- **Goal:** Node validation 100% accurate, <100ms latency

---

## 📅 Roadmap

### Phase 1: Project Scanner + Error Explainer (Current)
- **Timeline:** 4 weeks
- **Deliverable:** Terminal tool that validates node paths and explains crashes
- **RAM Target:** ≤2.0GB peak

### Phase 2: Context-Aware Q&A + Memory
- **Timeline:** 6-8 weeks
- **Deliverable:** Persistent chat panel with project memory
- **Feature:** "Why does my player fall through the floor?" → answers using YOUR CollisionShape2D

### Phase 3: VS Code Extension
- **Timeline:** 8-10 weeks
- **Deliverable:** Marketplace extension with inline validation
- **Revenue:** Free tier (basic) + Paid tier ($5/mo, unlimited Q&A)

### Phase 4: E+ Language Translator
- **Timeline:** 10-14 weeks
- **Deliverable:** English → GDScript compiler
- **Example:** `@when player jumps -> velocity.y = jump_force` → working GDScript

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Core** | Python 3.10+ | Main logic, parsers, orchestrator |
| **LLM Backend** | Ollama | Local inference (smollm2, qwen2.5-coder) |
| **Godot Parsing** | Custom regex + AST | Scene tree extraction |
| **Knowledge Base** | TF-IDF + Concept Graph | Wiki retrieval |
| **Memory** | Sliding window + Salience filter | Context compression |
| **Testing** | Pytest + Fixtures | Benchmark automation |

---

## 📂 Repository Structure

```
/workspace/
├── core/                      # Brain (Dev H)
│   ├── signal_schema.py       # Frozen v1.0
│   ├── intent_router.py       # Routing logic
│   ├── ram_monitor.py         # Memory safety
│   └── prompts/               # Compiler prompts
│
├── tools/                     # Hands (Dev S)
│   ├── godot/                 # Godot Specialist
│   │   ├── scene_parser.py
│   │   ├── script_parser.py
│   │   ├── project_map.py
│   │   └── log_watcher.py
│   ├── data_ops/              # Wiki compiler
│   └── tool_harness.py        # Executor
│
├── tests/                     # Benchmark fixtures
│   ├── fixture_project/
│   └── harness_runner.py
│
├── config.py                  # Model configs
├── com_chat.py                # Entry point
├── GOLDEN_STANDARD.md         # Execution plan
├── GOLDEN_BENCHMARK.md        # Test suites
└── README.md                  # This file
```

---

## 🧪 Running the Benchmark

```bash
# Full benchmark suite
python tests/harness_runner.py

# Specific pillar test
python tests/harness_runner.py --pillar 1  # Silent Killer Detection

# RAM stress test
python tests/harness_runner.py --ram-limit 512MB
```

**Target:** Silver Certification (All 7 pillars pass, RAM ≤1.8GB).

---

## 🤝 Contributing

1. **Read `GOLDEN_STANDARD.md`** – Understand the architecture before coding.
2. **Never break the schema** – `core/signal_schema.py` is frozen.
3. **Test on 2GB RAM** – If it doesn't run on potato hardware, it doesn't ship.
4. **Godot first** – General features are secondary to Godot super-intelligence.

---

## 📄 License

MIT License – Build freely, contribute back.

---

## 🚀 The Vision

> **We don't just write code faster. We write code that cannot fail silently.**

COM IDE is the first AI companion that:
- Knows your project structure without you explaining it
- Catches bugs before you run the game
- Runs on your old laptop with 2GB RAM
- Never hallucinates about your node paths

**Join us. Let's build the compiler with a brain.** 🛠️
