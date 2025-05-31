from services.coreiot_service import CoreIOTService
import os
from dotenv import load_dotenv

load_dotenv()

class LEDController:
    def __init__(self):
        self.coreiot_token = os.getenv('COREIOT_TOKEN', '')
        self.coreiot_service = CoreIOTService(token=self.coreiot_token)
        self.last_led_state = None
    
    def set_led_state(self, state):
        """Set LED state (connects to CoreIOT when called)"""
        try:
            # Validate input
            if isinstance(state, str):
                state = state.lower() in ['true', '1', 'on', 'yes']
            elif isinstance(state, int):
                state = bool(state)
            elif not isinstance(state, bool):
                return {
                    "status": "error",
                    "message": "Invalid state value"
                }
            
            # Send command to CoreIOT (connects temporarily)
            success = self.coreiot_service.send_led_command(state)
            
            if success:
                self.last_led_state = state
                return {
                    "status": "success",
                    "message": f"LED command sent: {'ON' if state else 'OFF'}",
                    "ledState": state
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to send LED command to CoreIOT"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"LED control error: {str(e)}"
            }
    
    def get_led_state(self):
        """Get last known LED state"""
        return {
            "status": "success",
            "data": {
                "lastLedState": self.last_led_state,
                "note": "Last command sent (actual device state may vary)"
            }
        }