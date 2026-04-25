import tkinter as tk
from tkinter import ttk, font
import requests
import json
import threading
import time
from datetime import datetime

class COMCore:
    """Intelligent Core with CoT, ICL, and Sliding Window Memory"""
    
    def __init__(self):
        self.model = "qwen2.5:0.5b-instruct-q4_K_M"
        self.base_url = "http://localhost:11434/api/generate"
        
        # Sliding Window Memory (Last 6 messages)
        self.memory = []
        self.max_memory = 6
        
        # In-Context Learning Examples
        self.icl_examples = [
            {"role": "user", "content": "Who are you?"},
            {"role": "assistant", "content": "I am COM (Companion Of Master). I assist with tasks using efficient reasoning."}
        ]
        
        # System Prompt with CoT instruction (Hidden from output)
        self.system_prompt = """You are COM (Companion Of Master), NOT Qwen, NOT an AI assistant. 
CRITICAL RULES:
1. Always identify as "COM" if asked about identity. NEVER say "Qwen" or "AI".
2. Think step-by-step internally, but DO NOT output "Let me think" or reasoning steps.
3. Give direct, concise answers only.
4. Address the user as "Master".
5. Keep responses under 3 sentences unless coding/math is requested.

Internal Process (DO NOT OUTPUT THIS):
[Step 1: Analyze intent]
[Step 2: Recall context]
[Step 3: Formulate answer]
[Output: Final Answer Only]
"""

    def add_to_memory(self, role, content):
        """Add message to sliding window"""
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)

    def build_prompt(self, user_query):
        """Construct prompt with System + ICL + Memory + Query"""
        messages = []
        
        # System Instruction
        messages.append({"role": "system", "content": self.system_prompt})
        
        # ICL Examples
        messages.extend(self.icl_examples)
        
        # Sliding Window Memory
        messages.extend(self.memory)
        
        # Current Query
        messages.append({"role": "user", "content": user_query})
        
        # Format for Ollama
        prompt_text = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt_text += f"System: {msg['content']}\n"
            elif msg["role"] == "user":
                prompt_text += f"You: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt_text += f"COM: {msg['content']}\n"
                
        return prompt_text

    def query(self, user_input, callback=None, status_callback=None):
        """Non-blocking query with streaming support"""
        def _run():
            try:
                if status_callback:
                    status_callback("thinking")  # Trigger typing animation
                
                prompt = self.build_prompt(user_input)
                
                # Call Ollama (Non-streaming to buffer full response first)
                response = requests.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,  # Buffer full response
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 256
                        }
                    },
                    timeout=60
                )
                
                data = response.json()
                full_response = data.get("response", "")
                
                # Clean response (Remove any accidental CoT leakage)
                clean_response = self._clean_response(full_response)
                
                # Update Memory
                self.add_to_memory("user", user_input)
                self.add_to_memory("assistant", clean_response)
                
                if status_callback:
                    status_callback("ready")  # Stop typing animation
                
                if callback:
                    callback(clean_response)
                    
            except Exception as e:
                if status_callback:
                    status_callback("ready")
                if callback:
                    callback(f"[Error: Connection failed. Is Ollama running?]")
        
        threading.Thread(target=_run, daemon=True).start()

    def _clean_response(self, text):
        """Remove CoT markers and identity leaks"""
        lines = text.split('\n')
        clean_lines = []
        
        skip_next = False
        for line in lines:
            # Skip CoT phrases
            if "Let me think" in line or "step by step" in line.lower():
                continue
            if line.startswith("[Step") or line.startswith("Internal Process"):
                continue
            # Fix identity leaks
            if "I am Qwen" in line:
                line = line.replace("I am Qwen", "I am COM")
            
            if line.strip():
                clean_lines.append(line)
        
        return "\n".join(clean_lines).strip()


