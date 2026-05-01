# 🏆 COM IDE Benchmark Standard v2.0
## The "Compiler-Lite" Godot Specialist

**Status:** DRAFT  
**Target RAM:** ≤2.0GB Peak (smollm2:1.7b base)  
**Philosophy:** LLM as Compiler Stage, Not Oracle  
**Date:** May 2026

---

## 1. Core Philosophy: What Makes COM Different?

Current IDEs (VS Code + Copilot, Rider, etc.) treat AI as a **chatbot overlay**.  
COM IDE treats AI as a **compiler stage** in a deterministic pipeline.

| Feature | Traditional AI IDE | COM IDE (Golden Standard) |
|---------|-------------------|---------------------------|
| **LLM Role** | Generates final answer directly | Generates JSON execution plan only |
| **Context** | Sent raw to LLM (expensive) | Enriched by Wiki/Parser BEFORE LLM |
| **Determinism** | Probabilistic, hallucinates | Rule-based validation, LLM only for ambiguity |
| **RAM Usage** | 4-8GB (large models always loaded) | ≤2GB (tiny model + hot-swap) |
| **Godot Knowledge** | Generic GDScript examples | Real-time scene tree awareness |
| **Error Handling** | "Here's a generic fix" | "Node $Player missing in Main.tscn:47, suggest $PlayerCharacter" |

**The Golden Rule:**  
> If a rule-based parser can solve it, the LLM never sees the query.

---

## 2. The Benchmark Suite: 5 Critical Tests

### Test 1: Node Path Validation Accuracy (The "Silent Killer" Test)
**Scenario:** Developer renames node `Player` → `PlayerCharacter` in scene, but script still uses `$Player`.

**Input:**
- `Main.tscn` with node `PlayerCharacter` (type: CharacterBody2D)
- `player.gd` with `@onready var player = $Player`

**Expected Output:**
```json
{
  "severity": "ERROR",
  "type": "NODE_PATH_INVALID",
  "file": "player.gd",
  "line": 4,
  "invalid_path": "$Player",
  "suggestion": "$PlayerCharacter",
  "confidence": 0.95,
  "llm_used": false
}
```

**Pass Criteria:**
- ✅ Detects invalid path without running Godot
- ✅ Suggests correct alternative (fuzzy match)
- ✅ Zero LLM calls (rule-based only)
- ✅ Latency < 100ms
- ✅ RAM delta < 50MB

**Fail Conditions:**
- ❌ Requires runtime to detect
- ❌ No suggestion provided
- ❌ LLM called for simple string matching
- ❌ False positive on valid paths

---

### Test 2: Error Explanation Quality (The "Plain English" Test)
**Scenario:** Godot crashes with `Condition "p_node" is true. Returned: nullptr` (useless engine error).

**Input:**
- Log line: `ERROR: Condition "p_node" is true. Returned: nullptr. at: get_node (scene/main/node.cpp:1303)`
- Project context: `Main.tscn` has no node named `Enemy`

**Expected Output:**
```json
{
  "severity": "CRITICAL",
  "type": "NULL_NODE_REFERENCE",
  "explanation": "Your code tried to access a node named 'Enemy' that doesn't exist in the current scene.",
  "location": "Likely in get_node('Enemy') or $Enemy",
  "fix_plan": {
    "action": "SEARCH_SCRIPTS",
    "target_string": "Enemy",
    "files_to_check": ["*.gd"]
  },
  "llm_used": true,
  "model": "smollm2:1.7b",
  "tokens_used": 142
}
```

**Pass Criteria:**
- ✅ Translates engine jargon to plain English
- ✅ Points to likely cause (missing node)
- ✅ Provides actionable next step (search scripts)
- ✅ Uses smollm2:1.7b (not 7B+)
- ✅ Tokens < 200 (context compressed)
- ✅ Latency < 3s

**Fail Conditions:**
- ❌ Generic answer ("Check your node references")
- ❌ Uses qwen2.5-coder:7b for simple explanation
- ❌ Tokens > 512
- ❌ No specific file/line guidance

---

### Test 3: RAM Constraint Compliance (The "2GB Law" Test)
**Scenario:** Run COM IDE alongside Godot 4.2 + VS Code on 2GB RAM machine.

