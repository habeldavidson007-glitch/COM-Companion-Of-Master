# 🚀 COM IDE: Godot AI Companion

> **The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that already thinks better even with small models. The limit is only your imagination.**

**COM IDE** is a **Compiler-AI Hybrid** that combines deterministic static analysis with LLM-powered planning. It is not a chatbot—it is a development companion that knows your project better than you do, runs on 2GB RAM, and never lies about your code structure.

---

## 🎯 Quick Start

```bash
# Install dependencies (including new production stack)
pip install -e .
pip install instructor litellm diskcache watchfiles logfire rich tiktoken

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
| **RAM Usage** | 4-8GB minimum | **<2GB** (model hot-swap + diskcache) |
| **Project Awareness** | None (generic answers) | **Deep** (knows your scene tree) |
| **Latency** | 3-10s per query | **<100ms** real-time validation (watchfiles) |
| **Offline** | No (cloud API) | **Yes** (local Ollama inference) |
| **Schema Safety** | Invalid JSON possible | **100% valid** (instructor enforced) |

---

## 🏗️ Architecture: Compiler-Lite Pipeline

graph LR
    A[User Input] --> B[Signal Parser + tiktoken]
    B --> C{Adaptive Router<br/>liteLLM + RAM Monitor}
    C -->|Check RAM| D{Select Model}
    D -->|Fit? Yes| E[Load Best Model<br/>Qwen-7B/Llama-3B]
    D -->|Fit? No| F[Fallback<br/>Smol-1.7B]
    E & F --> G[LLM: JSON Plan]
    G --> H[instructor: Schema]
    H --> I[Wiki + diskcache]
    I --> J[Harness Executor]
    J --> K[Output + rich]
    K --> L[logfire Trace]
    
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#ff9,stroke:#333,stroke-width:2px

```

**Key Innovation:** LLM appears **exactly ONCE** to generate an execution plan. All structural facts come from parsing, not probability. `liteLLM` adaptively selects the smartest model that fits current RAM availability.

---

## 🛠️ Production Tech Stack

| Library | Purpose | RAM Overhead | Critical For |
|---------|---------|--------------|--------------|
| **instructor** | Enforce strict JSON schema on LLM output | ~40MB | Zero Hallucination Policy |
| **tiktoken** | Precise token counting & truncation | ~30MB | 2GB RAM Law, Context Discipline |
| **diskcache** | Disk-backed caching for context & plans | ~20MB | RAM Offloading, Model Hot-Swapping |
| **watchfiles** | Async file system monitoring | ~15MB | Real-time Validation (<100ms) |
| **liteLLM** | Unified model routing & fallback chains | ~50MB | Model Agnosticism, Future Cloud |
| **logfire** | Structured observability & tracing | ~35MB | Debugging, Benchmark Verification |
| **rich** | Terminal UI for errors & progress | ~25MB | Flow State Latency, DX |

**Total Stack Overhead:** ~215MB (Negligible compared to model savings).

---

## 📦 Phase 1 Features (Current)

| Feature | Status | Description |
|---------|--------|-------------|
| **Node Path Validation** | ✅ Ready | Catches `$Player` → `$PlayerCharacter` renames pre-runtime |
| **Error Explanation** | ✅ Ready | Translates Godot crashes to plain English (Adaptive model via liteLLM) |
| **Project Map** | ✅ Ready | Builds in-memory scene tree from .tscn/.gd files |
| **Log Watcher** | ✅ Ready | Monitors Godot output.log in real-time (watchfiles) |
| **RAM Monitor** | ✅ Ready | Auto-unloads models after 10min idle (diskcache) |
| **Signal Schema v1.0** | ✅ Frozen | Strict JSON protocol (instructor enforced) |
| **Token Manager** | ✅ Ready | Hard 512-token context limit (tiktoken) |
| **Adaptive Router** | ✅ Ready | Selects best model based on available RAM (liteLLM) |
| **VS Code Extension** | 🚧 Phase 3 | Coming soon |
| **E+ Language** | 🚧 Phase 4 | English → GDScript compiler |

---

## 🏆 Benchmark Standards

COM IDE must pass the **7 Pillars of Excellence** to be certified:

1. **Silent Killer Detection** – 100% pre-runtime error catch rate
2. **Context-Aware Explanation** – References specific file/line/node
3. **2GB RAM Law** – Peak memory ≤2.0GB with Godot + VS Code running
4. **T-Shaped Intelligence** – Generic polyglot, Godot god
5. **Deterministic Core** – 0% hallucination on structural facts
6. **Refactor Safety Net** – Atomic changes with ripple detection
7. **Flow State Latency** – <100ms validation, <2s explanation

### Certification Levels
- 🥉 **Bronze:** 90% tests pass, RAM ≤2.2GB
- 🥈 **Silver (Phase 1 Target):** 100% tests pass, RAM ≤2.0GB
- 🥇 **Gold (Phase 3 Target):** 100% + Torture tests, RAM ≤1.8GB

---

## 👥 Division of Labor

### Developer H (You) – Core Architect
*Focus: The Brain, The Pipeline, The Constraints.*

| Component | Libraries | Responsibility |
|-----------|-----------|----------------|
| Signal Schema v1.0 | `instructor`, `pydantic` | Define strict JSON IR for all actions |
| Intent Router | `liteLLM` | Rule-first routing, model fallback |
| RAM Monitor | `psutil`, `diskcache` | Enforce 2GB limit, trigger unload |
| Token Manager | `tiktoken` | Hard limits on context (512 tokens) |
| Observability | `logfire` | Trace every pipeline step |

### Developer S (Friend) – Domain Specialist
*Focus: The Hands, The Godot Knowledge, The Parsers.*

| Component | Libraries | Responsibility |
|-----------|-----------|----------------|
| Scene Parser | `watchfiles` | Parse `.tscn` into memory tree |
| Script Parser | `tiktoken` | Extract `$NodePath`, `@onready` from `.gd` |
| Project Map | `diskcache` | Build cross-reference graph, cache to disk |
| Log Watcher | `watchfiles` | Monitor Godot logs, trigger explanations |
| Validation Logic | N/A | Rule-based checks (no LLM) |

---

## 📅 Roadmap Overview

| Phase | Name | Timeline | Goal |
|-------|------|----------|------|
| **Phase 1** | Compiler Core | Weeks 1-4 | Terminal scanner + error explainer |
| **Phase 2** | Knowledge Layer | Weeks 5-8 | Context-aware Q&A + session memory |
| **Phase 3** | Distribution | Weeks 9-16 | VS Code extension + monetization |
| **Phase 4** | Full Product | Weeks 17-28 | E+ language + standalone IDE |

See [`COM_IDE_Roadmap.md`](./COM_IDE_Roadmap.md) for detailed sprint plans.

---

## 🧪 Running Benchmarks

```bash
# Run full benchmark suite
python tests/benchmark_harness.py --all

# Run specific pillar test
python tests/benchmark_harness.py --pillar 1  # Silent Killer Detection

# Run torture chamber
python tests/benchmark_harness.py --torture
```

---

## 🤝 Contributing

1. **Read the Golden Standard** – Understand the Compiler-AI philosophy
2. **Pick a Pillar** – Choose a benchmark to improve
3. **Write Tests First** – All contributions must include benchmark coverage
4. **Respect the 2GB Law** – No PR that breaks RAM compliance

---

## 📄 License

MIT License – Build freely, share improvements.

---

**Ready to build the compiler?** Start with [`GOLDEN_STANDARD.md`](./GOLDEN_STANDARD.md).
