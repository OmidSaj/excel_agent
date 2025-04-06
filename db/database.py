"""
Database connection module for MongoDB using MongoEngine.
"""

import os
import logging
from typing import Optional
from mongoengine import connect, disconnect
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MongoDB connection details from environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/excel_llm")
DATABASE_NAME = os.getenv("DATABASE_NAME", "excel_agents")


def connect_db(uri: Optional[str] = None, db_name: Optional[str] = None) -> None:
    """
    Connect to MongoDB using MongoEngine.
    
    Args:
        uri: MongoDB connection URI. If None, uses environment variable.
        db_name: Database name. If None, uses environment variable.
    """
    try:
        connection_uri = uri or MONGODB_URI
        db = db_name or DATABASE_NAME
        
        logger.info(f"Connecting to database: {db}")
        connect(db=db, host=connection_uri)
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


def disconnect_db() -> None:
    """Disconnect from MongoDB."""
    try:
        logger.info("Disconnecting from MongoDB")
        disconnect()
        logger.info("Successfully disconnected from MongoDB")
    except Exception as e:
        logger.error(f"Error disconnecting from MongoDB: {str(e)}")
        raise 