# COM v4 Migration Plan - Incremental Upgrade (Option B)

## Executive Summary
This document outlines the **incremental upgrade path** to transform your existing V3 COM system into the V4 Cognitive Architecture without breaking existing functionality.

---

## Current State Analysis

### ✅ What You Have (V3 Foundation)
| Component | File | Status |
|-----------|------|--------|
| Signal-of-Thought Core | `core/com_core.py` | Working (811 lines) |
| Desktop UI | `com_chat.py` | Working (Tkinter) |
| Intent Router | `core/intent_router.py` | Integrated |
| Context Compressor | `core/context_compressor.py` | Integrated |
| Session Logger | `core/session_logger.py` | Integrated |
| Office Tools | `tools/excel_tool.py`, `pdf_tool.py`, `ppt_tool.py` | Working |
| Godot Tools | `tools/game_dev/` | Working |
| Wiki Components | `tools/wiki_compiler.py` | Present |
| Agent Loop (V4) | `core/agent_loop.py` | Created but NOT integrated |
| Context Manager (V4) | `core/context_manager.py` | Created but NOT integrated |
| Reflection Module (V4) | `core/reflection_module.py` | Created but NOT integrated |
| Modelfile | `config/modelfile_cognitive_v4` | Updated for qwen2.5:0.5b |

### ❌ Critical Gaps Identified
1. **No Integration**: `agent_loop.py` exists but `com_core.py` doesn't use it
2. **Dual Systems**: V3 logic runs in production, V4 code sits unused
3. **Model Mismatch**: Your custom model was built but `ollama run` bypasses Python loop
4. **Entry Point Confusion**: `main.py` imports non-existent classes

---

## The Problem: Why `ollama run` Failed

When you ran:
```powershell
ollama run com-v4-cognitive "What is the capital of France?"
```

The model responded incorrectly because:
- **No Python Loop**: The reflection mechanism lives in Python, not in the model
- **Template Conflict**: qwen2.5 has native chat templates that override custom TEMPLATE directives
- **Standalone Mode**: `ollama run` sends single prompts without the Thought→Action→Reflection cycle

**Solution**: Always use the Python entry point (`python main.py` or `com_chat.py`), never `ollama run` directly.

---

## Migration Strategy: Option B (Incremental Upgrade)

### Phase 1: Fix the Modelfile ✅ DONE
- Removed conflicting TEMPLATE directive
- Added stop sequences for structured tags
- Optimized SYSTEM prompt for 0.5B model
- Added concrete few-shot examples

**Command to rebuild:**
```powershell
ollama rm com-v4-cognitive
ollama create com-v4-cognitive -f config\modelfile_cognitive_v4
```

### Phase 2: Integrate V4 Agent Loop into V3 Core

#### Step 2.1: Update `core/__init__.py`
Export both V3 and V4 components for backward compatibility:

```python
# V3 Components (existing)
from .com_core import COMCore, classify_mode, is_signal, parse_signal

# V4 Components (new exports)
from .agent_loop import CognitiveAgent, ThoughtStep, AgentResponse
from .context_manager import ContextManager
from .reflection_module import ReflectionEngine

__all__ = [
    # V3
    'COMCore', 'classify_mode', 'is_signal', 'parse_signal',
    # V4
    'CognitiveAgent', 'ThoughtStep', 'AgentResponse',
    'ContextManager', 'ReflectionEngine'
]
```

#### Step 2.2: Create Hybrid Core Wrapper
Create `core/cognitive_engine.py`:

```python
"""
COM v4 Cognitive Engine - Wrapper for V3/V4 Integration
This bridges the existing COMCore with the new CognitiveAgent loop.
"""

from .com_core import COMCore
from .agent_loop import CognitiveAgent
from .context_manager import ContextManager

class CognitiveEngine:
    """
    Unified engine that uses V4 cognitive loop when available,
    falls back to V3 SoT for mode-specific tasks.
    """
    
    def __init__(self, use_v4=True):
        self.use_v4 = use_v4
        self.v3_core = COMCore()
        
        if use_v4:
            self.context_manager = ContextManager()
            self.v4_agent = CognitiveAgent(
                model_name="com-v4-cognitive",
                context_manager=self.context_manager,
                tools=self._build_v4_tools()
            )
        else:
            self.v4_agent = None
    
    def _build_v4_tools(self):
        """Build tool dictionary for V4 agent."""
        return {
            "wiki_search": lambda q: self.context_manager.inject_wiki_context(q),
            "execute_code": lambda c: self.v3_core.client.generate([
                {"role": "user", "content": f"Execute: {c}"}
            ]),
        }
    
    def process_query(self, query: str, callback=None) -> str:
        """Route to V4 or V3 based on query type and configuration."""
        if not self.use_v4:
            return self.v3_core.process_query(query, callback)
        
        # Use V4 for complex reasoning, knowledge queries
        if self._is_complex_query(query):
            response = self.v4_agent.run(query)
            if callback:
                callback(response.answer)
            return response.answer
        else:
            # Fall back to V3 for simple mode-specific tasks
            return self.v3_core.process_query(query, callback)
    
    def _is_complex_query(self, query: str) -> bool:
        """Determine if query needs V4 cognitive processing."""
        complex_indicators = [
            'explain', 'analyze', 'compare', 'why', 'how does',
            'what is the relationship', 'evaluate', 'discuss'
        ]
        query_lower = query.lower()
        return any(ind in query_lower for ind in complex_indicators)
```

