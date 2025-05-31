from datetime import datetime
from utils.db_connection import MongoDBConnection

class DataController:
    def __init__(self):
        self.db_connection = MongoDBConnection()
        self.db = self.db_connection.connect()
    
    def receive_data(self, json_data):
        try:
            if not self.db:
                return {"status": "error", "message": "Database connection failed"}
            
            # Add timestamp to the data
            json_data['timestamp'] = datetime.utcnow()
            
            # Insert data into MongoDB collection
            collection = self.db['sensor_data']  # Change collection name as needed
            result = collection.insert_one(json_data)
            
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