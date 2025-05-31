from flask import Flask
from flask_cors import CORS
from routes.api_routes import setup_routes

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, origins=["http://localhost:5173"])

# Or for development, allow all origins (less secure)
# CORS(app)

setup_routes(app)

if __name__ == "__main__":
    app.run(debug=True)