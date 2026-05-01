# COM IDE — Golden Standard Repository Structure
## For 2-3GB RAM Constraint | Godot AI Companion Focus

---

## Executive Summary

**Current State:** The repository has accumulated 6 versions of benchmark iterations with legacy code, unused directories, and features that exceed the 2-3GB RAM constraint.

**Target:** A lean, focused COM IDE for Godot developers that runs on minimal hardware while delivering maximum value through local inference.

**Golden Standard Principle:** Every file must justify its existence by either:
1. Directly supporting Phase 1 (Project Scanner + Error Explainer)
2. Being part of the core signal architecture that enables Phase 2+
3. Providing essential infrastructure (config, logging, safe I/O)

---

## Recommended Repository Tree (Golden Standard)

```
com_ide/
├── README.md                          # Keep - Update with 2-3GB focus
├── pyproject.toml                     # Keep - Packaging ready
├── requirements.txt                   # Keep - Pin to RAM-efficient deps
├── config.py                          # Keep - ModelConfig + SystemConfig
│
├── core/                              # CORE SIGNAL ARCHITECTURE
│   ├── __init__.py
│   ├── com_core.py                    # Keep - OllamaClient with health check
│   ├── intent_router.py               # Keep - 6-mode routing (GODOT, WIKI, etc.)
│   ├── context_compressor.py          # KEEP BUT OPTIMIZE - Reduce context window
│   ├── session_logger.py              # Keep - JSONL logging for debugging
│   └── memory_manager.py              # NEW - Sliding window with salience filter
│
├── tools/                             # TOOL LAYER
│   ├── __init__.py
│   ├── base.py                        # Keep - BaseTool interface
│   ├── tool_harness.py                # Keep - Fix @GDT alias bug first!
│   ├── safe_io.py                     # Keep - Atomic writes, path protection
│   │
│   ├── godot/                         # RENAMED FROM game_dev/ - GODOT IDE FOCUS
│   │   ├── __init__.py
│   │   ├── scene_parser.py            # NEW - Parse .tscn files (~150 lines)
│   │   ├── script_parser.py           # NEW - Parse .gd files, extract $NodePath
│   │   ├── project_map.py             # NEW - Unified scene tree + script refs
│   │   └── log_watcher.py             # NEW - Async file watcher on output.log
│   │
│   ├── data_ops/                      # KNOWLEDGE LAYER
│   │   ├── __init__.py
│   │   ├── wiki_compiler.py           # Keep - FIX truncation bug (line 307)
│   │   ├── wiki_indexer.py            # Keep - Concept graph + backlinks
│   │   └── wiki_retriever.py          # EXTRACT FROM wiki_compiler.py - TF-IDF
│   │
│   └── system/                        # SYSTEM TOOLS
│       ├── __init__.py
│       └── desktop_harness.py         # Keep - File operations
│
├── utils/                             # INFRASTRUCTURE
│   ├── __init__.py
│   ├── background_service.py          # Keep - BackgroundWikiService daemon
│   └── ram_monitor.py                 # NEW - RAM usage tracker + auto-unload
│
├── frontend/                          # UI LAYER (Phase 1: Minimal)
│   ├── __init__.py
│   ├── viewer.py                      # Keep - Tkinter base (RAM-efficient)
│   └── ide_window.py                  # NEW - 3-panel UI (Errors, Warnings, Chat)
│
├── scripts/                           # UTILITY SCRIPTS
│   ├── __init__.py
│   ├── setup_models.py                # NEW - Pull smollm2:1.7b, qwen2.5-coder:7b
│   └── benchmark_ram.py               # NEW - RAM profiling for each component
│
├── tests/                             # TESTING
│   ├── __init__.py
│   ├── test_scene_parser.py           # NEW - 10 unit tests for .tscn parsing
│   ├── test_script_parser.py          # NEW - 10 unit tests for .gd parsing
│   ├── test_project_map.py            # NEW - Integration tests
│   └── test_wiki_integration.py       # Keep - Existing wiki tests
│
├── data/                              # RUNTIME DATA (GitIgnored)
│   ├── wiki/                          # Compiled knowledge base
│   ├── raw/                           # Source documents for wiki
│   ├── cache/                         # LRU response cache
│   └── projects/                      # Indexed Godot project metadata
│
├── com_output/                        # GENERATED FILES
│   └── .gitkeep
│
└── docs/                              # DOCUMENTATION
    ├── architecture_v4.md             # Keep - Signal-of-Thought protocol
    ├── reflective_signal_protocol.md  # Keep - LLM response parsing
    ├── ram_optimization_guide.md      # NEW - 2-3GB specific optimizations
    └── phase1_implementation.md       # NEW - Week-by-week tasks
```

