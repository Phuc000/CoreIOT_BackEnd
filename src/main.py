from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from routes.api_routes import setup_routes
import json

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, origins=["http://localhost:5173"])

# Initialize SocketIO with CORS support
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple chatbot session (single session only)
class SimpleChatbot:
    def __init__(self):
        self.conversation_history = []
    
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

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('🔌 Client connected to chatbot')
    emit('message', {
        'message': 'Welcome! I\'m your IoT assistant. How can I help you today?',
        'error': None
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 Client disconnected from chatbot')

@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        user_message = data.get('message', '')
        print(f'📥 Received message: {user_message}')
        
        if not user_message:
            emit('message', {
                'message': '',
                'error': 'Message cannot be empty'
            })
            return
        
        # Process message with chatbot
        bot_response = chatbot.process_message(user_message)
        
        # Send response back
        emit('message', {
            'message': bot_response,
            'error': None
        })
        
    except Exception as e:
        print(f'❌ Chatbot error: {e}')
        emit('message', {
            'message': '',
            'error': str(e)
        })

@socketio.on('get_history')
def handle_get_history():
    try:
        history = chatbot.get_history()
        emit('history', {
            'history': history,
            'error': None
        })
    except Exception as e:
        emit('history', {
            'history': [],
            'error': str(e)
        })

# Setup API routes
setup_routes(app)

# Add chatbot status endpoint
@app.route('/chatbot/status')
def chatbot_status():
    return {
        "status": "active",
        "conversation_length": len(chatbot.conversation_history),
        "last_message": chatbot.conversation_history[-1] if chatbot.conversation_history else None
    }

if __name__ == "__main__":
    print("🚀 Starting IoT API Gateway with Chatbot...")
    print("📡 API Gateway: http://localhost:5000")
    print("💬 Chatbot WebSocket: ws://localhost:5000/socket.io/")
    print("📊 API Documentation available at endpoints")
    
    # Run with SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)