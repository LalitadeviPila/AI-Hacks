"""
Database Manager for Gene SQL Query System

MySQL database operations.
"""

import mysql.connector
from typing import List, Optional, Tuple, Any, Dict
from config import config


class DatabaseManager:
    """MySQL database manager for remote database operations."""
    
    def __init__(self):
        """
        Initialize database manager with MySQL connection.
        """
        self.connection: Optional[mysql.connector.MySQLConnection] = None
    
    def connect(self) -> mysql.connector.MySQLConnection:
        """
        Create and return database connection.
        
        Returns:
            mysql.connector.MySQLConnection: Database connection.
        """
        self.connection = config.get_database_connection()
        return self.connection
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, params: Tuple = None) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            query (str): SQL query to execute.
            params (Tuple, optional): Query parameters.
            
        Returns:
            Dict[str, Any]: Query results.
        """
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT') or query.strip().upper().startswith('SHOW') or query.strip().upper().startswith('DESCRIBE'):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return {"columns": columns, "data": results}
            else:
                self.connection.commit()
                return {"affected_rows": cursor.rowcount}
        
        except mysql.connector.Error as e:
            raise Exception(f"Database error: {e}")
        
        finally:
            cursor.close()
    
    def get_table_info(self) -> Dict[str, List[str]]:
        """
        Get information about all tables.
        
        Returns:
            Dict[str, List[str]]: Dictionary with table names and their columns.
        """
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            # Get all table names
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            table_info = {}
            for (table_name,) in tables:
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                table_info[table_name] = [col[0] for col in columns]  # col[0] is column name
            
            return table_info
        
        except mysql.connector.Error as e:
            raise Exception(f"Error getting table info: {e}")
        
        finally:
            cursor.close()
    
    def get_table_preview(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get a preview of table data.
        
        Args:
            table_name (str): Name of the table.
            limit (int): Number of rows to return.
            
        Returns:
            Dict[str, Any]: Table preview results.
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def get_database_connection():
    """
    Quick helper to get a database connection.
    
    Returns:
        mysql.connector.MySQLConnection: Database connection.
    """
    return config.get_database_connection()