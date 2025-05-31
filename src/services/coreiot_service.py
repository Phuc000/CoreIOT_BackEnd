import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime

class CoreIOTService:
    def __init__(self, token, server="app.coreiot.io", port=1883):
        self.token = token
        self.server = server
        self.port = port
        self.client = mqtt.Client()
        self.connected = False
        
        # Setup MQTT client
        self.client.username_pw_set(self.token)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Topics
        self.telemetry_topic = f"v1/devices/me/telemetry"
        self.attributes_topic = f"v1/devices/me/attributes"
        self.rpc_request_topic = f"v1/devices/me/rpc/request/+"
        self.rpc_response_topic = f"v1/devices/me/rpc/response/"
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ Connected to CoreIOT.app with result code {rc}")
            
            # Subscribe to RPC requests
            client.subscribe(self.rpc_request_topic)
            print(f"📡 Subscribed to RPC topic: {self.rpc_request_topic}")
            
            # Request shared attributes
            self._request_shared_attributes()
        else:
            self.connected = False
            print(f"❌ Failed to connect to CoreIOT.app with result code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"🔌 Disconnected from CoreIOT.app with result code {rc}")
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"📥 Received message on topic: {topic}")
            print(f"📄 Payload: {payload}")
            
            # Handle RPC requests
            if "rpc/request" in topic:
                self._handle_rpc_request(topic, payload)
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def _handle_rpc_request(self, topic, payload):
        """Handle RPC requests from ThingsBoard"""
        try:
            # Extract request ID from topic
            request_id = topic.split("/")[-1]
            
            method = payload.get("method")
            params = payload.get("params", {})
            
            print(f"🔧 RPC Method: {method}")
            print(f"📋 Parameters: {params}")
            
            response = {"error": "Unknown method"}
            
            if method == "setValueButtonLED":
                # Handle LED control
                led_state = params if isinstance(params, bool) else params.get("state", False)
                response = self._set_led_state(led_state)
                
            elif method == "getLedState":
                # Get current LED state
                response = {"ledState": True}  # You can store actual state
                
            # Send response back
            response_topic = f"{self.rpc_response_topic}{request_id}"
            self.client.publish(response_topic, json.dumps(response))
            print(f"📤 Sent RPC response: {response}")
            
        except Exception as e:
            print(f"❌ Error handling RPC request: {e}")
    
    def _set_led_state(self, state):
        """Set LED state and return response"""
        print(f"💡 Setting LED state to: {state}")
        
        # Here you would control actual hardware
        # For now, we'll just simulate and send attributes
        
        # Send attribute update
        attributes = {
            "ledState": state,
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        self.send_attributes(attributes)
        
        return {
            "success": True,
            "ledState": state,
            "message": f"LED turned {'ON' if state else 'OFF'}"
        }
    
    def connect(self):
        """Connect to CoreIOT.app"""
        try:
            print(f"🔌 Connecting to {self.server}:{self.port}...")
            self.client.connect(self.server, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(1)
                timeout -= 1
                
            return self.connected
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from CoreIOT.app"""
        self.client.loop_stop()
        self.client.disconnect()
        print("🔌 Disconnected from CoreIOT.app")
    
    def send_telemetry(self, data):
        """Send telemetry data"""
        if not self.connected:
            print("❌ Not connected to CoreIOT.app")
            return False
            
        try:
            payload = json.dumps(data)
            result = self.client.publish(self.telemetry_topic, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Telemetry sent: {payload}")
                return True
            else:
                print(f"❌ Failed to send telemetry: {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Error sending telemetry: {e}")
            return False
    
    def send_attributes(self, attributes):
        """Send device attributes"""
        if not self.connected:
            print("❌ Not connected to CoreIOT.app")
            return False
            
        try:
            payload = json.dumps(attributes)
            result = self.client.publish(self.attributes_topic, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Attributes sent: {payload}")
                return True
            else:
                print(f"❌ Failed to send attributes: {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Error sending attributes: {e}")
            return False
    
    def _request_shared_attributes(self):
        """Request shared attributes from server"""
        request_topic = "v1/devices/me/attributes/request/1"
        payload = json.dumps({
            "sharedKeys": ["ledState", "blinkingInterval", "ledMode"]
        })
        self.client.publish(request_topic, payload)
        print("📥 Requested shared attributes")
    
    def send_led_command(self, state):
        """Send LED command via attributes"""
        attributes = {
            "ledState": state,
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.send_attributes(attributes)