---

## Files to DELETE Immediately

### 1. Legacy Benchmark Directories
```
DELETE: /workspace/benchmark and test review/
DELETE: /workspace/benchmark_results.json
DELETE: /workspace/core/1/               # Empty directory
DELETE: /workspace/core/core_improvement_roadmap.md  # Superseded by this doc
DELETE: /workspace/tools/2/              # Unknown legacy directory
DELETE: /workspace/frontend/3/           # Unknown legacy directory
```

### 2. Unused Excel/Test Files
```
DELETE: /workspace/Inventory.xlsx
DELETE: /workspace/ParallelTest1.xlsx
DELETE: /workspace/Sales.xlsx
DELETE: /workspace/TestReport.xlsx
DELETE: /workspace/test.xlsx
DELETE: /workspace/com_output/TestReport.xlsx
```

### 3. Redundant Documentation
```
DELETE: /workspace/docs/__pycache__/     # Python cache
DELETE: /workspace/docs/architecture_v4.py        # Duplicate of .md version
DELETE: /workspace/docs/system_prompt_v3.py       # Obsolete v3
DELETE: /workspace/docs/system_prompt_v3.txt      # Obsolete v3
DELETE: /workspace/docs/system_prompt_v4_reflective.py  # Duplicate
DELETE: /workspace/docs/v4_implementation_summary.py    # Duplicate
```

### 4. Language Expert Tools (Not Needed for Phase 1)
```
DELETE: /workspace/tools/languages/      # Entire directory
       ├── cpp_expert.py
       ├── javascript_expert.py
       ├── json_expert.py
       ├── python_expert.py
       ├── python_expert_run.py
       └── web_stack.py
```
**Rationale:** These are general-purpose coding assistants. COM IDE is specialized for Godot + GDScript only in Phase 1. Reclaim ~800 lines of unused code.

### 5. Office Tools (Defer to Phase 3+)
```
KEEP BUT ISOLATE: /workspace/tools/excel_tool.py    # Not needed for Phase 1
KEEP BUT ISOLATE: /workspace/tools/ppt_tool.py      # Not needed for Phase 1
KEEP BUT ISOLATE: /workspace/tools/pdf_tool.py      # Not needed for Phase 1
```
**Action:** Move to `tools/_deferred/` directory to signal they're not in active use.

### 6. Game Dev Tool Refactor
```
RENAME: /workspace/tools/game_dev/ → /workspace/tools/godot/
DELETE: /workspace/tools/game_dev/godot_engine.py   # Too generic, rewrite for IDE
DELETE: /workspace/tools/game_dev/godot_engine_run.py
```
**Rationale:** Current files are knowledge-base aggregators, not project parsers. Need fresh implementation for Phase 1.

### 7. Node.js Artifacts (Accidental)
```
DELETE: /workspace/node_modules/         # Accidental npm install
DELETE: /workspace/package.json
DELETE: /workspace/package-lock.json
DELETE: /workspace/test.js
DELETE: /workspace/com_ide_roadmap.js    # Roadmap already exported as .docx
```

### 8. Miscellaneous
```
DELETE: /workspace/com_mov_2d.gd         # Random GDScript file
DELETE: /workspace/com_output.gd         # Random GDScript file
DELETE: /workspace/harness.py            # Duplicate of tools/tool_harness.py
DELETE: /workspace/com_chat.py           # Superseded by new architecture
DELETE: /workspace/benchmark.py          # Old benchmark runner
```

