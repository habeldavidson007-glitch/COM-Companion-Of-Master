"""
COM (Companion Of Master) — Hybrid Desktop Application
Combines tkinter floating mascot (desktop overlay) + web chat interface
Mascot floats on desktop, clicking opens browser chat
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime
import uuid
import json
import threading
import webbrowser
import time

# Import COM Core for LLM intelligence
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.com_core import COMCore, classify_mode, is_signal, parse_signal

# Try to import tkinter for desktop mascot
try:
    import tkinter as tk
    from tkinter import font as tkfont
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

app = FastAPI(title="COM - Companion Of Master")

# Initialize COM brain
com_brain = COMCore()

# Global reference to mascot window
mascot_window = None

# In-memory message store
class Message(BaseModel):
    id: str
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: str

class Conversation(BaseModel):
    id: str
    messages: List[Message]
    created_at: str
    mode: str = "GENERAL"

# Active conversations
conversations: dict[str, Conversation] = {}
active_websockets: dict[str, WebSocket] = {}

def create_desktop_mascot():
    """Create a floating tkinter mascot window that opens browser on click"""
    if not TKINTER_AVAILABLE:
        print("⚠️  Tkinter not available, running web-only mode")
        print("📍 Open http://localhost:8000 in your browser")
        return
    
    global mascot_window
    
    root = tk.Tk()
    root.title("COM - Companion Of Master")
    
    # Make window transparent and always on top
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.95)
    
    # Set window size and position (bottom-right corner)
    window_size = 120
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = screen_width - window_size - 30
    y = screen_height - window_size - 30
    root.geometry(f"{window_size}x{window_size}+{x}+{y}")
    
    # Make background transparent (Windows only)
    try:
        root.attributes('-transparentcolor', '#F0F0F0')
    except:
        pass
    
    # Create canvas for mascot
    canvas = tk.Canvas(root, width=window_size, height=window_size, bg='#F0F0F0', highlightthickness=0)
    canvas.pack()
    
    # Draw mascot (simplified version)
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
    canvas.create_arc(50, 65, 75, 80, start=0, extent=180, style=tk.ARC, outline='#6478B4', width=2)
    # Crown gem
    canvas.create_polygon(55, 25, 60, 15, 65, 25, fill='#C9A84C', outline='')
    
    # Add glow effect with shadow
    try:
        canvas.create_oval(20, 35, 100, 110, outline='#4A7FD4', width=1, dash=(2, 2))
    except:
        pass
    
    # Animation variables
    animation_offset = 0
    animating_up = True
    
    def animate():
        nonlocal animation_offset, animating_up
        
        # Move up and down
        if animating_up:
            animation_offset -= 0.5
            if animation_offset <= -8:
                animating_up = False
        else:
            animation_offset += 0.5
            if animation_offset >= 0:
                animating_up = True
        
        # Redraw mascot at new position
        canvas.move('all', 0, animation_offset - (canvas.coords('all')[1] - canvas.coords('all')[1]))
        
        # Schedule next frame
        try:
            root.after(50, animate)
        except:
            pass
    
    def open_chat(event=None):
        """Open browser to chat interface with #chat hash to auto-open chat window"""
        webbrowser.open('http://localhost:8000/#chat')
    
    # Bind click to open browser
    canvas.bind('<Button-1>', open_chat)
    root.bind('<Button-1>', open_chat)
    
    # Add tooltip label
    tooltip = tk.Label(root, text="Click to chat!", font=('Arial', 8), bg='#C9A84C', fg='#0A0F2C')
    tooltip.place(x=10, y=5)
    tooltip.lower()  # Put behind mascot
    
    def show_tooltip():
        tooltip.lift()
        root.after(2000, lambda: tooltip.lower())
    
    # Show tooltip periodically
    def tooltip_loop():
        show_tooltip()
        root.after(5000, tooltip_loop)
    
    root.after(1000, tooltip_loop)
    root.after(100, animate)
    
    mascot_window = root
    
    print("✨ COM Desktop Mascot created!")
    print("💬 Click the mascot to open chat in your browser")
    print("🌐 Or open http://localhost:8000 directly")
    
    # Start tkinter main loop in separate thread
    def run_tkinter():
        try:
            root.mainloop()
        except:
            pass
    
    tk_thread = threading.Thread(target=run_tkinter, daemon=True)
    tk_thread.start()

