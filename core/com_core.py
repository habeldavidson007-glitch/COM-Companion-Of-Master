"""
COM (Companion Of Master) - Signal-of-Thought (SoT) Core
Features: Mode Detection, Signal Byte Output, Response Cache
Model: qwen2.5:0.5b-instruct-q4_K_M (~500MB RAM)
"""

import json
import hashlib
import time
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict, Tuple

from .intent_router import IntentRouter
from .context_compressor import ContextCompressor
from .session_logger import SessionLogger

# ================================================================
# PHASE 1 — MODE CLASSIFIER
# ================================================================

MODES = {
    "GODOT":  ["godot", "gdscript", "game", "scene", "node",
               "physics", "animation", "script", "player"],
    "OFFICE": ["excel", "pdf", "ppt", "spreadsheet", "report",
               "dokumen", "laporan", "buat file", "tabel"],
    "GENERAL": []  # fallback
}

def classify_mode(user_input: str) -> str:
    """Pure Python keyword check for mode detection"""
    text = user_input.lower()
    for mode, keywords in MODES.items():
        if any(k in text for k in keywords):
            return mode
    return "GENERAL"


# ================================================================
# PHASE 2 — SoT PROMPT ENGINE
# ================================================================

SYSTEM_PROMPTS = {
    "GODOT": """You are COM. Output ONLY GDScript code or a @GDT signal.
Signal format: @GDT:CATEGORY:DETAIL
Examples: @GDT:MOV:2D  |  @GDT:ANIM:IDLE  |  @GDT:SCENE:PLAYER
If user wants a script, write GDScript only. No explanation.""",

    "OFFICE": """You are COM. Output ONLY a signal byte. Nothing else.
Signals:
  @XLS:filename:col1,col2,col3
  @PDF:filename:content text
  @PPT:filename:slide1|slide2|slide3
Example: @XLS:Inventory:Item,Qty,Price
One line. No explanation. Signal only.""",

    "GENERAL": """You are COM (Companion Of Master).
Answer in max 3 bullet points.
Format: • point
No greetings. No filler. Direct answer only."""
}

TOKEN_LIMITS = {
    "GODOT":   128,
    "OFFICE":  64,
    "GENERAL": 256
}

TEMPERATURES = {
    "GODOT":   0.2,  # deterministic code
    "OFFICE":  0.1,  # exact signal output
    "GENERAL": 0.7   # natural answers
}

NUM_CTX_BY_MODE = {
    "GODOT": 768,
    "OFFICE": 512,
    "GENERAL": 1024
}


# ================================================================
# PHASE 3 — RESPONSE CACHE
# ================================================================

class ResponseCache:
    """Stores hash(mode + input) → signal output for instant responses"""
    
    def __init__(self, max_size=100):
        self._cache = {}
        self._max = max_size

    def _key(self, mode, text):
        raw = f"{mode}:{text.strip().lower()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, mode, text):
        return self._cache.get(self._key(mode, text))

    def set(self, mode, text, signal):
        if len(self._cache) >= self._max:
            self._cache.pop(next(iter(self._cache)))
        self._cache[self._key(mode, text)] = signal


# ================================================================
# PHASE 4 — SIGNAL VALIDATOR
# ================================================================

VALID_PREFIXES = {"@GDT", "@XLS", "@PDF", "@PPT", "@ERR"}

def is_signal(text: str) -> bool:
    """Validate LLM output before passing to harness"""
    return text.strip()[:4] in VALID_PREFIXES

def parse_signal(text: str) -> Tuple[str, str]:
    """Parse signal into prefix and payload
    "@XLS:Inventory:Item,Qty" → ("@XLS", "Inventory:Item,Qty")
    """
    parts = text.strip().split(":", 1)
    prefix = parts[0]
    payload = parts[1] if len(parts) > 1 else ""
    return prefix, payload


# ================================================================
# MEMORY MANAGER
# ================================================================

