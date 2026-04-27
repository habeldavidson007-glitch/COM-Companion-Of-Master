# COM Harness Tools

Personal knowledge base harness with wiki compilation, TF-IDF retrieval, and LLM integration.

## Architecture

```
src/com/
├── core/          # LLM client (Ollama + SmolLM2)
├── tools/         # Utilities (safe_io, signal_parser)
└── wiki/          # Wiki system (compiler, indexer, retriever, health)

data/              # Git-ignored runtime data
├── raw/           # Source documents
├── wiki/          # Compiled markdown wiki
└── logs/          # Health reports and logs

bin/               # CLI entry points
```

## Installation

```bash
pip install -e .
```

## Usage

### Initialize data directories
```bash
com init
```

### Compile raw documents to wiki
```bash
# Place markdown/text files in data/raw/, then:
com compile

# Force recompile all
com compile --force
```

### Search wiki
```bash
com search "your query here"
```

### View index statistics
```bash
com index
```

### Run health check
```bash
com health
com health --export  # Save report to JSON
```

### Test signal parsing
```bash
com signal "@XLS:file.xlsx:col=A1 @FILE:doc.pdf"
com signal "text" --test-strict
```

## Your Role vs Friend's Role

**Your responsibilities (Harness Builder):**
- ✅ Repository structure and packaging (`pyproject.toml`)
- ✅ File I/O safety and validation (`safe_io.py`)
- ✅ Signal contract enforcement (`signal_parser.py`)
- ✅ Wiki compilation pipeline (`compiler.py`)
- ✅ Indexing and metadata (`indexer.py`)
- ✅ TF-IDF retrieval system (`retriever.py`)
- ✅ Health monitoring (`health.py`)
- ✅ CLI interface (`bin/com`)
- ✅ LLM client configuration (`client.py`)

**Friend's responsibilities (Core/Brain):**
- 🧠 System prompt design and tuning
- 🧠 Knowledge synthesis logic
- 🧠 Semantic evaluation strategies
- 🧠 Agent reasoning patterns
- 🧠 Concept extraction quality
- 🧠 Cross-document inference

**Boundary:** You build the deterministic infrastructure; they configure the probabilistic intelligence. The interface is the prompt/context window.

## Model Configuration

Default: `smollm2:1.7b-instruct-q4_K_M`
- Optimized for <2GB RAM
- Tighter context limits than Qwen
- Requires shorter, direct system prompts

## Next Steps

1. Add sample documents to `data/raw/`
2. Run `com compile` to build initial wiki
3. Use `com search` to query knowledge
4. Run `com health` regularly for maintenance
