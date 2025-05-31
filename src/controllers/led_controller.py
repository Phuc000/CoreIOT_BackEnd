from services.coreiot_service import CoreIOTService
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class LEDController:
    def __init__(self):
        # CoreIOT configuration
        self.coreiot_token = os.getenv('COREIOT_TOKEN', 'Xez0jZMwoHsJauxYccpN')
        self.coreiot_server = os.getenv('COREIOT_SERVER', 'app.coreiot.io')
        
        self.coreiot_service = CoreIOTService(
            token=self.coreiot_token,
            server=self.coreiot_server
        )
        
        self.led_state = False
        self.last_update = None
        
        # Connect to CoreIOT
        self._connect_to_coreiot()
    
    def _connect_to_coreiot(self):
        """Connect to CoreIOT.app"""
        try:
            success = self.coreiot_service.connect()
            if success:
                print("✅ LED Controller connected to CoreIOT.app")
            else:
                print("❌ Failed to connect LED Controller to CoreIOT.app")
            return success
        except Exception as e:
            print(f"❌ CoreIOT connection error: {e}")
            return False
    
    def set_led_state(self, state, source="api"):
        """Set LED state and send to CoreIOT"""
        try:
            # Validate input
            if not isinstance(state, bool):
                if isinstance(state, str):
                    state = state.lower() in ['true', '1', 'on', 'yes']
                elif isinstance(state, int):
                    state = bool(state)
                else:
                    return {
                        "status": "error",
                        "message": "Invalid state value. Use boolean, 'on'/'off', or 1/0"
                    }
            
            # Update local state
            previous_state = self.led_state
            self.led_state = state
            self.last_update = datetime.utcnow()
            
            # Send command to CoreIOT
            success = self.coreiot_service.send_led_command(state)
            
            if success:
                return {
                    "status": "success",
                    "message": f"LED turned {'ON' if state else 'OFF'}",
                    "data": {
                        "ledState": state,
                        "previousState": previous_state,
                        "timestamp": self.last_update.isoformat(),
                        "source": source
                    }
                }
            else:
                # Revert state if CoreIOT command failed
                self.led_state = previous_state
                return {
                    "status": "error",
                    "message": "Failed to send command to CoreIOT.app"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"LED control error: {str(e)}"
            }
    
    def get_led_state(self):
        """Get current LED state"""
        return {
            "status": "success",
            "data": {
                "ledState": self.led_state,
                "lastUpdate": self.last_update.isoformat() if self.last_update else None,
                "connected": self.coreiot_service.connected
            }
        }
    
    def toggle_led(self):
        """Toggle LED state"""
        new_state = not self.led_state
        return self.set_led_state(new_state, source="toggle")
    
    def disconnect(self):
        """Disconnect from CoreIOT"""
        self.coreiot_service.disconnect()