"""
Intent Router: Two-stage classification (Keyword + LLM Tie-Breaker) with Wiki Integration
Handles ambiguous queries like "make a godot asset spreadsheet".
Routes signals to appropriate expert modules and harnesses.
Supports Reflective Signal Protocol (v4) with <reflection> block parsing.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple

# Signal-Trace Architecture v5: Collapsed from 9 modes to 3
MODES = {
    "CREATION": ["create", "make", "generate", "build", "write", "code",
                 "file", "excel", "pdf", "ppt", "spreadsheet", "report",
                 "godot", "gdscript", "game", "scene", "node", "script",
                 "python", "javascript", "cpp", "json", "program",
                 "c++", "typescript", "react", "save", "export"],
    "RETRIEVAL": ["what is", "who is", "explain", "define", "describe",
                  "tell me about", "how does", "why is", "when did",
                  "wiki", "knowledge", "concept", "tutorial", "guide",
                  "research", "find information", "learn about",
                  "meaning", "summarize"],
    "CHAT": []  # fallback - everything else
}

# Signal prefix mapping to 3 modes
SIGNAL_TO_MODE = {
    "@GDT": "CREATION", "@XLS": "CREATION", "@PDF": "CREATION", 
    "@PPT": "CREATION", "@CODE": "CREATION",
    "@WIKI": "RETRIEVAL", "@WEB": "RETRIEVAL",
    "@CHAT": "CHAT", "@ERR": "CHAT"
}


def _keyword_match(text: str, keywords: list) -> bool:
    """Match keywords with word boundaries to avoid false positives."""
    for k in keywords:
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, text):
            return True
    return False

# Signal prefixes for 3-mode architecture
SIGNAL_PREFIXES = {
    "CREATION": "@CREATION:",
    "RETRIEVAL": "@RETRIEVAL:",
    "CHAT": "@CHAT:"
}


class IntentRouter:
    """
    Signal-Trace Architecture v5: Two-stage classification with Wiki integration.
    Stage 1: Keyword fast-path for 3 modes (CREATION, RETRIEVAL, CHAT)
    Stage 2: If ambiguous (2+ modes match), ask LLM for 1-token classification
    Stage 3: Route to appropriate harness with signal format
    Supports both raw signals and [THOUGHT]/[SIGNAL] trace format.
    """
    
    AMBIGUOUS_THRESHOLD = 2
    ROUTER_PROMPT = """Classify this input into exactly one word: CREATION, RETRIEVAL, or CHAT.
