"""
COM (Companion Of Master) - Signal-of-Thought (SoT) Core + Background Server
Features: Mode Detection, Signal Byte Output, Response Cache, TCP Server
Model: qwen2.5:0.5b-instruct-q4_K_M (~500MB RAM)
Runs as invisible background server for GUI client
"""

import json
import hashlib
import time
import socket
import threading
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
        """Get current context"""
        return list(self.history)
    
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
    
    def check_connection(self) -> bool:
        """Check if Ollama is running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_stream(self, messages: List[Dict], callback=None, 
                       max_tokens: int = 256, temperature: float = 0.7):
        """Stream response with low memory footprint"""
        import requests
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
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
    
    def generate(self, messages: List[Dict], max_tokens: int = 256, 
                temperature: float = 0.7) -> str:
        """Non-streaming generation"""
        result = []
        self.generate_stream(messages, callback=lambda x: result.append(x),
                           max_tokens=max_tokens, temperature=temperature)
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
        
        # Timeout safety: reset stuck processing flag
        if self.is_processing:
            if time.time() - self._processing_start > self._processing_timeout:
                self.is_processing = False  # force reset on timeout
            else:
                return "Already processing a request..."
        
        self.is_processing = True
        self._processing_start = time.time()
        
        try:
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
                                       max_tokens=max_tok, temperature=temp)
            
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


# ================================================================
# TCP SERVER FOR GUI CLIENT
# ================================================================

class COMServer:
    """Background TCP server for GUI client communication"""
    
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.core = COMCore()
        self.server_socket = None
        self.running = False
        self.clients = []
        
    def start(self):
        """Start the background server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)  # Allow checking running flag
        self.running = True
        
        print(f"🧠 COM Brain server started on {self.host}:{self.port}")
        print(f"   Model: {self.core.client.model}")
        print(f"   Status: {'Online' if self.core.client.check_connection() else 'Offline'}")
        
        # Accept clients in main thread
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"🔌 Client connected: {addr}")
                client_thread = threading.Thread(target=self.handle_client, 
                                                args=(client_socket, addr),
                                                daemon=True)
                client_thread.start()
                self.clients.append(client_socket)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
                    
    def handle_client(self, client_socket, addr):
        """Handle individual client connection"""
        buffer = ""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                buffer += data.decode('utf-8')
                
                # Process complete messages (newline-terminated)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.process_request(client_socket, line)
                    
        except Exception as e:
            print(f"Client {addr} error: {e}")
        finally:
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            print(f"🔌 Client disconnected: {addr}")
    
    def process_request(self, client_socket, request_line):
        """Process client request"""
        try:
            request = json.loads(request_line)
            cmd = request.get('cmd')
            
            if cmd == 'query':
                query = request.get('text', '')
                session_id = request.get('session', 'default')
                
                # Stream response back
                chunks = []
                def send_chunk(chunk):
                    response = json.dumps({'type': 'chunk', 'data': chunk}) + '\n'
                    client_socket.sendall(response.encode('utf-8'))
                    chunks.append(chunk)
                
                response = self.core.process_query(query, callback=send_chunk)
                
                # Send completion signal
                complete = json.dumps({
                    'type': 'complete',
                    'response': response,
                    'is_signal': is_signal(response)
                }) + '\n'
                client_socket.sendall(complete.encode('utf-8'))
                
            elif cmd == 'status':
                status = self.core.check_status()
                response = json.dumps({'type': 'status', 'data': status}) + '\n'
                client_socket.sendall(response.encode('utf-8'))
                
            elif cmd == 'clear':
                self.core.clear_memory()
                response = json.dumps({'type': 'cleared'}) + '\n'
                client_socket.sendall(response.encode('utf-8'))
                
            else:
                error = json.dumps({'type': 'error', 'message': f'Unknown cmd: {cmd}'}) + '\n'
                client_socket.sendall(error.encode('utf-8'))
                
        except json.JSONDecodeError as e:
            error = json.dumps({'type': 'error', 'message': f'Invalid JSON: {str(e)}'}) + '\n'
            client_socket.sendall(error.encode('utf-8'))
        except Exception as e:
            error = json.dumps({'type': 'error', 'message': str(e)}) + '\n'
            client_socket.sendall(error.encode('utf-8'))
    
    def stop(self):
        """Stop the server"""
        self.running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        print("🛑 COM Brain server stopped")


# Convenience function for UI integration
def create_com_core():
    """Factory function to create COM core instance"""
    return COMCore()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        # Run as background server
        server = COMServer()
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
    else:
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
            print("Query: 'siapa kamu?'\")
            response = com.process_query("siapa kamu?", callback=print)
            print(f"\n\nFull response received: {len(response)} characters")
            print(f"Is signal: {is_signal(response)}")
            print(f"\nMemory summary:\n{com.get_memory_summary()}")
        else:
            print("\nOllama is not running. Please start Ollama first.")
