"""
COM v4 Architecture - LLM as Pure Intent Router (BRAIN Only)
=============================================================

CORE PHILOSOPHY:
- LLM is ONLY a BRAIN that detects intent and emits signal bytes
- ALL execution, data processing, and answer generation happens in HARNESS tools
- LLM never generates answers directly - it only routes to the right harness

SIGNAL-OF-THOUGHT (SoT) v2:
---------------------------
The LLM outputs ONLY signal bytes in this format:
  @HARNESS_NAME:payload

Available Harnesses:
  @XLS     - Excel file creation/manipulation
  @PDF     - PDF generation
  @PPT     - PowerPoint creation
  @GDT     - Godot/GDScript code generation
  @WIKI    - Knowledge retrieval from wiki database
  @WEB     - Web search and live data fetching
  @CODE    - General code generation (Python, C++, etc.)
  @CHAT    - Simple conversational responses (greetings, thanks)
  @ERR     - Error/clarification requests

ARCHITECTURE FLOW:
==================

User Query → [LLM BRAIN] → Signal Byte → [HARNESS EXECUTOR] → Final Answer
              ↓                              ↓
         Intent Detection              Tool Execution
         Mode Classification            Data Processing
         Signal Emission                Answer Generation

KEY CHANGES FROM v3:
====================

1. NO Direct Answers from LLM
   - Even for greetings, LLM outputs: @CHAT:greeting_ack
   - Even for opinions, LLM outputs: @WIKI:search_query or @WEB:topic
   
2. All Harnesses Must Generate Final Output
   - @WIKI harness retrieves and synthesizes knowledge
   - @CHAT harness provides conversational responses
   - @CODE harness generates and explains code
   - Office harnesses (@XLS/@PDF/@PPT) create files and confirm

3. LLM Training Focus
   - Don't need smart/good model for answers
   - Need better SIGNAL DETECTION accuracy
   - Focus on: bigger training data for intent classification
   - Focus on: better signal taxonomy and routing logic

IMPLEMENTATION GUIDE:
=====================

System Prompt for LLM (BRAIN):
------------------------------
"You are COM v4 - a pure INTENT ROUTER.
You NEVER generate answers, explanations, or content.
You ONLY output signal bytes in format: @HARNESS:payload

Examples:
User: 'Hello' → @CHAT:greeting
User: 'Thanks' → @CHAT:thanks  
User: 'Create Excel for inventory' → @XLS:Inventory:Item,Qty,Price
User: 'What is AI?' → @WIKI:artificial intelligence definition
User: 'AI innovation trends' → @WIKI:AI innovation trends 2024
User: 'Make a Godot player script' → @GDT:player_controller_2d
User: 'Passive income project ideas' → @WIKI:passive income software projects

Output ONE signal line only. No explanation."

Harness Executor Responsibilities:
----------------------------------
Each harness must:
1. Parse its payload
2. Execute the task (file I/O, API calls, DB queries, etc.)
3. Generate the final user-facing answer
4. Return result to UI

Example @WIKI Harness:
```python
def execute_wiki(payload):
    query = payload
    results = wiki_search(query)
    if results:
        answer = synthesize_wiki_results(results)
        return f"📚 From knowledge base:\n{answer}"
    else:
        # Fall back to web search
        return execute_web(payload)
```

Example @CHAT Harness:
```python
def execute_chat(payload):
    if payload == "greeting":
        return "💬 Hi, I am COM. Ready to help with tasks."
    elif payload == "thanks":
        return "💬 You're welcome! What's next?"
    else:
        return "💬 How can I assist you?"
```

BENEFITS:
=========
1. Smaller/Cheaper LLM: Only needs signal classification, not reasoning
2. Better Accuracy: Harnesses are deterministic, reliable code
3. Scalable: Add new harnesses without retraining LLM
4. Maintainable: Logic separated from routing
5. Faster: Parallel harness execution, cached results
6. Transparent: Clear signal audit trail

TESTING STRATEGY:
=================
Test queries should verify:
✓ Greeting → @CHAT signal (not LLM-generated response)
✓ Knowledge query → @WIKI or @WEB signal
✓ File operation → @XLS/@PDF/@PPT signal
✓ Code request → @GDT or @CODE signal
✓ Ambiguous query → @ERR signal with clarification request

Metrics to track:
- Signal routing accuracy (% correct harness selected)
- Harness execution success rate
- End-to-end latency (signal detection + execution)
- Cache hit rate for repeated signals
"""

# Example signal routing table for LLM few-shot training
SIGNAL_ROUTING_EXAMPLES = [
    ("hello", "@CHAT:greeting"),
    ("hi there", "@CHAT:greeting"),
    ("thanks", "@CHAT:thanks"),
    ("thank you", "@CHAT:thanks"),
    ("create an excel file", "@XLS:untitled:col1,col2"),
    ("make a pdf report", "@PDF:report:content"),
    ("godot player movement", "@GDT:player_movement_2d"),
    ("what is machine learning", "@WIKI:machine learning definition"),
    ("AI trends 2024", "@WIKI:AI trends 2024"),
    ("passive income ideas", "@WIKI:passive income software projects"),
    ("weather today", "@WEB:current weather"),
    ("stock price AAPL", "@WEB:AAPL stock price"),
    ("write python function", "@CODE:python function"),
    ("explain quantum computing", "@WIKI:quantum computing basics"),
]

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "="*60)
    print("Signal Routing Examples:")
    print("="*60)
    for query, signal in SIGNAL_ROUTING_EXAMPLES:
        print(f"User: '{query}' → {signal}")
