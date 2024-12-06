# db.py
from pymongo import MongoClient
import os
import logging
import datetime
from bson import ObjectId 
# MongoDB connection URI
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')  # Update if using a remote MongoDB URI
client = MongoClient(MONGO_URI)
db = client['Chatbot']  # Database name
chats_collection = db['chats']  # Collection name for storing chats

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def save_chat(user_message: str, assistant_response: str, session_id: str):
    """
    Save a chat log to the database.
    Args:
        user_message (str): User's message.
        assistant_response (str): Assistant's response.
        session_id (str): Unique session ID for the chat.
    """
    chat_entry = {
        "session_id": session_id,
        "user_message": user_message,
        "assistant_response": assistant_response
    }
    chats_collection.insert_one(chat_entry)

# Retrieve all chat messages for a specific session ID
def get_chat_history_by_session_id(session_id: str):
    """
    Retrieve all chat logs for a specific session ID.
    Args:
        session_id (str): Session ID to filter chats.
    Returns:
        list: List of chat logs for the session.
    """
    return list(chats_collection.find({"session_id": session_id}, {"_id": 0}))

# Retrieve all chats (for admin or debugging purposes)
def get_all_chats():
    """
    Retrieve all chat logs from the database.
    Returns:
        list: List of all chat logs.
    """
    return list(chats_collection.find({}, {"_id": 0}))

# Delete a specific chat entry by its ID
def delete_chat_by_id(chat_id: str):
    """
    Delete a specific chat log by its ID.
    Args:
        chat_id (str): The unique ID of the chat log to delete.
    Returns:
        bool: True if a document was deleted, False otherwise.
    """
    result = chats_collection.delete_one({"_id": ObjectId(chat_id)})
    return result.deleted_count > 0

# Delete all chats for a specific session ID
def delete_chats_by_session_id(session_id: str):
    """
    Delete all chat logs for a specific session ID.
    Args:
        session_id (str): The session ID to filter and delete chats.
    Returns:
        int: Number of deleted documents.
    """
    result = chats_collection.delete_many({"session_id": session_id})
    return result.deleted_count