### 9. Python Cache Everywhere
```
DELETE: /workspace/**/__pycache__/       # All pycache directories
```

---

## Critical Bug Fixes Before Phase 1

### Fix #1: @GDT Alias (tools/tool_harness.py)
**Location:** Line 217-222 (`_check_all_tools`) and Line 740-744 (`executors` dict)

**Problem:** `health_checker.tool_status` has no "GDT" key. `is_tool_available("GDT")` returns False.

**Fix:**
```python
# In _check_all_tools():
self.tool_status = {
    'XLS': self._check_excel_tool(),
    'PPT': self._check_powerpoint_tool(),
    'PDF': self._check_pdf_tool(),
    'GODOT': self._check_godot_tool(),
    'GDT': self._check_godot_tool()  # ADD THIS LINE - alias to GODOT
}

# In execute_signal() executors dict (line 740):
executors = {
    'XLS': execute_xls,
    'PPT': execute_ppt,
    'PDF': execute_pdf,
    'GODOT': execute_godot,
    'GDT': execute_godot  # ADD THIS LINE
}
```

### Fix #2: WikiRetriever TF-IDF Truncation (tools/data_ops/wiki_compiler.py)
**Location:** Line 307 in `WikiRetriever.load_wiki()`

**Problem:** `self.documents[path] = content[:2000]` truncates ALL documents to 2000 chars before indexing.

**Fix:**
```python
class WikiRetriever:
    def __init__(self, data_dir: str):
        self.io = SafeIO(data_dir)
        self.documents: Dict[str, str] = {}  # path -> FULL content
        self.snippets: Dict[str, str] = {}   # path -> preview (first 200 chars)
        self.idf: Dict[str, float] = {}
        self._loaded = False

    def load_wiki(self) -> None:
        self.documents = {}
        self.snippets = {}  # ADD THIS
        
        try:
            md_files = self.io.list_files("wiki", "*.md")
            
            for path in md_files:
                if path == "wiki/_index.md":
                    continue
                
                try:
                    content = self.io.read_text(path)
                    self.documents[path] = content      # STORE FULL CONTENT
                    self.snippets[path] = content[:200] # SEPARATE PREVIEW
                except Exception:
                    continue
            
            self._compute_idf()
            self._loaded = True
            
        except Exception:
            self._loaded = False

    def search(self, query: str, top_k: int = 5) -> List[tuple]:
        # ... scoring logic unchanged ...
        
        results = []
        for path, score in sorted_results:
            content = self.documents[path]  # Use FULL content for snippet extraction
            snippet = content[:200].replace("\n", " ").strip() + "..."
            # OR BETTER: extract snippet around matched terms
            results.append((path, snippet, score))
        
        return results
```

---

## RAM Optimization Strategy (2-3GB Target)

### Memory Budget Breakdown
| Component | Base RAM | Burst RAM | Notes |
|-----------|----------|-----------|-------|
| **smollm2:1.7b** | 1.2 GB | 1.2 GB | Always loaded (intent routing) |
| **qwen2.5-coder:7b** | 0 GB | 4.5 GB | Load-on-demand, unload after 10 min idle |
| **COM Core** | 0.3 GB | 0.5 GB | Intent router, wiki indexer, session logger |
| **Godot Project Index** | 0.1 GB | 0.3 GB | Scales with project size |
| **UI (Tkinter)** | 0.1 GB | 0.1 GB | Minimal 3-panel interface |
| **OS + Godot Editor** | 1.5 GB | 2.0 GB | Outside COM, but must coexist |
| **TOTAL** | **~3.2 GB** | **~8.6 GB** | Must manage burst carefully |

### Key Techniques