#### Step 2.3: Update `main.py` Entry Point
Fix the broken imports:

```python
"""
COM v4 - Main Entry Point
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import hybrid engine instead of raw components
from core.cognitive_engine import CognitiveEngine


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def interactive_mode(engine: CognitiveEngine):
    """Run interactive chat mode."""
    print("\n" + "="*60)
    print("COM v4 Cognitive Agent - Interactive Mode")
    print("="*60)
    print("Commands: /quit, /clear, /stats, /toggle (V3↔V4)")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() == '/quit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == '/toggle':
                engine.use_v4 = not engine.use_v4
                mode = "V4 Cognitive" if engine.use_v4 else "V3 SoT"
                print(f"Switched to {mode} mode\n")
                continue
            
            elif user_input.lower() == '/clear':
                engine.v3_core.clear_memory()
                print("Memory cleared.\n")
                continue
            
            print("Thinking...", end="", flush=True)
            response = engine.process_query(user_input)
            print(f"\n\nCOM: {response}\n{'-'*60}\n")
            
        except KeyboardInterrupt:
            print("\nType /quit to exit.")
        except Exception as e:
            print(f"\nError: {e}")


def main():
    setup_logging()
    
    print("="*60)
    print("COM v4 - Cognitive Architecture")
    print("Making 0.5B models perform with deeper reasoning")
    print("="*60 + "\n")
    
    # Initialize hybrid engine
    engine = CognitiveEngine(use_v4=True)
    print("Cognitive engine ready!\n")
    
    interactive_mode(engine)


if __name__ == "__main__":
    main()
```

#### Step 2.4: Update `com_chat.py` (Optional V4 Toggle)
Add a toggle button in the UI to switch between V3 and V4 modes:

```python
# In __init__, add:
self.use_v4_mode = tk.BooleanVar(value=False)
self.engine = CognitiveEngine(use_v4=False)  # Start with V3

# Add menu item or button:
v4_toggle = tk.Checkbutton(
    header_frame, 
    text="V4 Cognitive Mode",
    variable=self.use_v4_mode,
    command=self._toggle_v4_mode,
    bg='#111736', fg='#C9A84C'
)
v4_toggle.pack(side=tk.RIGHT, padx=10)

def _toggle_v4_mode(self):
    self.engine.use_v4 = self.use_v4_mode.get()
    mode = "V4 ON" if self.use_v4_mode.get() else "V3 OFF"
    self.status_label.config(text=f"Mode: {mode}")
```

---

## Testing Strategy

### Test 1: Rebuild Model
```powershell
ollama rm com-v4-cognitive
ollama create com-v4-cognitive -f config\modelfile_cognitive_v4
ollama run com-v4-cognitive "What is 2+2? Show your thinking."
```
Expected: Model outputs `<thought>...</thought><answer>...</answer>` structure

### Test 2: V3 Fallback
```bash
python main.py
# Type: "buat excel laporan"
```
Expected: V3 SoT produces `@XLS:...` signal

### Test 3: V4 Cognitive
```bash
python main.py
# Type: "/toggle" then "Explain why the sky is blue"
```
Expected: V4 produces thought chain with reflection

### Test 4: UI Integration
```bash
python com_chat.py
```
Expected: Desktop app works with optional V4 toggle

---

## File Checklist

| File | Action | Priority |
|------|--------|----------|
| `config/modelfile_cognitive_v4` | ✅ Updated | CRITICAL |
| `core/__init__.py` | Add V4 exports | HIGH |
| `core/cognitive_engine.py` | CREATE NEW | CRITICAL |
| `main.py` | Rewrite for hybrid | CRITICAL |
| `com_chat.py` | Optional V4 toggle | MEDIUM |
| `core/agent_loop.py` | Fix Ollama integration | HIGH |
| `core/context_manager.py` | Verify wiki paths | MEDIUM |

---

## Next Steps

1. **Rebuild the model** with updated Modelfile
2. **Create `core/cognitive_engine.py`** (wrapper class)
3. **Update `core/__init__.py`** (exports)
4. **Rewrite `main.py`** (entry point)
5. **Test all modes** (V3, V4, hybrid)
6. **Optional**: Add V4 toggle to `com_chat.py`

---

## Rollback Plan

If V4 causes issues:
1. Set `use_v4=False` in `CognitiveEngine`
2. System reverts to proven V3 SoT behavior
3. No data loss, no breaking changes

---

## Key Insight

**The "intelligence boost" doesn't come from the model alone.** It comes from:
1. **Python-enforced structure** (Agent Loop)
2. **Iterative reflection** (catch errors before responding)
3. **Dynamic context injection** (Wiki retrieval)
4. **Self-verification** (confidence thresholds)

The model is just the "reasoning engine" - the Python code is the "cognitive architecture" that makes it smart.