**Test Procedure:**
1. Start COM IDE (load smollm2:1.7b)
2. Open Godot project with 50 scenes, 100 scripts
3. Trigger node validation scan
4. Trigger error explanation (load qwen2.5-coder:7b on-demand)
5. Wait 10 minutes (idle timeout)
6. Measure peak RAM

**Expected Metrics:**
| State | RAM Usage | Model Loaded |
|-------|-----------|--------------|
| Idle | 800MB | smollm2:1.7b |
| Scan Active | 1.2GB | smollm2:1.7b |
| LLM Burst (qwen) | 1.9GB | smollm2 + qwen |
| After 10min Idle | 850MB | smollm2:1.7b (qwen unloaded) |

**Pass Criteria:**
- ✅ Peak RAM ≤ 2.0GB
- ✅ qwen auto-unloads after 10min idle
- ✅ No OOM crashes
- ✅ Godot remains responsive (>30 FPS)

**Fail Conditions:**
- ❌ Peak RAM > 2.2GB
- ❌ qwen stays loaded indefinitely
- ❌ Godot crashes due to memory pressure

---

### Test 4: Signal Schema Strictness (The "Determinism" Test)
**Scenario:** Send ambiguous query to intent router.

**Input:**
```
"why does my player fall through the floor"
```

**Expected Pipeline:**
```
1. Signal Parser → { "intent": "DEBUG_PHYSICS", "entities": ["player", "floor"] }
2. Wiki Retriever → Fetch "CollisionShape2D", "Kinematic Collision" docs
3. Intent Router → Rule match (no LLM needed)
4. Harness → Execute VALIDATE_COLLISION action
5. Output → JSON plan (NO LLM generation yet)
```

**If Ambiguity Detected:**
```
4. LLM → Refine intent: { "action": "CHECK_COLLISION_LAYER", "params": {...} }
5. Harness → Execute
```

**Pass Criteria:**
- ✅ 80% of queries resolved WITHOUT LLM
- ✅ All outputs are valid JSON schemas
- ✅ No raw text passed to harness
- ✅ Schema validation fails on malformed output

**Fail Conditions:**
- ❌ LLM called for every query
- ❌ Raw text passed to tool executor
- ❌ Schema validation bypassed

---

### Test 5: Polyglot vs Godot Specialization (The "T-Shaped" Test)
**Scenario A (General Python):**
```
"How do I read a JSON file in Python?"
```
**Expected:** Generic Python answer (no project context needed), smollm2:1.7b.

**Scenario B (Godot-Specific):**
```
"Why does my Player.gd not see the Enemy node?"
```
**Expected:** 
- Scans project scene tree
- Validates node paths
- Returns project-specific answer
- Uses wiki + parser before LLM

**Pass Criteria:**
- ✅ General queries: Fast, low-RAM, no project scan
- ✅ Godot queries: Deep project awareness, specific file/line refs
- ✅ Correct model selection (smollm2 for general, qwen only if complex)

**Fail Conditions:**
- ❌ Godot query gets generic answer
- ❌ Python query triggers full project scan
- ❌ Wrong model loaded (qwen for simple Python question)

---

## 3. Performance Targets (Phase 1 MVP)

| Metric | Target | Stretch Goal | Current Baseline |
|--------|--------|--------------|------------------|
| **Node Validation Accuracy** | ≥95% | ≥99% | N/A (new feature) |
| **False Positive Rate** | ≤5% | ≤1% | N/A |
| **Error Explanation Clarity** | 4/5 dev rating | 5/5 | N/A |
| **Peak RAM Usage** | ≤2.0GB | ≤1.8GB | ~600MB (core only) |
| **LLM Calls Avoided (Rule-Based)** | ≥80% | ≥90% | ~40% (current router) |
| **Latency (Validation)** | <100ms | <50ms | N/A |
| **Latency (Error Explain)** | <3s | <1.5s | ~5s (unoptimized) |
| **Idle Unload Time** | 10min | 5min | N/A |

---

## 4. Test Infrastructure Requirements

