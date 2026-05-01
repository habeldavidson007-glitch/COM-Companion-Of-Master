# 🏆 COM IDE: God-Tier Benchmark Standard v5.0

> **"The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that already thinks better even with small models. The limit is only your imagination."**

---

## 🎯 Core Philosophy: Compiler, Not Chatbot

COM IDE does not "chat." It **compiles intent into action**.
- **Input:** Human language / Code context
- **Process:** Parse → Retrieve → Plan (LLM) → Execute (Deterministic)
- **Output:** Actionable result, validated fact, or fixed code

**The Moat:** Most AI IDEs are `User → LLM → Text`. Ours is `User → Parse → Plan → Execute`. This gives us **zero hallucination on structural facts** and **2GB RAM compliance**.

---

## 🔥 The 7 Pillars of Excellence (Stress-Tested)

### Pillar 1: Silent Killer Detection
**Goal:** Catch errors *before* runtime that crash Godot silently.
- **Test Suite A (Node Paths):** 50 injected `$NodePath` errors (renamed nodes, typos, moved scenes).
  - **Target:** 100% detection, 0 false positives.
  - **Latency:** <100ms (Real-time mode).
- **Test Suite B (Signal Ghosts):** 20 disconnected signals referenced in code.
  - **Target:** Flag exact line + suggest fix.
- **Test Suite C (Resource Phantoms):** 15 `preload()` paths to deleted resources.
  - **Target:** Detect missing assets before load failure.
- **Human Eval:** "Did it catch the error I didn't know I made?" (Pass if >90% agreement).

### Pillar 2: Context-Aware Explanation
**Goal:** Translate engine crashes into plain English using *your* project context.
- **Test Suite:** 20 real-world Godot crashes (RAM exhaustion, physics instability, binding errors).
  - **Input:** Raw log line + Project Map.
  - **Output:** ≤3 sentences explaining *why* in context of user's code.
  - **Constraint:** Must reference specific file/line/node from user project.
  - **Model:** smollm2:1.7b only (proves efficiency).
- **Expert Eval:** "Does this explanation reference specific project elements correctly?" (Pass/Fail).

### Pillar 3: The 2GB RAM Law
**Goal:** Run COM + Godot + VS Code on 2GB RAM machines without swapping.
- **Torture Test A (Memory Ceiling):**
  - Load Godot project (50 scenes, 100 scripts).
  - Run COM Deep Scan.
  - **Limit:** Peak RAM ≤ 2.0GB total system usage.
- **Torture Test B (Model Hot-Swap):**
  - Trigger qwen2.5-coder:7b load.
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
- **Expert Eval:** "Does the answer demonstrate knowledge of *this specific project*?"

### Pillar 5: Deterministic Core (Zero Hallucination)
**Goal:** Structural facts are never guessed.
- **Test Suite:** 100 queries about node existence, signal connections, resource paths.
  - **Source of Truth:** Parsed scene tree (not LLM).
  - **Target:** 100% accuracy.
  - **Mechanism:** If parser says "No", LLM cannot say "Yes".
- **Hallucination Trap:** Ask about non-existent node `$FakeNode`.
  - **Pass:** "Node $FakeNode not found in MainScene.tscn."
  - **Fail:** "Here is how you use $FakeNode..."

### Pillar 6: Refactor Safety Net
**Goal:** Safe, atomic refactoring with ripple effect analysis.
- **Complex Test:** Rename node `Player` → `Hero`.
  - **Step 1:** Identify all 15 scripts referencing `$Player`.
  - **Step 2:** Generate atomic patch for each file.
  - **Step 3:** Verify no broken paths remain.
  - **Human Eval:** "Would I trust COM to apply this automatically without breaking my game?" (Pass if ≥9/10 devs say Yes).

### Pillar 7: Flow State Latency
**Goal:** Invisible assistance.
- **Real-Time Mode:** Validation <100ms (heuristic/cached).
- **Deep Scan Mode:** Full analysis <2s (on save/command).
- **Stress Test:** Type 50 lines of code rapidly.
  - **Verify:** No lag, no blocking, errors flagged instantly.

---

## 🧪 Advanced Torture Chamber Tests

### 1. The Spaghetti Scene Test
- **Fixture:** A scene with 20 levels of nesting, 5 inherited scenes, 10 circular dependencies.
- **Task:** Validate all node paths.
- **Target:** Completes without stack overflow, identifies cycles, <3s latency.

### 2. The Version Jump Test
- **Fixture:** Project migrated from Godot 4.2 → 4.3 with deprecated APIs.
- **Task:** Identify all breaking changes.
- **Target:** List exact lines needing updates, suggest 4.3 equivalents.

### 3. The RAM Starvation Test
- **Condition:** Limit COM to 512MB RAM while Godot uses 1.5GB.
- **Task:** Explain a complex shader error.
- **Target:** Falls back to tinyllama:1.1b or rule-based explanation, completes successfully.

### 4. The Hallucination Trap
- **Setup:** Ask "What does the `@export_range('Fake')` decorator do?" (It doesn't exist).
- **Target:** "Decorator `@export_range('Fake')` is invalid. Did you mean `@export_range('min', 'max')`?"
- **Fail:** Inventing functionality.

### 5. The Multi-Language Maze
- **Fixture:** Project with GDScript, C# (via GodotSharp), and Python editor tools.
- **Task:** Switch contexts between languages seamlessly.
- **Target:** Correct syntax highlighting, linting, and explanation for each language without confusion.

---

## 📊 Certification Levels

| Level | Requirements | Badge |
|-------|--------------|-------|
| **🥇 Gold** | All 7 Pillars Pass + RAM ≤1.6GB + Latency <80ms | "Compiler-God" |
| **🥈 Silver** | All 7 Pillars Pass + RAM ≤1.8GB + Latency <100ms | "Phase 1 Target" |
| **🥉 Bronze** | 6/7 Pillars Pass + RAM ≤2.0GB | "Beta Ready" |
| **Fail** | Any Pillar 1/5 Fail OR RAM >2.2GB | "Refactor Needed" |

---

## 🛠️ Implementation & Scoring

### Scoring Protocol
1. **Automated Harness:** Runs all tests, logs pass/fail, measures RAM/latency.
2. **Human Eval Panel:** 3 Godot devs rate explanations/refactors (1-5 scale).
3. **Expert Review:** Senior engineer verifies zero-hallucination claims.

### Division of Labor
- **Developer H (Core):** Build test harness, fixture generator, RAM monitor, schema validator.
- **Developer S (Godot):** Create spaghetti scene fixture, inject errors, write human eval scripts.

### Weekly Cadence
- **Week 1:** Build harness + fixture project.
- **Week 2:** Run baseline tests (expect failures), tune parsers.
- **Week 3:** Optimize RAM/latency, re-run.
- **Week 4:** Final certification run, record demo video.

---

## 🚀 The Ultimate Claim

> **COM IDE is the first AI companion that knows your project better than you do, runs on your potato laptop, and never lies about your code structure.**

If it passes this benchmark, it is not just "another AI tool." It is a **compiler with a brain**.
