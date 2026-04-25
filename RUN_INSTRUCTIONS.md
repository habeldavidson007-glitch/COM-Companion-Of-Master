# COM (Companion Of Master) - Running Instructions

## Features Implemented
✅ **Chain-of-Thought (CoT)**: Model reasons step-by-step before answering
✅ **In-Context Learning (ICL)**: 2 built-in examples teach the model how to respond
✅ **Sliding Window Memory**: Remembers last 6 messages (RAG-light alternative)
✅ **Quantized Model**: Uses `qwen2.5:0.5b-instruct-q4_K_M` (~500MB RAM)
✅ **Streaming Responses**: See AI typing in real-time
✅ **Low RAM Optimized**: Designed for 2GB available RAM

## Prerequisites

1. **Install Ollama** (if not already installed):
   - Download from: https://ollama.ai
   - Or on Windows: `winget install Ollama.Ollama`

2. **Pull the quantized model**:
   ```bash
   ollama pull qwen2.5:0.5b-instruct-q4_K_M
   ```

3. **Start Ollama** (usually auto-starts, but verify):
   ```bash
   ollama serve
   ```

4. **Verify Ollama is running**:
   ```bash
   ollama list
   ```
   You should see `qwen2.5:0.5b-instruct-q4_K_M` in the list.

## Running the Application

### On Windows (your case):
```powershell
cd "C:\Users\habil\Downloads\COM (Companion Of Master)"
python floating_llm.py
```

### On Linux/Mac:
```bash
cd /path/to/COM
python floating_llm.py
```

## Keyboard Shortcuts
- **Ctrl+Q**: Quit application
- **Ctrl+N**: Clear chat history
- **Enter**: Send message
- **Shift+Enter**: New line in input

## Architecture

```
floating_llm.py (UI Layer)
    ↓
core/com_core.py (Core Logic)
    ├── MemoryManager (sliding window, 6 messages)
    ├── PromptEngine (CoT + ICL)
    └── OllamaClient (streaming API)
```

## Memory Usage
- **Model**: ~500MB (quantized qwen2.5:0.5b)
- **Python + Tkinter**: ~100MB
- **Context Memory**: ~10MB (6 messages max)
- **Total**: ~650MB (well within your 2GB limit)

## Troubleshooting

### "Cannot connect to Ollama"
1. Check if Ollama is running: `ollama list`
2. Start Ollama: `ollama serve`
3. Verify model exists: `ollama pull qwen2.5:0.5b-instruct-q4_K_M`

### Model too slow
- The 0.5B model is optimized for speed on low-RAM systems
- If still slow, try closing other applications

### Out of memory
- The app limits memory to 6 conversation turns
- Clear chat with Ctrl+N if needed

## What Was Removed (for RAM optimization)
❌ Neural Architecture Search (requires GPU + GBs of RAM)
❌ Full RAG with embeddings (requires additional 500MB+)
❌ Zstd compression (adds CPU overhead, minimal benefit)

## What Was Added Instead
✅ Prompt engineering for CoT (zero RAM cost)
✅ Hardcoded ICL examples (minimal RAM)
✅ Sliding window memory (fixed RAM usage)
✅ Streaming for better UX (no extra RAM)
