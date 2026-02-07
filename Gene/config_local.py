"""
Local Database Configuration Module for Gene SQL Query System

Configuration for local MySQL database connection.
"""

import os
import mysql.connector
from typing import Optional, Dict, Any

# Configuration uses hardcoded values - no .env file dependency
# If you need to use environment variables, set them directly


class LocalConfig:
    """Configuration management for local MySQL database connection."""
    
    def __init__(self):
        # OpenAI Configuration (for OpenAI engine)
        self.OPENAI_API_KEY = ""  # Set your OpenAI API key here or use environment variable
        self.OPENAI_MODEL = "gpt-4"  # or "gpt-3.5-turbo"
        
        # Local MySQL Database Configuration
        self.DB_HOST = "127.0.0.1"  # localhost
        self.DB_PORT = "3306"
        self.DB_USER = "newuser"
        self.DB_PASSWORD = ""  # Updated password
        self.DB_NAME = "employee"  # Database name
        
        # Connection settings
        self.CONNECTION_TIMEOUT = 30
        self.AUTOCOMMIT = True

    def get_database_connection(self) -> mysql.connector.MySQLConnection:
        """
        Get a local MySQL database connection.
        
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
                autocommit=self.AUTOCOMMIT,
                connection_timeout=self.CONNECTION_TIMEOUT
            )
            return connection
        except mysql.connector.Error as e:
            raise ConnectionError(f"Failed to connect to local MySQL database: {e}")
    
    def get_database_uri(self) -> str:
        """
        Get database URI for SQLAlchemy.
        
        Returns:
            str: Database URI string.
        """
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            connection = self.get_database_connection()
            connection.close()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, str]:
        """
        Get connection information for display/debugging.
        
        Returns:
            Dict[str, str]: Connection details (password excluded).
        """
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "user": self.DB_USER,
            "database": self.DB_NAME,
            "password": "***" if self.DB_PASSWORD else "(empty)"
        }


# Global local configuration instance
local_config = LocalConfig()

# For backward compatibility, expose as config
config = local_config