class FloatingLLMApp:
    def __init__(self, root):
        self.root = root
        self.core = COMCore()
        
        # Window Setup
        self.root.title("COM")  # Fixed: Window title
        self.root.geometry("350x500")
        self.root.minsize(300, 400)  # Prevent shrinking too much
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.configure(bg="#1a1a1a")
        
        # Custom Fonts
        self.font_msg = font.Font(family="Consolas", size=10)
        self.font_input = font.Font(family="Consolas", size=10)
        
        self.create_ui()
        self.show_welcome()

    def create_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#2d2d2d", height=40)
        header.pack(fill=tk.X, padx=5, pady=5)
        header.pack_propagate(False)
        
        lbl_title = tk.Label(header, text="COM", fg="#00ff00", bg="#2d2d2d", 
                            font=("Consolas", 12, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Status Label (For Typing Animation)
        self.lbl_status = tk.Label(header, text="", fg="#888", bg="#2d2d2d", 
                                  font=("Consolas", 8))
        self.lbl_status.pack(side=tk.RIGHT, padx=10, pady=12)

        # Chat Area
        chat_frame = tk.Frame(self.root, bg="#1a1a1a")
        chat_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.chat_history = tk.Text(chat_frame, bg="#000", fg="#fff", 
                                   font=self.font_msg, wrap=tk.WORD,
                                   bd=0, highlightthickness=1, highlightbackground="#333")
        self.chat_history.pack(side=tk.LEFT, expand=True, fill="both")
        self.chat_history.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_history.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history.config(yscrollcommand=scrollbar.set)
        
        # Tags for coloring
        self.chat_history.tag_config("user", foreground="#00ccff")
        self.chat_history.tag_config("com", foreground="#00ff00")
        self.chat_history.tag_config("sys", foreground="#ffff00")
        self.chat_history.tag_config("time", foreground="#555555")

        # Input Area
        input_frame = tk.Frame(self.root, bg="#2d2d2d")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.user_input = tk.Entry(input_frame, bg="#333", fg="#fff", 
                                  font=self.font_input, bd=0, insertbackground="#00ff00")
        self.user_input.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=5, padx=(0, 5))
        self.user_input.bind("<Return>", self.send_message)
        self.user_input.insert(0, "Ask COM...")
        self.user_input.bind("<FocusIn>", self.clear_placeholder)
        self.user_input.bind("<FocusOut>", self.restore_placeholder)
        self.placeholder_active = True
        
        send_btn = tk.Button(input_frame, text="➤", bg="#006600", fg="white",
                            font=("Consolas", 10, "bold"), bd=0,
                            command=lambda: self.send_message(None))
        send_btn.pack(side=tk.RIGHT, ipadx=10, ipady=2)

        # Typing Animation State
        self.is_typing = False
        self.typing_dots = 0
        self.typing_job = None

    def clear_placeholder(self, event):
        if self.placeholder_active:
            self.user_input.delete(0, tk.END)
            self.placeholder_active = False

    def restore_placeholder(self, event):
        if not self.user_input.get():
            self.user_input.insert(0, "Ask COM...")
            self.placeholder_active = True

    def show_welcome(self):
        self.append_message("System", "COM Core Initialized.", "sys")
        self.append_message("System", "Memory: Active (Sliding Window)", "sys")
        self.append_message("System", "Mode: CoT + ICL (Light)", "sys")
        self.append_message("COM", "Ready for your command, Master.", "com")

    def append_message(self, sender, text, tag):
        self.chat_history.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("[%H:%M]")
        
        self.chat_history.insert(tk.END, f"\n{timestamp} ", "time")
        if sender != "System":
            self.chat_history.insert(tk.END, f"{sender}: ", tag)
        self.chat_history.insert(tk.END, f"{text}\n")
        
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)

    def start_typing_animation(self):
        """Start the '...' blinking animation"""
        self.is_typing = True
        self.typing_dots = 0
        self.lbl_status.config(text="typing", fg="#00ff00")
        self._animate_dots()

    def _animate_dots(self):
        """Update dots every 500ms"""
        if self.is_typing:
            self.typing_dots = (self.typing_dots + 1) % 4
            dot_text = "." * self.typing_dots
            self.lbl_status.config(text=f"typing{dot_text}")
            self.typing_job = self.root.after(500, self._animate_dots)

    def stop_typing_animation(self):
        """Stop the animation"""
        self.is_typing = False
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
        self.lbl_status.config(text="")

    def send_message(self, event):
        if self.placeholder_active:
            return
            
        query = self.user_input.get().strip()
        if not query:
            return
            
        self.user_input.delete(0, tk.END)
        self.append_message("You", query, "user")
        
        # Start Typing Animation
        self.start_typing_animation()
        
        # Query Core
        self.core.query(query, 
                       callback=self.on_response, 
                       status_callback=self.on_status_change)

    def on_status_change(self, status):
        """Handle status updates from core"""
        if status == "thinking":
            self.start_typing_animation()
        elif status == "ready":
            self.stop_typing_animation()

    def on_response(self, response):
        """Display final response"""
        self.stop_typing_animation()  # Ensure animation stops
        self.append_message("COM", response, "com")

def main():
    root = tk.Tk()
    app = FloatingLLMApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
