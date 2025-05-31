from flask import Blueprint, request, jsonify
from controllers.data_controller import DataController
from controllers.led_controller import LEDController
import random
from datetime import datetime, timedelta

api_routes = Blueprint('api_routes', __name__)
data_controller = DataController()
led_controller = LEDController()

@api_routes.route('/data', methods=['POST'])
def receive_data():
    json_data = request.get_json()
    response = data_controller.receive_data(json_data)
    print(f"Received data: {json_data}")
    return jsonify(response)

@api_routes.route('/telemetry', methods=['GET'])
def get_telemetry():
    """Fetch telemetry data for frontend"""
    try:
        real_data = data_controller.get_latest_telemetry()
        
        if real_data:
            return jsonify({
                "status": "success",
                "data": real_data,
                "source": "database"
            })
        else:
            test_data = generate_test_telemetry()
            return jsonify({
                "status": "success",
                "data": test_data,
                "source": "test_data",
                "timestamp": datetime.utcnow().isoformat()
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch telemetry data: {str(e)}"
        }), 500

@api_routes.route('/telemetry/history', methods=['GET'])
def get_telemetry_history():
    """Fetch historical telemetry data"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Generate historical test data
        historical_data = []
        for i in range(limit):
            timestamp = datetime.utcnow() - timedelta(minutes=i*5)
            data = generate_test_telemetry()
            data['timestamp'] = timestamp.isoformat()
            historical_data.append(data)
        
        return jsonify({
            "status": "success",
            "data": historical_data,
            "count": len(historical_data)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch historical data: {str(e)}"
        }), 500

# LED Control Endpoints
@api_routes.route('/led', methods=['POST'])
def control_led():
    """Control LED (connects to CoreIOT on-demand)"""
    try:
        json_data = request.get_json()
        
        if not json_data or 'state' not in json_data:
            return jsonify({
                "status": "error",
                "message": "Missing 'state' parameter"
            }), 400
        
        # This will connect to CoreIOT, send command, and disconnect
        response = led_controller.set_led_state(json_data['state'])
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"LED control error: {str(e)}"
        }), 500

@api_routes.route('/led/status', methods=['GET'])
def get_led_status():
    """Get last known LED status"""
    try:
        response = led_controller.get_led_state()
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get LED status: {str(e)}"
        }), 500

@api_routes.route('/led/toggle', methods=['POST'])
def toggle_led():
    """Toggle LED state"""
    try:
        response = led_controller.toggle_led()
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"LED toggle error: {str(e)}"
        }), 500

def generate_test_telemetry():
    """Generate test telemetry data"""
    return {
        'temp': {
            'value': round(random.uniform(20.0, 35.0), 1),
            'unit': 'C'
        },
        'humid': {
            'value': round(random.uniform(30.0, 80.0), 1),
            'unit': '%'
        },
        'light': {
            'value': round(random.uniform(100.0, 1000.0), 1),
            'unit': 'lux'
        }
    }

def setup_routes(app):
    app.register_blueprint(api_routes)