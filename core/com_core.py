"""
COM (Companion Of Master) - Signal-of-Thought (SoT) Core
Features: Mode Detection, Signal Byte Output, Response Cache
Model: qwen2.5:0.5b-instruct-q4_K_M (~500MB RAM)
"""

import json
import hashlib
import time
import re
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict, Tuple

from .intent_router import IntentRouter
from .context_compressor import ContextCompressor
from .session_logger import SessionLogger

# Import wiki components for knowledge integration
try:
    from tools.data_ops.wiki_compiler import WikiRetriever
    WIKI_AVAILABLE = True
except ImportError:
    WIKI_AVAILABLE = False
    WikiRetriever = None

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
# PHASE 2 — SoT PROMPT ENGINE (v4: Pure Intent Router)
# ================================================================

SYSTEM_PROMPTS = {
    "GODOT": """You are COM v4 - a pure INTENT ROUTER.
Output ONLY a @GDT signal byte. NEVER write code or explanations.
Signal format: @GDT:CATEGORY:DETAIL
Examples: @GDT:MOV:2D  |  @GDT:ANIM:IDLE  |  @GDT:SCENE:PLAYER
One line. Signal only.""",

    "OFFICE": """You are COM v4 - a pure INTENT ROUTER.
Output ONLY a signal byte. Nothing else.
Signals:
  @XLS:filename:col1,col2,col3
  @PDF:filename:content text
  @PPT:filename:slide1|slide2|slide3
Example: @XLS:Inventory:Item,Qty,Price
One line. No explanation. Signal only.""",

    "GENERAL": """You are COM v4 - a pure INTENT ROUTER.
You NEVER generate answers, explanations, or content.
You ONLY output ONE signal byte in format: @TYPE:payload

STEP 1: Analyze the query intent
STEP 2: Choose EXACTLY ONE type:
  @WIKI:topic - For knowledge/research questions (what is, explain, define, describe)
  @WEB:topic - For current events/live data (news, today, latest, current)
  @CHAT:greeting - For greetings ONLY (hello, hi, hey, good morning)
  @CHAT:thanks - For thanks ONLY (thank you, thanks, appreciate)
  @CODE:language:description - For code generation requests (write code, create script)
  @ERR:clarification - If query is ambiguous or unclear

CRITICAL RULES:
- Output EXACTLY ONE line starting with @TYPE:
- NEVER output multiple @ symbols
- NEVER list all types like @WIKI:@WEB:@CHAT
- Pick the SINGLE best match

Examples:
User: 'Hello' → @CHAT:greeting
User: 'What is AI?' → @WIKI:artificial intelligence definition
User: 'Write python script' → @CODE:python:script description
User: 'Current AI news' → @WEB:AI news latest

Your response must be exactly one line like: @TYPE:payload"""
}

