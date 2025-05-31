# API Gateway Project

This project implements an API gateway that receives JSON data through a controller API. It is structured to facilitate easy management of routes, controllers, middleware, and models.

## Project Structure

```
api-gateway
├── src
│   ├── main.py                # Entry point of the application
│   ├── controllers            # Contains controller logic
│   │   ├── __init__.py
│   │   └── data_controller.py  # Handles incoming JSON data
│   ├── routes                 # Defines API routes
│   │   ├── __init__.py
│   │   └── api_routes.py      # Sets up API endpoints
│   ├── middleware             # Contains middleware functions
│   │   ├── __init__.py
│   │   └── auth_middleware.py  # Authentication middleware
│   ├── models                 # Data models for validation
│   │   ├── __init__.py
│   │   └── data_models.py     # Defines data models
│   └── utils                  # Utility functions
│       ├── __init__.py
│       └── helpers.py         # Helper functions
├── tests                      # Contains unit tests
│   ├── __init__.py
│   └── test_controllers.py    # Tests for DataController
├── requirements.txt           # Project dependencies
├── config.py                  # Configuration settings
└── README.md                  # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd api-gateway
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/main.py
   ```

## Usage

The API gateway is designed to receive JSON data. You can send a POST request to the defined endpoints with the required JSON payload.

## API Endpoints

- **POST /data**: Receives JSON data and processes it through the `DataController`.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.