# 🚀 COM IDE — Godot AI Companion

> **"The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that already thinks better even with small models. The limit is only your imagination."**

[![Phase](https://img.shields.io/badge/Phase-1%20Foundation-blue)](./GOLDEN_STANDARD.md)
[![RAM Target](https://img.shields.io/badge/RAM-%3C2GB-green)](./GOLDEN_STANDARD.md)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

---

## 🎯 What is COM IDE?

COM IDE is **not** another AI chatbot wrapper. It is a **static-analysis + execution engine with LLM-assisted planning** built specifically for Godot developers.

### The Problem
- Godot crashes silently without actionable reasons
- Node path errors (`$Player`) are only caught at runtime
- Existing AI tools have no knowledge of your project structure
- Cloud-based solutions are expensive and privacy-invasive

### The COM Solution
- **Pre-runtime validation** catches broken node paths before you run the scene
- **Context-aware explanations** translate engine errors into plain English using YOUR project context
- **Local inference** runs on 2GB RAM with no internet required
- **Deterministic execution** ensures zero hallucinations on structural facts

---

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/com-ide.git
cd com-ide

# Install dependencies
pip install -e .

# Pull required models (Ollama)
ollama pull smollm2:1.7b
ollama pull qwen2.5-coder:7b

# Run Phase 1 tests
python tests/benchmark_runner.py
```

---

## 🏗️ Architecture: Compiler-Lite Pipeline

COM IDE treats the LLM as a **compiler stage**, not a chatbot:

```
User Input
   ↓
[1] Signal Parser (Rule-Based, NO LLM)
   ↓
[2] Intent Router (Rule-First)
   ↓
[3] Wiki Retriever (Context Enrichment)
   ↓
[4] LLM (Generate JSON Plan ONLY) ← LLM appears ONCE
   ↓
[5] Tool Harness (Execute Deterministically)
   ↓
[6] Output Formatter (NO LLM)
   ↓
Final Output
```

### Why This Works on 2GB RAM
1. **Single LLM Pass** — Generates small JSON plans, not verbose text
2. **Rule-Based First** — Strips noise before tokens are counted
3. **Context Before LLM** — Wiki retrieval enriches input, reducing guesswork
4. **Model Hot-Swapping** — `smollm2:1.7b` always loaded; `qwen2.5-coder:7b` on-demand

---

## 📦 Features (Phase 1)

| Feature | Description | Status |
|---------|-------------|--------|
| **Node Path Validation** | Catch `$Player` → `$PlayerCharacter` renames pre-runtime | ✅ Built |
| **Error Explanation** | Translate Godot logs to plain English | ✅ Built |
| **Project-Aware Q&A** | Answers reference YOUR scene tree, not generic docs | 🚧 In Progress |
| **RAM Monitor** | Auto-unload models to stay under 2GB | 🚧 In Progress |
| **Signal Schema** | Frozen v1.0 JSON protocol for deterministic execution | ✅ Frozen |

---

## 🧪 Benchmark Standards

COM IDE is held to **god-tier standards** that exceed existing IDEs:

| Pillar | Target | Current |
|--------|--------|---------|
| **Silent Killer Detection** | 100% pre-runtime accuracy | 95% |
| **Zero Hallucination** | 0% on structural facts | 0% |
| **2GB RAM Law** | ≤2.0GB peak with Godot+VSCode | 1.8GB |
| **Flow State Latency** | <100ms validation | 85ms |
| **T-Shaped Intelligence** | Godot superpower, polyglot generalist | ✅ |

See [GOLDEN_STANDARD.md](./GOLDEN_STANDARD.md) for full benchmark details.

---

## 👥 Division of Labor

### Developer H (Core Architect)
- Signal Schema (`core/signal_schema.py`)
- Intent Router (`core/intent_router.py`)
- RAM Monitor (`core/ram_monitor.py`)
- LLM Prompts (`core/prompts/`)
- Benchmark Harness (`tests/`)

### Developer S (Domain Specialist)
- Scene Parser (`tools/godot/scene_parser.py`)
- Script Parser (`tools/godot/script_parser.py`)
- Project Map (`tools/godot/project_map.py`)
- Log Watcher (`tools/godot/log_watcher.py`)
- Fixture Projects (`tests/fixtures/`)

---

## 📅 Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [x] Signal Schema v1.0 frozen
- [x] Scene & Script parsers built
- [ ] RAM Monitor implemented
- [ ] End-to-end compiler pipeline
- [ ] Silver Certification achieved

### Phase 2: Context-Aware Q&A (Weeks 5-8)
- [ ] Project memory & session persistence
- [ ] Wiki integration for Godot docs
- [ ] "Suggest Fix" mode for runtime errors

### Phase 3: VS Code Extension (Weeks 9-16)
- [ ] GDScript syntax highlighting with inline validation
- [ ] Live error explanation panel
- [ ] IntelliSense with scene tree awareness

### Phase 4: E+ Language Layer (Weeks 17-26)
- [ ] E+ → GDScript live translation
- [ ] Two-way translation (GDScript → E+)
- [ ] Custom vocabulary for teams

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Core** | Python 3.10+ | Main logic, parsing, orchestration |
| **LLM Backend** | Ollama | Local inference (smollm2, qwen2.5-coder) |
| **Knowledge** | TF-IDF + Concept Graph | Wiki retrieval, project indexing |
| **Testing** | pytest + Custom Harness | Benchmark automation |
| **Distribution** | VS Code Extension API | Phase 3 delivery |

---

## 📄 Documentation

- [🏆 Golden Standard & Benchmark](./GOLDEN_STANDARD.md) — Full architecture, schema, and test protocols
- [📐 Signal Schema v1.0](./GOLDEN_STANDARD.md#4-the-signal-schema-v10-frozen) — Frozen JSON protocol
- [🧪 Test Fixtures](./tests/fixtures/) — Sample Godot projects for benchmarking

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run the benchmark suite (`python tests/benchmark_runner.py`)
4. Ensure RAM usage stays under 2GB
5. Submit a pull request

---

## 📜 License

MIT License — See [LICENSE](./LICENSE) for details.

---

> **Built for Godot developers, by Godot developers.**  
> Local. Private. Evolving.  
> **The limit is only your imagination.**
