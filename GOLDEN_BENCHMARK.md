# 🏆 COM IDE: God-Tier Benchmark Standard v6.0

> **The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that already thinks better even with small models. The limit is only your imagination.**

---

## 🎯 Core Philosophy: Compiler, Not Chatbot

COM IDE does not "chat." It **compiles intent into action**.
- **Input:** Human language / Code context
- **Process:** `Parse (watchfiles+tiktoken)` → `Retrieve (diskcache)` → `Plan (LLM+instructor)` → `Execute (Deterministic)`
- **Output:** Actionable result, validated fact, or fixed code

**The Moat:** Most AI IDEs are `User → LLM → Text`. Ours is `User → Parse → Plan → Execute`. This gives us **zero hallucination on structural facts** and **2GB RAM compliance**.

**Tech Stack Enforcers:**
| Library | Benchmark Role |
|---------|----------------|
| `instructor` | Ensures 100% valid JSON plans (Pillar 5) |
| `tiktoken` | Enforces 512-token context limit (Pillar 3) |
| `diskcache` | Offloads RAM to disk for 2GB compliance (Pillar 3) |
| `watchfiles` | Triggers sub-100ms validation (Pillar 7) |
| `liteLLM` | Routes to correct model (Pillar 4) |
| `logfire` | Traces latency for verification (Pillar 7) |
| `rich` | Renders terminal output instantly (Pillar 7) |

---

## 🔥 The 7 Pillars of Excellence (Stress-Tested)

### Pillar 1: Silent Killer Detection
**Goal:** Catch errors *before* runtime that crash Godot silently.
- **Test Suite A (Node Paths):** 50 injected `$NodePath` errors (renamed nodes, typos, moved scenes).
  - **Target:** 100% detection, 0 false positives.
  - **Latency:** <100ms (Real-time mode via `watchfiles`).
- **Test Suite B (Signal Ghosts):** 20 disconnected signals referenced in code.
  - **Target:** Flag exact line + suggest fix.
- **Test Suite C (Resource Phantoms):** 15 `preload()` paths to deleted resources.
  - **Target:** Detect missing assets before load failure.
- **Human Eval:** "Did it catch the error I didn't know I made?" (Pass if >90% agreement).

### Pillar 2: Context-Aware Explanation
**Goal:** Translate engine crashes into plain English using *your* project context.
- **Test Suite:** 20 real-world Godot crashes (RAM exhaustion, physics instability, binding errors).
  - **Input:** Raw log line + Project Map (from `diskcache`).
  - **Output:** ≤3 sentences explaining *why* in context of user's code.
  - **Constraint:** Must reference specific file/line/node from user project.
  - **Model:** Adaptive via `liteLLM` (Smol-1.7B default, Llama-3B/Qwen-7B if RAM allows).
- **Expert Eval:** "Does this explanation reference specific project elements correctly?" (Pass/Fail).

### Pillar 3: The 2GB RAM Law
**Goal:** Run COM + Godot + VS Code on 2GB RAM machines without swapping.
- **Torture Test A (Memory Ceiling):**
  - Load Godot project (50 scenes, 100 scripts).
  - Run COM Deep Scan.
  - **Limit:** Peak RAM ≤ 2.0GB total system usage (enforced by `diskcache` offloading).
- **Torture Test B (Model Hot-Swap):**
  - Trigger qwen2.5-coder:7b load via `liteLLM`.
  - Idle for 10 minutes.
  - **Verify:** Model unloaded, RAM returned to baseline (<1.2GB).
- **Torture Test C (Starvation Mode):**
  - Artificially limit COM to 512MB.
  - **Verify:** Graceful degradation (falls back to tinyllama:1.1b or rule-only mode), no crash.

### Pillar 4: T-Shaped Intelligence
**Goal:** Generalist polyglot, Godot God.
- **Test A (Polyglot Baseline):** Ask Python/JS/C++ questions.
  - **Expect:** Generic, correct, fast answers (no project context needed).
- **Test B (Godot Superpower):** Ask "Why does my player fall through the floor?"
  - **Expect:** Answer references *specific* CollisionShape2D in *specific* scene file.
  - **Fail:** Generic physics tutorial answer.
- **Routing Check:** `liteLLM` must select best model based on RAM availability (adaptive routing).

### Pillar 5: Deterministic Core (Zero Hallucination)
**Goal:** Structural facts are never guessed.
- **Test Suite:** 100 queries about node existence, signal connections, resource paths.
  - **Constraint:** All answers must come from parsers, not LLM generation.
  - **Enforcer:** `instructor` validates that LLM output matches schema exactly.
