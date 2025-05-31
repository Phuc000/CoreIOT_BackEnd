import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoDBConnection:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI', '')
        self.client = None
        self.db = None
    
    def connect(self):
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client['iot_database']  # Change database name as needed
            return self.db
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None
    
    def close(self):
        if self.client:
            self.client.close()