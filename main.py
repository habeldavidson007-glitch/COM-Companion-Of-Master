"""
COM (Companion of Master) - Local LLM Assistant
Optimized for low-RAM systems (2GB available)
Uses Ollama with qwen2.5:0.5b-instruct-q4_K_M model
"""

import tkinter as tk
from tkinter import ttk, font, messagebox
import requests
import json
import threading
import os
import re
from datetime import datetime
from collections import deque

# Voice libraries (optional, graceful fallback if not installed)
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class COMAssistant:
    """COM - Companion of Master: A lightweight local LLM assistant"""
    
    # Configuration
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL_NAME = "qwen2.5:0.5b-instruct-q4_K_M"
    HISTORY_FILE = "com_history.json"
    MAX_CONTEXT_MESSAGES = 6  # Sliding window size
    
    # Colors (Dark theme with Lime/Green text)
    COLORS = {
        'bg_primary': '#0a0a0a',      # Near black
        'bg_secondary': '#1a1a1a',    # Dark gray
        'bg_tertiary': '#2a2a2a',     # Lighter dark gray
        'text_primary': '#00ff00',    # Lime green
        'text_secondary': '#00cc00',  # Darker green
        'text_dim': '#008800',        # Dim green
        'accent': '#00ff88',          # Bright accent
        'error': '#ff4444',           # Red for errors
        'warning': '#ffaa00',         # Orange for warnings
        'user_msg_bg': '#1a2a1a',     # Dark green tint
        'ai_msg_bg': '#0a1a0a',       # Darker green tint
    }
    
    # System prompt with identity enforcement, CoT instruction, and few-shot examples
    SYSTEM_PROMPT = """You are COM (Companion of Master), a helpful AI assistant. 
IMPORTANT: You must ALWAYS identify yourself as "COM" or "Companion of Master". 
NEVER say you are "Qwen", "AI Assistant", or any other name. You are COM.

Think step-by-step internally to solve problems, but only output your final answer.
Do not show your reasoning process - only provide the clean final response.

Here are some examples of how to respond:

Example 1:
User: What is 2 + 2?
COM: 2 + 2 equals 4.

Example 2:
User: Tell me a short joke.
COM: Why don't scientists trust atoms? Because they make up everything!

Remember: Be concise, helpful, and always identify as COM."""

    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_styles()
        self.setup_variables()
        self.create_ui()
        self.bind_events()
        self.load_history()
        self.check_ollama_status()
        
        # Welcome message
        self.add_system_message("🖥 COM (Companion of Master) initialized. Ready to assist.")
        
    def setup_window(self):
        """Configure the main window"""
        self.root.title("✨ COM - Companion of Master")
        self.root.geometry("500x650")
        self.root.minsize(400, 500)  # Minimum size enforcement
        
        # Floating window settings
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        
        # Dark background
        self.root.configure(bg=self.COLORS['bg_primary'])
        
    def setup_styles(self):
        """Configure custom fonts and styles"""
        # Custom fonts
        self.font_header = font.Font(family="Consolas", size=12, weight="bold")
        self.font_chat = font.Font(family="Consolas", size=10)
        self.font_input = font.Font(family="Consolas", size=11)
        self.font_status = font.Font(family="Consolas", size=8)
        self.font_small = font.Font(family="Consolas", size=9)
        
        # Configure ttk style
        style = ttk.Style()
        style.theme_use('clam')
        
    def setup_variables(self):
        """Initialize application variables"""
        self.is_generating = False
        self.tts_enabled = True
        self.message_history = deque(maxlen=self.MAX_CONTEXT_MESSAGES)
        self.full_history = []  # For persistent storage
        self.typing_animation_id = None
        self.tts_engine = None
        
        # Initialize TTS engine if available
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 175)
                self.tts_engine.setProperty('volume', 0.9)
            except Exception:
                self.tts_engine = None
                
        # Initialize speech recognizer if available
        if SPEECH_RECOGNITION_AVAILABLE:
            self.speech_recognizer = sr.Recognizer()
        else:
            self.speech_recognizer = None
            
    def create_ui(self):
        """Create all UI components"""
        self.create_header()
        self.create_chat_area()
        self.create_input_area()
        self.create_status_bar()
        
    def create_header(self):
        """Create the header section"""
        header_frame = tk.Frame(self.root, bg=self.COLORS['bg_secondary'], height=55)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title with identity
        title_label = tk.Label(
            header_frame,
            text="🤖 COM - Companion of Master",
            font=self.font_header,
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_primary']
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=12)
        
        # Control buttons frame
        btn_frame = tk.Frame(header_frame, bg=self.COLORS['bg_secondary'])
        btn_frame.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # Clear button
        clear_btn = tk.Button(
            btn_frame, text="🗑 Clear", command=self.clear_chat,
            bg=self.COLORS['bg_tertiary'], fg=self.COLORS['text_primary'],
            font=self.font_small, border=1, cursor="hand2",
            activebackground=self.COLORS['accent'], activeforeground='#000000'
        )
        clear_btn.pack(side=tk.LEFT, padx=3)
        
        # Mic button (Speech-to-Text)
        self.mic_btn = tk.Button(
            btn_frame, text="🎤 Mic", command=self.toggle_voice_input,
            bg=self.COLORS['bg_tertiary'], fg=self.COLORS['text_primary'],
            font=self.font_small, border=1, cursor="hand2",
            activebackground=self.COLORS['accent'], activeforeground='#000000'
        )
        self.mic_btn.pack(side=tk.LEFT, padx=3)
        
        # TTS button (Text-to-Speech toggle)
        self.tts_btn = tk.Button(
            btn_frame, text="🔊 TTS", command=self.toggle_tts,
            bg=self.COLORS['bg_tertiary'], fg=self.COLORS['text_primary'],
            font=self.font_small, border=1, cursor="hand2",
            activebackground=self.COLORS['accent'], activeforeground='#000000'
        )
        self.tts_btn.pack(side=tk.LEFT, padx=3)
        
        self.update_tts_button_state()
        
    def create_chat_area(self):
        """Create the chat display area"""
        chat_frame = tk.Frame(self.root, bg=self.COLORS['bg_primary'])
        chat_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Chat history text widget
        self.chat_display = tk.Text(
            chat_frame,
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['text_primary'],
            font=self.font_chat,
            wrap=tk.WORD,
            border=0,
            highlightthickness=0,
            selectbackground=self.COLORS['text_dim'],
            selectforeground=self.COLORS['bg_primary'],
            cursor="arrow",
            state='normal'
        )
        self.chat_display.pack(side=tk.LEFT, expand=True, fill="both")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        # Message tags
        self.chat_display.tag_configure("user",
            background=self.COLORS['user_msg_bg'],
            foreground=self.COLORS['text_primary'],
            lmargin1=8, lmargin2=8, rmargin=8,
            spacing1=4, spacing2=2, spacing3=2)
            
        self.chat_display.tag_configure("assistant",
            background=self.COLORS['ai_msg_bg'],
            foreground=self.COLORS['text_primary'],
            lmargin1=8, lmargin2=8, rmargin=8,
            spacing1=4, spacing2=2, spacing3=2)
            
        self.chat_display.tag_configure("system",
            foreground=self.COLORS['text_dim'],
            lmargin1=8, lmargin2=8, rmargin=8,
            spacing1=3, spacing2=1, spacing3=1,
            font=self.font_small)
            
        self.chat_display.tag_configure("error",
            foreground=self.COLORS['error'],
            lmargin1=8, lmargin2=8, rmargin=8,
            spacing1=3, spacing2=1, spacing3=1)
            
        self.chat_display.tag_configure("context",
            foreground=self.COLORS['text_secondary'],
            lmargin1=8, lmargin2=8, rmargin=8,
            spacing1=2, spacing2=1, spacing3=1,
            font=self.font_small)
            
    def create_input_area(self):
        """Create the message input area"""
        input_frame = tk.Frame(self.root, bg=self.COLORS['bg_secondary'])
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Text input field
        self.input_field = tk.Entry(
            input_frame,
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['text_primary'],
            font=self.font_input,
            border=1,
            highlightthickness=1,
            highlightbackground=self.COLORS['text_dim'],
            highlightcolor=self.COLORS['accent'],
            insertbackground=self.COLORS['text_primary']
        )
        self.input_field.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.input_field.bind("<Return>", self.on_enter_pressed)
        
        # Placeholder text
        self.placeholder_text = "Type your message... (Enter to send)"
        self.input_field.insert(0, self.placeholder_text)
        self.input_field.bind("<FocusIn>", self.on_focus_in)
        self.input_field.bind("<FocusOut>", self.on_focus_out)
        self.showing_placeholder = True
        
        # Send button
        send_btn = tk.Button(
            input_frame, text="➤ Send", command=self.send_message,
            bg=self.COLORS['accent'], fg='#000000',
            font=("Consolas", 10, "bold"),
            border=0, cursor="hand2", padx=12, pady=6
        )
        send_btn.pack(side=tk.RIGHT)
        send_btn.bind("<Enter>", lambda e: send_btn.config(bg='#00ffaa'))
        send_btn.bind("<Leave>", lambda e: send_btn.config(bg=self.COLORS['accent']))
        
    def create_status_bar(self):
        """Create the status bar with typing animation"""
        status_frame = tk.Frame(self.root, bg=self.COLORS['bg_secondary'], height=28)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text=f"COM | Model: {self.MODEL_NAME} | Ready",
            font=self.font_status,
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Connection indicator
        self.conn_indicator = tk.Canvas(
            status_frame, width=12, height=12,
            bg=self.COLORS['bg_secondary'], highlightthickness=0
        )
        self.conn_indicator.pack(side=tk.RIGHT, padx=10)
        self.conn_indicator.create_oval(2, 2, 10, 10, fill=self.COLORS['text_dim'], outline="")
        
    def bind_events(self):
        """Bind keyboard shortcuts and events"""
        # Quit
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-Q>", lambda e: self.root.quit())
        
        # Clear chat
        self.root.bind("<Control-n>", lambda e: self.clear_chat())
        self.root.bind("<Control-N>", lambda e: self.clear_chat())
        
        # Voice input (Ctrl+M)
        self.root.bind("<Control-m>", lambda e: self.toggle_voice_input())
        self.root.bind("<Control-M>", lambda e: self.toggle_voice_input())
        
        # Toggle TTS (Ctrl+T)
        self.root.bind("<Control-t>", lambda e: self.toggle_tts())
        self.root.bind("<Control-T>", lambda e: self.toggle_tts())
        
    def on_focus_in(self, event):
        """Handle input field focus in"""
        if self.showing_placeholder:
            self.input_field.delete(0, tk.END)
            self.showing_placeholder = False
            
    def on_focus_out(self, event):
        """Handle input field focus out"""
        if not self.input_field.get():
            self.input_field.insert(0, self.placeholder_text)
            self.showing_placeholder = True
            
    def on_enter_pressed(self, event):
        """Handle Enter key press"""
        if not self.showing_placeholder and self.input_field.get().strip():
            self.send_message()
            
    def check_ollama_status(self):
        """Check if Ollama is running"""
        def check():
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    self.update_status(f"COM | Model: {self.MODEL_NAME} | Connected", "success")
                    self.set_connection_indicator("success")
                else:
                    raise Exception("API error")
            except Exception:
                self.update_status(f"COM | Model: {self.MODEL_NAME} | Disconnected", "error")
                self.set_connection_indicator("error")
                self.add_system_message("⚠ Warning: Cannot connect to Ollama. Please ensure Ollama is running.")
                
        thread = threading.Thread(target=check)
        thread.daemon = True
        thread.start()
        
    def set_connection_indicator(self, status):
        """Update connection indicator color"""
        colors = {
            "success": self.COLORS['text_primary'],
            "error": self.COLORS['error'],
            "warning": self.COLORS['warning']
        }
        items = self.conn_indicator.find_all()
        if items:
            self.conn_indicator.itemconfig(items[-1], fill=colors.get(status, self.COLORS['text_dim']))
            
    def update_status(self, message, status_type="info"):
        """Update status bar message"""
        self.status_label.config(text=message)
        if status_type == "success":
            self.set_connection_indicator("success")
        elif status_type == "error":
            self.set_connection_indicator("error")
        elif status_type == "warning":
            self.set_connection_indicator("warning")
            
    def start_typing_animation(self):
        """Start the typing animation in status bar"""
        self.typing_frames = ["⡀", "⠄", "⠂", "⠁", "⠈", "⠐", "⠠", "⢀"]
        self.typing_index = 0
        
        def animate():
            if self.is_generating:
                frame = self.typing_frames[self.typing_index]
                self.status_label.config(
                    text=f"COM | {frame} Typing..."
                )
                self.typing_index = (self.typing_index + 1) % len(self.typing_frames)
                self.typing_animation_id = self.root.after(100, animate)
                
        animate()
        
    def stop_typing_animation(self):
        """Stop the typing animation"""
        if self.typing_animation_id:
            self.root.after_cancel(self.typing_animation_id)
            self.typing_animation_id = None
            
    def add_message(self, role, content):
        """Add a message to the chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if role == "user":
            prefix = f"[{timestamp}] You:"
            tag = "user"
        elif role == "assistant":
            prefix = f"[{timestamp}] COM:"
            tag = "assistant"
        else:
            prefix = f"[{timestamp}]"
            tag = "system"
            
        self.chat_display.insert(tk.END, f"\n{prefix} {content}\n", tag)
        self.chat_display.see(tk.END)
        
    def add_system_message(self, content):
        """Add a system message"""
        self.add_message("system", content)
        
    def add_context_message(self, content):
        """Add context from RAG search"""
        self.chat_display.insert(tk.END, f"\n[Context: {content}]\n", "context")
        self.chat_display.see(tk.END)
        
    def save_history(self):
        """Save chat history to file"""
        try:
            data = {
                "full_history": self.full_history,
                "saved_at": datetime.now().isoformat()
            }
            with open(self.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def load_history(self):
        """Load chat history from file"""
        if not os.path.exists(self.HISTORY_FILE):
            # Create empty history file
            self.save_history()
            return
            
        try:
            with open(self.HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.full_history = data.get("full_history", [])
                
            # Restore recent messages to display
            for msg in self.full_history[-10:]:  # Show last 10 messages
                role = msg.get("role", "system")
                content = msg.get("content", "")
                if role in ["user", "assistant"]:
                    self.add_message(role, content)
                    
            # Restore context window
            recent = self.full_history[-self.MAX_CONTEXT_MESSAGES:]
            self.message_history = deque(
                [(m.get("role", ""), m.get("content", "")) for m in recent],
                maxlen=self.MAX_CONTEXT_MESSAGES
            )
            
            if self.full_history:
                self.add_system_message(f"📁 Loaded {len(self.full_history)} messages from history.")
                
        except Exception as e:
            self.add_system_message(f"⚠ Error loading history: {e}")
            self.full_history = []
            
    def keyword_search(self, query, max_results=2):
        """Simple keyword-based search in history (RAG-Light)"""
        query_words = set(query.lower().split())
        scores = []
        
        for i, msg in enumerate(self.full_history):
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "").lower()
            content_words = set(content.split())
            
            # Calculate overlap
            overlap = len(query_words & content_words)
            if overlap > 0:
                scores.append((i, overlap, msg.get("content", "")[:150]))
                
        # Sort by score and get top results
        scores.sort(key=lambda x: x[1], reverse=True)
        results = scores[:max_results]
        
        if results:
            snippets = [r[2] for r in results]
            return "... ".join(snippets)
        return None
        
    def build_prompt(self, user_query):
        """Build the complete prompt with context, CoT, and ICL"""
        # Search for relevant context
        context = self.keyword_search(user_query)
        
        # Build conversation history
        history_text = ""
        for role, content in self.message_history:
            if role == "user":
                history_text += f"User: {content}\n"
            elif role == "assistant":
                history_text += f"COM: {content}\n"
                
        # Add context if found
        context_instruction = ""
        if context:
            context_instruction = f"\n[Relevant context from memory: {context}]\nUse this context if helpful.\n"
            
        # Final prompt
        prompt = f"""{self.SYSTEM_PROMPT}

