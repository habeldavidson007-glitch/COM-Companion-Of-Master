# COM v4 - Cognitive Architecture Repository Structure

```
com-v4/
├── core/                       # The "Brain" - Agent loop, Context Manager, Reflection Module
│   ├── __init__.py
│   ├── agent_loop.py           # Thought -> Action -> Observation -> Reflection -> Response cycle
│   ├── context_manager.py      # Context compression and Wiki injection
│   └── reflection_module.py    # Self-verification and error analysis
│
├── tools/                      # The "Hands" - Secure execution, Wiki Compiler, Live Fetcher
│   ├── __init__.py
│   ├── secure_executor.py      # Sandboxed subprocess execution with timeouts
│   ├── wiki_compiler.py        # Compiles raw knowledge into structured chunks
│   └── live_fetcher.py         # Optional: fetch external data (with safety limits)
│
├── knowledge/                  # The "Long-Term Memory"
│   ├── raw/                    # Raw markdown/text files dropped by users
│   │   └── .gitkeep
│   ├── compiled_wiki/          # Processed, chunked knowledge base
│   │   └── .gitkeep
│   └── vector_indices/         # Embedding indices for fast retrieval
│       └── .gitkeep
│
├── config/                     # The "Personality" - Modelfile templates, System Prompts
│   ├── modelfile_cognitive_v4  # Ollama Modelfile optimized for 1.5B models
│   ├── system_prompt.txt       # Base system instructions
│   └── few_shot_examples.json  # Structured examples for complex reasoning
│
├── interface/                  # User interaction layer
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   └── api.py                  # REST API endpoints (optional)
│
├── tests/                      # Validation suite
│   ├── __init__.py
│   ├── test_agent_loop.py
│   ├── test_context_manager.py
│   └── test_tools.py
│
├── README.md                   # Integration guide and documentation
├── requirements.txt            # Minimal dependencies
└── main.py                     # Entry point
```

## Directory Purpose Summary

| Directory | Role | Key Files |
|-----------|------|-----------|
| `core/` | Cognitive engine driving the reflection loop | `agent_loop.py`, `context_manager.py` |
| `tools/` | Safe tool execution and knowledge processing | `secure_executor.py`, `wiki_compiler.py` |
| `knowledge/` | Persistent memory storage | Raw input → Compiled chunks → Vector indices |
| `config/` | Model personality and behavior tuning | `modelfile_cognitive_v4` |
| `interface/` | User-facing interaction | CLI and API |
| `tests/` | Quality assurance | Unit tests for all core components |
