# mongo_connection.py
import os
from pymongo import MongoClient

# Get MongoDB connection string and database details
connection_string = os.getenv("COSMOS_DB_CONNECTION_STRING")
database_name = os.getenv("COSMOS_DB_DATABASE_NAME")

# Create MongoDB client and database reference
client = MongoClient(connection_string)
db = client[database_name]

# Function to get a collection by name
def get_collection(collection_name):
    return db[collection_name]
