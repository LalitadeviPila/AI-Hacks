"""
Gene Package Initialization

Simple SQL query system for local database operations.
"""

from config_local import LocalConfig, local_config
from database_local import LocalDatabaseManager
from query_engine import OpenAISQLEngine, create_openai_sql_engine

__all__ = [
    'LocalConfig',
    'local_config',
    'LocalDatabaseManager',
    'OpenAISQLEngine',
    'create_openai_sql_engine'
]

__version__ = '1.0.0'
__description__ = 'Simple SQL Query Engine for Local Operations'