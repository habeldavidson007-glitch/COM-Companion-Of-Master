# 🏆 COM IDE: The "God-Tier" Benchmark Standard v4.0
## *The Ultimate Stress Test for the Next Generation of Game Development Tools*

> **Mission:** To establish a benchmark so rigorous, so unforgiving, and so comprehensive that passing it proves COM IDE is not just "another plugin," but a fundamental evolution in developer tooling.
>
> **Philosophy:** We do not test for "features." We test for **survival**, **sanity**, and **super-intelligence**. If an IDE cannot pass these tests on a 2GB RAM machine while handling a chaotic, real-world project, it does not deserve to be called "Intelligent."

---

## 🛡️ The 7 Pillars of Excellence (The "Impossible" Standards)

These are not suggestions. These are the **minimum viable standards** for COM IDE to be considered superior to existing tools (VS Code + Copilot, Rider, Godot Editor).

### PILLAR 1: THE "SILENT KILLER" DETECTION (Pre-Runtime Omniscience)
**Standard:** Detect 100% of structural breakages *before* the user hits "Play."
**Why it matters:** Godot's biggest pain point is silent failures. COM must be the safety net that never misses.

#### 🔴 Test Suite 1.1: The Node Path Nightmare
- **Scenario:** A complex scene (`BossArena.tscn`) with 50+ nodes. The user renames `Player` to `HeroCharacter` in the scene tree but forgets to update 12 scripts referencing `$Player`.
- **Requirement:** COM must flag all 12 broken references instantly (<200ms) upon file save.
- **Complexity:** Must handle inherited scenes, dynamic path construction (`get_node("Enemy/" + type)`), and signal connections.
- **Human Eval:** "Did it catch the one reference I hid inside a nested `call_deferred` string?"
- **Pass Criteria:** 100% detection rate, 0 false positives, <200ms latency.

#### 🔴 Test Suite 1.2: The Signal Ghost
- **Scenario:** A script connects to `on_body_entered` via code, but the node emitting the signal has been removed or renamed.
- **Requirement:** COM must detect the disconnected signal and suggest the correct node name based on type matching.
- **Expert Eval:** Does it understand Godot's signal architecture deeply, or just regex strings?
- **Pass Criteria:** Correctly identifies orphaned signals and suggests valid reconnections.

#### 🔴 Test Suite 1.3: The Resource Phantom
- **Scenario:** A script references a resource (`preload("res://assets/player.tres")`) that was moved or deleted.
- **Requirement:** COM must trace the resource dependency graph and flag the broken link before runtime.
- **Pass Criteria:** Detects missing resources in `preload`, `load`, and `@export` fields.

---

### PILLAR 2: CONTEXT-AWARE EXPLANATION (The "Plain English" Translator)
**Standard:** Translate cryptic engine errors into actionable, project-specific advice in <3 seconds.
**Why it matters:** Developers don't care about "Condition '!p_data' is true." They care about "Your player script is trying to access a null node."

#### 🔴 Test Suite 2.1: The Cryptic Crash Decoder
- **Scenario:** Godot crashes with `Segmentation fault (core dumped)` or `Index p_index = -1 is out of bounds`.
- **Requirement:** COM must analyze the stack trace + project context + recent code changes to explain: "You are accessing an array index that doesn't exist in `inventory.gd` line 42 because the item list is empty."
- **Human Eval:** "Did this explanation save me 20 minutes of debugging?"
- **Pass Criteria:** Explanation is specific to the user's code, not a generic Google search result.

#### 🔴 Test Suite 2.2: The "Why Is This Happening?" Query
- **Scenario:** User asks, "Why does my player fall through the floor only on the second jump?"
- **Requirement:** COM must analyze the physics layers, collision masks, and `is_on_floor()` logic in the specific script to identify the bug.
- **Expert Eval:** Does it understand Godot's physics engine quirks (e.g., `move_and_slide` behavior)?
- **Pass Criteria:** Identifies the specific logic error (e.g., "You are resetting velocity incorrectly in `_physics_process`").

