# COM IDE Roadmap: Godot AI Companion

> *The stronger the model for COM IDE to use, the Stronger it becomes. We created an evolving IDE with revolutionary pipeline that's already thinks better even with small model, the limit only your imagination.*

COM IDE
Godot AI Companion - Compiler-AI Architecture
The stronger the model COM IDE uses, the stronger it becomes.
An evolving IDE with a revolutionary pipeline that already thinks better even with small models.


## 01  The Architecture - Compiler-AI Pipeline

COM IDE is not a chatbot wrapper. It is a static-analysis engine with an LLM-assisted planning layer.

### 1.1  The Single-Pass Pipeline

1.  Signal Parser (Rule-Based): Strips noise, extracts intent, enforces schema. NO LLM.
2.  Wiki Retriever: Enriches context with project knowledge BEFORE LLM sees it.
3.  LLM (Compiler Stage): Generates a JSON execution plan ONLY. One pass. No chat.
4.  Harness Executor: Deterministically executes the plan. No guessing.
5.  Output Formatter: Returns structured result. No summarization LLM call.


## 02  Build Phases - From Schema to Shipping

Phase 1: Schema + Parsers + Validator (4 weeks)  [CURRENT FOCUS]
Freeze Signal Schema v1.0 (JSON protocol).
Build Godot Parsers: scene_parser.py (.tscn), script_parser.py (.gd).
Implement ProjectMap: Cross-reference nodes vs scripts.
Build Rule-Based Validator: Detect broken paths WITHOUT LLM.
Integrate smollm2:1.7b for error explanation ONLY (single pass).
RAM Target: <=2.0GB peak with Godot + VS Code running.

Phase 2: Wiki Integration + Deep Scan (4 weeks)  [KNOWLEDGE LAYER]
Index project files into WikiRetriever (TF-IDF).
Implement Dual-Mode Latency: Real-time (<100ms) vs Deep Scan (1-3s).
Add Refactor Safety Net: Identify all breakages before renaming.

Phase 3: VS Code Extension + UI (6 weeks)  [DISTRIBUTION]
Port core logic to VS Code Extension (Node.js/Python bridge).
Inline decorations: Red underline for broken node paths.
Model Hot-Swapping: Auto-load qwen2.5:7b for complex tasks, unload after 10min.

Phase 4: E+ Language + Full IDE (8 weeks)  [EVOLUTION]
Implement E+ grammar parser (deterministic translation to GDScript).
Live preview: E+ to GDScript side-by-side.
Plugin System: Community tools (Blender, Aseprite integration).



## 03  Team Structure - Core vs Domain


### Developer H (Core Architect)

Owns the Brain: Signal Schema, Routing, RAM Safety.

• core/signal_schema.py - Frozen JSON protocol
• core/intent_router.py - Rule-first routing
• core/ram_monitor.py - Memory watchdog (2GB law)
• core/prompts/ - LLM compiler prompts
• Fix @GDT alias in tool_harness.py
• Benchmark Infrastructure

### Developer S (Domain Specialist)

Owns the Hands: Godot Parsing, Validation, Tools.

• tools/godot/scene_parser.py - .tscn parsing
• tools/godot/script_parser.py - .gd extraction
• tools/godot/project_map.py - Cross-referencing
• tools/godot/log_watcher.py - Error monitoring
• tools/godot/specialist.py - Godot-specific logic
• Unit Tests for Parsers


## 04  The God-Tier Benchmark


### Certification Levels

🥇 Gold: All tests + RAM <=1.6GB + Latency <80ms
🥈 Silver: All tests + RAM <=1.8GB + Latency <100ms (Phase 1 Target)
🥉 Bronze: 90% tests + RAM <=2.0GB

### Key Metrics

- Silent Killer Detection: 100% detection of broken $NodePaths before runtime
• RAM Compliance: Peak RAM <=2.0GB with Godot + VS Code running
• Deterministic Core: 0% hallucination on structural facts
• Rule-Based: 80% of queries resolved WITHOUT LLM


## 05  First 30 Days - Sprint Plan

Week 1: Foundation
Dev H: Freeze signal_schema.py (JSON structure).
Dev S: Create tools/godot/, write scene_parser.py.
Dev S: Write script_parser.py (regex for $NodePath).
Both: Sync on schema alignment (30 mins).
Week 2: Knowledge & Validation
Dev S: Build project_map.py (cross-reference scenes/scripts).
Dev S: Implement validate_node_paths() (rule-based).
Dev H: Integrate WikiRetriever (context enrichment).
Dev H: Fix @GDT alias bug in tool_harness.py.
Week 3: RAM Safety & Execution
Dev H: Build ram_monitor.py (auto-unload logic).
Dev H: Write LLM prompts for JSON plan generation.
Dev S: Wire log_watcher.py to OllamaClient.
Both: Stress test RAM usage (target <2.0GB).
Week 4: Polish & Demo
Test on 3 real Godot projects (open source).
Record demo video: "Finding a bug before hitting Play".
Document false positives/negatives.
Release Phase 1 Terminal Tool (GitHub).


## 06  Summary - The Path Forward

You are building a compiler, not a chatbot. This distinction is your moat.

Final Mandate:
1.  Freeze the Signal Schema. Everything depends on it.
2.  Enforce the 2GB RAM Law. Optimize for low-end hardware first.
3.  Trust the Pipeline. Parse - Plan - Execute. No shortcuts.
4.  Scale with Models. The architecture supports anything from 1.7B to 70B.

The stronger the model you plug in, the stronger COM becomes.
But even with the smallest model, it thinks better than any chatbot because it knows YOUR code.

Build for the developer who is tired of silent crashes. Build the compiler they deserve.