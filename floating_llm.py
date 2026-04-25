import tkinter as tk
from tkinter import ttk, font
import requests
import json
import threading
from datetime import datetime

class FloatingLLMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("COM")
        self.root.geometry("450x600")
        self.root.minsize(350, 400)  # Prevent window from getting too small
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        
        # Configure style
        self.setup_styles()
        
        # Variables
        self.is_streaming = False
        self.api_url = "http://localhost:11434/api/generate"
        self.model_name = "qwen2.5:1.5b"
        
        # Create UI
        self.create_header()
        self.create_chat_area()
        self.create_input_area()
        self.create_status_bar()
        
        # Bind events
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-n>", lambda e: self.clear_chat())
        
    def setup_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom fonts
        self.header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.chat_font = font.Font(family="Consolas", size=10)
        self.input_font = font.Font(family="Segoe UI", size=11)
        self.status_font = font.Font(family="Segoe UI", size=8)
        
        # Color scheme
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent': '#e94560',
            'text_primary': '#ffffff',
            'text_secondary': '#a0a0a0',
            'user_msg_bg': '#0f3460',
            'ai_msg_bg': '#1a1a2e',
            'input_bg': '#0f0f1a',
            'success': '#4ade80',
            'error': '#f87171'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
    def create_header(self):
        """Create the header section"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_medium'], height=50)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="🤖 COM", 
            font=self.header_font,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Clear button
        clear_btn = tk.Button(
            header_frame,
            text="🗑️ Clear",
            command=self.clear_chat,
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            font=("Segoe UI", 9),
            border=0,
            cursor="hand2",
            padx=10,
            pady=5
        )
        clear_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(bg='#ff6b7a'))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(bg=self.colors['accent']))
        
    def create_chat_area(self):
        """Create the chat history area"""
        chat_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        chat_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Chat display with scrollbar
        self.chat_history = tk.Text(
            chat_frame,
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary'],
            font=self.chat_font,
            wrap=tk.WORD,
            border=0,
            highlightthickness=0,
            selectbackground=self.colors['bg_light'],
            selectforeground=self.colors['text_primary'],
            cursor="arrow"
        )
        self.chat_history.pack(side=tk.LEFT, expand=True, fill="both")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_history.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history.config(yscrollcommand=scrollbar.set)
        
        # Configure tags for different message types
        self.chat_history.tag_configure("user_tag", 
                                       background=self.colors['user_msg_bg'],
                                       foreground=self.colors['text_primary'],
                                       lmargin1=10, lmargin2=10, rmargin=10,
                                       spacing1=5, spacing2=5, spacing3=5)
        self.chat_history.tag_configure("ai_tag",
                                       background=self.colors['ai_msg_bg'],
                                       foreground=self.colors['text_primary'],
                                       lmargin1=10, lmargin2=10, rmargin=10,
                                       spacing1=5, spacing2=5, spacing3=5)
        self.chat_history.tag_configure("error_tag",
                                       foreground=self.colors['error'],
                                       lmargin1=10, lmargin2=10, rmargin=10,
                                       spacing1=3, spacing2=3, spacing3=3)
        self.chat_history.tag_configure("system_tag",
                                       foreground=self.colors['text_secondary'],
                                       lmargin1=10, lmargin2=10, rmargin=10,
                                       spacing1=3, spacing2=3, spacing3=3,
                                       font=("Segoe UI", 9, "italic"))
        
        # Make text read-only (except for insertions)
        self.chat_history.config(state='normal')
        
    def create_input_area(self):
        """Create the input area"""
        input_frame = tk.Frame(self.root, bg=self.colors['bg_medium'])
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Input field
        self.user_input = tk.Entry(
            input_frame,
            bg=self.colors['input_bg'],
            fg=self.colors['text_primary'],
            font=self.input_font,
            border=0,
            highlightthickness=2,
            highlightbackground=self.colors['bg_light'],
            highlightcolor=self.colors['accent'],
            insertbackground=self.colors['text_primary']
        )
        self.user_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10), ipady=5)
        self.user_input.bind("<Return>", self.send_message)
        self.user_input.bind("<Shift-Return>", lambda e: None)  # Allow Shift+Enter
        
        # Send button
        send_btn = tk.Button(
            input_frame,
            text="➤ Send",
            command=lambda: self.send_message(None),
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            font=("Segoe UI", 10, "bold"),
            border=0,
            cursor="hand2",
            padx=15,
            pady=8
        )
        send_btn.pack(side=tk.RIGHT, fill=tk.Y)
        send_btn.bind("<Enter>", lambda e: send_btn.config(bg='#ff6b7a'))
        send_btn.bind("<Leave>", lambda e: send_btn.config(bg=self.colors['accent']))
        
        # Placeholder text functionality
        self.user_input.insert(0, "Type your message... (Press Enter to send)")
        self.user_input.bind("<FocusIn>", self.on_focus_in)
        self.user_input.bind("<FocusOut>", self.on_focus_out)
        self.placeholder_shown = True
        
    def create_status_bar(self):
        """Create the status bar"""
        status_frame = tk.Frame(self.root, bg=self.colors['bg_medium'], height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text=f"Model: {self.model_name} | Ready",
            font=self.status_font,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Connection indicator
        self.connection_indicator = tk.Canvas(
            status_frame, width=10, height=10, 
            bg=self.colors['bg_medium'], highlightthickness=0
        )
        self.connection_indicator.pack(side=tk.RIGHT, padx=10)
        self.connection_indicator.create_oval(2, 2, 8, 8, fill=self.colors['success'], outline="")
        
    def on_focus_in(self, event):
        """Handle focus in event for placeholder"""
        if self.placeholder_shown:
            self.user_input.delete(0, tk.END)
            self.placeholder_shown = False
            
    def on_focus_out(self, event):
        """Handle focus out event for placeholder"""
        if not self.user_input.get():
            self.user_input.insert(0, "Type your message... (Press Enter to send)")
            self.placeholder_shown = True
            
    def send_message(self, event):
        """Send user message to LLM"""
        query = self.user_input.get().strip()
        
        # Don't send if placeholder is shown or empty
        if self.placeholder_shown or not query:
            return
            
        # Don't send while streaming
        if self.is_streaming:
            return
        
        # Add user message to chat
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_history.insert(tk.END, f"\n[{timestamp}] You: {query}\n", "user_tag")
        self.chat_history.see(tk.END)
        
        # Clear input
        self.user_input.delete(0, tk.END)
        self.placeholder_shown = True
        self.user_input.insert(0, "Type your message... (Press Enter to send)")
        
        # Disable input during generation
        self.is_streaming = True
        self.update_status("Generating response...", "warning")
        
        # Start generation in separate thread
        thread = threading.Thread(target=self.generate_response, args=(query,))
        thread.daemon = True
        thread.start()
        
    def generate_response(self, query):
        """Generate response from LLM (runs in separate thread)"""
        try:
            # Check connection first
            self.check_connection()
            
            # Use streaming for better UX
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": query,
                    "stream": True
                },
                stream=True
            )
            
            # Add AI response header
            timestamp = datetime.now().strftime("%H:%M")
            self.root.after(0, lambda: self.chat_history.insert(
                tk.END, f"\n[{timestamp}] COM: ", "ai_tag"
            ))
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            chunk = data['response']
                            full_response += chunk
                            # Update UI in main thread
                            self.root.after(0, lambda c=chunk: self.chat_history.insert(
                                tk.END, c, "ai_tag"
                            ))
                            self.root.after(0, lambda: self.chat_history.see(tk.END))
                    except json.JSONDecodeError:
                        continue
                        
            # Add newline after response
            self.root.after(0, lambda: self.chat_history.insert(tk.END, "\n", "ai_tag"))
            self.root.after(0, lambda: self.update_status(f"Model: {self.model_name} | Ready", "success"))
            
        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.handle_error("Cannot connect to Ollama. Is it running?"))
        except Exception as e:
            self.root.after(0, lambda: self.handle_error(f"Error: {str(e)}"))
        finally:
            self.root.after(0, lambda: setattr(self, 'is_streaming', False))
            
    def handle_error(self, error_msg):
        """Handle and display errors"""
        self.chat_history.insert(tk.END, f"\n⚠️ {error_msg}\n", "error_tag")
        self.chat_history.see(tk.END)
        self.update_status("Error occurred", "error")
        
    def update_status(self, message, status_type="info"):
        """Update status bar"""
        self.status_label.config(text=message)
        
        # Update connection indicator color
        colors = {
            "success": self.colors['success'],
            "error": self.colors['error'],
            "warning": '#fbbf24',
            "info": self.colors['success']
        }
        
        items = self.connection_indicator.find_all()
        if items:
            self.connection_indicator.itemconfig(items[-1], fill=colors.get(status_type, self.colors['success']))
            
    def check_connection(self):
        """Check if Ollama is running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code != 200:
                raise Exception("Ollama API not responding correctly")
        except:
            raise requests.exceptions.ConnectionError("Cannot connect to Ollama")
            
    def clear_chat(self):
        """Clear chat history"""
        self.chat_history.delete(1.0, tk.END)
        self.update_status(f"Model: {self.model_name} | Ready", "success")
        self.chat_history.insert(tk.END, "💬 Chat cleared. Start a new conversation!\n", "system_tag")


def main():
    root = tk.Tk()
    
    # Set window icon (optional, requires .ico file)
    # root.iconbitmap("icon.ico")
    
    app = FloatingLLMApp(root)
    
    # Add welcome message
    root.after(100, lambda: app.chat_history.insert(
        tk.END, 
        "✨ Welcome to COM!\nType your message below and press Enter.\n\n",
        "system_tag"
    ))
    
    root.mainloop()


if __name__ == "__main__":
    main()
