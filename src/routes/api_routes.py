from flask import Blueprint, request, jsonify
from controllers.data_controller import DataController

api_routes = Blueprint('api_routes', __name__)
data_controller = DataController()

@api_routes.route('/data', methods=['POST'])
def receive_data():
    json_data = request.get_json()
    response = data_controller.receive_data(json_data)
    print(f"Received data: {json_data}")  # Debugging output
    return jsonify(response)

def setup_routes(app):
    app.register_blueprint(api_routes)