#### 1. Model Hot-Swapping
```python
# utils/model_manager.py
class ModelManager:
    def __init__(self):
        self.loaded_model = None
        self.last_used = {}
        self.idle_timeout = 600  # 10 minutes
    
    def ensure_model(self, model_name: str):
        """Load model if not loaded, unload others."""
        if self.loaded_model != model_name:
            if self.loaded_model:
                self._unload_model(self.loaded_model)
            self._load_model(model_name)
            self.loaded_model = model_name
        self.last_used[model_name] = time.time()
    
    def check_idle_unload(self):
        """Unload models idle for >10 minutes."""
        now = time.time()
        if self.loaded_model and (now - self.last_used.get(self.loaded_model, 0) > self.idle_timeout):
            self._unload_model(self.loaded_model)
            self.loaded_model = None
```

#### 2. Response Streaming (Prevent RAM Spike)
```python
# core/com_core.py
def generate_stream(self, prompt: str, model: str = "smollm2:1.7b"):
    """Stream response token-by-token instead of buffering full response."""
    response = ""
    for chunk in self.client.generate_stream(prompt, model=model):
        token = chunk['token']
        response += token
        yield token  # Yield immediately, don't buffer
        if len(response) > 500:  # Hard limit for fast replies
            break
```

#### 3. Aggressive Context Window Discipline
```python
# core/context_compressor.py
MAX_CONTEXT_TOKENS = 512  # Reduce from 2048 for 2-3GB RAM

def compress_context(self, context: str, max_tokens: int = MAX_CONTEXT_TOKENS):
    """Aggressively truncate context while preserving key info."""
    tokens = context.split()
    if len(tokens) <= max_tokens:
        return context
    
    # Keep first 60% and last 40% (preserves intro + conclusion)
    split_point = int(max_tokens * 0.6)
    return " ".join(tokens[:split_point]) + " ... " + " ".join(tokens[-(max_tokens-split_point):])
```

#### 4. Query Classification Before LLM
```python
# core/intent_router.py
def route_with_rules_first(self, query: str):
    """Use rule-based classification before invoking LLM."""
    # Fast path: keyword matching (no RAM cost)
    if any(kw in query.lower() for kw in ["$NodePath", "@onready", "signal"]):
        return {"mode": "GODOT", "method": "keyword", "ram_cost": 0}
    
    # Slow path: LLM classification (1.2GB RAM for smollm2)
    if self.client:
        return self._llm_classify(query)
    
    return {"mode": "GENERAL", "method": "fallback"}
```

#### 5. RAM Monitor with Auto-Unload
```python
# utils/ram_monitor.py
import psutil

class RAMMonitor:
    def __init__(self, max_ram_gb: float = 2.5):
        self.max_ram = max_ram_gb * 1024 * 1024 * 1024
        self.model_manager = None  # Injected
    
    def check_and_unload(self):
        """If RAM > 90% of limit, unload largest model."""
        current_ram = psutil.Process().memory_info().rss
        if current_ram > self.max_ram * 0.9:
            if self.model_manager and self.model_manager.loaded_model:
                self.model_manager.unload_model(self.model_manager.loaded_model)
                logger.warning(f"RAM critical: unloaded {self.model_manager.loaded_model}")
```

---

## Phase 1 Implementation Checklist (Week-by-Week)

### Week 1 — Godot Project Parser
- [ ] Create `tools/godot/scene_parser.py` (150 lines)
  - Parse `.tscn` format (text-based, well-documented)
  - Extract: node name, type, parent path
  - Output: `Dict[node_path] -> {type, parent, properties}`
  
- [ ] Create `tools/godot/script_parser.py` (150 lines)
  - Parse `.gd` files with regex
  - Extract: `@onready var`, `$NodePath` strings, `signal.connect()`
  - Output: `List[{file, line, node_path, type}]`

- [ ] Create `tools/godot/project_map.py` (100 lines)
  - Combine scene tree + script references
  - Build unified in-memory representation
  - Method: `validate_node_paths()` → `List[ValidationError]`

- [ ] Write 10 unit tests
  - Test nested scenes, inherited scripts, renamed nodes

