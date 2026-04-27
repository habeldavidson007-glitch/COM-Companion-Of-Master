# COM (Cognitive Operating Module) v2.0
### The Local-First, Signal-Constrained Agentic Assistant

**COM** is a lightweight, offline-capable AI desktop assistant designed for **low-resource environments (4GB RAM)**. It bridges the gap between the probabilistic nature of Small Language Models (SLMs) and the deterministic requirements of desktop automation.

By enforcing a **Signal-of-Thought (SoT)** protocol, COM transforms a quantized 1.5B parameter model into a reliable agent capable of generating Excel reports, PDFs, PowerPoint decks, Godot scripts, and maintaining a personal knowledge wiki—all without sending data to the cloud.

---

## 🚀 Core Architecture

COM operates on a **Hybrid Probabilistic-Deterministic** architecture:

1.  **The Brain (Probabilistic):** A locally hosted **1.5B Quantized SLM** acts as a *Semantic Router*. It does not write code directly; it classifies intent and outputs structured control signals.
2.  **The Hands (Deterministic):** A Python-based **Tool Harness** executes strict logic based on those signals. This ensures 100% reliability in file I/O, math, and system operations, bypassing LLM hallucination.

### The Signal-of-Thought (SoT) Protocol
Instead of asking the LLM to "write a script," COM forces the model to output a single-line structured command:
`@XLS:Report:Date,Sales,Profit` → `Python Executor` → `report.xlsx`

This **Constraint Engineering** approach allows a tiny model to perform complex tasks by reducing its cognitive load to simple classification and slot-filling.

---

## 🧠 Key Capabilities

### 1. Multi-Domain Tool Execution
*   **📊 Office Automation:** Generates `.xlsx` (with formulas), `.pdf` (reports), and `.pptx` (decks) with collision avoidance and safe I/O.
*   **🎮 Game Dev Specialist:** Integrated **Godot Engine Expert** (`@GDT`) that generates GDScript (CharacterBody2D, shaders, plugins) using domain-specific knowledge bases.
*   **💻 Code Generation:** Dedicated experts for **Python (`@PY`)**, **C++ (`@CPP`)**, and **Web (`@WEB`)** stacks with safety analysis.
*   **📚 Personal Knowledge Wiki:** Incremental compilation of research notes. Ingests raw data (PDFs, URLs) into a structured Markdown wiki with auto-linking, concept extraction, and integrity health checks (`@WIKI`).

### 2. Advanced Routing & Memory
*   **Hierarchical Specificity Scoring:** Resolves keyword collisions (e.g., "game design doc" vs. "excel sheet") using weighted density scoring rather than simple first-match.
*   **Salience-Filtered Memory:** A sliding window deque that retains only high-salience context, preventing context runaway on low-RAM machines.
*   **Dual-Layer Caching:** Deduplicates repeated queries at both the intent and execution layers.

### 3. Production-Grade Reliability
*   **Auto-Repair Loop:** If the LLM outputs malformed signals, an automated regex-based repair engine attempts to fix the syntax before failing.
*   **Concurrency Safety:** Thread-safe tool harness with LRU caching and timeout guards.
*   **Secure I/O:** All file operations are sandboxed to `./data/com_output/` with path traversal protection.

---

## 🛠 Technical Specifications

| Component | Specification |
| :--- | :--- |
| **Model Backend** | **1.5B Parameter Quantized SLM** (e.g., Qwen2.5-1.5B-Instruct-Q4_K_M) |
| **Runtime** | Python 3.8+ (Tkinter UI, Ollama/Llama.cpp backend) |
| **RAM Footprint** | < 2.5GB Idle (Optimized for 4GB systems) |
| **Routing Logic** | Hybrid Keyword Density + LLM Tie-Breaker |
| **Memory Model** | Salience-weighted Deque + Micro-RAG |
| **Signal Types** | `@XLS`, `@PDF`, `@PPT`, `@GDT`, `@PY`, `@CPP`, `@WEB`, `@WIKI`, `@ERR` |

---

## 📂 Project Structure

```text
COM/
├── bin/                      # Executable entry points
│   ├── com_gui.py           # Tkinter GUI launcher
│   └── com_cli.py           # Command-line interface
├── src/com/                  # Source code package
│   ├── core/
│   │   ├── com_core.py      # Main loop, memory, salience, normalization
│   │   └── intent_router.py # Hierarchical specificity scoring & weighting
│   ├── tools/
│   │   ├── tool_harness.py  # Unified executor, safe_write, concurrency
│   │   ├── excel_tool.py    # XLSX generation
│   │   ├── pdf_tool.py      # PDF generation
│   │   ├── ppt_tool.py      # PPTX generation
│   │   ├── game_dev/
│   │   │   └── godot_engine.py  # Godot specialist (500+ lines of logic)
│   │   ├── languages/
│   │   │   ├── python_expert.py
│   │   │   ├── cpp_expert.py
│   │   │   └── web_stack.py
│   │   └── data_ops/
│   │       └── wiki_compiler.py # Knowledge base ingestion & health checks
│   └── utils/               # Shared utilities
├── tests/                    # Test suite & benchmarks
├── docs/                     # Extended documentation
├── scripts/                  # Maintenance & utility scripts
├── data/                     # Runtime data (git-ignored)
│   ├── raw/                 # Raw data ingest for Wiki
│   ├── wiki/                # Compiled Markdown knowledge base
│   └── com_output/          # Sandboxed output directory
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites
1.  **Ollama** installed and running.
2.  Pull the model: `ollama pull qwen2.5:1.5b` (or your preferred 1.5B quant).
3.  Install dependencies: `pip install -r requirements.txt`

### Running COM
```bash
# GUI Mode
python bin/com_gui.py

# CLI Mode
python bin/com_cli.py "create an excel report of sales"

# Run Tests
pytest tests/
```

### Example Interactions
*   *"Create an excel sheet of my monthly expenses with columns for Date, Item, and Cost."*
    *   → Routes to `@XLS`, generates `data/com_output/expenses_2026.xlsx`.
*   *"Write a 2D movement script for Godot 4."*
    *   → Routes to `@GDT`, invokes `GodotEngineTool`, generates `data/com_output/movement.gd`.
*   *"Ingest these three papers on LLM agents and compile a wiki summary."*
    *   → Routes to `@WIKI:INGEST`, updates `data/wiki/` with linked markdown files.

---

## 🏆 Benchmark Performance
**Current Score: 95%+ (323/340 Tests)**
*   **100%** Pass Rate on Tool Execution (Excel, PDF, PPT, Godot).
*   **100%** Pass Rate on Concurrency Stress Tests (100 threads).
*   **Fixed** critical routing collisions and regex parsing errors in v2.0.

---

## 📜 License & Philosophy
COM is built on the theory that **local AI should be an operating system extension, not just a chatbot.** By separating *intent recognition* (LLM) from *execution* (Code), we achieve reliability impossible with pure generative models, all while respecting user privacy and hardware constraints.
