"""
COM Chat - Web-based chat interface following Thuki's design patterns
FastAPI backend with WebSocket support for real-time messaging
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime
import uuid

app = FastAPI(title="COM Chat")

# In-memory message store (replace with SQLite for persistence)
class Message(BaseModel):
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str

class Conversation(BaseModel):
    id: str
    messages: List[Message]
    created_at: str

# Active conversations
conversations: dict[str, Conversation] = {}
active_websockets: List[WebSocket] = []

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the chat UI"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COM Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .chat-container {
            width: 100%;
            max-width: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 80vh;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .chat-header p {
            font-size: 14px;
            opacity: 0.9;
            margin-top: 4px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 16px;
            display: flex;
            flex-direction: column;
        }
        
        .message.user {
            align-items: flex-end;
        }
        
        .message.assistant {
            align-items: flex-start;
        }
        
        .message-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-bubble {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
        }
        
        .message-time {
            font-size: 11px;
            color: #999;
            margin-top: 4px;
            padding: 0 4px;
        }
        
        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .chat-input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            padding: 14px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 24px;
            font-size: 15px;
            resize: none;
            outline: none;
            transition: border-color 0.2s;
            font-family: inherit;
            max-height: 120px;
            min-height: 50px;
        }
        
        .chat-input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
            flex-shrink: 0;
        }
        
        .send-button:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .send-button:active {
            transform: scale(0.95);
        }
        
        .send-button svg {
            width: 22px;
            height: 22px;
        }
        
        .typing-indicator {
            display: none;
            align-items: center;
            gap: 4px;
            padding: 12px 16px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 18px;
            width: fit-content;
            margin-bottom: 16px;
        }
        
        .typing-indicator.active {
            display: flex;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: #667eea;
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
            color: #999;
        }
        
        .empty-state svg {
            width: 64px;
            height: 64px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>💬 COM Chat</h1>
            <p>Your AI assistant - powered by local LLM</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="empty-state" id="emptyState">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                </svg>
                <p>Start a conversation...</p>
                <p style="font-size: 12px; margin-top: 8px;">Type a message and press Enter or click send</p>
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
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        const emptyState = document.getElementById('emptyState');
        
        let ws;
        let conversationId = null;
        
        function connect() {
            ws = new WebSocket(`ws://${location.host}/ws`);
            
            ws.onopen = () => {
                console.log('Connected to COM Chat');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'conversation_id') {
                    conversationId = data.id;
                } else if (data.type === 'message') {
                    addMessage(data.message);
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
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
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
        
        // Focus input
        chatInput.focus();
    </script>
</body>
</html>
""")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        # Create new conversation
        conv_id = str(uuid.uuid4())
        conversations[conv_id] = Conversation(
            id=conv_id,
            messages=[],
            created_at=datetime.now().isoformat()
        )
        
        # Send conversation ID to client
        await websocket.send_json({
            "type": "conversation_id",
            "id": conv_id
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "user_message":
                content = data.get("content", "")
                conv_id = data.get("conversation_id")
                
                if not conv_id or conv_id not in conversations:
                    conv_id = str(uuid.uuid4())
                    conversations[conv_id] = Conversation(
                        id=conv_id,
                        messages=[],
                        created_at=datetime.now().isoformat()
                    )
                
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
                
                # Generate AI response (simple echo for now - integrate with your LLM)
                # TODO: Replace with actual LLM integration
                ai_response = f"I received your message: '{content}'. This is a demo response. Integrate with your LLM backend!"
                
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
    
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
    except Exception as e:
        print(f"Error: {e}")
        if websocket in active_websockets:
            active_websockets.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting COM Chat server...")
    print("📍 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
