"""
COM (Companion Of Master) — Launcher
Start COM Brain server + Desktop GUI client
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.com_core import COMServer, COMCore


def main():
    print("=" * 60)
    print("  COM — Companion Of Master")
    print("=" * 60)
    
    # Check Ollama status first
    core = COMCore()
    status = core.check_status()
    
    if not status["ollama_running"]:
        print("\n⚠️  WARNING: Ollama not running!")
        print("   Run in a separate terminal: ollama serve")
        print("   COM will work in offline mode (file operations only)\n")
    else:
        print(f"\n✅ Ollama OK — model: {status['model']}\n")
    
    # Start COM Brain server in background thread
    print("🧠 Starting COM Brain server...")
    server = COMServer()
    # Use daemon=False so the thread doesn't die when main thread blocks on GUI
    server_thread = threading.Thread(target=server.start, daemon=False)
    server_thread.start()
    
    # Wait for server to initialize
    time.sleep(1.5)
    
    # Start desktop GUI client
    print("💬 Starting Desktop GUI client...\n")
    from com_chat import COMDesktopApp
    
    try:
        app = COMDesktopApp()
        app.run()
    finally:
        # Cleanup on exit
        print("\n👋 Shutting down COM...")
        server.stop()
        server_thread.join(timeout=2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 COM interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