class MemoryManager:
    """Lightweight sliding window memory (RAG-light alternative)"""
    
    def __init__(self, max_messages: int = 6):
        self.max_messages = max_messages
        self.history = deque(maxlen=max_messages)
    
    def add_message(self, role: str, content: str):
        """Add message to sliding window"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M")
        })
    
    def get_context(self) -> List[Dict]:
        """Get context in chat API format (role/content only)."""
        return [{"role": m["role"], "content": m["content"]} for m in self.history]
    
    def clear(self):
        """Clear conversation history"""
        self.history.clear()
    
    def get_summary(self) -> str:
        """Get text summary of recent conversation"""
        if not self.history:
            return "No previous conversation."
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.history])


# ================================================================
# OLLAMA CLIENT
# ================================================================

class OllamaClient:
    """Optimized Ollama client for low-RAM systems"""
    
    def __init__(self, model: str = "qwen2.5:0.5b-instruct-q4_K_M"):
        self.model = model
        self.base_url = "http://localhost:11434"
        self.timeout = 30
        self.num_ctx = 1024
        self.keep_alive = "10m"
        self._last_healthcheck_ts = 0.0
        self._last_healthcheck_ok = False
        self._healthcheck_ttl = 10.0
    
    def check_connection(self) -> bool:
        """Check if Ollama is running"""
        now = time.time()
        if (now - self._last_healthcheck_ts) < self._healthcheck_ttl:
            return self._last_healthcheck_ok

        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self._last_healthcheck_ok = (response.status_code == 200)
            self._last_healthcheck_ts = now
            return self._last_healthcheck_ok
        except:
            self._last_healthcheck_ok = False
            self._last_healthcheck_ts = now
            return False
    
    def generate_stream(self, messages: List[Dict], callback=None,
                       max_tokens: int = 256, temperature: float = 0.7,
                       num_ctx: Optional[int] = None):
        """Stream response with low memory footprint"""
        import requests
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
                "num_ctx": num_ctx or self.num_ctx,
                "num_batch": 16
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=(5, self.timeout)
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

    def warmup(self) -> bool:
        """Warm model in background to reduce first-token latency."""
        try:
            self.generate(
                [{"role": "user", "content": "ping"}],
                max_tokens=4,
                temperature=0.0
            )
            return True
        except Exception:
            return False
    
    def generate(self, messages: List[Dict], max_tokens: int = 256,
                temperature: float = 0.7, num_ctx: Optional[int] = None) -> str:
        """Non-streaming generation - FIXED to actually return response"""
        result = []
        self.generate_stream(messages, callback=lambda x: result.append(x),
                           max_tokens=max_tokens, temperature=temperature,
                           num_ctx=num_ctx)
        return "".join(result)


# ================================================================
# COM CORE
# ================================================================

class COMCore:
    """Main COM core integrating all components"""
    
    def __init__(self):
        self.memory = MemoryManager(max_messages=6)
        self.client = OllamaClient()
        self.cache = ResponseCache()
        
        # Initialize new modules
        self.router = IntentRouter(client=self.client)
        self.compressor = ContextCompressor(client=self.client)
        self.logger = SessionLogger()
        
        # Processing state with timeout safety
        self.is_processing = False
        self._processing_start = 0
        self._processing_timeout = 45  # seconds
        self._fast_replies = {
            "hello": "• Hi, I am COM.\n• Local mode is active.\n• Ask me a task to continue.",
            "hi": "• Hi, I am COM.\n• Local mode is active.\n• Ask me a task to continue.",
        }
    
    def check_status(self) -> Dict:
        """Check system status"""
        return {
            "ollama_running": self.client.check_connection(),
            "model": self.client.model,
            "memory_size": len(self.memory.history),
            "max_memory": self.memory.max_messages,
            "cache_size": len(self.cache._cache)
        }
    
    def process_query(self, query: str, callback=None) -> str:
        """Process user query with full pipeline"""
        start_time = time.time()
        cache_hit = False
        normalized_query = query.strip().lower()
        
        # Timeout safety: reset stuck processing flag
        if self.is_processing:
            if time.time() - self._processing_start > self._processing_timeout:
                self.is_processing = False  # force reset on timeout
            else:
                return "Already processing a request..."
        
        self.is_processing = True
        self._processing_start = time.time()
        
        try:
            # Ultra-fast fallback for greeting smoke tests
            if normalized_query in self._fast_replies:
                quick = self._fast_replies[normalized_query]
                if callback:
                    callback(quick)
                return quick

            # IMPROVED: Use IntentRouter instead of simple classify_mode
            mode = self.router.route(query)
            
            # PHASE 3: Check cache — zero LLM call on hit
            cached = self.cache.get(mode, query)
            if cached:
                cache_hit = True
                if callback:
                    callback(cached)
                elapsed_ms = int((time.time() - start_time) * 1000)
                self.logger.log(mode, query, cached, cache_hit, elapsed_ms)
                return cached
            
            # PHASE 2: Build SoT prompt
            system = SYSTEM_PROMPTS[mode]
            max_tok = TOKEN_LIMITS[mode]
            temp = TEMPERATURES[mode]
            num_ctx = NUM_CTX_BY_MODE[mode]
            
            context = self.memory.get_context()
            messages = [{"role": "system", "content": system}]
            messages += context
            messages.append({"role": "user", "content": query})
            
            # Check Ollama connection before calling
            if not self.client.check_connection():
                raise ConnectionError("Ollama is not running. Please start 'ollama serve' and ensure the model is installed.")
            
            # Call Ollama with tight token limit
            full_response = ""
            def stream_cb(chunk):
                nonlocal full_response
                full_response += chunk
                if callback:
                    callback(chunk)
            
            self.client.generate_stream(messages, callback=stream_cb,
                                       max_tokens=max_tok, temperature=temp,
                                       num_ctx=num_ctx)
            
            # PHASE 3: Cache result (OFFICE only, not GODOT scripts that go stale)
            if mode != "GODOT":
                self.cache.set(mode, query, full_response)
            
            # PHASE 2: Store in sliding window memory (GENERAL only)
            if mode == "GENERAL":
                self.memory.add_message("user", query)
                self.memory.add_message("assistant", full_response)
                
                # Check if we should compress old messages
                if len(self.memory.history) >= self.memory.max_messages:
                    compressed = self.compressor.compress(list(self.memory.history))
                    if compressed:
                        # Replace oldest 4 messages with compressed summary
                        for _ in range(4):
                            if len(self.memory.history) > 2:
                                self.memory.history.popleft()
                        self.memory.history.appendleft(compressed)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.logger.log(mode, query, full_response, cache_hit, elapsed_ms)
            
            return full_response
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if callback:
                callback(f"\n{error_msg}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.logger.log("ERROR", query, error_msg, cache_hit, elapsed_ms)
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
    print("Testing COM Core (SoT Version)...")
    com = COMCore()
    
    status = com.check_status()
    print(f"Status: {status}")
    
    # Test Phase 1: Mode Classification
    print("\n--- Testing Mode Classification ---")
    test_queries = [
        "buat excel laporan",
        "create godot player script",
        "what is the weather"
    ]
    for q in test_queries:
        mode = classify_mode(q)
        print(f"'{q}' → {mode}")
    
    # Test Phase 4: Signal Validation
    print("\n--- Testing Signal Validation ---")
    test_signals = [
        "@XLS:Laporan:No,Item,Harga",
        "@GDT:MOV:2D",
        "regular text"
    ]
    for s in test_signals:
        valid = is_signal(s)
        prefix, payload = parse_signal(s)
        print(f"'{s}' → Valid: {valid}, Prefix: {prefix}, Payload: {payload}")
    
    # Test Phase 3: Cache
    print("\n--- Testing Response Cache ---")
    test_query = "test cache query"
    com.cache.set("GENERAL", test_query, "cached response")
    cached = com.cache.get("GENERAL", test_query)
    print(f"Cached value: {cached}")
    
    if status["ollama_running"]:
        print("\n--- Live LLM Test ---")
        print("Query: 'siapa kamu?'")
        response = com.process_query("siapa kamu?", callback=print)
        print(f"\n\nFull response received: {len(response)} characters")
        print(f"Is signal: {is_signal(response)}")
        print(f"\nMemory summary:\n{com.get_memory_summary()}")
    else:
        print("\nOllama is not running. Please start Ollama first.")
