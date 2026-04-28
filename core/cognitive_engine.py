import ollama
import json
import re
import logging
from typing import Dict, Any, Optional
from tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class CognitiveEngine:
    def __init__(self, model_name: str = "com-v4-cognitive"):
        self.model_name = model_name
        self.history = []
        # Fast path keywords
        self.greetings = {'hello', 'hi', 'hey', 'good morning', 'good night', 'thanks', 'thank you'}

    def chat(self, user_query: str) -> str:
        """Main entry point: Commander Pattern."""
        logger.info(f"Processing: {user_query[:50]}...")

        # 1. FAST PATH: Instant response for greetings
        if self._is_greeting(user_query):
            return self._fast_reply(user_query)

        try:
            # 2. PHASE 1: Intent Classification (LLM outputs JSON only)
            intent_data = self._classify_intent(user_query)
            
            # 3. PHASE 2: Execution (Python does the heavy lifting)
            observation = ""
            if intent_data.get("action") != "none":
                observation = self._execute_tool(intent_data)
            
            # 4. PHASE 3: Synthesis (LLM formats the result)
            final_response = self._synthesize_response(user_query, intent_data, observation)
            
            return final_response

        except Exception as e:
            logger.error(f"Commander Engine Error: {e}")
            return f"System error: {str(e)}. Trying basic mode..."

    def _is_greeting(self, text: str) -> bool:
        clean = text.lower().strip().strip('?!.')
        return clean in self.greetings or len(clean.split()) <= 2 and clean in self.greetings

    def _fast_reply(self, text: str) -> str:
        try:
            resp = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": text}])
            return resp['message']['content']
        except:
            return "Hello! I am ready."

    def _classify_intent(self, query: str) -> Dict[str, Any]:
        """Forces LLM to output STRICT JSON only."""
        prompt = f"""
Analyze the user query and output ONLY a valid JSON object. No markdown, no text outside JSON.
Schema: {{"action": "tool_name_or_none", "arguments": {{}}}}

Available Tools:
- calculate: For math (args: expression)
- search_wiki: For local knowledge (args: query)
- read_file: For reading files (args: path)
- web_search: For live info (args: query)
- none: For chat/opinion

User Query: "{query}"

JSON Output:
"""
        try:
            resp = ollama.chat(
                model=self.model_name, 
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 150}
            )
            content = resp['message']['content']
            # Clean markdown if LLM adds it
            content = re.sub(r'```json|```', '', content).strip()
            return json.loads(content)
        except Exception as e:
            logger.warning(f"Intent parsing failed: {e}. Defaulting to 'none'.")
            return {"action": "none", "arguments": {}}

    def _execute_tool(self, intent: Dict[str, Any]) -> str:
        """Python executes the tool instantly."""
        action = intent.get("action")
        args = intent.get("arguments", {})
        
        if action == "none":
            return ""
        
        logger.info(f"Executing Tool: {action} with {args}")
        try:
            return ToolRegistry.execute(action, args)
        except Exception as e:
            return f"Tool execution failed: {str(e)}"

    def _synthesize_response(self, query: str, intent: Dict[str, Any], observation: str) -> str:
        """LLM formats the final answer based on tool output."""
        if not observation:
            # No tool used, just chat
            prompt = f"User: {query}\nAssistant:"
            try:
                resp = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": prompt}])
                return resp['message']['content']
            except:
                return "I processed your request."
        
        # Tool was used, format the result
        prompt = f"""
User asked: "{query}"
Tool Result: {observation}

Provide a clear, natural language answer based on the tool result. Do not mention the tool name, just give the answer.
"""
        try:
            resp = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": prompt}])
            return resp['message']['content']
        except:
            return f"Result: {observation}"

    def reset(self):
        self.history = []