---

### PILLAR 3: THE "2GB RAM LAW" (Efficiency Under Fire)
**Standard:** Operate flawlessly on a 2GB RAM constraint while Godot, browser, and OS are running.
**Why it matters:** Most AI tools require 16GB+ RAM. COM must be the lightweight champion for indie devs on old hardware.

#### 🔴 Test Suite 3.1: The Memory Torture Chamber
- **Scenario:** Run COM IDE alongside Godot 4.x, VS Code, Chrome (10 tabs), and Discord on a 2GB VM.
- **Requirement:** Peak RAM usage must never exceed 1.8GB (leaving 200MB for OS swap).
- **Stress Test:** Load a 500-script project, run a full validation scan, generate a refactor plan, and explain a complex error—all in one session.
- **Pass Criteria:** No OOM crashes, no swapping thrashing, graceful degradation (queue tasks) if RAM > 1.6GB.

#### 🔴 Test Suite 3.2: The Model Hot-Swap
- **Scenario:** User triggers a heavy code generation task (requires `qwen2.5-coder:7b`) while `smollm2:1.7b` is already loaded.
- **Requirement:** COM must load the 7B model, complete the task, and **unload it within 30 seconds** of idle to return to baseline RAM.
- **Pass Criteria:** RAM spikes temporarily but returns to <1.2GB baseline automatically.

---

### PILLAR 4: T-SHAPED INTELLIGENCE (Polyglot Generalist, Godot God)
**Standard:** Be a competent assistant for Python/JS/C++, but an **unrivaled expert** for Godot/GDScript.
**Why it matters:** Generic LLMs know "coding." COM must know "Godot coding."