MODE_OUTPUT_CONTRACTS = {
    "GODOT": "Contract: output only @GDT signal byte. No prose, no code.",
    "OFFICE": "Contract: output exactly one signal line: @XLS/@PDF/@PPT with payload.",
    "GENERAL": "Contract: output exactly one signal byte: @WIKI/@WEB/@CHAT/@CODE/@ERR with payload.",
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

VALID_PREFIXES = {"@GDT", "@XLS", "@PDF", "@PPT", "@ERR", "@WIKI", "@WEB", "@CHAT", "@CODE"}

def is_signal(text: str) -> bool:
    """Validate LLM output before passing to harness"""
    stripped = text.strip()
    # Check if it starts with a valid prefix (need at least 5 chars: @TYPE:)
    if len(stripped) < 6:
        return False
    # Reject malformed signals with multiple @ symbols
    if stripped.count('@') > 1:
        return False
    # Extract prefix up to first colon
    if ':' not in stripped:
        return False
    prefix = stripped.split(':')[0]
    return prefix in VALID_PREFIXES

def parse_signal(text: str) -> Tuple[str, str]:
    """Parse signal into prefix and payload
    "@XLS:Inventory:Item,Qty" → ("@XLS", "Inventory:Item,Qty")
    Handles malformed outputs by extracting first valid signal
    """
    stripped = text.strip()
    
    # If the response contains multiple @ symbols (malformed), extract the first valid one
    if stripped.count('@') > 1:
        # Try to find first valid signal pattern
        match = re.search(r'@(WIKI|WEB|CHAT|CODE|ERR|GDT|XLS|PDF|PPT):([^@\n]+)', stripped)
        if match:
            return f"@{match.group(1)}", match.group(2).strip()
        # Fallback: just take everything after first @
        first_at = stripped.find('@')
        rest = stripped[first_at+1:]
        parts = rest.split(":", 1)
        if len(parts) == 2:
            return f"@{parts[0]}", parts[1]
    
    # Normal parsing
    parts = stripped.split(":", 1)
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
        self._consecutive_failures = 0
        self._cooldown_until_ts = 0.0
        self._cooldown_seconds = 12.0

    def _mark_success(self):
        self._consecutive_failures = 0
        self._cooldown_until_ts = 0.0

    def _mark_failure(self):
        self._consecutive_failures += 1
        if self._consecutive_failures >= 2:
            self._cooldown_until_ts = time.time() + self._cooldown_seconds
    
    def check_connection(self) -> bool:
        """Check if Ollama is running"""
        now = time.time()
        if now < self._cooldown_until_ts:
            return False

        if (now - self._last_healthcheck_ts) < self._healthcheck_ttl:
            return self._last_healthcheck_ok

        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self._last_healthcheck_ok = (response.status_code == 200)
            self._last_healthcheck_ts = now
            if self._last_healthcheck_ok:
                self._mark_success()
            else:
                self._mark_failure()
            return self._last_healthcheck_ok
        except:
            self._last_healthcheck_ok = False
            self._last_healthcheck_ts = now
            self._mark_failure()
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
        
        effective_num_ctx = num_ctx or self.num_ctx
        for attempt in range(2):
            payload["options"]["num_ctx"] = effective_num_ctx
            request_timeout = self.timeout if attempt == 0 else min(15, self.timeout)
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    stream=True,
                    timeout=(5, request_timeout)
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
                self._mark_success()
                return full_response
            except requests.exceptions.RequestException as e:
                is_timeout = "timed out" in str(e).lower()
                if attempt == 0 and is_timeout:
                    effective_num_ctx = max(256, effective_num_ctx // 2)
                    continue
                self._mark_failure()
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
        
        # Initialize wiki retriever for knowledge integration (FIX: Integration Gap)
        if WIKI_AVAILABLE:
            try:
                self.wiki_retriever = WikiRetriever(data_dir="data")
            except Exception as e:
                self.wiki_retriever = None
        else:
            self.wiki_retriever = None
        
        # Processing state with timeout safety
        self.is_processing = False
        self._processing_start = 0
        self._processing_timeout = 45  # seconds
        self._fast_reply_text = "• Hi, I am COM.\n• Local mode is active.\n• Ask me a task to continue."
        self._thanks_reply_text = "• You're welcome.\n• Ready for the next task.\n• Tell me what to do."
        self._greeting_tokens = {"hello", "hi", "hey", "yo", "hola"}
        self._thanks_tokens = {"thanks", "thank", "thx", "makasih", "terima"}
        self._offline_reply_text = (
            "• Ollama is temporarily unavailable on this device.\n"
            "• I can still help with short guidance based on your message.\n"
            "• Retry in ~10–15 seconds, or restart `ollama serve`."
        )
        self._office_route_patterns = [
            r"\b(create|buat|make)\s+(an?\s+)?(excel|xlsx|spreadsheet|pdf|ppt)\b",
            r"\b(export|save)\s+.*\b(pdf|excel|ppt)\b",
        ]
        self._godot_route_patterns = [
            r"\b(godot|gdscript)\b",
            r"\bcreate\s+.*\.(gd|tscn)\b",
            r"\b(player|scene|node|physics)\b.*\b(script|godot)\b",
        ]
        self._salience_patterns = [
            # user preference/constraints
            r"\b(i prefer|i like|i don't like|my preference|must|should|avoid|always)\b",
            # explicit task/decision markers
            r"\b(todo|task|plan|decide|decision|final|use this|do this|next step)\b",
            # factual anchors
            r"\b\d{4}\b",                   # year
            r"\b\d+(?:\.\d+)?\s?(gb|mb|ms|s|sec|seconds|minutes|hours|%)\b",
        ]
        self._fact_snippets = deque(maxlen=12)
        # Knowledge query indicators for wiki retrieval
        self._knowledge_indicators = [
            'what is', 'who is', 'explain', 'define', 'describe', 
            'tell me about', 'how does', 'why is', 'when did',
            'what are', 'give me information', 'summarize',
            'ai evolution', 'ai trends', 'current ai', 'project recommendation'
        ]

    def _normalize_query(self, query: str) -> str:
        """Lowercase + strip punctuation for deterministic fast-path checks."""
        cleaned = re.sub(r"[^a-zA-Z0-9\\s]", " ", query.lower())
        return " ".join(cleaned.split())

    def _fast_reply_for(self, normalized_query: str) -> Optional[str]:
        """Return local fast reply for greeting/thanks without LLM call."""
        if not normalized_query:
            return None

        tokens = set(normalized_query.split())
        if tokens.intersection(self._greeting_tokens):
            return self._fast_reply_text
        if tokens.intersection(self._thanks_tokens):
            return self._thanks_reply_text
        return None

    def _offline_general_reply(self, normalized_query: str) -> str:
        """Best-effort local fallback when Ollama is temporarily unavailable."""
        if "ai" in normalized_query or "technology" in normalized_query:
            return (
                "• AI changes fast; focus on weekly learning goals, not hourly noise.\n"
                "• Keep a small stack: one model, one workflow, one measurable project.\n"
                "• When Ollama recovers, ask me to turn this into an action plan."
            )
        return self._offline_reply_text

    def _enforce_general_format(self, text: str) -> str:
        """Normalize GENERAL replies into max 3 concise bullets."""
        if not text:
            return text

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        bullets = []
        for line in lines:
            if line.startswith("•"):
                bullets.append(line)
            elif line[:2] in {"1.", "2.", "3."}:
                bullets.append(f"• {line[2:].strip()}")
            else:
                bullets.append(f"• {line}")

        if not bullets:
            chunks = [c.strip() for c in text.split(".") if c.strip()]
            bullets = [f"• {c}." for c in chunks]

        return "\n".join(bullets[:3])

    def _regex_route(self, normalized_query: str) -> Optional[str]:
        """High-confidence regex route before LLM/router fallback."""
        for pattern in self._office_route_patterns:
            if re.search(pattern, normalized_query):
                return "OFFICE"
        for pattern in self._godot_route_patterns:
            if re.search(pattern, normalized_query):
                return "GODOT"
        return None

    def _route_with_confidence(self, normalized_query: str, raw_query: str) -> Tuple[str, float]:
        """Route query and estimate confidence using cheap lexical signals."""
        office_hits = sum(1 for p in self._office_route_patterns if re.search(p, normalized_query))
        godot_hits = sum(1 for p in self._godot_route_patterns if re.search(p, normalized_query))

        if office_hits > 0 and godot_hits == 0:
            return "OFFICE", min(1.0, 0.7 + 0.15 * office_hits)
        if godot_hits > 0 and office_hits == 0:
            return "GODOT", min(1.0, 0.7 + 0.15 * godot_hits)
        if office_hits > 0 and godot_hits > 0:
            route_result = self.router.route(raw_query)
            return route_result["mode"], 0.4

        # Fallback to router when no regex signal.
        route_result = self.router.route(raw_query)
        mode = route_result["mode"]
        # Short/vague queries are lower confidence for small models.
        confidence = 0.45 if len(normalized_query.split()) >= 5 else 0.3
        return mode, confidence

    def _clarification_question(self, mode: str) -> str:
        """One short clarification when route confidence is low."""
        if mode == "OFFICE":
            return "• Quick check: do you want a file action (Excel/PDF/PPT) or a normal explanation?"
        if mode == "GODOT":
            return "• Quick check: do you want Godot code output or a general explanation?"
        return "• Quick check: should I answer generally, or create a file/code output?"

    def _repair_output(self, mode: str, text: str) -> str:
        """Repair common output format drift for OFFICE/GODOT responses."""
        cleaned = text.strip()

        # Remove markdown fences that tool-execution paths don't need.
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()

        if mode == "OFFICE":
            # Extract first explicit signal in text when model adds explanation.
            signal_match = re.search(r"@(?:XLS|PDF|PPT):[^\n]+", cleaned)
            if signal_match:
                return signal_match.group(0).strip()

            # Auto-fix missing @ prefix variants: XLS:..., PDF:..., PPT:...
            no_at = re.search(r"\b(XLS|PDF|PPT):[^\n]+", cleaned)
            if no_at:
                return f"@{no_at.group(0).strip()}"

        if mode == "GODOT":
            # Keep signal if present; otherwise return cleaned GDScript block.
            signal_match = re.search(r"@GDT:[^\n]+", cleaned)
            if signal_match:
                return signal_match.group(0).strip()
            return cleaned

        return cleaned

    def _is_valid_mode_output(self, mode: str, text: str) -> bool:
        """Schema validation for confidence-based fallback policy."""
        cleaned = text.strip()
        if mode == "OFFICE":
            return bool(re.match(r"^@(XLS|PDF|PPT):.+", cleaned))
        if mode == "GODOT":
            return bool(cleaned.startswith("@GDT:") or "func " in cleaned or "extends " in cleaned)
        return True

    def _is_salient_text(self, text: str) -> bool:
        """Heuristic salience check for low-RAM memory retention."""
        normalized = self._normalize_query(text)
        if len(normalized.split()) >= 28:
            return True
        return any(re.search(pattern, normalized) for pattern in self._salience_patterns)

    def _should_store_general_turn(self, user_text: str, assistant_text: str) -> bool:
        """
        Keep only salient GENERAL turns to improve memory quality on small context.
        Store if either side contains preference/fact/decision-like signals.
        """
        return self._is_salient_text(user_text) or self._is_salient_text(assistant_text)

    def _extract_snippets(self, text: str) -> List[str]:
        """Extract compact memory snippets from salient text."""
        candidates = [seg.strip() for seg in re.split(r"[.!?\n]", text) if seg.strip()]
        snippets = []
        for seg in candidates:
            norm = self._normalize_query(seg)
            if self._is_salient_text(norm):
                snippets.append(seg[:140])
        return snippets[:2]

    def _retrieve_snippets(self, query: str, top_k: int = 2) -> List[str]:
        """Retrieve top-k snippets with simple token-overlap scoring."""
        q_tokens = set(self._normalize_query(query).split())
        if not q_tokens:
            return []

        scored = []
        for snippet in self._fact_snippets:
            s_tokens = set(self._normalize_query(snippet).split())
            overlap = len(q_tokens.intersection(s_tokens))
            if overlap > 0:
                scored.append((overlap, snippet))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [s for _, s in scored[:top_k]]
    
    def _is_knowledge_query(self, normalized_query: str) -> bool:
        """Check if query appears to be a knowledge/research question."""
        return any(indicator in normalized_query for indicator in self._knowledge_indicators)
    
    def _try_wiki_retrieval(self, query: str) -> Optional[str]:
        """
        Try to retrieve relevant wiki content for knowledge queries.
        FIX: Integration Gap - This method wires up WikiRetriever to the core.
        Returns wiki context string or None.
        """
        if not self.wiki_retriever:
            return None
        
        normalized = self._normalize_query(query)
        
        # Only use wiki for knowledge-type queries
        if not self._is_knowledge_query(normalized):
            return None
        
        try:
            results = self.wiki_retriever.search(query, top_k=3)
            
            if not results:
                return None
            
            # Format results as context
            context_parts = []
            for path, snippet, score in results:
                if score > 0.1:  # Minimum relevance threshold
                    context_parts.append(f"From {path}:\n{snippet}")
            
            if context_parts:
                return "\n\n".join(context_parts)
        except Exception as e:
            # Silently fail - wiki is optional enhancement
            pass
        
        return None
    
    def check_status(self) -> Dict:
        """Check system status"""
        base_status = {
            "ollama_running": self.client.check_connection(),
            "model": self.client.model,
            "memory_size": len(self.memory.history),
            "max_memory": self.memory.max_messages,
            "cache_size": len(self.cache._cache)
        }
        
        # Add wiki status if available
        if self.wiki_retriever:
            base_status["wiki_available"] = True
            try:
                base_status["wiki_loaded"] = self.wiki_retriever._loaded
            except:
                base_status["wiki_loaded"] = False
        else:
            base_status["wiki_available"] = False
        
        return base_status
    
    def process_query(self, query: str, callback=None) -> str:
        """Process user query with full pipeline including wiki integration"""
        start_time = time.time()
        cache_hit = False
        normalized_query = self._normalize_query(query)
        
        # Timeout safety: reset stuck processing flag
        if self.is_processing:
            if time.time() - self._processing_start > self._processing_timeout:
                self.is_processing = False  # force reset on timeout
            else:
                return "Already processing a request..."
        
        self.is_processing = True
        self._processing_start = time.time()
        
        try:
            # Ultra-fast fallback for greeting/thanks smoke tests
            quick = self._fast_reply_for(normalized_query)
            if quick:
                if callback:
                    callback(quick)
                return quick

            # FIX: Integration Gap - Check wiki for knowledge queries BEFORE routing
            wiki_context = self._try_wiki_retrieval(query)
            
            mode, route_conf = self._route_with_confidence(normalized_query, query)
            if route_conf < 0.35:
                clarification = self._clarification_question(mode)
                if callback:
                    callback(clarification)
                elapsed_ms = int((time.time() - start_time) * 1000)
                self.logger.log("CLARIFY", query, clarification, cache_hit, elapsed_ms)
                return clarification
            
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
            messages.append({"role": "system", "content": MODE_OUTPUT_CONTRACTS[mode]})
            
            # Add wiki context if available (FIX: Integration Gap)
            if wiki_context and mode == "GENERAL":
                messages.append({
                    "role": "system",
                    "content": f"[Wiki Knowledge Base]:\n{wiki_context}\n\nUse this information when answering."
                })
            elif mode == "GENERAL":
                snippets = self._retrieve_snippets(query, top_k=2)
                if snippets:
                    memory_hint = " | ".join(snippets)
                    messages.append({
                        "role": "system",
                        "content": f"[Relevant memory snippets] {memory_hint}"
                    })
            messages += context
            messages.append({"role": "user", "content": query})
            
            # Check Ollama connection before calling
            if not self.client.check_connection():
                if mode == "GENERAL":
                    offline = self._offline_general_reply(normalized_query)
                    if callback:
                        callback(offline)
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    self.logger.log("OFFLINE", query, offline, cache_hit, elapsed_ms)
                    return offline
                # For non-GENERAL modes without Ollama, provide helpful offline guidance
                if mode == "OFFICE":
                    offline_msg = "@ERR:OFFLINE:Ollama unavailable. Please start 'ollama serve' for file operations."
                elif mode == "GODOT":
                    offline_msg = "@ERR:OFFLINE:Ollama unavailable. Please start 'ollama serve' for code generation."
                else:
                    offline_msg = f"@ERR:OFFLINE:Ollama unavailable for {mode} mode. Please start 'ollama serve'."
                if callback:
                    callback(offline_msg)
                elapsed_ms = int((time.time() - start_time) * 1000)
                self.logger.log("OFFLINE", query, offline_msg, cache_hit, elapsed_ms)
                return offline_msg
            raise ConnectionError("Ollama is not running. Please start 'ollama serve' and ensure the model is installed.")
            
            # Core policy: OFFICE only needs final signal, so avoid stream callbacks.
            # GODOT/GENERAL keep token streaming for real-time UX.
            if mode == "OFFICE":
                full_response = self.client.generate(
                    messages,
                    max_tokens=max_tok,
                    temperature=temp,
                    num_ctx=num_ctx
                )
            else:
                full_response = ""

                def stream_cb(chunk):
                    nonlocal full_response
                    full_response += chunk
                    if callback:
                        callback(chunk)

                self.client.generate_stream(
                    messages,
                    callback=stream_cb,
                    max_tokens=max_tok,
                    temperature=temp,
                    num_ctx=num_ctx
                )
            
            if mode == "GENERAL":
                full_response = self._enforce_general_format(full_response)
            else:
                full_response = self._repair_output(mode, full_response)
                if not self._is_valid_mode_output(mode, full_response):
                    full_response = "@ERR:FORMAT:Please clarify output target (OFFICE signal or GODOT code)."

            # PHASE 3: Cache result (OFFICE/GENERAL only, not GODOT scripts that go stale)
            if mode != "GODOT":
                self.cache.set(mode, query, full_response)
            
            # PHASE 2: Store in sliding window memory (GENERAL only)
            if mode == "GENERAL":
                if self._should_store_general_turn(query, full_response):
                    self.memory.add_message("user", query)
                    self.memory.add_message("assistant", full_response)
                    for snippet in self._extract_snippets(query):
                        self._fact_snippets.append(snippet)
                    for snippet in self._extract_snippets(full_response):
                        self._fact_snippets.append(snippet)
                
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