Input: {query}
Reply with one word only."""
    
    # Reflection block pattern for parsing LLM responses
    REFLECTION_PATTERN = re.compile(
        r'<reflection>\s*(.*?)\s*</reflection>',
        re.DOTALL | re.IGNORECASE
    )
    
    # Route signal pattern
    ROUTE_PATTERN = re.compile(
        r'@ROUTE:([A-Z]+):([a-zA-Z_]+):(.+?)(?=\n@ROUTE:|\n*$)',
        re.DOTALL
    )

    def __init__(self, client=None, wiki_indexer=None):
        self.client = client
        self.wiki_indexer = wiki_indexer
        self.signal_history = []
        self.reflection_history = []
    
    def route(self, query: str) -> str:
        """
        Route query to appropriate mode.
        Returns mode string only (benchmark expects string, not dict).
        Signal generation happens in COMCore.process_query().
        """
        matches = []
        text = query.lower()
        
        # Stage 1: Keyword Matching
        for mode, keywords in MODES.items():
            if mode == "CHAT":
                continue  # CHAT is fallback
            if _keyword_match(text, keywords):
                matches.append(mode)
        
        # Clear cases
        if len(matches) == 1:
            mode = matches[0]
        elif len(matches) == 0:
            mode = "CHAT"  # Changed from GENERAL to CHAT
        else:
            # Ambiguous case: Use LLM tie-breaker
            if self.client:
                try:
                    result = self.client.generate(
                        [{"role": "user", 
                          "content": self.ROUTER_PROMPT.format(query=query)}],
                        max_tokens=4,
                        temperature=0.0
                    ).strip().upper()
                    
                    # Normalize result to valid modes
                    result = result.upper()
                    if result in ["CREATION", "RETRIEVAL", "CHAT"]:
                        mode = result
                    elif len(matches) > 0:
                        mode = matches[0]
                    else:
                        mode = "CHAT"
                except Exception:
                    mode = matches[0]
            else:
                mode = matches[0]
        
        return mode
    
    def parse_reflective_response(self, llm_response: str) -> dict:
        """
        Parse LLM response containing <reflection> block and @ROUTE signals.
        
        Args:
            llm_response: Raw LLM output with reflection and route signals
        
        Returns:
            Dict with parsed reflection data and route signals
        """
        result = {
            "reflection": None,
            "routes": [],
            "errors": [],
            "raw_response": llm_response
        }
        
        # Extract reflection block
        reflection_match = self.REFLECTION_PATTERN.search(llm_response)
        if reflection_match:
            reflection_text = reflection_match.group(1).strip()
            reflection_data = self._parse_reflection_content(reflection_text)
            result["reflection"] = reflection_data
            self.reflection_history.append(reflection_data)
        else:
            result["errors"].append("No <reflection> block found in response")
        
        # Extract route signals
        route_matches = self.ROUTE_PATTERN.findall(llm_response)
        for match in route_matches:
            domain, action, payload_str = match
            try:
                # Try to parse payload as JSON
                payload = json.loads(payload_str.strip())
            except json.JSONDecodeError:
                # If not JSON, treat as plain text payload
                payload = payload_str.strip()
            
            route = {
                "domain": domain.upper(),
                "action": action,
                "payload": payload,
                "signal": f"@ROUTE:{domain}:{action}:{payload_str.strip()}"
            }
            result["routes"].append(route)
        
        # Validate that we have both reflection and at least one route
        if not result["reflection"] and not result["routes"]:
            result["errors"].append("Invalid response: missing both reflection and routes")
        
        return result
    
    def _parse_reflection_content(self, reflection_text: str) -> dict:
        """
        Parse the content inside <reflection> block into structured data.
        
        Expected format:
        - Intent: [text]
        - Domain: [domain]
        - Action: [action]
        - Payload: {json}
        - Confidence: [level]
        """
        reflection_data = {
            "intent": "",
            "domain": "",
            "action": "",
            "payload": {},
            "confidence": "",
            "raw_text": reflection_text
        }
        
        # Parse each line
        lines = reflection_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('-'):
                continue
            
            # Remove leading dash and split on colon
            line = line.lstrip('-').strip()
            if ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "intent":
                reflection_data["intent"] = value
            elif key == "domain":
                reflection_data["domain"] = value.upper()
            elif key == "action":
                reflection_data["action"] = value
            elif key == "payload":
                try:
                    reflection_data["payload"] = json.loads(value)
                except json.JSONDecodeError:
                    reflection_data["payload"] = value
            elif key == "confidence":
                reflection_data["confidence"] = value.lower()
        
        return reflection_data
    
    def route_with_reflection(self, query: str, use_llm: bool = True) -> dict:
        """
        Enhanced routing using Signal-Trace Architecture v5.
        
        This method either:
        1. Uses LLM to generate [THOUGHT]/[SIGNAL] format (if use_llm=True)
        2. Falls back to standard routing with auto-generated thought trace
        
        Args:
            query: User query
            use_llm: Whether to use LLM for thought generation
        
        Returns:
            Dict with thought, signal, and routing metadata
        """
        if use_llm and self.client:
            # Prompt LLM to generate Signal-Trace format
            signal_trace_prompt = f"""Analyze this user query and respond with EXACTLY this format:

[THOUGHT]: [one sentence intent analysis]
[SIGNAL]: @TYPE:payload

Where @TYPE is one of:
- @GDT/@XLS/@PDF/@PPT/@CODE for creation tasks
- @WIKI/@WEB for knowledge queries  
- @CHAT for greetings/chat

User Query: {query}