@app.on_event("startup")
async def startup_event():
    """Start desktop mascot on server startup"""
    create_desktop_mascot()
    # Auto-open browser after a short delay with #chat hash
    time.sleep(0.5)
    webbrowser.open('http://localhost:8000/#chat')

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the unified COM UI with mascot and chat"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COM - Companion Of Master</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #0A0F2C 0%, #1A2355 50%, #0D1435 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            overflow: hidden;
            cursor: default;
        }
        
        /* Hide the web mascot since we have desktop mascot */
        .mascot-container {
            display: none;
        }
        
        /* Chat Window */
        .chat-container {
            width: 100%;
            max-width: 500px;
            background: #0D1435;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 0 2px #C9A84C;
            overflow: hidden;
            display: none;
            flex-direction: column;
            height: 70vh;
            max-height: 600px;
            position: relative;
            z-index: 999;
        }
        
        .chat-container.visible {
            display: flex;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #111736 0%, #1A2355 100%);
            color: white;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid #C9A84C;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            background: #4ADE80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .chat-header h1 {
            font-size: 18px;
            font-weight: 600;
            color: #C9A84C;
        }
        
        .chat-header p {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .close-btn {
            margin-left: auto;
            background: none;
            border: none;
            color: #7A8BB5;
            font-size: 20px;
            cursor: pointer;
            padding: 4px;
            transition: color 0.2s;
        }
        
        .close-btn:hover {
            color: #F87171;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: #0D1435;
        }
        
        .message {
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
        }
        
        .message.user {
            align-items: flex-end;
        }
        
        .message.assistant, .message.system {
            align-items: flex-start;
        }
        
        .message-bubble {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 16px;
            line-height: 1.4;
            word-wrap: break-word;
            font-size: 14px;
        }
        
        .message.user .message-bubble {
            background: linear-gradient(135deg, #1A2F6E 0%, #2A4A8E 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-bubble {
            background: #111736;
            color: #F0F4FF;
            border: 1px solid #1A2355;
            border-bottom-left-radius: 4px;
        }
        
        .message.system .message-bubble {
            background: transparent;
            color: #7A8BB5;
            font-size: 12px;
            font-style: italic;
            text-align: center;
            max-width: 100%;
        }
        
        .message-time {
            font-size: 10px;
            color: #7A8BB5;
            margin-top: 4px;
            padding: 0 4px;
        }
        
        .chat-input-container {
            padding: 16px;
            background: #111736;
            border-top: 1px solid #1A2355;
        }
        
        .chat-input-wrapper {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #1A2355;
            border-radius: 24px;
            font-size: 14px;
            resize: none;
            outline: none;
            transition: border-color 0.2s;
            font-family: inherit;
            background: #080D28;
            color: #F0F4FF;
            max-height: 100px;
            min-height: 44px;
        }
        
        .chat-input:focus {
            border-color: #C9A84C;
        }
        
        .send-button {
            width: 44px;
            height: 44px;
            border: none;
            border-radius: 50%;
            background: linear-gradient(135deg, #C9A84C 0%, #E8C96A 100%);
            color: #0A0F2C;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
            flex-shrink: 0;
        }
        
        .send-button:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(201, 168, 76, 0.4);
        }
        
        .send-button:active {
            transform: scale(0.95);
        }
        
        .typing-indicator {
            display: none;
            align-items: center;
            gap: 4px;
            padding: 10px 14px;
            background: #111736;
            border: 1px solid #1A2355;
            border-radius: 16px;
            width: fit-content;
            margin-bottom: 12px;
        }
        
        .typing-indicator.active {
            display: flex;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            background: #C9A84C;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.4;
            }
            30% {
                transform: translateY(-4px);
                opacity: 1;
            }
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #7A8BB5;
        }
        
        .mode-indicator {
            font-size: 11px;
            padding: 4px 8px;
            background: #1A2355;
            border-radius: 8px;
            color: #C9A84C;
            margin-left: 8px;
        }
        
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0D1435;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #1A2355;
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #C9A84C;
        }
    </style>
