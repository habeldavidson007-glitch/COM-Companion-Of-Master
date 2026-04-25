"""
COM (Companion Of Master) - Optimized Core for Low-RAM Systems
Features: Chain-of-Thought, In-Context Learning, Sliding Window Memory
Model: qwen2.5:0.5b-instruct-q4_K_M (~500MB RAM)
"""

import json
import threading
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict


class MemoryManager:
    """Lightweight sliding window memory (RAG-light alternative)"""
    
    def __init__(self, max_messages: int = 6):
        self.max_messages = max_messages
        self.history = deque(maxlen=max_messages)
        self.context_examples = [
            {
                "role": "user",
                "content": "What is 2 + 2?"
            },
            {
                "role": "assistant", 
                "content": "Let me think step by step:\n1. We have two numbers: 2 and 2\n2. Adding them together: 2 + 2\n3. The result is 4\n\nAnswer: 4"
            }
        ]
    
    def add_message(self, role: str, content: str):
        """Add message to sliding window"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M")
        })
    
    def get_context(self) -> List[Dict]:
        """Get current context with ICL examples"""
        return self.context_examples + list(self.history)
    
    def clear(self):
        """Clear conversation history"""
        self.history.clear()
    
    def get_summary(self) -> str:
        """Get text summary of recent conversation"""
        if not self.history:
            return "No previous conversation."
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.history])


class PromptEngine:
    """Chain-of-Thought prompt engineering for qwen2.5:0.5b"""
    
    SYSTEM_PROMPT = """You are COM (Companion Of Master), an intelligent assistant.
Always use Chain-of-Thought reasoning before answering.
Format your response as:
1. Break down the problem step-by-step
2. Show your reasoning clearly
3. Provide a concise final answer

Be helpful, concise, and accurate."""

    COT_TRIGGER = "Let me think step by step:"
    
    @classmethod
    def build_prompt(cls, user_query: str, context: List[Dict]) -> str:
        """Build optimized prompt with context and CoT"""
        messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]
        messages.extend(context)
        messages.append({"role": "user", "content": user_query})
        
        # Format for Ollama chat API
        return messages
    
    @classmethod
    def extract_reasoning(cls, response: str) -> tuple[str, str]:
        """Separate reasoning from final answer"""
        if cls.COT_TRIGGER in response:
            parts = response.split(cls.COT_TRIGGER, 1)
            reasoning = cls.COT_TRIGGER + parts[1] if len(parts) > 1 else ""
            return reasoning, response
        return "", response


class OllamaClient:
    """Optimized Ollama client for low-RAM systems"""
    
    def __init__(self, model: str = "qwen2.5:0.5b-instruct-q4_K_M"):
        self.model = model
        self.base_url = "http://localhost:11434"
        self.timeout = 30
    
    def check_connection(self) -> bool:
        """Check if Ollama is running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_stream(self, messages: List[Dict], callback=None):
        """Stream response with low memory footprint"""
        import requests
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 512,
                "num_ctx": 2048
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            chunk = data["message"]["content"]
                            full_response += chunk
                            if callback:
                                callback(chunk)
                    except json.JSONDecodeError:
                        continue
            
            return full_response
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ollama connection failed: {str(e)}")
    
    def generate(self, messages: List[Dict]) -> str:
        """Non-streaming generation"""
        full_response = ""
        self.generate_stream(messages, callback=lambda x: None)
        return full_response


class COMCore:
    """Main COM core integrating all components"""
    
    def __init__(self):
        self.memory = MemoryManager(max_messages=6)
        self.prompt_engine = PromptEngine()
        self.client = OllamaClient()
        self.is_processing = False
    
    def check_status(self) -> Dict:
        """Check system status"""
        return {
            "ollama_running": self.client.check_connection(),
            "model": self.client.model,
            "memory_size": len(self.memory.history),
            "max_memory": self.memory.max_messages
        }
    
    def process_query(self, query: str, callback=None) -> str:
        """Process user query with full pipeline"""
        if self.is_processing:
            return "Already processing a request..."
        
        self.is_processing = True
        
        try:
            # Build context-aware prompt
            context = self.memory.get_context()
            messages = self.prompt_engine.build_prompt(query, context)
            
            # Stream response
            full_response = ""
            def stream_callback(chunk):
                nonlocal full_response
                full_response += chunk
                if callback:
                    callback(chunk)
            
            response = self.client.generate_stream(messages, callback=stream_callback)
            
            # Store in memory
            self.memory.add_message("user", query)
            self.memory.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if callback:
                callback(f"\n{error_msg}")
            return error_msg
        
        finally:
            self.is_processing = False
    
    def clear_memory(self):
        """Clear conversation history"""
        self.memory.clear()
    
    def get_memory_summary(self) -> str:
        """Get current memory state"""
        return self.memory.get_summary()


# Convenience function for UI integration
def create_com_core():
    """Factory function to create COM core instance"""
    return COMCore()


if __name__ == "__main__":
    # Test the core
    print("Testing COM Core...")
    com = COMCore()
    
    status = com.check_status()
    print(f"Status: {status}")
    
    if status["ollama_running"]:
        print("\nAsking a question...")
        response = com.process_query("What is machine learning?", callback=print)
        print(f"\nFull response received: {len(response)} characters")
        print(f"\nMemory summary:\n{com.get_memory_summary()}")
    else:
        print("Ollama is not running. Please start Ollama first.")
