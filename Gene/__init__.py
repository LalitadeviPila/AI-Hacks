"""
Gene Package Initialization

Simple SQL query system for local database operations.
"""

from config import config
from database import DatabaseManager, get_database_connection
from query_engine import SimpleSQLEngine, create_sql_engine

__all__ = [
    'config',
    'DatabaseManager',
    'get_database_connection', 
    'SimpleSQLEngine',
    'create_sql_engine'
]

__version__ = '1.0.0'
__description__ = 'Simple SQL Query Engine for Local Operations'