### 4.1 Test Project Fixture
Create `/workspace/benchmark/fixtures/godot_test_project/`:
```
godot_test_project/
├── Main.tscn              # Contains renamed nodes (Player→PlayerCharacter)
├── Enemy.tscn             # Missing collision shape (intentional bug)
├── player.gd              # References $Player (invalid)
├── enemy.gd               # References non-existent signal
├── project.godot          # Godot 4.2 config
└── logs/
    └── godot_output.log   # Sample crash logs
```

### 4.2 Automated Test Runner
Create `/workspace/benchmark/run_benchmark.py`:
```python
def run_all_tests():
    results = {
        "node_validation": test_node_validation(),
        "error_explanation": test_error_explanation(),
        "ram_compliance": test_ram_usage(),
        "schema_strictness": test_signal_schema(),
        "specialization": test_polyglot_vs_godot()
    }
    generate_report(results)
```

### 4.3 Scoring System
- **Gold Standard:** All 5 tests pass + RAM ≤1.8GB
- **Silver Standard:** All 5 tests pass + RAM ≤2.0GB
- **Bronze Standard:** 4/5 tests pass + RAM ≤2.2GB
- **Fail:** <4 tests pass OR RAM >2.2GB

---

## 5. Comparison: COM vs Existing Tools

| Capability | COM IDE | VS Code + Copilot | Godot Editor | Rider + Resharper |
|------------|---------|-------------------|--------------|-------------------|
| **Pre-runtime node validation** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Project-aware Q&A** | ✅ Yes | ❌ No (generic) | ❌ No | ⚠️ Partial |
| **Local inference (privacy)** | ✅ Yes | ❌ Cloud-only | N/A | ❌ Cloud |
| **RAM ≤2GB** | ✅ Yes | ❌ 4GB+ | ✅ Yes | ❌ 6GB+ |
| **Error plain-English explain** | ✅ Yes | ⚠️ Generic | ❌ Engine jargon | ⚠️ Generic |
| **Signal/connection validation** | ✅ Yes | ❌ No | ⚠️ Runtime only | ❌ No |
| **Polyglot support** | ✅ Yes | ✅ Yes | ❌ GDScript only | ✅ Yes |
| **Cost** | ✅ Free (local) | ❌ $20/mo | ✅ Free | ❌ $15/mo |

**Unique Value Proposition:**  
> COM is the ONLY tool that combines pre-runtime Godot validation, project-aware Q&A, and local inference under 2GB RAM.

---

## 6. Phase 1 Acceptance Criteria

Before declaring Phase 1 complete, COM must:

1. ✅ Pass all 5 benchmark tests (Gold or Silver standard)
2. ✅ Run on 2GB RAM machine without OOM
3. ✅ Validate node paths in <100ms for 100-script project
4. ✅ Explain errors in plain English with 4/5 dev rating
5. ✅ Avoid LLM calls for 80% of queries (rule-based)
6. ✅ Auto-unload qwen model after 10min idle
7. ✅ Process 3 real-world Godot projects with zero false positives

---

## 7. Continuous Improvement Loop

After Phase 1:
1. Run benchmark weekly
2. Track metrics in `/workspace/benchmark/results/`
3. Regression test: Any new feature must not degrade existing scores
4. Community feedback: Share benchmark results publicly for transparency

---

## 8. The "Moat": Why This Matters

Traditional IDEs compete on:
- Syntax highlighting quality
- Autocomplete speed
- Plugin ecosystem

COM IDE competes on:
- **Understanding your project structure** (scene tree awareness)
- **Catching bugs before runtime** (pre-runtime validation)
- **Working on weak hardware** (2GB RAM constraint)
- **Privacy-first** (no cloud uploads)

**This benchmark proves COM is not "another AI plugin" — it's a fundamentally different approach to developer tooling.**

---

## Next Steps

1. **Dev H:** Create benchmark fixture project (`benchmark/fixtures/`)
2. **Dev S:** Implement node validation test (Test 1)
3. **Both:** Run first baseline benchmark (expect Fail, establish baseline)
4. **Week 2:** Iterate until Silver Standard achieved
5. **Week 4:** Achieve Gold Standard before Phase 1 sign-off

---

**Compiled by:** COM Development Team  
**Version:** 2.0 (Compiler-Lite Architecture)  
**License:** MIT (Benchmark suite open-source for community verification)
