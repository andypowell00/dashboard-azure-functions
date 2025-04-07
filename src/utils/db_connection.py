import os
from pymongo import MongoClient
import logging

# Get MongoDB connection string and database details
connection_string = os.getenv("COSMOS_DB_CONNECTION_STRING")
database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "dashboard")  # Default to 'dashboard' if not specified

# Create MongoDB client and database reference
try:
    client = MongoClient(connection_string)
    
    # Quick test of the connection
    client.server_info()
    
    db = client[database_name]
    logging.info(f"Connected to MongoDB database: {database_name}")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {str(e)}")
    # Still create client and db variables to avoid NameError
    client = None
    db = None

# Function to get a collection by name
def get_collection(collection_name):
    if db is None:
        logging.error("Database connection is not established. Cannot get collection.")
        raise ConnectionError("MongoDB connection is not established.")
    
    # If collection name is None, use a default
    if collection_name is None:
        collection_name = "items"
        logging.warning(f"No collection name provided, using default: {collection_name}")
    
    return db[collection_name]