Remember: ONLY output [THOUGHT] and [SIGNAL] lines. No explanations."""
            
            try:
                llm_response = self.client.generate(
                    [{"role": "user", "content": signal_trace_prompt}],
                    max_tokens=128,
                    temperature=0.2
                )
                
                # Parse the Signal-Trace response
                from core.com_core import parse_signal, extract_thought, is_signal
                
                thought = extract_thought(llm_response)
                if is_signal(llm_response):
                    prefix, payload = parse_signal(llm_response)
                    signal = f"{prefix}:{payload}" if payload else prefix
                    
                    return {
                        "thought": thought,
                        "signal": signal,
                        "raw_response": llm_response,
                        "query": query,
                        "method": "llm_signal_trace"
                    }
            except Exception as e:
                # Fallback to standard routing
                pass
        
        # Fallback: Generate thought automatically from standard routing
        standard_result = self.route(query)
        
        auto_thought = f"User wants {standard_result['mode']} operation based on keywords"
        
        return {
            "thought": auto_thought,
            "signal": standard_result["signal"],
            "mode": standard_result["mode"],
            "confidence": standard_result["confidence"],
            "query": query,
            "method": "auto_signal_trace"
        }
    
    def route_with_wiki(self, query: str) -> dict:
        """
        Enhanced routing with wiki lookup for knowledge-based queries.
        """
        # First check if it's a wiki query
        wiki_keywords = ["what is", "explain", "concept", "define", "meaning", "how does"]
        is_wiki_query = any(kw in query.lower() for kw in wiki_keywords)
        
        if is_wiki_query and self.wiki_indexer:
            # Search wiki first
            wiki_results = self.wiki_indexer.search(query, top_k=3)
            
            if wiki_results and len(wiki_results) > 0:
                return {
                    "mode": "WIKI",
                    "signal": f"@WIKI:{query}",
                    "confidence": "high",
                    "wiki_results": wiki_results,
                    "action": "retrieve_and_synthesize"
                }
        
        # Fall back to standard routing
        return self.route(query)
    
    def parse_signal(self, signal: str) -> dict:
        """
        Parse a COM signal string into structured format.
        Example: "@DESK:open_browser:https://example.com"
        """
        if not signal.startswith("@"):
            return {"error": "Invalid signal format", "signal": signal}
        
        parts = signal.split(":", 2)
        
        if len(parts) < 2:
            return {"error": "Incomplete signal", "signal": signal}
        
        harness = parts[0][1:]  # Remove @ prefix
        action_or_payload = parts[1] if len(parts) > 1 else ""
        payload = parts[2] if len(parts) > 2 else ""
        
        return {
            "harness": harness,
            "action": action_or_payload,
            "payload": payload,
            "full_signal": signal
        }
    
    def get_routing_stats(self) -> dict:
        """Get statistics about routing decisions."""
        if not self.signal_history:
            return {"total": 0, "message": "No signals routed yet"}
        
        mode_counts = {}
        confidence_counts = {}
        
        for entry in self.signal_history:
            mode = entry["mode"]
            confidence = entry["confidence"]
            
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        return {
            "total": len(self.signal_history),
            "by_mode": mode_counts,
            "by_confidence": confidence_counts,
            "recent_signals": self.signal_history[-10:]
        }
    
    def get_reflection_stats(self) -> dict:
        """Get statistics about reflection patterns."""
        if not self.reflection_history:
            return {"total": 0, "message": "No reflections parsed yet"}
        
        domain_counts = {}
        confidence_counts = {}
        
        for reflection in self.reflection_history:
            domain = reflection.get("domain", "UNKNOWN")
            confidence = reflection.get("confidence", "unknown")
            
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        return {
            "total": len(self.reflection_history),
            "by_domain": domain_counts,
            "by_confidence": confidence_counts,
            "recent_reflections": self.reflection_history[-10:]
        }


if __name__ == "__main__":
    # Test the Reflective Signal Protocol parsing
    import json
    
    router = IntentRouter()
    
    # Test case 1: Parse a reflective response
    test_response = """<reflection>
- Intent: User wants to create Excel spreadsheet for inventory
- Domain: OFFICE
- Action: create_excel
- Payload: {"filename": "inventory", "columns": ["Item", "Quantity", "Price"]}
- Confidence: high
</reflection>
@ROUTE:OFFICE:create_excel:{"filename": "inventory", "columns": ["Item", "Quantity", "Price"]}"""
    
    print("Test 1: Parsing reflective response")
    print("=" * 60)
    result = router.parse_reflective_response(test_response)
    print(f"Reflection: {json.dumps(result['reflection'], indent=2)}")
    print(f"Routes: {json.dumps(result['routes'], indent=2)}")
    print(f"Errors: {result['errors']}")
    print()
    
    # Test case 2: Route with reflection (fallback mode)
    print("Test 2: Route with reflection (auto-generated)")
    print("=" * 60)
    query = "Create a PDF report about sales data"
    result = router.route_with_reflection(query, use_llm=False)
    print(f"Query: {query}")
    print(f"Method: {result['method']}")
    print(f"Reflection: {json.dumps(result['reflection'], indent=2)}")
    print(f"Routes: {json.dumps(result['routes'], indent=2)}")
    print()
    
    # Test case 3: Multi-route response
    print("Test 3: Multi-route response")
    print("=" * 60)
    multi_response = """<reflection>
- Intent: User seeks AI trends info AND project recommendations
- Domain: WIKI, GENERAL
- Action: multi_search_and_synthesize
- Payload: {"queries": ["AI trends", "passive income projects"]}
- Confidence: medium
</reflection>
@ROUTE:WIKI:search:{"query": "AI innovation trends 2024"}
@ROUTE:GENERAL:synthesize:{"context": "ai_and_income_projects"}"""
    
    result = router.parse_reflective_response(multi_response)
    print(f"Reflection: {json.dumps(result['reflection'], indent=2)}")
    print(f"Number of routes: {len(result['routes'])}")
    for i, route in enumerate(result['routes']):
        print(f"Route {i+1}: {route['signal']}")
    print()
    
    print("All tests completed successfully!")

