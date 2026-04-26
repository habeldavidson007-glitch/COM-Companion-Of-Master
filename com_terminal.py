"""
COM (Companion Of Master) — Terminal Edition
No GUI dependencies - works everywhere
Offline fallback mode built-in
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.com_core import COMCore
from tools.excel_tool import run as excel_run
from tools.pdf_tool import run as pdf_run
from tools.ppt_tool import run as ppt_run
from core.com_core import is_signal, parse_signal


class COMTerminalApp:
    """Terminal-based COM application with offline fallback"""
    
    def __init__(self):
        self.com_brain = COMCore()
        self.offline_mode = False
        self.messages = []
        
    def check_system(self):
        """Check system status and set mode"""
        status = self.com_brain.check_status()
        
        if not status["ollama_running"]:
            print("\n⚠️  Ollama not detected - starting in OFFLINE MODE")
            print("   File operations (Excel/PDF/PPT) will work normally")
            print("   Chat responses will use rule-based fallback")
            print("   To enable AI: start Ollama with 'ollama serve'\n")
            self.offline_mode = True
        else:
            print(f"\n✅ Ollama connected - Model: {status['model']}\n")
            self.offline_mode = False
            
        return status
    
    def get_offline_response(self, user_input):
        """Generate rule-based response when offline"""
        text = user_input.lower()
        
        # Greetings
        if any(g in text for g in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return "👋 Hello! I'm COM (Companion Of Master). I'm currently in offline mode. I can still help you create Excel, PDF, and PowerPoint files using the commands below!"
        
        # Help
        if 'help' in text or '?' in text:
            return """📖 COM Offline Help:
            
Available commands:
• Create Excel: "create excel file.xlsx with columns: Name,Age,City"
• Create PDF: "create pdf report.pdf with content: Hello World"
• Create PPT: "create ppt presentation.pptx with slides: Intro|Data|Conclusion"
• Open file: "open file.xlsx"

Note: AI chat requires Ollama. Start it with: ollama serve"""
        
        # Excel creation
        if 'excel' in text and ('create' in text or 'new' in text):
            return "📊 To create Excel: Type the full command like:\n   'create excel data.xlsx with columns: Item,Qty,Price'"
        
        # PDF creation
        if 'pdf' in text and ('create' in text or 'new' in text):
            return "📄 To create PDF: Type the full command like:\n   'create pdf report.pdf with content: Your text here'"
        
        # PPT creation
        if 'ppt' in text or 'powerpoint' in text:
            return "📽 To create PowerPoint: Type the full command like:\n   'create ppt slides.pptx with slides: Intro|Methods|Results'"
        
        # Default
        return "🤔 I'm in offline mode. Try asking for help, or create files with commands like 'create excel file.xlsx with columns: A,B,C'. For AI chat, start Ollama first."
    
    def process_command(self, user_input):
        """Process user input - either tool command or chat"""
        text = user_input.strip()
        
        # Check for direct tool commands
        if text.startswith('create excel'):
            # Parse: create excel filename.xlsx with columns: A,B,C
            try:
                parts = text.split('with columns:')
                if len(parts) == 2:
                    filename = parts[0].replace('create excel', '').strip()
                    columns = parts[1].strip()
                    payload = f"{filename}:{columns}"
                    result = excel_run(payload)
                    return result
            except Exception as e:
                return f"❌ Error: {str(e)}"
                
        elif text.startswith('create pdf'):
            # Parse: create pdf filename.pdf with content: text
            try:
                parts = text.split('with content:')
                if len(parts) == 2:
                    filename = parts[0].replace('create pdf', '').strip()
                    content = parts[1].strip()
                    payload = f"{filename}:{content}"
                    result = pdf_run(payload)
                    return result
            except Exception as e:
                return f"❌ Error: {str(e)}"
                
        elif text.startswith('create ppt'):
            # Parse: create ppt filename.pptx with slides: A|B|C
            try:
                parts = text.split('with slides:')
                if len(parts) == 2:
                    filename = parts[0].replace('create ppt', '').strip()
                    slides = parts[1].strip()
                    payload = f"{filename}:{slides}"
                    result = ppt_run(payload)
                    return result
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # Check for open file command
        elif text.startswith('open '):
            filename = text.replace('open ', '').strip()
            if os.path.exists(filename):
                return f"📂 Opened: {os.path.abspath(filename)}"
            else:
                return f"❌ File not found: {filename}"
        
        # If offline, use rule-based responses
        if self.offline_mode:
            return self.get_offline_response(text)
        
        # Otherwise, use COMCore with streaming
        print("💭 Thinking...", end='', flush=True)
        
        response_chunks = []
        def callback(chunk):
            print(chunk, end='', flush=True)
            response_chunks.append(chunk)
        
        try:
            response = self.com_brain.process_query(text, callback=callback)
            print()  # New line after streaming
            
            # Check for signals
            if is_signal(response):
                prefix, payload = parse_signal(response)
                if prefix == "@XLS":
                    return f"\n📊 Executing Excel: {excel_run(payload)}"
                elif prefix == "@PDF":
                    return f"\n📄 Executing PDF: {pdf_run(payload)}"
                elif prefix == "@PPT":
                    return f"\n📽 Executing PPT: {ppt_run(payload)}"
            
            return ''.join(response_chunks) if response_chunks else response
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return "An error occurred while processing your request."
    
    def show_banner(self):
        """Display welcome banner"""
        print("=" * 60)
        print("  👋 COM - Companion Of Master (Terminal Edition)")
        print("=" * 60)
        mode = "OFFLINE MODE" if self.offline_mode else "AI MODE"
        print(f"  Status: {mode}")
        print("  Type 'help' for commands, 'quit' to exit")
        print("=" * 60)
    
    def run(self):
        """Main application loop"""
        self.check_system()
        self.show_banner()
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("\n👋 Goodbye! COM shutting down...")
                    break
                
                # Show timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{timestamp}] COM: ", end='')
                
                # Process and display response
                response = self.process_command(user_input)
                if response and not response.startswith('\n'):
                    print(response)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break


def main():
    """Entry point"""
    app = COMTerminalApp()
    app.run()


if __name__ == "__main__":
    main()
