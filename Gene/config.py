"""
Configuration Module for Gene SQL Query System

Handles MySQL database connections and Deere AI Gateway configurations.
"""

import os
import mysql.connector
import sys
from typing import Optional, Dict, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in parent directory (project root)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
    print(f"Loading .env from: {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables from .env file may not be loaded.")

# Add app directory to path to access helpers
app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app')
sys.path.insert(0, app_dir)

try:
    from helpers.auth_helper import get_access_token
except ImportError:
    print("Warning: Could not import auth_helper. AI functionality may not work.")
    get_access_token = None


class Config:
    """Configuration management for the SQL Query System."""
    
    def __init__(self):
        # Deere AI Gateway Configuration
        self.AI_GATEWAY_URL = "https://ai-gateway.deere.com/openai/chat/completions"
        self.LLM_MODEL_NAME = "gpt-4o-2024-11-20"
        # Try both possible environment variable names
        self.REGISTRATION_ID = (
            os.getenv("AI_GATEWAY_REGISTRATION_ID") or 
            os.getenv("AI_GATEWAY_CLIENT_REGISTRATION")
        )
        
        # MySQL Database Configuration
        self.DB_HOST = "work-dispatcher-schedule20220617050747894200000001.cluster-cmqnpz2pbdyf.us-east-1.rds.amazonaws.com"
        self.DB_PORT = "3306"
        self.DB_USER = "j188lkplu1geg0a"
        self.DB_PASSWORD = "dsdext5xae79gda"
        self.DB_NAME = "dispatchwork"

    def get_database_connection(self) -> mysql.connector.MySQLConnection:
        """
        Get a MySQL database connection.
        
        Returns:
            mysql.connector.MySQLConnection: Database connection object.
        """
        try:
            connection = mysql.connector.connect(
                host=self.DB_HOST,
                port=self.DB_PORT,
                user=self.DB_USER,
                password=self.DB_PASSWORD,
                database=self.DB_NAME,
                autocommit=True
            )
            return connection
        except mysql.connector.Error as e:
            raise ConnectionError(f"Failed to connect to MySQL database: {e}")
    
    def get_database_uri(self) -> str:
        """
        Get database URI for SQLAlchemy.
        
        Returns:
            str: Database URI string.
        """
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def get_ai_headers(self, access_token: str) -> Dict[str, str]:
        """
        Get headers for AI Gateway requests.
        
        Args:
            access_token (str): Bearer token for authentication.
            
        Returns:
            Dict[str, str]: Headers for API requests.
        """
        return {
            "Authorization": f"Bearer {access_token}",
            "deere-ai-gateway-registration-id": self.REGISTRATION_ID,
            "Content-Type": "application/json",
        }


# Global configuration instance
config = Config()