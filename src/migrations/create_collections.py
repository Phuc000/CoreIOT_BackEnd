import os
import sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Add src directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import MongoDBConnection

load_dotenv()

class MongoMigration:
    def __init__(self):
        self.db_connection = MongoDBConnection()
        self.db = self.db_connection.connect()
    
    def create_collections_and_indexes(self):
        """Create collections and indexes for the IoT application"""
        try:
            if self.db is None:
                print("❌ Failed to connect to database")
                return False
            
            print("🚀 Starting MongoDB migration...")
            
            # Create sensor_data collection with schema validation
            self.create_sensor_data_collection()
            
            # Create indexes for better performance
            self.create_indexes()
            
            # Insert sample data
            self.insert_sample_data()
            
            print("✅ Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
        finally:
            self.db_connection.close()
    
    def create_sensor_data_collection(self):
        """Create sensor_data collection with validation schema"""
        collection_name = 'sensor_data'
        
        # Check if collection already exists
        if collection_name in self.db.list_collection_names():
            print(f"📦 Collection '{collection_name}' already exists")
            return
        
        # JSON Schema validation
        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["temperature", "humidity", "light", "timestamp"],
                "properties": {
                    "temperature": {
                        "bsonType": "number",
                        "description": "Temperature in Celsius"
                    },
                    "humidity": {
                        "bsonType": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Humidity percentage (0-100)"
                    },
                    "light": {
                        "bsonType": "number",
                        "minimum": 0,
                        "description": "Light intensity in lux"
                    },
                    "lightPercentage": {
                        "bsonType": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Light percentage (0-100)"
                    },
                    "rssi": {
                        "bsonType": "number",
                        "description": "WiFi signal strength"
                    },
                    "localIp": {
                        "bsonType": "string",
                        "description": "Device local IP address"
                    },
                    "timestamp": {
                        "bsonType": "date",
                        "description": "Data timestamp"
                    }
                }
            }
        }
        
        # Create collection with validation
        self.db.create_collection(collection_name, validator=validator)
        print(f"✅ Created collection '{collection_name}' with schema validation")
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        collection = self.db['sensor_data']
        
        # Create compound index on timestamp (descending) for latest data queries
        collection.create_index([("timestamp", DESCENDING)], name="timestamp_desc")
        print("✅ Created index: timestamp_desc")
        
        # Create compound index for time-based queries
        collection.create_index([
            ("timestamp", DESCENDING),
            ("temperature", ASCENDING)
        ], name="timestamp_temp")
        print("✅ Created index: timestamp_temp")
        
        # Create index for IP-based queries
        collection.create_index([("localIp", ASCENDING)], name="localIp_asc")
        print("✅ Created index: localIp_asc")
    
    def insert_sample_data(self):
        """Insert sample data for testing"""
        collection = self.db['sensor_data']
        
        sample_data = [
            {
                "temperature": 25.5,
                "humidity": 60.2,
                "light": 450.0,
                "lightPercentage": 75.0,
                "rssi": -45,
                "localIp": "192.168.1.100",
                "timestamp": datetime.utcnow()
            },
            {
                "temperature": 26.1,
                "humidity": 58.7,
                "light": 520.0,
                "lightPercentage": 80.0,
                "rssi": -42,
                "localIp": "192.168.1.100",
                "timestamp": datetime.utcnow()
            }
        ]
        
        result = collection.insert_many(sample_data)
        print(f"✅ Inserted {len(result.inserted_ids)} sample documents")
    
    def drop_collections(self):
        """Drop all collections (use with caution!)"""
        try:
            collections = ['sensor_data']
            for collection_name in collections:
                if collection_name in self.db.list_collection_names():
                    self.db.drop_collection(collection_name)
                    print(f"🗑️ Dropped collection: {collection_name}")
        except Exception as e:
            print(f"❌ Error dropping collections: {e}")

def main():
    """Main migration function"""
    migration = MongoMigration()
    
    print("MongoDB Migration Script")
    print("========================")
    print("1. Run migration (create collections and indexes)")
    print("2. Drop all collections (DANGER!)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        migration.create_collections_and_indexes()
    elif choice == "2":
        confirm = input("⚠️ This will delete ALL data! Type 'DELETE' to confirm: ")
        if confirm == "DELETE":
            migration.drop_collections()
        else:
            print("❌ Operation cancelled")
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()