#### 🔴 Test Suite 4.1: The Context Switch
- **Scenario:** User asks a Python question ("How do I use list comprehensions?") then immediately asks a Godot question ("How do I connect a signal to this node?").
- **Requirement:** Python answer is generic/correct. Godot answer is **project-aware** (references actual nodes in the user's scene).
- **Expert Eval:** Does the Godot answer demonstrate knowledge of the user's specific scene tree?
- **Pass Criteria:** Clear distinction between generic knowledge and project-specific insight.

#### 🔴 Test Suite 4.2: The Godot Deep Dive
- **Scenario:** User asks, "Is my `Player` node using the correct collision layer?"
- **Requirement:** COM must read the `Player.tscn` file, check the `CollisionLayer` property, and compare it against the `Enemy` layer settings.
- **Pass Criteria:** Provides a specific yes/no with evidence from the project files.

---

### PILLAR 5: DETERMINISTIC CORE (Zero Hallucination Policy)
**Standard:** 0% hallucination on structural facts (paths, types, signals).
**Why it matters:** An AI that lies about node names is worse than no AI at all.

#### 🔴 Test Suite 5.1: The Truth Serum
- **Scenario:** Ask COM, "Does the node `$UI/HUD/ScoreLabel` exist?" when it actually exists as `$UI/HUD/ScoreText`.
- **Requirement:** COM must say "No, but `$UI/HUD/ScoreText` exists" based on **parsing**, not probability.
- **Pass Criteria:** 100% accuracy on existence checks. No "I think..." or "Maybe...".

#### 🔴 Test Suite 5.2: The Type Guardian
- **Scenario:** User tries to call `player.take_damage("5")` (string instead of int).
- **Requirement:** COM must flag the type mismatch based on the function signature in `player.gd`.
- **Pass Criteria:** Detects type errors statically without running the code.

---

### PILLAR 6: REFACTOR SAFETY NET (The "Atomic Change" Protocol)
**Standard:** Identify ALL impact points before a rename/refactor and execute changes atomically.
**Why it matters:** Refactoring in Godot is scary. COM must make it safe.

#### 🔴 Test Suite 6.1: The Ripple Effect
- **Scenario:** User wants to rename `GameManager` to `GameController`.
- **Requirement:** COM must list every script, scene, and signal connection that will break, then offer a one-click fix to update all of them.
- **Human Eval:** "Would I trust COM to apply this automatically without breaking my project?"
- **Pass Criteria:** 100% coverage of impact points, atomic execution (all or nothing).

#### 🔴 Test Suite 6.2: The Inheritance Chain
- **Scenario:** Rename a method in a base class (`Entity.gd`) that is inherited by 10 subclasses.
- **Requirement:** COM must detect all overrides and usages in subclasses and update them consistently.
- **Pass Criteria:** Handles GDScript inheritance correctly.

---

### PILLAR 7: FLOW STATE LATENCY (The "Instant" Promise)
**Standard:** Validation <100ms, Explanations <2s, Refactor Plans <5s.
**Why it matters:** If the tool is slow, developers won't use it. It must feel like part of the editor.

#### 🔴 Test Suite 7.1: The Typing Speed Test
- **Scenario:** User types a `$NodePath` incorrectly.
- **Requirement:** COM must underline the error **before** the user finishes typing the line.
- **Pass Criteria:** Latency <100ms from keystroke to warning.

#### 🔴 Test Suite 7.2: The Log Stream
- **Scenario:** Godot outputs 50 lines of errors per second during a crash loop.
- **Requirement:** COM must parse, explain, and prioritize the **root cause** error in real-time without lagging.
- **Pass Criteria:** Identifies the first error as the root cause, ignores cascading errors.

---

## 🧪 The "Torture Chamber" (Advanced Stress Tests)

These tests are designed to break weak implementations. Only a true "God-Tier" IDE will survive.

### 1. The Spaghetti Scene
- **Input:** A scene with 20 levels of nesting, circular dependencies, and mixed inheritance.
- **Test:** Can COM build the scene tree map without crashing or looping infinitely?
- **Pass:** Parses successfully, flags circular deps.

### 2. The Version Jump
- **Input:** A project migrated from Godot 4.2 to 4.3 with deprecated API calls.
- **Test:** Does COM identify deprecated calls (`move_and_slide` changes) and suggest fixes?
- **Pass:** Lists all deprecated APIs with migration paths.

### 3. The RAM Starvation
- **Input:** Force COM to run with only 512MB available RAM.
- **Test:** Does it gracefully queue tasks and disable heavy features instead of crashing?
- **Pass:** Degrades gracefully, keeps core validation alive.

### 4. The Hallucination Trap
- **Input:** Ask about a node that doesn't exist (`$NonExistentNode`).
- **Test:** Does COM invent a fake path or admit ignorance?
- **Pass:** "Node not found. Did you mean $ExistingNode?"

### 5. The Multi-Language Maze
- **Input:** A project with GDScript, C# (via GodotSharp), and Python tools.
- **Test:** Can COM switch contexts correctly and apply the right rules for each language?
- **Pass:** Correctly handles syntax and API differences.

---

## 📊 Scoring & Certification

To be certified as **"COM IDE Gold Standard"**, a build must achieve:

| Metric | Target | Critical Threshold |
| :--- | :--- | :--- |
| **Pre-Runtime Accuracy** | 100% | <95% = Fail |
| **Hallucination Rate** | 0% | >1% = Fail |
| **Peak RAM Usage** | <1.8GB | >2.0GB = Fail |
| **Validation Latency** | <100ms | >200ms = Fail |
| **Explanation Quality** | Human-Rated 4.5/5 | <3.5/5 = Fail |
| **Refactor Safety** | 100% Coverage | Missed ref = Fail |

### 🏅 Certification Levels
- **🥇 Gold:** All tests passed, RAM ≤1.6GB, Latency <80ms.
- **🥈 Silver:** All tests passed, RAM ≤1.8GB, Latency <100ms. **(Phase 1 Target)**
- **🥉 Bronze:** 90% tests passed, RAM ≤2.0GB.
- **❌ Fail:** Any critical test failed or RAM >2.0GB.

---

## 👥 Evaluation Protocol

### Human Evaluation (The "Dev Experience" Score)
- **Tester:** Indie Godot Developer (Target User)
- **Task:** Fix 5 intentional bugs in a sample project using ONLY COM IDE.
- **Metric:** Time saved vs. vanilla Godot, frustration level, trust in suggestions.

### Expert Evaluation (The "Architect" Score)
- **Evaluator:** Senior Engine Programmer
- **Task:** Review code quality, architectural soundness, and edge case handling.
- **Metric:** Code correctness, robustness, adherence to Godot best practices.

### Automated Evaluation (The "CI/CD" Score)
- **Runner:** GitHub Actions / Local CI
- **Task:** Run the full test suite on every commit.
- **Metric:** Pass/Fail status, performance regression detection.

---

## 🚀 Implementation Roadmap

1.  **Fixture Project Creation:** Build a "Poisonous Godot Project" with all the edge cases above.
2.  **Test Harness Development:** Write Python scripts to automate the testing of COM against the fixture.
3.  **Baseline Measurement:** Run current COM version to establish a baseline score.
4.  **Iterative Improvement:** Fix failures one by one until Gold Standard is reached.

---

## 👤 Division of Labor for Benchmark Implementation

### Developer H (Core Architect) - Benchmark Infrastructure
- **Task 1:** Create `benchmark/fixtures/` directory structure
- **Task 2:** Build the "Poisonous Godot Project" fixture with intentional bugs:
  - Broken node paths (`$Player` → `$PlayerCharacter`)
  - Orphaned signal connections
  - Missing resource references
  - Type mismatches in function calls
  - Circular scene dependencies
- **Task 3:** Write `benchmark/run_benchmark.py` - automated test harness
- **Task 4:** Implement RAM monitoring during tests (`benchmark/ram_monitor.py`)
- **Task 5:** Create scoring system and certification logic

### Developer S (Domain Specialist) - Test Validation
- **Task 1:** Implement node path validation test (Pillar 1, Test Suite 1.1)
- **Task 2:** Implement signal ghost detection test (Pillar 1, Test Suite 1.2)
- **Task 3:** Implement resource phantom test (Pillar 1, Test Suite 1.3)
- **Task 4:** Write human evaluation scripts for explanation quality (Pillar 2)
- **Task 5:** Create latency measurement tools (Pillar 7)

### Joint Tasks (Both Developers)
- **Week 1:** Run first baseline benchmark (expect Fail, establish baseline score)
- **Week 2:** Iterate on failures until Silver Standard achieved (RAM ≤1.8GB)
- **Week 3:** Optimize for Gold Standard (RAM ≤1.6GB, Latency <80ms)
- **Week 4:** Final certification before Phase 1 sign-off

---

## 📋 Immediate Next Steps (This Week)

| Day | Developer H | Developer S |
|-----|-------------|-------------|
| **Mon** | Create `benchmark/` dir structure | Review fixture requirements |
| **Tue** | Build poisonous project fixture | Write node path test logic |
| **Wed** | Implement RAM monitor | Write signal ghost test logic |
| **Thu** | Create test harness runner | Write resource phantom test |
| **Fri** | **Run first baseline benchmark together** | **Analyze failures, plan fixes** |

---

> **Final Word:** This benchmark is not just a test; it is our **compass**. Every line of code we write must move us closer to passing these tests. If a feature does not help us pass these tests, it does not belong in Phase 1.
>
> **Success Metric:** When an indie developer can say *"COM caught a bug I didn't know I had, explained it in plain English, and fixed it without crashing my 2GB laptop"* — that's when we've won.

---

**Compiled by:** COM Development Team  
**Version:** 4.0 (God-Tier Standard)  
**License:** MIT (Benchmark suite open-source for community verification)