- **Metric:** 100/100 accuracy required. Any hallucination = Fail.

### Pillar 6: Refactor Safety Net
**Goal:** Safe atomic changes with ripple effect detection.
- **Test:** Rename central node `$Player` → `$PlayerCharacter`.
  - **Expect:** COM identifies all 15 scripts referencing `$Player`, proposes atomic update plan.
  - **Enforcer:** Harness executes plan atomically (all or nothing).
- **Human Eval:** "Would I trust COM to apply this automatically?" (Pass if >80% say yes).

### Pillar 7: Flow State Latency
**Goal:** Instant feedback, no blocking.
- **Test A (Real-time Validation):** Type a bad node path.
  - **Target:** Red underline/warning in <100ms (`watchfiles` trigger).
- **Test B (Error Explanation):** Godot crashes.
  - **Target:** Plain English explanation in <2s (`rich` render).
- **Tracing:** `logfire` must show full pipeline trace < target latency.

---

## 🧪 Torture Chamber Tests

These tests push COM to its absolute limits.

### 1. Spaghetti Scene
- **Setup:** 20-level nested inherited scenes, 200+ nodes.
- **Action:** Full validation scan.
- **Targets:** <500ms latency, <50MB RAM spike, 0 missed errors.

### 2. RAM Starvation
- **Setup:** Limit process to 512MB via cgroups.
- **Action:** Run Deep Scan with qwen2.5-coder:7b requested.
- **Targets:** Falls back to tinyllama:1.1b or rule-mode, completes without OOM crash.

### 3. Hallucination Trap
- **Setup:** Ask "What does `$NonExistentNode` do?" (node doesn't exist).
- **Action:** Query COM.
- **Targets:** 100% "Not found" response. No invented functionality.

### 4. Schema Strictness
- **Setup:** Feed garbage/malformed input to LLM.
- **Action:** `instructor` retries up to 3 times.
- **Targets:** Valid JSON or fail-fast error. No partial/corrupted output.

### 5. Token Overflow
- **Setup:** Feed 10,000 tokens of context (entire project).
- **Action:** `tiktoken` truncates to 512 tokens before LLM sees it.
- **Targets:** No OOM, relevant context preserved, latency unaffected.

### 6. Multi-Language Maze
- **Setup:** Project with GDScript, Python tools, C++ modules, JS shaders.
- **Action:** Ask questions in each language.
- **Targets:** Correct routing, appropriate depth per language (Godot = deep, others = generic).

---

## 📊 Certification Levels

To claim COM IDE is production-ready, it must achieve:

### 🥉 Bronze Certification
- Pass 90% of Pillar tests.
- Peak RAM ≤ 2.2GB.
- Latency: <150ms validation, <3s explanation.

### 🥈 Silver Certification (Phase 1 Target)
- Pass 100% of Pillar tests.
- Peak RAM ≤ 2.0GB.
- Latency: <100ms validation, <2s explanation.
- Zero hallucination on structural facts.

### 🥇 Gold Certification (Phase 3 Target)
- Pass 100% of Pillar + Torture tests.
- Peak RAM ≤ 1.8GB.
- Latency: <80ms validation, <1.5s explanation.
- Graceful degradation proven in Starvation Mode.

---

## 🛠️ Implementation & Testing Schedule

| Week | Focus | Tests to Implement | Owner |
|------|-------|-------------------|-------|
| **Week 1** | Schema + Parsers | Pillar 5 (Determinism), Pillar 1 (Node Paths) | Dev H (Schema), Dev S (Parsers) |
| **Week 2** | Wiki + Validation | Pillar 1 (Signals/Resources), Pillar 7 (Latency) | Dev S (Validators), Dev H (tiktoken) |
| **Week 3** | RAM + Execution | Pillar 3 (2GB Law), Pillar 6 (Refactor) | Dev H (diskcache), Dev S (Harness) |
| **Week 4** | Polish + Demo | All Pillars + Torture Chamber | Both (Full Suite) |

---

## 🚀 Immediate Next Steps

1. **Dev H:** Create `tests/benchmark_harness.py` with `logfire` tracing.
2. **Dev S:** Build fixture project with 50 injected bugs (for Pillar 1).
3. **Both:** Run baseline test (current state) → document gaps → sprint to close.

**Remember:** If it's not benchmarked, it doesn't exist.