### Week 2 — Node Path Validator + Log Watcher
- [ ] Implement `ProjectMap.validate_node_paths()`
  - Return `ValidationError(file, line, path, suggestion)`
  - Add similarity matching: `$Player` not found → suggest `$PlayerCharacter`

- [ ] Create `tools/godot/log_watcher.py` (50 lines)
  - `asyncio` file watcher on Godot's `output.log`
  - Emit new log lines as events

- [ ] Wire log watcher through OllamaClient
  - Inject `ProjectMap` as context
  - Prompt: "Explain this error using project context: {error}"

### Week 3 — First UI (Tkinter)
- [ ] Create `frontend/ide_window.py` (200 lines)
  - Three panels: Errors, Warnings, Chat
  - Reuse `frontend/viewer.py` pattern

- [ ] Errors panel
  - Show `ValidationError` list
  - Update on file change (watch `.godot` directory)

- [ ] Chat panel
  - Accept developer questions
  - Inject `ProjectMap` context
  - Return Ollama response via `smollm2:1.7b`

- [ ] "Explain last error" button
  - Take most recent Godot log line
  - Send to Ollama with project context

### Week 4 — Integration + Polish
- [ ] Test against 3 real Godot projects
  - Your own project
  - 2 open-source projects from GitHub

- [ ] Document false positives/negatives
  - Track every incorrect validation

- [ ] Fix top 5 most common false positives

- [ ] Record 60-second demo
  - Start COM IDE
  - Open Godot project with known bug
  - Show COM finding it

---

## What Makes This the Golden Standard?

### 1. Single Responsibility
Every file has one clear purpose. No "kitchen sink" modules.

### 2. RAM-Aware Design
- Lazy loading everywhere
- Model hot-swapping
- Aggressive caching with LRU eviction
- Streaming responses (no buffering)

### 3. Testable Units
- Each parser is <200 lines
- Unit tests for edge cases
- Integration tests for full workflow

### 4. Progressive Enhancement
- Phase 1 works standalone
- Phase 2 adds wiki knowledge
- Phase 3 adds VS Code extension
- No phase blocks another

### 5. Debuggable
- JSONL session logs
- RAM monitoring
- Health checks on startup

---

## Next Actions (This Week)

1. **Run cleanup script** (provided below)
2. **Fix @GDT alias bug** (30 minutes)
3. **Fix WikiRetriever truncation** (45 minutes)
4. **Create `tools/godot/` directory**
5. **Write `scene_parser.py`** (first 50 lines)

---

## Cleanup Script

```bash
#!/bin/bash
# cleanup.sh - Remove all legacy files

echo "Starting cleanup..."

# Delete benchmark artifacts
rm -rf "benchmark and test review/"
rm -f benchmark_results.json
rm -rf core/1/
rm -f core/core_improvement_roadmap.md

# Delete legacy directories
rm -rf tools/2/
rm -rf frontend/3/
rm -rf tools/languages/
rm -rf node_modules/

# Delete test files
rm -f Inventory.xlsx ParallelTest1.xlsx Sales.xlsx TestReport.xlsx test.xlsx
rm -f com_output/TestReport.xlsx

# Delete documentation duplicates
rm -rf docs/__pycache__/
rm -f docs/architecture_v4.py
rm -f docs/system_prompt_v3.py docs/system_prompt_v3.txt
rm -f docs/system_prompt_v4_reflective.py
rm -f docs/v4_implementation_summary.py

# Delete game dev tools (to be rewritten)
rm -f tools/game_dev/godot_engine.py tools/game_dev/godot_engine_run.py

# Delete Node.js artifacts
rm -f package.json package-lock.json test.js com_ide_roadmap.js

# Delete miscellaneous
rm -f com_mov_2d.gd com_output.gd harness.py com_chat.py benchmark.py

# Delete Python caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Rename game_dev to godot
mv tools/game_dev tools/godot 2>/dev/null || mkdir -p tools/godot

echo "Cleanup complete!"
```

---

**Document Version:** 1.0  
**Compiled:** May 2026  
**Status:** Ready for Phase 1 Implementation  
