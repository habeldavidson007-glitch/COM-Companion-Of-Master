"""
COM v4 - Cognitive Agent Loop

Implements the Thought -> Action -> Observation -> Reflection -> Response cycle.
This is the core mechanism that enables small models to achieve deep reasoning.
"""

from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Possible states in the agent lifecycle."""
    THINKING = auto()
    ACTING = auto()
    OBSERVING = auto()
    REFLECTING = auto()
    RESPONDING = auto()
    ERROR = auto()


@dataclass
class ThoughtStep:
    """Represents a single step in the reasoning chain."""
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    reflection: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None


@dataclass
class AgentResponse:
    """Final response from the cognitive agent."""
    answer: str
    thought_chain: list[ThoughtStep] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    confidence: float = 0.0
    required_reflections: int = 0


class CognitiveAgent:
    """
    Main agent loop implementing the cognitive architecture.
    
    The agent follows this cycle:
    1. THOUGHT: Generate internal reasoning before acting
    2. ACTION: Execute tools or generate response
    3. OBSERVATION: Capture tool output or validate response
    4. REFLECTION: Analyze errors or low-confidence outputs
    5. RESPONSE: Deliver final answer after verification
    
    This loop compensates for smaller parameter counts by enforcing
    structured thinking and self-verification.
    """
    
    MAX_REFLECTIONS = 3
    MIN_CONFIDENCE_THRESHOLD = 0.7
    MAX_TURNS = 10
    
    def __init__(
        self,
        model_name: str = "com-v4-cognitive",
        tools: Optional[dict[str, Callable]] = None,
        context_manager: Optional[Any] = None,
        reflection_engine: Optional[Any] = None,
    ):
        """
        Initialize the cognitive agent.
        
        Args:
            model_name: Name of the Ollama model to use
            tools: Dictionary of tool_name -> callable function
            context_manager: ContextManager instance for prompt building
            reflection_engine: ReflectionEngine instance for self-analysis
        """
        self.model_name = model_name
        self.tools = tools or {}
        self.context_manager = context_manager
        self.reflection_engine = reflection_engine
        self.state = AgentState.THINKING
        self._turn_count = 0
        
    def _parse_model_output(self, raw_output: str) -> dict[str, Any]:
        """
        Parse the model's raw output to extract structured components.
        
        Expected format:
        <thought>...</thought>
        <action>{"name": "...", "arguments": {...}}</action>
        <confidence>0.85</confidence>
        
        Returns:
            Dictionary with thought, action, confidence keys
        """
        result = {
            "thought": "",
            "action": None,
            "confidence": 0.5,
            "raw_response": raw_output
        }
        
        # Extract thought block
        thought_match = re.search(
            r'<thought>\s*(.*?)\s*</thought>',
            raw_output,
            re.DOTALL | re.IGNORECASE
        )
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # Extract action block (JSON)
        action_match = re.search(
            r'<action>\s*(\{.*?\})\s*</action>',
            raw_output,
            re.DOTALL | re.IGNORECASE
        )
        if action_match:
            try:
                result["action"] = json.loads(action_match.group(1))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse action JSON: {e}")
                result["action"] = None
        
        # Extract confidence score
        conf_match = re.search(
            r'<confidence>\s*([\d.]+)\s*</confidence>',
            raw_output,
            re.IGNORECASE
        )
        if conf_match:
            try:
                result["confidence"] = float(conf_match.group(1))
            except ValueError:
                pass
        
        return result
    
    def _execute_tool(self, action: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """
        Safely execute a tool and return (observation, error).
        
        Args:
            action: Dictionary with 'name' and 'arguments' keys
            
        Returns:
            Tuple of (observation_string, error_string)
        """
        tool_name = action.get("name")
        arguments = action.get("arguments", {})
        
        if tool_name not in self.tools:
            return None, f"Unknown tool: {tool_name}"
        
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**arguments)
            
            # Convert result to string observation
            if isinstance(result, (dict, list)):
                observation = json.dumps(result, indent=2)
            else:
                observation = str(result)
                
            return observation, None
            
        except Exception as e:
            logger.exception(f"Tool execution failed: {tool_name}")
            return None, f"Tool error: {str(e)}"
    
    def _generate_response(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a response from the model.
        
        In production, this would call Ollama's API. For now, it's a placeholder
        that demonstrates the integration point.
        """
        # Placeholder for Ollama integration
        # In production:
        # import ollama
        # response = ollama.generate(
        #     model=self.model_name,
        #     prompt=prompt,
        #     options={"temperature": temperature, "num_predict": max_tokens}
        # )
        # return response["response"]
        
        logger.info(f"Generating response with prompt length: {len(prompt)}")
        return "<thought>Analyzing request...</thought><action>{\"name\": \"response\", \"arguments\": {\"text\": \"Placeholder response\"}}</action><confidence>0.9</confidence>"
    
    def self_reflect(
        self,
        thought_step: ThoughtStep,
        error_context: Optional[str] = None
    ) -> str:
        """
        Force the model to reflect on its previous output or error.
        
        This is the key mechanism that compensates for smaller parameter counts.
        By requiring explicit self-analysis, we catch errors before they propagate.
        
        Args:
            thought_step: The previous thought/action/observation to reflect on
            error_context: Optional error message that triggered reflection
            
        Returns:
            Reflection text from the model
        """
        self.state = AgentState.REFLECTING
        
        reflection_prompt = f"""
<reflection_task>
Analyze the previous reasoning step and identify potential issues.

PREVIOUS THOUGHT: {thought_step.thought}
PREVIOUS ACTION: {thought_step.action}
OBSERVATION: {thought_step.observation}
ERROR (if any): {error_context or "None"}

Questions to answer:
1. Was the initial assumption correct?
2. Did the tool produce expected results?
3. What alternative approaches should be considered?
4. What is the corrected plan?

Provide your reflection in the following format:
<reflection>
[Your analysis here]
</reflection>
<corrected_plan>
[Your revised approach]
</corrected_plan>
<new_confidence>
[0.0-1.0]
</new_confidence>
</reflection_task>
"""
        
        reflection_output = self._generate_response(reflection_prompt)
        
        # Extract reflection content
        reflection_match = re.search(
            r'<reflection>\s*(.*?)\s*</reflection>',
            reflection_output,
            re.DOTALL | re.IGNORECASE
        )
        
        if reflection_match:
            thought_step.reflection = reflection_match.group(1).strip()
        
        return reflection_output
    
    def run(self, query: str) -> AgentResponse:
        """
        Execute the full cognitive loop for a given query.
        
        Args:
            query: User's input question or command
            
        Returns:
            AgentResponse with answer, thought chain, and metadata
        """
        self._turn_count = 0
        thought_chain: list[ThoughtStep] = []
        tools_used: list[str] = []
        reflection_count = 0
        
        # Build initial prompt with context
        if self.context_manager:
            prompt = self.context_manager.build_prompt(query)
        else:
            prompt = f"<user_query>{query}</user_query>"
        
        current_prompt = prompt
        last_error: Optional[str] = None
        
        while self._turn_count < self.MAX_TURNS:
            self._turn_count += 1
            self.state = AgentState.THINKING
            
            # Generate thought + action
            logger.info(f"Turn {self._turn_count}: Generating thought and action")
            raw_output = self._generate_response(current_prompt)
            parsed = self._parse_model_output(raw_output)
            
            thought_step = ThoughtStep(
                thought=parsed["thought"],
                confidence=parsed["confidence"]
            )
            
            # Check if action is a final response or tool call
            action = parsed["action"]
            
            if action is None:
                # No structured action - treat as final response
                logger.info("No action detected, treating as final response")
                thought_step.action = "response"
                thought_chain.append(thought_step)
                
                # Extract response from thought or raw output
                response_text = parsed["thought"] or raw_output
                break
                
            elif action.get("name") == "response":
                # Explicit response action
                logger.info("Response action detected")
                thought_step.action = "response"
                thought_chain.append(thought_step)
                break
                
            else:
                # Tool execution required
                self.state = AgentState.ACTING
                thought_step.action = json.dumps(action)
                
                logger.info(f"Executing tool: {action.get('name')}")
                observation, error = self._execute_tool(action)
                
                self.state = AgentState.OBSERVING
                thought_step.observation = observation
                thought_step.error = error
                
                if error:
                    tools_used.append(f"{action.get('name')} (failed)")
                else:
                    tools_used.append(action.get("name", "unknown"))
                
                # Check if reflection is needed
                needs_reflection = (
                    error is not None or
                    parsed["confidence"] < self.MIN_CONFIDENCE_THRESHOLD
                )
                
                if needs_reflection and reflection_count < self.MAX_REFLECTIONS:
                    logger.info(f"Triggering reflection (error={error}, confidence={parsed['confidence']})")
                    self.self_reflect(thought_step, error_context=error)
                    reflection_count += 1
                    
                    # Update prompt with reflection and retry
                    if self.context_manager:
                        current_prompt = self.context_manager.build_prompt(
                            query,
                            additional_context=f"\n<reflection_history>{thought_step.reflection}</reflection_history>"
                        )
                    continue
                
                thought_chain.append(thought_step)
                
                # Prepare next turn with observation
                if self.context_manager:
                    current_prompt = self.context_manager.build_prompt(
                        query,
                        additional_context=f"\n<last_observation>{observation}</last_observation>"
                    )
        
        # Compile final response
        final_answer = thought_chain[-1].thought if thought_chain else "Unable to process query"
        avg_confidence = sum(ts.confidence for ts in thought_chain) / len(thought_chain) if thought_chain else 0.0
        
        return AgentResponse(
            answer=final_answer,
            thought_chain=thought_chain,
            tools_used=tools_used,
            confidence=avg_confidence,
            required_reflections=reflection_count
        )
    
    def chat(self, query: str) -> str:
        """
        Simple chat interface that returns just the answer.
        
        Args:
            query: User's question
            
        Returns:
            String response
        """
        response = self.run(query)
        return response.answer
