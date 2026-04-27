"""
COM Core Client - Handles LLM communication with SmolLM2-1.7B-Q4
This is the bridge between your harness tools and the LLM brain.
"""
import ollama
from typing import Dict, Any, Optional, List


class OllamaClient:
    """Client for interacting with Ollama server using SmolLM2."""
    
    # Model configuration for SmolLM2-1.7B-Q4
    MODEL_NAME = "smollm2:1.7b-instruct-q4_K_M"
    
    # Context limits tightened for SmolLM2 stability under 2GB RAM
    NUM_CTX_BY_MODE = {
        "GODOT": 512,    # Scripts don't need long context
        "OFFICE": 256,   # Signal output is always short
        "GENERAL": 768,  # Reasonable for wiki queries
    }
    
    # Token limits stricter for SmolLM2 signal discipline
    TOKEN_LIMITS = {
        "GODOT": 96,
        "OFFICE": 48,
        "GENERAL": 192,
    }
    
    # System prompts shortened for SmolLM2 (responds better to direct instructions)
    SYSTEM_PROMPTS = {
        "GODOT": "You are a Godot scripting assistant. Output valid GDScript code only.",
        "OFFICE": "Output strict signal format. No explanations. Use @XLS:file:col syntax.",
        "GENERAL": "You are a helpful research assistant. Be concise and accurate.",
    }

    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.client = ollama.Client(host=host)
        
    def generate(
        self, 
        prompt: str, 
        mode: str = "GENERAL",
        system_override: Optional[str] = None
    ) -> str:
        """Generate a response from the model."""
        if mode not in self.NUM_CTX_BY_MODE:
            raise ValueError(f"Invalid mode: {mode}. Choose from {list(self.NUM_CTX_BY_MODE.keys())}")
        
        system_prompt = system_override or self.SYSTEM_PROMPTS.get(mode, self.SYSTEM_PROMPTS["GENERAL"])
        num_ctx = self.NUM_CTX_BY_MODE[mode]
        max_tokens = self.TOKEN_LIMITS[mode]
        
        try:
            response = self.client.generate(
                model=self.MODEL_NAME,
                prompt=prompt,
                system=system_prompt,
                options={
                    "num_ctx": num_ctx,
                    "num_predict": max_tokens,
                    "repeat_penalty": 1.1,  # Prevents looping on short outputs
                    "temperature": 0.2,     # Low temp for deterministic output
                }
            )
            return response["response"]
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        mode: str = "GENERAL"
    ) -> str:
        """Chat with the model using message history."""
        if mode not in self.NUM_CTX_BY_MODE:
            raise ValueError(f"Invalid mode: {mode}")
            
        system_prompt = self.SYSTEM_PROMPTS.get(mode, self.SYSTEM_PROMPTS["GENERAL"])
        num_ctx = self.NUM_CTX_BY_MODE[mode]
        max_tokens = self.TOKEN_LIMITS[mode]
        
        # Inject system message at the start
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            response = self.client.chat(
                model=self.MODEL_NAME,
                messages=full_messages,
                options={
                    "num_ctx": num_ctx,
                    "num_predict": max_tokens,
                    "repeat_penalty": 1.1,
                    "temperature": 0.2,
                }
            )
            return response["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"LLM chat failed: {e}")
