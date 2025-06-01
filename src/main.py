from flask import Flask, request
from flask_cors import CORS
from routes.api_routes import setup_routes
import json
import asyncio
import websockets
import threading
from werkzeug.serving import make_server

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, origins=["http://localhost:5173"])

# Simple chatbot session (single session only)
class SimpleChatbot:
    def __init__(self):
        self.conversation_history = []
        self.connected_clients = set()
    
    def process_message(self, message):
        """Simple chatbot response - replace with your RAG implementation"""
        # Store user message
        self.conversation_history.append({"role": "user", "content": message})
        
        # Simple response logic (replace with your RAG chatbot)
        if "temperature" in message.lower():
            response = "I can help you with temperature data. Current temperature readings are available via the /telemetry endpoint."
        elif "led" in message.lower():
            response = "I can help you control the LED. Use the LED control endpoints to turn it on/off."
        elif "sensor" in message.lower():
            response = "I can provide sensor data including temperature, humidity, and light readings."
        else:
            response = "Hello! I'm your IoT assistant. I can help you with sensor data and LED control. What would you like to know?"
        
        # Store bot response
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def get_history(self):
        return self.conversation_history

# Single chatbot instance
chatbot = SimpleChatbot()

# WebSocket handler - REMOVED the 'path' parameter
async def handle_websocket(websocket):
    """Handle WebSocket connections"""
    print('🔌 Client connected to chatbot')
    chatbot.connected_clients.add(websocket)
    
    # Send welcome message
    welcome_message = {
        'type': 'message',
        'message': 'Welcome! I\'m your IoT assistant. How can I help you today?',
        'error': None
    }
    await websocket.send(json.dumps(welcome_message))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type', '')
                
                if message_type == 'chat_message':
                    user_message = data.get('message', '')
                    print(f'📥 Received message: {user_message}')
                    
                    if not user_message:
                        response = {
                            'type': 'message',
                            'message': '',
                            'error': 'Message cannot be empty'
                        }
                    else:
                        # Process message with chatbot
                        bot_response = chatbot.process_message(user_message)
                        
                        response = {
                            'type': 'message',
                            'message': bot_response,
                            'error': None
                        }
                    
                    await websocket.send(json.dumps(response))
                
                elif message_type == 'get_history':
                    history = chatbot.get_history()
                    response = {
                        'type': 'history',
                        'history': history,
                        'error': None
                    }
                    await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                error_response = {
                    'type': 'error',
                    'message': 'Invalid JSON format',
                    'error': 'JSON decode error'
                }
                await websocket.send(json.dumps(error_response))
            
            except Exception as e:
                print(f'❌ Chatbot error: {e}')
                error_response = {
                    'type': 'error',
                    'message': '',
                    'error': str(e)
                }
                await websocket.send(json.dumps(error_response))
    
    except websockets.exceptions.ConnectionClosed:
        print('🔌 Client disconnected from chatbot')
    finally:
        chatbot.connected_clients.discard(websocket)

# Setup API routes
setup_routes(app)

# Add chatbot status endpoint
@app.route('/chatbot/status')
def chatbot_status():
    return {
        "status": "active",
        "conversation_length": len(chatbot.conversation_history),
        "connected_clients": len(chatbot.connected_clients),
        "last_message": chatbot.conversation_history[-1] if chatbot.conversation_history else None
    }

async def start_websocket_server():
    """Start WebSocket server"""
    print("💬 Chatbot WebSocket: ws://localhost:5001")
    server = await websockets.serve(handle_websocket, "localhost", 5001)
    await server.wait_closed()

def run_websocket_server():
    """Run WebSocket server in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(start_websocket_server())
    except KeyboardInterrupt:
        print("💬 WebSocket server stopped")
    finally:
        loop.close()

if __name__ == "__main__":
    print("🚀 Starting IoT API Gateway with Chatbot...")
    print("📡 API Gateway: http://localhost:5000")
    
    # Start WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
    websocket_thread.start()
    
    print("📊 API Documentation available at endpoints")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)