</head>
<body>
    <!-- Desktop mascot handles clicks, web mascot hidden via CSS -->
    <div class="mascot-container" id="mascot" style="display:none;"></div>
    
    <!-- Chat Window -->
    <div class="chat-container" id="chatContainer">
        <div class="chat-header">
            <div class="status-dot"></div>
            <div>
                <h1>COM <span class="mode-indicator" id="modeIndicator">GENERAL</span></h1>
                <p>Companion Of Master</p>
            </div>
            <button class="close-btn" id="closeBtn">×</button>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="empty-state" id="emptyState">
                <p style="font-size: 32px; margin-bottom: 12px;">💬</p>
                <p>Start a conversation with COM...</p>
                <p style="font-size: 12px; margin-top: 8px; opacity: 0.7;">Type a message and press Enter or click send</p>
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <textarea 
                    class="chat-input" 
                    id="chatInput" 
                    placeholder="Type your message..."
                    rows="1"
                ></textarea>
                <button class="send-button" id="sendButton">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const mascot = document.getElementById('mascot');
        const chatContainer = document.getElementById('chatContainer');
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        const emptyState = document.getElementById('emptyState');
        const closeBtn = document.getElementById('closeBtn');
        const modeIndicator = document.getElementById('modeIndicator');
        
        let ws;
        let conversationId = null;
        let currentMode = 'GENERAL';
        
        // Desktop mascot handles opening, so chat starts visible or can be opened via URL param
        // Check if opened from mascot (URL hash)
        if (location.hash === '#chat') {
            chatContainer.classList.add('visible');
            setTimeout(() => chatInput.focus(), 100);
        }
        
        // Close button
        closeBtn.addEventListener('click', () => {
            chatContainer.classList.remove('visible');
        });
        
        function connect() {
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${location.host}/ws`);
            
            ws.onopen = () => {
                console.log('Connected to COM');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'conversation_id') {
                    conversationId = data.id;
                    currentMode = data.mode || 'GENERAL';
                    modeIndicator.textContent = currentMode;
                } else if (data.type === 'message') {
                    addMessage(data.message);
                } else if (data.type === 'mode_update') {
                    currentMode = data.mode;
                    modeIndicator.textContent = currentMode;
                }
            };
            
            ws.onclose = () => {
                console.log('Disconnected, reconnecting...');
                setTimeout(connect, 1000);
            };
        }
        
        function addMessage(message) {
            emptyState.style.display = 'none';
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${message.role}`;
            
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.textContent = message.content;
            
            const time = document.createElement('div');
            time.className = 'message-time';
            time.textContent = new Date(message.timestamp).toLocaleTimeString();
            
            messageDiv.appendChild(bubble);
            messageDiv.appendChild(time);
            
            // Insert before typing indicator
            chatMessages.insertBefore(messageDiv, typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function sendMessage() {
            const content = chatInput.value.trim();
            if (!content || !ws || ws.readyState !== WebSocket.OPEN) return;
            
            ws.send(JSON.stringify({
                type: 'user_message',
                content: content,
                conversation_id: conversationId
            }));
            
            // Add user message immediately
            addMessage({
                role: 'user',
                content: content,
                timestamp: new Date().toISOString()
            });
            
            chatInput.value = '';
            chatInput.style.height = 'auto';
            typingIndicator.classList.add('active');
        }
        
        // Auto-resize textarea
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });
        
        // Send on Enter (Shift+Enter for new line)
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendButton.addEventListener('click', sendMessage);
        
        // Connect on load
        connect();
    </script>
</body>
</html>
""")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Create new conversation
    conv_id = str(uuid.uuid4())
    conversations[conv_id] = Conversation(
        id=conv_id,
        messages=[],
        created_at=datetime.now().isoformat(),
        mode="GENERAL"
    )
    active_websockets[conv_id] = websocket
    
    try:
        # Send conversation ID and initial mode to client
        await websocket.send_json({
            "type": "conversation_id",
            "id": conv_id,
            "mode": "GENERAL"
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "user_message":
                content = data.get("content", "")
                
                # Detect mode from user input
                detected_mode = classify_mode(content)
                conversations[conv_id].mode = detected_mode
                
                # Send mode update to client
                await websocket.send_json({
                    "type": "mode_update",
                    "mode": detected_mode
                })
                
                # Add user message
                user_msg = Message(
                    id=str(uuid.uuid4()),
                    role="user",
                    content=content,
                    timestamp=datetime.now().isoformat()
                )
                conversations[conv_id].messages.append(user_msg)
                
                # Broadcast user message
                await websocket.send_json({
                    "type": "message",
                    "message": user_msg.dict()
                })
                
                try:
                    # Generate AI response using COM Core
                    ai_response = com_brain.process_query(content)
                    
                    assistant_msg = Message(
                        id=str(uuid.uuid4()),
                        role="assistant",
                        content=ai_response,
                        timestamp=datetime.now().isoformat()
                    )
                    conversations[conv_id].messages.append(assistant_msg)
                    
                    # Send AI response
                    await websocket.send_json({
                        "type": "message",
                        "message": assistant_msg.dict()
                    })
                except Exception as e:
                    # Fallback if LLM fails
                    error_response = f"I received your message: '{content}'. (LLM not available - {str(e)})"
                    assistant_msg = Message(
                        id=str(uuid.uuid4()),
                        role="assistant",
                        content=error_response,
                        timestamp=datetime.now().isoformat()
                    )
                    conversations[conv_id].messages.append(assistant_msg)
                    await websocket.send_json({
                        "type": "message",
                        "message": assistant_msg.dict()
                    })
    
    except WebSocketDisconnect:
        if conv_id in active_websockets:
            del active_websockets[conv_id]
    except Exception as e:
        print(f"Error: {e}")
        if conv_id in active_websockets:
            del active_websockets[conv_id]

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting COM Chat server...")
    print("📍 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
