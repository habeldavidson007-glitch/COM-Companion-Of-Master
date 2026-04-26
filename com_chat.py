"""
COM (Companion Of Master) — Pure Tkinter Desktop Application
Floating mascot + native desktop chat window
Direct COMCore integration - no web server dependency
Native file dialogs for Excel/PDF/PPT operations
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.com_core import COMCore, classify_mode, is_signal, parse_signal

# Import tool modules for direct execution
from tools.excel_tool import run as excel_run
from tools.pdf_tool import run as pdf_run
from tools.ppt_tool import run as ppt_run


class COMDesktopApp:
    """Pure tkinter desktop chat application with floating mascot"""
    
    def __init__(self):
        self.root = None
        self.chat_window = None
        self.mascot_window = None
        self.com_brain = COMCore()
        self.messages: List[Dict] = []
        self.is_processing = False
        self.current_file_path = None
        self._window_closed = False
        
    def create_mascot(self):
        """Create floating mascot window that opens chat on click"""
        self.mascot_window = tk.Tk()
        self.mascot_window.title("COM - Companion Of Master")
        
        # Make window transparent and always on top
        self.mascot_window.overrideredirect(True)
        self.mascot_window.attributes('-topmost', True)
        self.mascot_window.attributes('-alpha', 0.95)
        
        # Set window size and position (bottom-right corner)
        window_size = 120
        screen_width = self.mascot_window.winfo_screenwidth()
        screen_height = self.mascot_window.winfo_screenheight()
        x = screen_width - window_size - 30
        y = screen_height - window_size - 30
        self.mascot_window.geometry(f"{window_size}x{window_size}+{x}+{y}")
        
        # Make background transparent (Windows only)
        try:
            self.mascot_window.attributes('-transparentcolor', '#F0F0F0')
        except:
            pass
        
        # Create canvas for mascot
        canvas = tk.Canvas(self.mascot_window, width=window_size, height=window_size, 
                          bg='#F0F0F0', highlightthickness=0)
        canvas.pack()
        
        # Draw mascot
        self._draw_mascot(canvas)
        
        # Animation variables
        self.animation_offset = 0
        self.animating_up = True
        
        # Bind click to open chat
        canvas.bind('<Button-1>', lambda e: self.open_chat())
        self.mascot_window.bind('<Button-1>', lambda e: self.open_chat())
        
        # Add tooltip label
        self.tooltip = tk.Label(self.mascot_window, text="Click to chat!", 
                               font=('Arial', 8), bg='#C9A84C', fg='#0A0F2C')
        self.tooltip.place(x=10, y=5)
        self.tooltip.lower()
        
        # Start animation
        self._animate_mascot(canvas)
        self._tooltip_loop()
        
        print("✨ COM Desktop Mascot created!")
        print("💬 Click the mascot to open chat window")
        
    def _draw_mascot(self, canvas):
        """Draw the COM mascot"""
        # Body
        canvas.create_oval(25, 40, 95, 105, fill='#F0F4FF', outline='#C9A84C', width=2)
        # Flame hair
        canvas.create_oval(45, 20, 65, 45, fill='#508CF0', outline='')
        canvas.create_oval(55, 15, 70, 40, fill='#649AF4', outline='')
        canvas.create_oval(65, 22, 80, 45, fill='#508CF0', outline='')
        # Eyes
        canvas.create_oval(45, 55, 58, 68, fill='#143CB8', outline='')
        canvas.create_oval(67, 55, 80, 68, fill='#143CB8', outline='')
        canvas.create_oval(43, 53, 50, 60, fill='#B4D2FF', outline='')
        canvas.create_oval(65, 53, 72, 60, fill='#B4D2FF', outline='')
        # Smile
        canvas.create_arc(50, 65, 75, 80, start=0, extent=180, style=tk.ARC, 
                         outline='#6478B4', width=2)
        # Crown gem
        canvas.create_polygon(55, 25, 60, 15, 65, 25, fill='#C9A84C', outline='')
        # Glow effect
        try:
            canvas.create_oval(20, 35, 100, 110, outline='#4A7FD4', width=1, dash=(2, 2))
        except:
            pass
            
    def _animate_mascot(self, canvas):
        """Animate mascot floating up and down"""
        if self.animating_up:
            self.animation_offset -= 0.5
            if self.animation_offset <= -8:
                self.animating_up = False
        else:
            self.animation_offset += 0.5
            if self.animation_offset >= 0:
                self.animating_up = True
        
        # Redraw mascot at new position
        canvas.delete('all')
        self._draw_mascot(canvas)
        canvas.move('all', 0, self.animation_offset)
        
        # Schedule next frame
        try:
            self.mascot_window.after(50, lambda: self._animate_mascot(canvas))
        except:
            pass
            
    def _tooltip_loop(self):
        """Show tooltip periodically"""
        if self.mascot_window:
            self.tooltip.lift()
            self.mascot_window.after(2000, lambda: self.tooltip.lower())
            self.mascot_window.after(5000, self._tooltip_loop)
    
    def open_chat(self):
        """Open the main chat window"""
        if self.chat_window is None or not self.chat_window.winfo_exists():
            self.create_chat_window()
        else:
            self.chat_window.lift()
            self.chat_window.focus_force()
    
    def create_chat_window(self):
        """Create the main chat window"""
        self.chat_window = tk.Toplevel(self.root) if self.root else tk.Tk()
        self.chat_window.title("COM - Companion Of Master")
        self.chat_window.geometry("600x700")
        self.chat_window.minsize(500, 600)
        
        # Set window icon and style
        self.chat_window.configure(bg='#0D1435')
        
        # Center window
        screen_width = self.chat_window.winfo_screenwidth()
        screen_height = self.chat_window.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 700) // 2
        self.chat_window.geometry(f"600x700+{x}+{y}")
        
        # Handle window close event
        def on_close():
            self._window_closed = True
            self.chat_window.destroy()
            self.chat_window = None
        
        self.chat_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Reset window closed flag when reopening
        self._window_closed = False
        
        # Create UI components
        self._create_chat_ui()
        
        # Add welcome message
        self._add_system_message("💬 COM Desktop ready! How can I help you?")
        
    def _create_chat_ui(self):
        """Create chat interface components"""
        # Header frame
        header_frame = tk.Frame(self.chat_window, bg='#111736', height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Status indicator
        status_dot = tk.Canvas(header_frame, width=12, height=12, bg='#111736', 
                              highlightthickness=0)
        status_dot.create_oval(2, 2, 10, 10, fill='#4ADE80', outline='')
        status_dot.pack(side=tk.LEFT, padx=15, pady=18)
        
        # Title
        title_label = tk.Label(header_frame, text="COM", font=('Arial', 16, 'bold'),
                              bg='#111736', fg='#C9A84C')
        title_label.pack(side=tk.LEFT, pady=18)
        
        mode_label = tk.Label(header_frame, text="GENERAL", font=('Arial', 10),
                             bg='#C9A84C', fg='#0A0F2C', padx=8, pady=2)
        mode_label.pack(side=tk.LEFT, padx=10, pady=20)
        self.mode_indicator = mode_label
        
        subtitle = tk.Label(header_frame, text="Companion Of Master", 
                           font=('Arial', 9), bg='#111736', fg='#7A8BB5')
        subtitle.pack(side=tk.LEFT, padx=10, pady=22)
        
        # File button
        file_btn = tk.Button(header_frame, text="📁", font=('Arial', 14),
                            bg='#1A2355', fg='#C9A84C', relief=tk.FLAT,
                            command=self._handle_file_operation,
                            activebackground='#2A3A6E', activeforeground='#F0F4FF')
        file_btn.pack(side=tk.RIGHT, padx=10, pady=12)
        
        # Clear button
        clear_btn = tk.Button(header_frame, text="🗑", font=('Arial', 14),
                             bg='#1A2355', fg='#7A8BB5', relief=tk.FLAT,
                             command=self._clear_chat,
                             activebackground='#2A3A6E', activeforeground='#F87171')
        clear_btn.pack(side=tk.RIGHT, padx=5, pady=12)
        
        # Messages area
        messages_frame = tk.Frame(self.chat_window, bg='#0D1435')
        messages_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Create scrolled text for messages
        self.messages_text = scrolledtext.ScrolledText(
            messages_frame,
            wrap=tk.WORD,
            bg='#0D1435',
            fg='#F0F4FF',
            font=('Segoe UI', 11),
            borderwidth=0,
            highlightthickness=0,
            insertbackground='#C9A84C'
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for message styling
        self.messages_text.tag_configure('user', foreground='#FFFFFF', 
                                        background='#1A2F6E', justify='right')
        self.messages_text.tag_configure('assistant', foreground='#F0F4FF',
                                        background='#111736', justify='left')
        self.messages_text.tag_configure('system', foreground='#7A8BB5',
                                        justify='center')
        self.messages_text.tag_configure('error', foreground='#F87171',
                                        justify='center')
        
        # Input area
        input_frame = tk.Frame(self.chat_window, bg='#111736')
        input_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # Text input
        self.input_text = tk.Text(input_frame, height=3, wrap=tk.WORD,
                                 bg='#080D28', fg='#F0F4FF',
                                 font=('Segoe UI', 11),
                                 borderwidth=0, highlightthickness=1,
                                 highlightbackground='#1A2355',
                                 highlightcolor='#C9A84C',
                                 insertbackground='#C9A84C')
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_text.bind('<Return>', self._on_enter_key)
        self.input_text.bind('<Shift-Return>', lambda e: None)  # Allow Shift+Enter
        
        # Send button
        send_btn = tk.Button(input_frame, text="➤", font=('Arial', 16, 'bold'),
                            bg='#C9A84C', fg='#0A0F2C', relief=tk.FLAT,
                            width=3, command=self._send_message,
                            activebackground='#E8C96A', activeforeground='#0A0F2C')
        send_btn.pack(side=tk.RIGHT)
        
        # Status bar
        status_frame = tk.Frame(self.chat_window, bg='#0A0F2C', height=24)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Ready", font=('Arial', 9),
                                    bg='#0A0F2C', fg='#7A8BB5', anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10)
        
    def _on_enter_key(self, event):
        """Handle Enter key press"""
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return 'break'
        return None
        
    def _send_message(self):
        """Send user message and get response"""
        if self.is_processing:
            return
            
        user_input = self.input_text.get('1.0', tk.END).strip()
        if not user_input:
            return
            
        # Clear input
        self.input_text.delete('1.0', tk.END)
        
        # Add user message
        self._add_user_message(user_input)
        
        # Process in background thread
        self.is_processing = True
        self.status_label.config(text="Processing...")
        self.messages_text.config(state=tk.DISABLED)
        
        # Create placeholder for assistant response
        self.messages_text.insert(tk.END, '\n')
        
        def process_thread():
            try:
                response_chunks = []
                
                def safe_ui_update(func):
                    """Safely update UI, handling window closure"""
                    if not hasattr(self, '_window_closed'):
                        try:
                            if self.chat_window and self.chat_window.winfo_exists():
                                self.chat_window.after(0, func)
                        except (RuntimeError, AttributeError):
                            pass
                
                def callback(chunk):
                    response_chunks.append(chunk)
                    # Safely update UI in main thread
                    safe_ui_update(lambda c=chunk: self._append_to_last_message(c))
                
                response = self.com_brain.process_query(user_input, callback=callback)
                
                # Check if response is a signal that needs tool execution
                if is_signal(response):
                    prefix, payload = parse_signal(response)
                    tool_result = self._execute_signal(prefix, payload)
                    if tool_result:
                        safe_ui_update(lambda r=tool_result: self._add_system_message(r))
                
                safe_ui_update(lambda: self._finish_processing())
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                safe_ui_update(lambda m=error_msg: self._add_system_message(m, tag='error'))
                safe_ui_update(lambda: self._finish_processing())
        
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
        
    def _append_to_last_message(self, chunk):
        """Append chunk to the last message being written"""
        self.messages_text.insert(tk.END, chunk)
        self.messages_text.see(tk.END)
        
    def _finish_processing(self):
        """Mark processing as complete"""
        self.is_processing = False
        self.status_label.config(text="Ready")
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, '\n\n')
        self.messages_text.see(tk.END)
        
    def _add_user_message(self, content):
        """Add user message to chat"""
        timestamp = datetime.now().strftime("%H:%M")
        self.messages_text.insert(tk.END, f"[{timestamp}] You: {content}\n\n")
        self.messages_text.see(tk.END)
        self.messages.append({'role': 'user', 'content': content})
        
    def _add_assistant_message(self, content):
        """Add assistant message to chat"""
        timestamp = datetime.now().strftime("%H:%M")
        self.messages_text.insert(tk.END, f"[{timestamp}] COM: {content}\n\n")
        self.messages_text.see(tk.END)
        self.messages.append({'role': 'assistant', 'content': content})
        
    def _add_system_message(self, content, tag='system'):
        """Add system message to chat"""
        self.messages_text.insert(tk.END, f"  {content}\n\n", tag)
        self.messages_text.see(tk.END)
        
    def _clear_chat(self):
        """Clear chat history"""
        if messagebox.askyesno("Clear Chat", "Clear all messages?"):
            self.messages_text.delete('1.0', tk.END)
            self.messages.clear()
            self.com_brain.clear_memory()
            self._add_system_message("Chat cleared.")
            
    def _handle_file_operation(self):
        """Handle file operations via native dialogs"""
        file_menu = tk.Menu(self.chat_window, tearoff=0)
        file_menu.add_command(label="📊 New Excel File", command=self._new_excel)
        file_menu.add_command(label="📄 New PDF File", command=self._new_pdf)
        file_menu.add_command(label="📽 New PowerPoint", command=self._new_ppt)
        file_menu.add_separator()
        file_menu.add_command(label="📂 Open Existing File", command=self._open_file)
        
        # Show menu at cursor position
        try:
            file_menu.tk_popup(self.chat_window.winfo_pointerx(), 
                              self.chat_window.winfo_pointery())
        finally:
            file_menu.grab_release()
            
    def _new_excel(self):
        """Create new Excel file via dialog"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Create New Excel File"
        )
        if filename:
            columns = simpledialog.askstring("Excel Columns", 
                "Enter column names (comma-separated):\nExample: Item,Qty,Price")
            if columns:
                payload = f"{os.path.basename(filename)}:{columns}"
                result = excel_run(payload)
                self._add_system_message(result)
                
    def _new_pdf(self):
        """Create new PDF file via dialog"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Create New PDF File"
        )
        if filename:
            content = simpledialog.askstring("PDF Content",
                "Enter PDF content:")
            if content:
                payload = f"{os.path.basename(filename)}:{content}"
                result = pdf_run(payload)
                self._add_system_message(result)
                
    def _new_ppt(self):
        """Create new PowerPoint file via dialog"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pptx",
            filetypes=[("PowerPoint files", "*.pptx"), ("All files", "*.*")],
            title="Create New PowerPoint File"
        )
        if filename:
            slides = simpledialog.askstring("PowerPoint Slides",
                "Enter slide titles (pipe-separated):\nExample: Intro|Data|Conclusion")
            if slides:
                payload = f"{os.path.basename(filename)}:{slides}"
                result = ppt_run(payload)
                self._add_system_message(result)
                
    def _open_file(self):
        """Open existing file"""
        filename = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("PDF files", "*.pdf"),
                ("PowerPoint files", "*.pptx"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.current_file_path = filename
            self._add_system_message(f"📂 Opened: {filename}")
            # Auto-detect mode based on file type
            ext = os.path.splitext(filename)[1].lower()
            mode_map = {'.xlsx': 'OFFICE (Excel)', '.pdf': 'OFFICE (PDF)', 
                       '.pptx': 'OFFICE (PowerPoint)'}
            mode = mode_map.get(ext, 'GENERAL')
            self.mode_indicator.config(text=mode)
            
    def _execute_signal(self, prefix, payload):
        """Execute signal bytes directly"""
        try:
            if prefix == "@XLS":
                return excel_run(payload)
            elif prefix == "@PDF":
                return pdf_run(payload)
            elif prefix == "@PPT":
                return ppt_run(payload)
            elif prefix == "@GDT":
                return f"🎮 GDScript signal: {prefix}:{payload}"
            elif prefix == "@ERR":
                return f"⚠️ Error signal: {payload}"
        except Exception as e:
            return f"❌ Signal execution failed: {str(e)}"
        return None
        
    def run(self):
        """Start the desktop application"""
        # Create hidden root window
        self.root = tk.Tk()
        self.root.withdraw()  # Hide root window
        
        # Create mascot
        self.create_mascot()
        
        print("\n🚀 COM Desktop App started!")
        print("💡 Click the mascot to open chat window")
        print("📁 Use the file button for Excel/PDF/PPT operations")
        
        # Start mascot main loop
        try:
            self.mascot_window.mainloop()
        except KeyboardInterrupt:
            print("\n👋 COM shutting down...")


def main():
    """Entry point for COM Desktop App"""
    print("=" * 50)
    print("  COM - Companion Of Master (Desktop Edition)")
    print("=" * 50)
    
    # Check Ollama status
    com_core = COMCore()
    status = com_core.check_status()
    
    if not status["ollama_running"]:
        print("\n⚠️  WARNING: Ollama is not running!")
        print("   Please start Ollama first:")
        print("   $ ollama serve")
        print("\n   The app will still start but LLM features won't work.")
        print()
    
    # Start desktop app
    app = COMDesktopApp()
    app.run()


if __name__ == "__main__":
    main()
