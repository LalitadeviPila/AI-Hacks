"""
Local Database Manager for Gene SQL Query System

Handles MySQL database operations for local development environment.
"""

import mysql.connector
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from config_local import local_config


class LocalDatabaseManager:
    """Database manager for local MySQL database operations."""
    
    def __init__(self):
        """Initialize the local database manager."""
        self.config = local_config
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = self.config.get_database_connection()
            yield connection
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def __enter__(self):
        """Enter context manager."""
        self.connection = self.config.get_database_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            query (str): SQL query to execute.
            
        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries.
        """
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("No active database connection. Use within context manager.")
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query)
            
            # Handle different query types
            if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                results = cursor.fetchall()
                return results if results else []
            else:
                # For INSERT, UPDATE, DELETE, etc.
                self.connection.commit()
                return [{"affected_rows": cursor.rowcount}]
                
        except mysql.connector.Error as e:
            raise RuntimeError(f"SQL execution failed: {e}")
        finally:
            cursor.close()
    
    def get_table_info(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get information about all tables and their columns.
        
        Returns:
            Dict[str, List[Dict[str, str]]]: Dictionary mapping table names to column info.
        """
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("No active database connection. Use within context manager.")
        
        cursor = self.connection.cursor(dictionary=True)
        tables_info = {}
        
        try:
            # Get all table names
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            db_name = self.config.DB_NAME
            table_key = f"Tables_in_{db_name}"
            
            for table_row in tables:
                table_name = table_row[table_key]
                
                # Get column information for each table
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                # Format column information
                formatted_columns = []
                for col in columns:
                    formatted_columns.append({
                        "name": col["Field"],
                        "type": col["Type"],
                        "null": col["Null"],
                        "key": col["Key"],
                        "default": col["Default"],
                        "extra": col["Extra"]
                    })
                
                tables_info[table_name] = formatted_columns
                
        except mysql.connector.Error as e:
            raise RuntimeError(f"Failed to get table info: {e}")
        finally:
            cursor.close()
        
        return tables_info
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get general database information.
        
        Returns:
            Dict[str, Any]: Database information.
        """
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("No active database connection. Use within context manager.")
        
        cursor = self.connection.cursor(dictionary=True)
        info = {}
        
        try:
            # Get database version
            cursor.execute("SELECT VERSION() AS version")
            version_result = cursor.fetchone()
            info["mysql_version"] = version_result["version"]
            
            # Get current database
            cursor.execute("SELECT DATABASE() AS current_db")
            db_result = cursor.fetchone()
            info["current_database"] = db_result["current_db"]
            
            # Get table count
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            info["table_count"] = len(tables)
            
            # Connection info
            info["connection"] = self.config.get_connection_info()
            
        except mysql.connector.Error as e:
            raise RuntimeError(f"Failed to get database info: {e}")
        finally:
            cursor.close()
        
        return info


# Example usage and testing
if __name__ == "__main__":
    # Test the local database manager
    print("Testing Local Database Manager...")
    
    try:
        # Test connection
        db_manager = LocalDatabaseManager()
        print(f"Connection info: {local_config.get_connection_info()}")
        
        if db_manager.test_connection():
            print("✅ Database connection successful!")
            
            # Get database info
            with db_manager:
                info = db_manager.get_database_info()
                print(f"Database info: {info}")
                
                # Get table info
                tables = db_manager.get_table_info()
                print(f"Found {len(tables)} tables: {list(tables.keys())}")
                
        else:
            print("❌ Database connection failed!")
            
    except Exception as e:
        print(f"Error: {e}")