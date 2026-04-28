# File: core/cognitive_engine.py
import ollama
import json
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ThoughtStep:
    type: str  # 'thought', 'action', 'observation', 'reflection', 'answer'
    content: str

class CognitiveEngine:
    def __init__(self, model_name: str = "com-v4-cognitive"):
        self.model_name = model_name
        self.max_iterations = 5
        self.history: List[Dict[str, str]] = []
        
    def chat(self, user_query: str) -> str:
        """Main entry point for V4 Cognitive Chat."""
        logger.info(f"Processing query with V4 Engine: {user_query[:50]}...")
        
        # Add user query to history
        self.history.append({"role": "user", "content": user_query})
        
        try:
            # Start the Reflection Loop
            final_response = self._run_reflection_loop(user_query)
            
            # Add assistant response to history
            self.history.append({"role": "assistant", "content": final_response})
            return final_response
            
        except Exception as e:
            logger.error(f"V4 Engine failed: {e}")
            return f"System Error: {str(e)}. Falling back to basic mode."

    def _run_reflection_loop(self, query: str) -> str:
        """Executes the Thought -> Action -> Reflection cycle."""
        steps: List[ThoughtStep] = []
        current_context = query
        
        for i in range(self.max_iterations):
            logger.debug(f"Iteration {i+1}/{self.max_iterations}")
            
            # 1. Generate Thought/Action
            response = self._call_model(current_context, steps)
            
            # Parse the response for structured tags
            thought = self._extract_tag(response, "thought")
            action = self._extract_tag(response, "action")
            answer = self._extract_tag(response, "answer")
            
            if thought:
                steps.append(ThoughtStep("thought", thought))
                logger.info(f"Thought: {thought[:100]}...")
            
            if action:
                # Execute Tool
                observation = self._execute_action(action)
                steps.append(ThoughtStep("observation", observation))
                current_context = f"Previous Action Result: {observation}\nContinue reasoning."
                continue # Loop again to reflect on result
            
            if answer:
                # Final Answer Found
                steps.append(ThoughtStep("answer", answer))
                return self._format_final_output(steps)
            
            # If no tags found but we have text, treat as simple answer (fallback)
            if not thought and not action and not answer:
                clean_text = re.sub(r'<.*?>', '', response).strip()
                if clean_text:
                    return clean_text
                    
            # If we have thought but no action/answer, force a conclusion
            if thought and not action and not answer:
                return self._synthesize_conclusion(steps)
        
        return "I reached the maximum reasoning depth without a clear conclusion."

    def _call_model(self, context: str, steps: List[ThoughtStep]) -> str:
        """Calls Ollama with the current cognitive context."""
        # Build the prompt dynamically
        prompt_parts = [f"<|query|>\n{context}\n</|query|>"]
        
        # Inject recent steps as context
        if steps:
            recent_steps = steps[-3:] # Keep last 3 steps in context
            history_str = "\n".join([f"<{s.type}>{s.content}</{s.type}>" for s in recent_steps])
            prompt_parts.insert(0, f"<|history|>\n{history_str}\n</|history|>")
        
        full_prompt = "\n".join(prompt_parts)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": full_prompt}],
                options={"temperature": 0.3, "num_predict": 1024}
            )
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Ollama connection failed: {e}")

    def _execute_action(self, action_json: str) -> str:
        """Parses and executes a tool action."""
        try:
            # Clean JSON string
            json_match = re.search(r'\{.*\}', action_json, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                tool_name = data.get("name", "unknown")
                args = data.get("arguments", {})
                
                logger.info(f"Executing tool: {tool_name}")
                
                # TODO: Integrate with your existing tools from com_core.py
                # For now, return a mock observation
                return f"Tool '{tool_name}' executed with args {args}. Result: Success (Mock)."
            else:
                return "Invalid JSON format in action tag."
        except json.JSONDecodeError:
            return "Error: Could not parse action JSON."
        except Exception as e:
            return f"Tool execution error: {str(e)}"

    def _synthesize_conclusion(self, steps: List[ThoughtStep]) -> str:
        """Forces a conclusion if the model stops mid-thought."""
        thoughts = [s.content for s in steps if s.type == "thought"]
        if not thoughts:
            return "I have processed your request."
        
        last_thought = thoughts[-1]
        return f"Based on my analysis: {last_thought}"

    def _format_final_output(self, steps: List[ThoughtStep]) -> str:
        """Formats the final response for the user."""
        # In V4, we might want to hide the raw XML tags from the user 
        # or show a summarized version. For now, return the clean answer.
        answer_step = next((s for s in steps if s.type == "answer"), None)
        if answer_step:
            return answer_step.content
        return "No final answer generated."

    def _extract_tag(self, text: str, tag_name: str) -> Optional[str]:
        """Extracts content between <tag>...</tag>."""
        pattern = f"<{tag_name}>(.*?)</{tag_name}>"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def reset(self):
        """Clears conversation history."""
        self.history = []
        logger.info("Conversation history cleared.")
