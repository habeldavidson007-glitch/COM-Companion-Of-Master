# COM (Cognitive Operating Module) v2.0

## Professional Repository Structure

```
COM/
├── bin/                    # Entry points
│   ├── com_gui.py         # Tkinter GUI launcher
│   └── com_cli.py         # Command-line interface
├── src/com/               # Source code
│   ├── core/              # Core logic (routing, memory, normalization)
│   ├── tools/             # Tool implementations
│   │   ├── game_dev/      # Godot specialist
│   │   ├── languages/     # Python, C++, Web experts
│   │   └── data_ops/      # Wiki compiler, doc scanner
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scripts/               # Maintenance scripts
├── data/                  # Runtime data (git-ignored)
│   ├── raw/               # Raw data ingest
│   ├── wiki/              # Compiled knowledge base
│   └── com_output/        # Generated files
├── .gitignore
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# GUI Mode
python bin/com_gui.py

# CLI Mode
python bin/com_cli.py "create excel report"

# Run Tests
pytest tests/
```

## Features

- **Signal-of-Thought Protocol**: Structured AI commands for deterministic execution
- **Multi-Domain Tools**: Excel, PDF, PPT, Godot, Python, C++, Web
- **Personal Knowledge Wiki**: Auto-compile research into linked markdown
- **Low-RAM Optimized**: Runs on 4GB systems with 1.5B quantized models

See `docs/README.md` for full documentation.
