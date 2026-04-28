# Reflective Signal Protocol v4

## Overview

The **Reflective Signal Protocol (RSP)** is a revolutionary approach to LLM-based intent routing based on recent research showing that **prompt repetition improves non-reasoning LLM performance**. 

Instead of having the LLM generate direct answers, it acts purely as a **BRAIN** that:
1. **REFLECTS** the user's intent in structured Signal Parse language
2. **ROUTES** signals to specialized harnesses/experts
3. **NEVER** generates content directly

## Architecture

```
User Query → [LLM Reflection] → [Signal Parser] → [Intent Router] → [Harness Execution]
                ↑                    ↑                  ↑                 ↑
         (structured           (parse <reflection>  (route to        (execute actual
          thinking)             block & @ROUTE)      domain)           work)
```

## Key Benefits

### 1. Research-Backed Performance
Based on recent studies showing prompt repetition improves LLM accuracy:
- **Anchors attention** to task structure rather than content generation
- **Reduces hallucinations** by forcing structured thinking
- **Improves routing accuracy** through explicit intent declaration

### 2. Modular Execution
- LLM only thinks and directs (minimal compute)
- Specialized harnesses execute domain-specific tasks
- Easy to add new domains without retraining LLM

### 3. Deterministic Parsing
- Structured `<reflection>` blocks enable reliable parsing
- JSON payloads ensure data integrity
- Multiple routes per query supported

## Protocol Format

### Required Output Structure

Every LLM response MUST follow this exact format:

```xml
<reflection>
- Intent: [Clear one-sentence intent detection]
- Domain: [GODOT/OFFICE/CPP/PYTHON/JS/JSON/DESKTOP/WIKI/GENERAL]
- Action: [Specific action needed]
- Payload: {Structured JSON data}
- Confidence: [high/medium/low]
</reflection>

@ROUTE:[DOMAIN]:[action]:{payload_json}
```

### Example Responses

#### Knowledge Query
**User:** "What is machine learning?"

**LLM Response:**
```xml
<reflection>
- Intent: User seeks definition and explanation of machine learning concept
- Domain: WIKI
- Action: search_and_synthesize
- Payload: {"query": "machine learning", "top_k": 3}
- Confidence: high
</reflection>

@ROUTE:WIKI:search:{"query": "machine learning", "top_k": 3}
```

#### File Creation
**User:** "Create an Excel file for inventory tracking"

**LLM Response:**
```xml
<reflection>
- Intent: User wants to create Excel spreadsheet for inventory
- Domain: OFFICE
- Action: create_excel
- Payload: {"filename": "inventory", "columns": ["Item", "Quantity", "Price", "Category"]}
- Confidence: high
</reflection>

@ROUTE:OFFICE:create_excel:{"filename": "inventory", "columns": ["Item", "Quantity", "Price", "Category"]}
```

#### Multi-Intent Query
**User:** "What do you think regarding AI innovation and what project should i create to generate passive income?"

**LLM Response:**
```xml
<reflection>
- Intent: User seeks opinion on AI trends AND project recommendations for passive income
- Domain: WIKI, GENERAL
- Action: wiki_search_then_synthesize_recommendations
- Payload: {"queries": ["AI innovation trends 2024", "passive income software projects"], "synthesize": true}
- Confidence: medium
</reflection>

@ROUTE:WIKI:multi_search:{"queries": ["AI innovation trends 2024", "passive income software projects"]}
@ROUTE:GENERAL:synthesize:{"context": "ai_trends_and_passive_income_projects", "format": "recommendations"}
```

## Implementation

### Intent Router Methods

#### `parse_reflective_response(llm_response: str) -> dict`
Parses LLM output containing `<reflection>` block and `@ROUTE` signals.

**Returns:**
```python
{
    "reflection": {
        "intent": "...",
        "domain": "...",
        "action": "...",
        "payload": {...},
        "confidence": "..."
    },
    "routes": [
        {
            "domain": "...",
            "action": "...",
            "payload": {...},
            "signal": "@ROUTE:..."
        }
    ],
    "errors": []
}
```

