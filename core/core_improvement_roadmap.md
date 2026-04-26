# COM Core Improvement Roadmap (2GB RAM target)

## Goal
Make COM feel closer to a larger model (7B-8B quality) by improving routing, memory quality, and output reliability without increasing model size.

## Priority 1 (Do Now)

### 1) Add Regex/Rule Guard Layer before and after LLM
- **Before LLM (input rules):** detect high-confidence intents (`create pdf`, `create excel`, `godot script`) with regex to reduce router mistakes.
- **After LLM (output rules):** validate OFFICE/GODOT output format and auto-repair minor formatting errors.
- **Why:** small models drift on exact formatting; regex rules improve determinism with near-zero RAM cost.

### 2) Adaptive Memory (salience-based)
- Store only turns that contain:
  - user preferences ("I prefer..."),
  - facts (dates/names/numbers),
  - explicit decisions/tasks.
- Drop low-value chit-chat from long-term memory.
- **Why:** better context quality beats bigger context size on 0.5B–1.5B models.

### 3) Confidence-based fallback policy
- If route confidence is low, ask one short clarification question.
- If output violates schema twice, return strict fallback template.
- **Why:** prevents hallucinated or malformed outputs from propagating.

## Priority 2 (Next)

### 4) Lightweight retrieval snippets (micro-RAG)
- Keep a small local note index (last N key facts/tasks), retrieve top-2 snippets only.
- Insert snippets into system/user prompt compactly.
- **Why:** improves factual continuity without large context windows.

### 5) Prompt contracts per mode (stricter)
- Convert each mode to explicit mini-schema instructions.
- Add a short "bad examples" section to prevent common drift.
- **Why:** small models respond better to narrow contracts than broad instructions.

## Priority 3 (Quality hardening)

### 6) Self-check pass for GENERAL responses
- Add optional 1-pass local checker prompt (very short) only for risky questions.
- Checker verifies: relevance, contradiction, verbosity.
- **Why:** catches obvious drifts before returning final answer.

### 7) Telemetry-driven tuning
- Track: route mismatches, schema failures, retries, timeout frequency, cache hit rate.
- Tune thresholds weekly from real usage logs.
- **Why:** iterative tuning is how small models approach larger-model UX.

## What gives biggest impact per RAM spent?
1. Regex guard layer (very high)
2. Adaptive memory (very high)
3. Confidence-based clarification (high)
4. Micro-RAG (medium-high)

## Suggested implementation order
1. Regex guard layer
2. Adaptive memory salience scoring
3. Confidence-based clarification
4. Micro-RAG snippets