{context_instruction}
Previous conversation:
{history_text}
User: {user_query}
COM:"""

        return prompt
        
    def send_message(self):
        """Send user message to the model"""
        if self.is_generating:
            return
            
        query = self.input_field.get().strip()
        if not query or self.showing_placeholder:
            return
            
        # Add user message to display
        self.add_message("user", query)
        
        # Clear input
        self.input_field.delete(0, tk.END)
        self.showing_placeholder = True
        self.input_field.insert(0, self.placeholder_text)
        
        # Update state
        self.is_generating = True
        self.update_status("COM | Generating...", "warning")
        self.start_typing_animation()
        
        # Start generation thread
        thread = threading.Thread(target=self.generate_response, args=(query,))
        thread.daemon = True
        thread.start()
        
    def generate_response(self, user_query):
        """Generate response from Ollama (runs in thread)"""
        try:
            # Build prompt with context
            prompt = self.build_prompt(user_query)
            
            # Call Ollama API
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 512,
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
                
            data = response.json()
            assistant_response = data.get("response", "No response generated.")
            
            # Clean up response (remove any CoT artifacts if present)
            assistant_response = self.clean_response(assistant_response)
            
            # Update message history (sliding window)
            self.message_history.append(("user", user_query))
            self.message_history.append(("assistant", assistant_response))
            
            # Save to full history
            self.full_history.append({"role": "user", "content": user_query, "timestamp": datetime.now().isoformat()})
            self.full_history.append({"role": "assistant", "content": assistant_response, "timestamp": datetime.now().isoformat()})
            
            # Persist history
            self.save_history()
            
            # Update UI
            self.root.after(0, lambda: self.add_message("assistant", assistant_response))
            self.root.after(0, lambda: self.update_status(f"COM | Model: {self.MODEL_NAME} | Ready", "success"))
            self.root.after(0, lambda: self.stop_typing_animation())
            
            # Speak response if TTS enabled
            if self.tts_enabled and self.tts_engine:
                self.speak_response(assistant_response)
                
        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.handle_error("Cannot connect to Ollama. Is it running?"))
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.handle_error("Request timed out. Try again."))
        except Exception as e:
            self.root.after(0, lambda: self.handle_error(f"Error: {str(e)}"))
        finally:
            self.root.after(0, lambda: setattr(self, 'is_generating', False))
            
    def clean_response(self, response):
        """Clean the response, removing any internal reasoning markers"""
        # Remove common CoT markers
        patterns = [
            r"Step \d+:.*?(?=\n|$)",
            r"Thinking:.*?(?=\n|$)",
            r"Reasoning:.*?(?=\n|$)",
            r"Let me think.*?(?=\n|$)",
        ]
        cleaned = response
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()
        
    def handle_error(self, error_msg):
        """Handle and display errors"""
        self.stop_typing_animation()
        self.add_message("system", f"⚠ {error_msg}")
        self.update_status(f"COM | Error", "error")
        self.is_generating = False
        
    def speak_response(self, text):
        """Speak the response using TTS"""
        def speak():
            if self.tts_engine:
                try:
                    # Clean text for speech
                    clean_text = re.sub(r'[^\w\s.,!?]', '', text)
                    if len(clean_text) > 200:
                        clean_text = clean_text[:200] + "..."
                    self.tts_engine.say(clean_text)
                    self.tts_engine.runAndWait()
                except Exception:
                    pass
                    
        thread = threading.Thread(target=speak)
        thread.daemon = True
        thread.start()
        
    def toggle_tts(self):
        """Toggle text-to-speech on/off"""
        self.tts_enabled = not self.tts_enabled
        self.update_tts_button_state()
        
        if self.tts_enabled:
            self.update_status("COM | TTS Enabled", "success")
        else:
            self.update_status("COM | TTS Disabled", "info")
            
    def update_tts_button_state(self):
        """Update TTS button appearance"""
        if self.tts_enabled:
            self.tts_btn.config(bg=self.COLORS['accent'], fg='#000000')
        else:
            self.tts_btn.config(bg=self.COLORS['bg_tertiary'], fg=self.COLORS['text_dim'])
            
    def toggle_voice_input(self):
        """Toggle voice input (speech-to-text)"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            messagebox.showwarning("Voice Input", "SpeechRecognition library not installed.\nInstall with: pip install SpeechRecognition")
            return
            
        if self.is_generating:
            return
            
        # Visual feedback
        original_bg = self.mic_btn.cget('bg')
        self.mic_btn.config(bg=self.COLORS['warning'])
        
        def listen():
            try:
                with sr.Microphone() as source:
                    self.speech_recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.speech_recognizer.listen(source, timeout=5)
                    
                # Recognize speech using Google API
                text = self.speech_recognizer.recognize_google(audio)
                
                if text:
                    self.root.after(0, lambda: self.input_field.delete(0, tk.END))
                    self.root.after(0, lambda: self.input_field.insert(0, text))
                    self.root.after(0, lambda: setattr(self, 'showing_placeholder', False))
                    self.root.after(0, lambda: self.update_status(f"COM | Heard: '{text}'", "success"))
                    
            except sr.WaitTimeoutError:
                self.root.after(0, lambda: self.update_status("COM | No speech detected", "warning"))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.update_status("COM | Could not understand audio", "warning"))
            except sr.RequestError:
                self.root.after(0, lambda: self.update_status("COM | Speech API unavailable (offline?)", "error"))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"COM | Mic error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.mic_btn.config(bg=original_bg))
                
        thread = threading.Thread(target=listen)
        thread.daemon = True
        thread.start()
        
    def clear_chat(self):
        """Clear chat history"""
        if self.is_generating:
            return
            
        self.chat_display.delete(1.0, tk.END)
        self.message_history.clear()
        self.full_history = []
        self.save_history()
        self.add_system_message("💬 Chat cleared. Ready for new conversation.")
        self.update_status(f"COM | Model: {self.MODEL_NAME} | Ready", "success")


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        # root.iconbitmap("com_icon.ico")
        pass
    except Exception:
        pass
        
    app = COMAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()
