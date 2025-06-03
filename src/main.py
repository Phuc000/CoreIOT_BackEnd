from flask import Flask, request
from flask_cors import CORS
from routes.api_routes import setup_routes
from services.simple_rag_chatbot import SimpleRAGChatbot
import json
import asyncio
import websockets
import threading
from werkzeug.serving import make_server

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, origins=["http://localhost:5173"])

# Single RAG chatbot instance
chatbot = SimpleRAGChatbot()

# WebSocket handler
async def handle_websocket(websocket):
    """Handle WebSocket connections"""
    print('🔌 Client connected to chatbot')
    
    # Send welcome message
    welcome_message = {
        'type': 'message',
        'message': 'Welcome! I\'m your smart room assistant. I can help you monitor temperature, humidity, and lighting conditions. What would you like to know?',
        'error': None
    }
    await websocket.send(json.dumps(welcome_message))
    
    try:
        async for message in websocket:
            print(f'📥 Received message: {message}')
            try:
                data = json.loads(message)
                message_type = data.get('type', '')
                
                if True:
                    user_message = data.get('message', '')
                    print(f'📥 Received message: {user_message}')
                    
                    if not user_message:
                        response = {
                            'type': 'message',
                            'message': '',
                            'error': 'Message cannot be empty'
                        }
                    else:
                        # Process message with RAG chatbot
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
                
                elif message_type == 'clear_history':
                    chatbot.clear_history()
                    response = {
                        'type': 'message',
                        'message': 'Chat history cleared. How can I help you?',
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
                    'message': 'Sorry, I encountered an error processing your request.',
                    'error': str(e)
                }
                await websocket.send(json.dumps(error_response))
    
    except websockets.exceptions.ConnectionClosed:
        print('🔌 Client disconnected from chatbot')

# Setup API routes
setup_routes(app)

# Add chatbot status endpoint
@app.route('/chatbot/status')
def chatbot_status():
    return {
        "status": "active",
        "conversation_length": len(chatbot.conversation_history),
        "last_message": chatbot.conversation_history[-1] if chatbot.conversation_history else None,
        "capabilities": ["temperature_monitoring", "humidity_monitoring", "light_monitoring", "room_analysis"]
    }

async def start_websocket_server():
    """Start WebSocket server"""
    print("💬 Smart Room Chatbot WebSocket: ws://localhost:5001")
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
    print("🚀 Starting IoT API Gateway with Smart Room Chatbot...")
    print("📡 API Gateway: http://localhost:5000")
    
    # Start WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
    websocket_thread.start()
    
    print("🏠 Smart Room Assistant ready!")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)