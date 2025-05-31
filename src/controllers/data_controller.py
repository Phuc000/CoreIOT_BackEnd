from datetime import datetime
from utils.db_connection import MongoDBConnection

class DataController:
    def __init__(self):
        self.db_connection = MongoDBConnection()
        self.db = self.db_connection.connect()
    
    def receive_data(self, json_data):
        try:
            # Check if database connection exists properly
            if self.db is None:
                return {"status": "error", "message": "Database connection failed"}
            
            # Extract and validate fields from request body
            temperature = json_data.get("temperature")
            humidity = json_data.get("humidity")
            light = json_data.get("light")
            lightPercentage = json_data.get("lightPercentage")
            rssi = json_data.get("rssi")
            localIp = json_data.get("localIp")
            
            # Validate required fields
            if None in (temperature, humidity, light, lightPercentage, rssi, localIp):
                return {"status": "error", "message": "Missing required fields"}
            
            # Create document to insert
            document = {
                "temperature": temperature,
                "humidity": humidity,
                "light": light,
                "lightPercentage": lightPercentage,
                "rssi": rssi,
                "localIp": localIp,
                "timestamp": datetime.utcnow()
            }
            
            # Insert data into MongoDB collection
            collection = self.db['sensor_data']
            result = collection.insert_one(document)
            
            return {
                "status": "success", 
                "message": "Data saved successfully",
                "id": str(result.inserted_id)
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to save data: {str(e)}"
            }
    
    def get_latest_telemetry(self):
        """Get the latest telemetry data from database"""
        try:
            if self.db is None:
                return None
            
            collection = self.db['sensor_data']
            latest_data = collection.find_one(sort=[('timestamp', -1)])
            
            if latest_data:
                # Convert MongoDB document to the expected format
                return {
                    'temp': {
                        'value': latest_data.get('temperature'),
                        'unit': 'C'
                    },
                    'humid': {
                        'value': latest_data.get('humidity'),
                        'unit': '%'
                    },
                    'light': {
                        'value': latest_data.get('light'),
                        'unit': 'lux'
                    },
                    'timestamp': latest_data.get('timestamp').isoformat() if latest_data.get('timestamp') else None
                }
            return None
        except Exception as e:
            print(f"Error fetching telemetry data: {e}")
            return None