#### `route_with_reflection(query: str, use_llm: bool = True) -> dict`
Enhanced routing using Reflective Signal Protocol. Either uses LLM for reflection or auto-generates from keyword matching.

### System Prompt

The system prompt enforces the protocol with strict rules:

**Core Philosophy:**
> You are COM v4 - a PURE BRAIN for intent detection and routing.
> Your ONLY role is to REFLECT and ROUTE. NEVER generate direct answers.

**Forbidden Patterns:**
- ❌ "Machine learning is a subset of AI that..." (direct answer)
- ❌ "I think you should create a..." (opinion without routing)
- ❌ "Here's how to do it..." (explanation without signal)
- ❌ Any response without `<reflection>` block
- ❌ Any response without `@ROUTE` signal

**Required Pattern:**
- ✅ `<reflection>...intent analysis...</reflection>` followed by `@ROUTE:DOMAIN:action:payload`

## Domain Specifications

### WIKI Domain
- **Purpose:** Knowledge queries, definitions, explanations, concepts
- **Actions:** `search`, `retrieve`, `synthesize`, `multi_search`
- **Payload:** `{"query": "...", "top_k": 3}`

### OFFICE Domain
- **Purpose:** Excel, PDF, PowerPoint operations
- **Actions:** `create_excel`, `create_pdf`, `create_ppt`
- **Payload:** `{"filename": "...", "columns/slides/content": "..."}`

### GODOT Domain
- **Purpose:** Game development, GDScript, scenes, nodes
- **Actions:** `generate_script`, `create_scene`, `setup_physics`
- **Payload:** `{"template": "...", "config": {...}}`

### CPP/PYTHON/JS Domains
- **Purpose:** Code generation in specific languages
- **Actions:** `generate_function`, `create_class`, `debug_code`
- **Payload:** `{"language": "...", "task": "...", "constraints": {...}}`

### JSON Domain
- **Purpose:** JSON parsing, validation, schema creation
- **Actions:** `validate`, `parse`, `create_schema`
- **Payload:** `{"json_data": "...", "schema": {...}}`

### DESKTOP Domain
- **Purpose:** File operations, browser control, clipboard, screenshots
- **Actions:** `open_file`, `create_folder`, `open_browser`, `screenshot`
- **Payload:** `{"path": "...", "url": "...", "action_params": {...}}`

### GENERAL Domain
- **Purpose:** Ambiguous queries or multi-domain synthesis
- **Actions:** `synthesize`, `clarify`, `route_multi`
- **Payload:** `{"context": "...", "format": "..."}`

## Testing

Run the built-in tests:

```bash
python core/intent_router.py
```

Expected output shows successful parsing of:
1. Single-route reflective responses
2. Auto-generated reflections (fallback mode)
3. Multi-route responses

## Migration from v3

### v3 (Old Approach)
```python
# LLM generates direct answer
response = llm.generate(prompt)
# May include tool calls but mixed with prose
```

### v4 (Reflective Protocol)
```python
# LLM generates structured reflection + route
response = llm.generate(reflective_prompt)
parsed = router.parse_reflective_response(response)
# Execute routes through harnesses
for route in parsed['routes']:
    harness.execute(route)
```

## Best Practices

1. **Always validate reflection blocks** - Check for required fields
2. **Handle multi-route responses** - Support parallel execution
3. **Log reflection patterns** - Track domain distribution and confidence
4. **Fallback gracefully** - Auto-generate reflections if LLM fails
5. **Keep payloads structured** - Use JSON for complex data

## Future Enhancements

- [ ] Reflection quality scoring
- [ ] Learning from successful routes
- [ ] Dynamic domain expansion
- [ ] Cross-domain dependency resolution
- [ ] Reflection compression for token efficiency

## References

- Research: "Prompt Repetition Improves Non-Reasoning LLMs" (2024)
- COM Architecture v3: Editor Philosophy
- Signal Parse Language Specification
