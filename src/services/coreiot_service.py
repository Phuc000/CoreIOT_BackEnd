import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

class CoreIOTService:
    def __init__(self, token, server="app.coreiot.io", port=1883):
        self.token = token
        self.server = server
        self.port = port
    
    def send_led_command(self, state):
        """Send LED command via RPC (connect, send, disconnect)"""
        client = None
        try:
            # Create and configure client
            client = mqtt.Client()
            client.username_pw_set(self.token)
            
            connected = False
            
            def on_connect(client, userdata, flags, rc):
                nonlocal connected
                connected = (rc == 0)
                if connected:
                    print(f"✅ Connected to CoreIOT for LED command")
                else:
                    print(f"❌ Failed to connect: {rc}")
            
            client.on_connect = on_connect
            
            # Connect
            print(f"🔌 Connecting to {self.server} for LED command...")
            client.connect(self.server, self.port, 60)
            client.loop_start()
            
            # Wait for connection
            timeout = 5
            while not connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            if not connected:
                return False
            
            # Send RPC command to device
            rpc_topic = "v1/devices/me/rpc/request/1"
            rpc_payload = {
                "method": "setValueButtonLED",
                "params": state
            }
            
            result = client.publish(rpc_topic, json.dumps(rpc_payload))
            print(f"📤 Sent LED RPC command: {state}")
            
            # Wait for publish
            time.sleep(0.5)
            
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"❌ LED command error: {e}")
            return False
        finally:
            if client:
                client.loop_stop()
                client.disconnect()
                print("🔌 Disconnected from CoreIOT")