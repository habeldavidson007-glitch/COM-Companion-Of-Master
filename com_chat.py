"""
COM (Companion Of Master) — Unified Web Application
Combines mascot visualization + working chat interface
Follows Thuki's web-overlay pattern with FastAPI backend
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime
import uuid
import json

# Import COM Core for LLM intelligence
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.com_core import COMCore, classify_mode, is_signal, parse_signal

app = FastAPI(title="COM - Companion Of Master")

# Initialize COM brain
com_brain = COMCore()

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
        }
        
        /* Floating Mascot Container */
        .mascot-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 140px;
            height: 140px;
            cursor: pointer;
            transition: transform 0.3s ease;
            z-index: 1000;
            animation: float 3s ease-in-out infinite;
        }
        
        .mascot-container:hover {
            transform: scale(1.1);
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .mascot-svg {
            width: 100%;
            height: 100%;
            filter: drop-shadow(0 0 20px rgba(201, 168, 76, 0.5));
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
    <!-- Floating Mascot -->
    <div class="mascot-container" id="mascot" title="Click to open chat">
        <svg class="mascot-svg" viewBox="0 0 140 140">
            <!-- Glow ring -->
            <ellipse cx="70" cy="70" rx="65" ry="65" fill="none" stroke="#4A7FD4" stroke-width="2" opacity="0.5"/>
            <!-- Body -->
            <ellipse cx="70" cy="75" rx="45" ry="55" fill="#F0F4FF"/>
            <!-- Flame hair -->
            <ellipse cx="62" cy="35" rx="18" ry="22" fill="#508CF0" opacity="0.7"/>
            <ellipse cx="70" cy="28" rx="14" ry="18" fill="#649AF4" opacity="0.8"/>
            <ellipse cx="80" cy="33" rx="16" ry="20" fill="#508CF0" opacity="0.65"/>
            <ellipse cx="56" cy="40" rx="12" ry="15" fill="#4680E8" opacity="0.55"/>
            <ellipse cx="86" cy="38" rx="10" ry="13" fill="#4680E8" opacity="0.55"/>
            <!-- Eyes -->
            <ellipse cx="58" cy="68" rx="8" ry="9" fill="#143CB8"/>
            <ellipse cx="82" cy="68" rx="8" ry="9" fill="#143CB8"/>
            <ellipse cx="56" cy="66" rx="3" ry="3.5" fill="#B4D2FF"/>
            <ellipse cx="80" cy="66" rx="3" ry="3.5" fill="#B4D2FF"/>
            <!-- Crown gem -->
            <polygon points="66,28 70,20 74,28" fill="#C9A84C"/>
            <!-- Blush -->
            <ellipse cx="46" cy="78" rx="8" ry="4" fill="#FFB4B4" opacity="0.4"/>
            <ellipse cx="94" cy="78" rx="8" ry="4" fill="#FFB4B4" opacity="0.4"/>
            <!-- Smile -->
            <path d="M 62 82 Q 70 88 78 82" stroke="#6478B4" stroke-width="2" fill="none"/>
            <!-- Jacket -->
            <ellipse cx="70" cy="110" rx="35" ry="25" fill="#0F143C" opacity="0.9"/>
            <line x1="70" y1="95" x2="70" y2="125" stroke="#F0EBD2" stroke-width="3"/>
        </svg>
    </div>
    
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
        
        // Toggle chat on mascot click
        mascot.addEventListener('click', () => {
            chatContainer.classList.toggle('visible');
            if (chatContainer.classList.contains('visible')) {
                setTimeout(() => chatInput.focus(), 100);
            }
        });
        
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
