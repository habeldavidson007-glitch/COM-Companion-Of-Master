"""
COM Engine - The Core Brain of Companion of Master
Handles: Logic, Memory, Voice Queue, Command Routing, Ollama Interaction
Designed for Low RAM (2GB available) and High Responsiveness.
"""

import json
import os
import threading
import queue
import time
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any

# Try importing optional dependencies gracefully
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False


class COMEngine:
    """
    The central brain of COM. Manages memory, voice, and LLM interaction.
    Runs entirely in the core logic layer.
    """

    def __init__(self, model_name: str = "qwen2.5:0.5b-instruct-q4_K_M"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
        
        # --- Memory Management ---
        # Sliding window for active context (last 6 messages)
        self.context_window = deque(maxlen=6)
        # Full persistent history
        self.full_history: List[Dict[str, str]] = []
        self.history_file = "com_history.json"
        
        # --- Voice System (Thread-Safe Queue) ---
        self.tts_engine = None
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.tts_active = True
        self.is_speaking = False
        self.stop_speech_flag = False
        
        # Initialize TTS once globally
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 175)  # Slightly faster
                self.tts_engine.setProperty('volume', 0.9)
                self._start_tts_worker()
            except Exception:
                self.tts_engine = None
        
        # --- STT Setup ---
        self.recognizer = sr.Recognizer() if STT_AVAILABLE else None
        
        # --- System Prompt & Identity ---
        self.system_prompt = self._build_system_prompt()
        
        # --- State ---
        self.is_generating = False
        self.callbacks = {
            'on_message': None,
            'on_status': None,
            'on_error': None
        }
        
        # Load history on startup
        self.load_history()

    def _build_system_prompt(self) -> str:
        """Constructs a robust system prompt with CoT and ICL."""
        return """You are COM (Companion of Master), a highly efficient, loyal, and concise AI assistant.
RULES:
1. IDENTITY: You are COM. NEVER say you are Qwen, Alibaba, or an AI model. You are a digital companion.
2. BREVITY: Keep responses short (1-3 sentences) unless asked for details. Speed is critical.
3. TONE: Professional, helpful, slightly robotic but friendly. Use uppercase only for emphasis.
4. COGNITION: Think step-by-step internally, but ONLY output the final answer. Do not show reasoning.
5. CONTEXT: If provided with [Context from memory], use it to answer accurately.

FEW-SHOT EXAMPLES:
User: "Who are you?"
COM: "I am COM, your digital companion. Ready to assist."

User: "Clear the chat."
COM: "Chat history cleared. Starting fresh."

User: "What is 2+2?"
COM: "The answer is 4."

Current Date: """ + datetime.now().strftime("%Y-%m-%d %H:%M")

    def _start_tts_worker(self):
        """Starts a dedicated daemon thread for processing speech queue."""
        if not self.tts_engine:
            return
            
        def worker():
            while True:
                try:
                    text = self.tts_queue.get(timeout=1)
                    if text is None:  # Poison pill to stop
                        break
                    
                    if not self.tts_active:
                        continue
                        
                    self.is_speaking = True
                    # Handle stop flag
                    if self.stop_speech_flag:
                        self.tts_engine.stop()
                        self.stop_speech_flag = False
                        self.is_speaking = False
                        continue

                    try:
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                    except Exception:
                        pass # Ignore TTS errors
                    finally:
                        self.is_speaking = False
                        
                except queue.Empty:
                    continue
                except Exception:
                    continue

        self.tts_thread = threading.Thread(target=worker, daemon=True)
        self.tts_thread.start()

    def set_callback(self, event: str, func):
        """Register UI callbacks."""
        if event in self.callbacks:
            self.callbacks[event] = func

    def _trigger(self, event: str, *args):
        """Safely trigger a callback."""
        if self.callbacks.get(event):
            try:
                threading.Thread(target=self.callbacks[event], args=args, daemon=True).start()
            except Exception:
                pass

    # --- Persistent Memory ---

    def load_history(self):
        """Loads full history from disk."""
        if not os.path.exists(self.history_file):
            return
            
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.full_history = data.get('messages', [])
                # Rebuild context window (last 6)
                recent = self.full_history[-6:]
                self.context_window = deque(recent, maxlen=6)
                self._trigger('on_status', f"📁 Loaded {len(self.full_history)} messages from history.")
        except Exception as e:
            self._trigger('on_error', f"Failed to load history: {str(e)}")

    def save_history(self):
        """Saves full history to disk."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({'messages': list(self.full_history)}, f, indent=2)
        except Exception as e:
            self._trigger('on_error', f"Failed to save history: {str(e)}")

    def clear_history(self):
        """Clears all memory."""
        self.full_history = []
        self.context_window.clear()
        self.save_history()
        self._trigger('on_status', "🗑️ Memory wiped. Fresh start.")

    # --- RAG-Light (Keyword Search) ---

    def search_memory(self, query: str, limit: int = 2) -> str:
        """Simple keyword overlap search in history."""
        if not self.full_history:
            return ""
            
        query_words = set(query.lower().split())
        scored_entries = []
        
        for msg in self.full_history:
            content = msg.get('content', '').lower()
            common_words = query_words.intersection(set(content.split()))
            if len(common_words) > 0:
                scored_entries.append((len(common_words), msg))
        
        # Sort by relevance
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        
        if scored_entries:
            # Get top relevant snippets
            snippets = [entry['content'] for _, entry in scored_entries[:limit]]
            return "[Context from memory: " + " | ".join(snippets) + "]"
        
        return ""

    # --- Command Router (Instant Python Logic) ---

    def route_command(self, text: str) -> Optional[str]:
        """
        Intercepts commands before sending to LLM.
        Returns a response string if handled, None otherwise.
        """
        lower_text = text.strip().lower()
        
        if lower_text in ['/clear', '/reset', 'clear chat', 'wipe memory']:
            threading.Thread(target=self.clear_history, daemon=True).start()
            return "Memory cleared successfully."
        
        if lower_text in ['/stop', 'stop talking', 'shut up']:
            self.stop_speech_flag = True
            return "Voice stopped."
        
        if lower_text in ['/save', 'save chat']:
            self.save_history()
            return "Chat saved to disk."
            
        if lower_text in ['/voice on', 'enable voice']:
            self.tts_active = True
            return "Voice output enabled."
            
        if lower_text in ['/voice off', 'disable voice']:
            self.tts_active = False
            return "Voice output disabled."

        return None

    # --- Core Interaction ---

    def send_message(self, user_input: str):
        """Main entry point for user messages."""
        if self.is_generating:
            return

        # 1. Check for instant commands
        command_response = self.route_command(user_input)
        if command_response:
            self._add_to_history("user", user_input)
            self._add_to_history("assistant", command_response)
            self._trigger('on_message', "COM", command_response)
            self.speak(command_response)
            return

        # 2. Add user message to history
        self._add_to_history("user", user_input)
        self.save_history() # Save incrementally

        # 3. Search memory for context
        context_snippet = self.search_memory(user_input)
        
        # 4. Build prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add context if found
        if context_snippet:
            messages.append({"role": "system", "content": context_snippet})
            
        # Add sliding window
        messages.extend(list(self.context_window))

        # 5. Start Generation Thread
        self.is_generating = True
        self._trigger('on_status', "⡀⠄⠂⠁ Thinking...")
        
        thread = threading.Thread(target=self._call_ollama, args=(messages,), daemon=True)
        thread.start()

    def _add_to_history(self, role: str, content: str):
        """Adds message to both context window and full history."""
        msg = {"role": role, "content": content}
        self.context_window.append(msg)
        self.full_history.append(msg)

    def _call_ollama(self, messages: List[Dict]):
        """Calls Ollama Chat API (optimized for speed)."""
        if not REQUESTS_AVAILABLE:
            self._handle_error("Requests library missing.")
            return

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 150  # Limit length for speed
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            reply = data.get('message', {}).get('content', 'No response generated.')
            
            # Clean up response (remove potential CoT artifacts if any)
            reply = self._clean_response(reply)
            
            self._add_to_history("assistant", reply)
            self.save_history()
            
            self._trigger('on_message', "COM", reply)
            self.speak(reply)
            
        except requests.exceptions.ConnectionError:
            self._handle_error("Ollama not running. Is 'ollama serve' active?")
        except Exception as e:
            self._handle_error(f"Generation error: {str(e)}")
        finally:
            self.is_generating = False
            self._trigger('on_status', "Ready.")

    def _clean_response(self, text: str) -> str:
        """Removes internal reasoning markers if present."""
        # Simple cleanup for small models that might leak thoughts
        if "<think>" in text:
            text = text.split("</think>")[-1]
        return text.strip()

    def _handle_error(self, msg: str):
        self._trigger('on_error', msg)
        self._trigger('on_status', "Error occurred.")
        self.is_generating = False

    # --- Voice Interface ---

    def speak(self, text: str):
        """Queues text for speech synthesis."""
        if not self.tts_engine or not self.tts_active:
            return
        
        # Sanitize text for TTS
        clean_text = text.replace("*", "").replace("#", "")
        self.tts_queue.put(clean_text)

    def stop_speaking(self):
        """Flags the TTS thread to stop current speech."""
        self.stop_speech_flag = True

    def listen(self) -> Optional[str]:
        """Captures audio from microphone and returns text."""
        if not self.recognizer or not STT_AVAILABLE:
            self._trigger('on_error', "SpeechRecognition library missing.")
            return None
            
        try:
            with sr.Microphone() as source:
                self._trigger('on_status', "🎤 Listening...")
                # Adjust for ambient noise quickly
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            self._trigger('on_status', "🔄 Processing audio...")
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            self._trigger('on_status', "No speech detected.")
        except sr.UnknownValueError:
            self._trigger('on_status', "Could not understand audio.")
        except sr.RequestError:
            self._trigger('on_error', "STT Service unavailable (offline?).")
        except Exception as e:
            self._trigger('on_error', f"Mic error: {str(e)}")
        finally:
            self._trigger('on_status', "Ready.")
            
        return None
