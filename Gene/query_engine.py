"""
Simple SQL Query Engine for Gene System

Converts natural language to SQL queries and executes them against MySQL database
using Deere AI Gateway for OpenAI API calls.
"""

import requests
from typing import Dict, Any, List, Optional
from config import config
from database import DatabaseManager

# Import auth helper for Deere AI Gateway
try:
    import sys
    import os
    app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app')
    sys.path.insert(0, app_dir)
    from helpers.auth_helper import get_access_token
    AI_AVAILABLE = True
except ImportError:
    print("Warning: Could not import auth_helper. AI functionality will not work.")
    get_access_token = None
    AI_AVAILABLE = False


class SimpleSQLEngine:
    """Simple SQL query engine that converts natural language to SQL using Deere AI Gateway."""
    
    def __init__(self, use_ai: bool = True):
        """
        Initialize the SQL engine.
        
        Args:
            use_ai (bool): Whether to use AI for query generation.
        """
        self.db_manager = DatabaseManager()
        self.use_ai = use_ai and AI_AVAILABLE
        
        # Get database schema for context
        self.schema_context = ""
        self._build_schema_context()
    
    def _build_schema_context(self) -> None:
        """Build schema context string for AI queries."""
        try:
            with self.db_manager:
                table_info = self.db_manager.get_table_info()
                
                schema_parts = ["Database Schema:"]
                for table, columns in table_info.items():
                    schema_parts.append(f"\nTable: {table}")
                    schema_parts.append(f"Columns: {', '.join(columns)}")
                
                self.schema_context = "\n".join(schema_parts)
                
        except Exception as e:
            print(f"Warning: Could not build schema context: {e}")
            self.schema_context = "No schema information available."
    
    def _generate_sql_with_ai(self, natural_query: str) -> str:
        """
        Generate SQL using Deere AI Gateway.
        
        Args:
            natural_query (str): Natural language query.
            
        Returns:
            str: Generated SQL query.
        """
        if not get_access_token:
            raise RuntimeError("Deere AI Gateway not available. Check auth_helper import.")
        
        # Check if registration ID is available
        if not config.REGISTRATION_ID:
            raise RuntimeError(
                "AI_GATEWAY_CLIENT_REGISTRATION environment variable not set. "
                "Please set this environment variable with your registration ID, "
                "or add it directly to config.py: self.REGISTRATION_ID = 'your-registration-id'"
            )
        
        # Get access token
        try:
            access_token = get_access_token()
        except Exception as e:
            raise RuntimeError(f"Failed to get access token: {e}")
        
        # Prepare system prompt
        system_prompt = f"""You are a MySQL expert. Convert natural language queries to SQL.

{self.schema_context}

Rules:
1. Return ONLY the SQL query, no explanations
2. Use proper MySQL syntax
3. Table and column names are case sensitive
4. If the query is unclear, make reasonable assumptions based on the schema
5. For aggregations, include appropriate GROUP BY clauses
6. Use JOIN when querying multiple tables
7. Use LIMIT for large result sets when appropriate

Example:
Natural: "How many users are there?"
SQL: SELECT COUNT(*) as user_count FROM users
"""
        
        # Prepare request data
        headers = config.get_ai_headers(access_token)
        data = {
            "model": config.LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": natural_query}
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        try:
            response = requests.post(config.AI_GATEWAY_URL, headers=headers, json=data)
            
            # Print detailed error info for debugging
            if response.status_code != 200:
                print(f"❌ AI Gateway Error:")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                print(f"   Headers sent: {headers}")
                print(f"   Data sent: {data}")
            
            response.raise_for_status()
            
            ai_response = response.json()["choices"][0]["message"]["content"]
            
            # Clean up the response (remove any markdown formatting)
            sql_query = ai_response.strip()
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except requests.RequestException as e:
            raise RuntimeError(f"Error calling Deere AI Gateway: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Invalid response from AI Gateway: {e}")
    
    def execute_natural_query(self, natural_query: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Execute a natural language query.
        
        Args:
            natural_query (str): Natural language query.
            verbose (bool): Whether to show generated SQL.
            
        Returns:
            Dict[str, Any]: Query results with metadata.
        """
        if self.use_ai:
            # Generate SQL using AI
            try:
                sql_query = self._generate_sql_with_ai(natural_query)
                if verbose:
                    print(f"Generated SQL: {sql_query}")
                
                return self.execute_sql_query(sql_query, natural_query)
                
            except Exception as e:
                return {
                    "error": f"Failed to generate/execute SQL: {e}",
                    "natural_query": natural_query
                }
        else:
            return {
                "error": "AI functionality not available. Use execute_sql_query() directly.",
                "natural_query": natural_query
            }
    
    def execute_sql_query(self, sql_query: str, natural_query: str = None) -> Dict[str, Any]:
        """
        Execute a SQL query directly.
        
        Args:
            sql_query (str): SQL query to execute.
            natural_query (str, optional): Original natural language query.
            
        Returns:
            Dict[str, Any]: Query results with metadata.
        """
        try:
            with self.db_manager:
                results = self.db_manager.execute_query(sql_query)
                
                response = {
                    "success": True,
                    "sql_query": sql_query,
                    "results": results
                }
                
                if natural_query:
                    response["natural_query"] = natural_query
                
                return response
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql_query": sql_query,
                "natural_query": natural_query
            }
    
    def get_table_preview(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get a preview of table data.
        
        Args:
            table_name (str): Name of the table.
            limit (int): Number of rows to return.
            
        Returns:
            Dict[str, Any]: Table preview results.
        """
        sql_query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_sql_query(sql_query, f"Preview of {table_name} table")
    
    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the database.
        
        Returns:
            Dict[str, Any]: List of tables with their information.
        """
        try:
            with self.db_manager:
                table_info = self.db_manager.get_table_info()
                return {
                    "success": True,
                    "tables": table_info
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_results(self, results: Dict[str, Any], max_rows: int = 20) -> str:
        """
        Format query results for display.
        
        Args:
            results (Dict[str, Any]): Query results.
            max_rows (int): Maximum rows to display.
            
        Returns:
            str: Formatted results string.
        """
        if not results.get("success", True):
            return f"❌ Error: {results.get('error', 'Unknown error')}"
        
        query_results = results.get("results", {})
        
        if "columns" in query_results and "data" in query_results:
            # SELECT query results
            columns = query_results["columns"]
            data = query_results["data"]
            
            if not data:
                return "No results found."
            
            # Create formatted table
            lines = []
            lines.append("📊 Query Results:")
            lines.append("-" * 50)
            
            # Header
            header = " | ".join(f"{col:<15}" for col in columns)
            lines.append(header)
            lines.append("-" * len(header))
            
            # Data rows (limit display)
            display_data = data[:max_rows]
            for row in display_data:
                row_str = " | ".join(f"{str(val):<15}" for val in row)
                lines.append(row_str)
            
            if len(data) > max_rows:
                lines.append(f"... and {len(data) - max_rows} more rows")
            
            lines.append(f"\nTotal rows: {len(data)}")
            
        elif "affected_rows" in query_results:
            # Non-SELECT query results
            lines = [
                "✅ Query executed successfully",
                f"Affected rows: {query_results['affected_rows']}"
            ]
        else:
            lines = ["✅ Query executed successfully"]
        
        return "\n".join(lines)


def create_sql_engine(use_ai: bool = True) -> SimpleSQLEngine:
    """
    Factory function to create a SQL engine.
    
    Args:
        use_ai (bool): Whether to use AI for query generation.
        
    Returns:
        SimpleSQLEngine: Configured SQL engine.
    """
    return SimpleSQLEngine(use_ai=use_ai)