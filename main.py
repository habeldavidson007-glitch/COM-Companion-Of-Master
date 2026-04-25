"""
COM (Companion of Master) - Main UI Application
Single-file, highly optimized Tkinter interface.
Connects to com_engine.py for all logic operations.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import sys

# Import the core engine
from com_engine import COMEngine

class COMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("COM - Companion of Master")
        self.root.geometry("450x600")
        self.root.minsize(400, 500)
        
        # Window Styling (Floating, Transparent)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg="#1a1a1a")
        
        # Initialize Core Engine
        self.engine = COMEngine()
        self.engine.set_callback('on_message', self.update_chat)
        self.engine.set_callback('on_status', self.update_status)
        self.engine.set_callback('on_error', self.show_error)
        
        # Setup UI Components
        self.setup_ui()
        self.setup_bindings()
        
        # Initial Status
        self.status_label.config(text="🖥 COM initialized. Ready to assist.")

    def setup_ui(self):
        """Builds the Dark Theme UI."""
        
        # --- Header ---
        header_frame = tk.Frame(self.root, bg="#000000", height=50)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="COM", 
            font=("Consolas", 18, "bold"), 
            fg="#32CD32", # Lime Green
            bg="#000000"
        )
        title_label.pack(pady=10)
        
        # --- Chat Display ---
        self.chat_display = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg="#121212",
            fg="#32CD32",
            font=("Consolas", 11),
            insertbackground="#32CD32",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#333333"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure tags for coloring
        self.chat_display.tag_configure("user", foreground="#00FFFF", justify=tk.RIGHT) # Cyan
        self.chat_display.tag_configure("com", foreground="#32CD32", justify=tk.LEFT)   # Lime
        self.chat_display.tag_configure("system", foreground="#808080", justify=tk.CENTER) # Gray
        self.chat_display.tag_configure("timestamp", foreground="#555555", font=("Consolas", 8))

        # --- Input Area ---
        input_frame = tk.Frame(self.root, bg="#1a1a1a")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Text Entry with Placeholder Logic
        self.entry_box = tk.Text(
            input_frame,
            height=3,
            bg="#2a2a2a",
            fg="#FFFFFF",
            font=("Consolas", 11),
            borderwidth=1,
            highlightbackground="#444444",
            highlightcolor="#32CD32"
        )
        self.entry_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Placeholder handling
        self.placeholder_text = "Type your message here..."
        self.entry_box.insert("1.0", self.placeholder_text)
        self.entry_box.config(fg="#666666")
        self.has_placeholder = True
        
        self.entry_box.bind("<FocusIn>", self.on_entry_focus)
        self.entry_box.bind("<FocusOut>", self.on_entry_focus)
        self.entry_box.bind("<Return>", self.on_enter_key)
        
        # Send Button
        self.send_btn = tk.Button(
            input_frame,
            text="➤",
            command=self.send_message,
            bg="#32CD32",
            fg="#000000",
            font=("Consolas", 14, "bold"),
            borderwidth=0,
            width=3,
            cursor="hand2"
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # --- Control Bar (Voice & Tools) ---
        control_frame = tk.Frame(self.root, bg="#1a1a1a")
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Mic Button
        self.mic_btn = tk.Button(
            control_frame,
            text="🎤",
            command=self.activate_mic,
            bg="#333333",
            fg="#FFFFFF",
            font=("Segoe UI Emoji", 12),
            borderwidth=0,
            width=3,
            cursor="hand2"
        )
        self.mic_btn.pack(side=tk.LEFT, padx=5)
        
        # TTS Toggle Button
        self.tts_btn = tk.Button(
            control_frame,
            text="🔊",
            command=self.toggle_tts,
            bg="#32CD32", # Active color
            fg="#000000",
            font=("Segoe UI Emoji", 12),
            borderwidth=0,
            width=3,
            cursor="hand2"
        )
        self.tts_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear Button
        clear_btn = tk.Button(
            control_frame,
            text="🗑️",
            command=lambda: self.engine.clear_history(),
            bg="#333333",
            fg="#FF4444",
            font=("Segoe UI Emoji", 12),
            borderwidth=0,
            width=3,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # --- Status Bar ---
        self.status_label = tk.Label(
            self.root,
            text="Initializing...",
            font=("Consolas", 9),
            fg="#808080",
            bg="#000000",
            anchor=tk.W,
            padx=10,
            pady=5
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def setup_bindings(self):
        """Keyboard shortcuts."""
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-n>', lambda e: self.engine.clear_history())
        self.root.bind('<Control-m>', lambda e: self.activate_mic())
        self.root.bind('<Control-t>', lambda e: self.toggle_tts())

    # --- Event Handlers ---

    def on_entry_focus(self, event):
        """Handles placeholder text visibility."""
        if event.type == "FocusIn":
            if self.has_placeholder:
                self.entry_box.delete("1.0", tk.END)
                self.entry_box.config(fg="#FFFFFF")
                self.has_placeholder = False
        elif event.type == "FocusOut":
            if not self.entry_box.get("1.0", tk.END).strip():
                self.entry_box.insert("1.0", self.placeholder_text)
                self.entry_box.config(fg="#666666")
                self.has_placeholder = True

    def on_enter_key(self, event):
        """Sends message on Enter (Shift+Enter for newline)."""
        if not event.state & 0x1: # Shift key not pressed
            self.send_message()
            return "break" # Prevent newline
        return None

    def get_input_text(self) -> str:
        """Retrieves text from input box, handling placeholder."""
        text = self.entry_box.get("1.0", tk.END).strip()
        if text == self.placeholder_text or not text:
            return ""
        return text

    def clear_input(self):
        """Resets input box to placeholder state."""
        self.entry_box.delete("1.0", tk.END)
        self.entry_box.insert("1.0", self.placeholder_text)
        self.entry_box.config(fg="#666666")
        self.has_placeholder = True

    # --- Actions ---

    def send_message(self):
        """Triggers message sending."""
        text = self.get_input_text()
        if not text:
            return
            
        self.clear_input()
        
        # Show user message immediately
        self.append_to_chat("You", text, tag="user")
        
        # Send to engine
        threading.Thread(target=self.engine.send_message, args=(text,), daemon=True).start()

    def activate_mic(self):
        """Activates voice input."""
        def listen_thread():
            text = self.engine.listen()
            if text:
                # Schedule UI update on main thread
                self.root.after(0, lambda: self.process_voice_input(text))
                
        threading.Thread(target=listen_thread, daemon=True).start()

    def process_voice_input(self, text: str):
        """Inserts recognized speech into input box and sends."""
        self.entry_box.delete("1.0", tk.END)
        self.entry_box.insert("1.0", text)
        self.entry_box.config(fg="#FFFFFF")
        self.has_placeholder = False
        self.send_message()

    def toggle_tts(self):
        """Toggles Text-to-Speech on/off."""
        self.engine.tts_active = not self.engine.tts_active
        if self.engine.tts_active:
            self.tts_btn.config(bg="#32CD32", fg="#000000") # Green
            self.update_status("🔊 Voice Enabled")
        else:
            self.tts_btn.config(bg="#333333", fg="#808080") # Gray
            self.update_status("🔇 Voice Disabled")

    # --- UI Updates (Thread-Safe) ---

    def append_to_chat(self, sender: str, message: str, tag: str):
        """Appends a message to the chat display."""
        timestamp = threading.Thread(target=lambda: None) # Dummy for scope
        
        def _update():
            from datetime import datetime
            time_str = datetime.now().strftime("[%H:%M:%S]")
            
            self.chat_display.config(state=tk.NORMAL)
            
            # Timestamp
            self.chat_display.insert(tk.END, f"{time_str} ", "timestamp")
            
            # Sender
            self.chat_display.insert(tk.END, f"{sender}: ", tag)
            
            # Message
            self.chat_display.insert(tk.END, f"{message}\n\n", tag)
            
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.yview(tk.END)
            
        # Ensure update happens on main thread
        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)

    def update_chat(self, sender: str, message: str):
        """Callback for new messages from engine."""
        tag = "com" if sender == "COM" else "user"
        self.append_to_chat(sender, message, tag)

    def update_status(self, text: str):
        """Updates the status bar."""
        def _set():
            self.status_label.config(text=text)
            
        if threading.current_thread() is threading.main_thread():
            _set()
        else:
            self.root.after(0, _set)

    def show_error(self, message: str):
        """Shows an error toast/status."""
        self.update_status(f"❌ {message}")
        # Optional: Popup for critical errors
        # self.root.after(100, lambda: messagebox.showerror("COM Error", message))

if __name__ == "__main__":
    root = tk.Tk()
    app = COMApp(root)
    root.mainloop()
