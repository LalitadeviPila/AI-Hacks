"""
OpenAI SQL Query Engine for Gene System

Converts natural language to SQL queries and executes them against MySQL database
using direct OpenAI API calls.
"""

import os
import sys
import json
import requests
from typing import Dict, Any, List, Optional
from config_local import LocalConfig
from database_local import LocalDatabaseManager


class OpenAISQLEngine:
    """SQL query engine that converts natural language to SQL using direct OpenAI API."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4", use_ai: bool = True):
        """
        Initialize the OpenAI SQL engine.
        
        Args:
            api_key (str): OpenAI API key. If None, will try to get from environment.
            model (str): OpenAI model to use (default: gpt-4).
            use_ai (bool): Whether to use AI for query generation.
        """
        self.db_manager = LocalDatabaseManager()
        self.use_ai = use_ai
        
        # Setup OpenAI configuration - prioritize config file over environment
        local_config = LocalConfig()
        
        # Priority: explicit parameter > config file > environment variable
        if api_key:
            self.api_key = api_key
        elif local_config.OPENAI_API_KEY:
            self.api_key = local_config.OPENAI_API_KEY
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')
            
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        if self.use_ai and not self.api_key:
            print("Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            self.use_ai = False
        
        # Get database schema for context
        self.schema_context = ""
        self._build_schema_context()
    
    def _build_schema_context(self) -> None:
        """Build schema context string for AI queries."""
        try:
            with self.db_manager:
                tables = self.db_manager.get_table_info()
                schema_parts = []
                for table_name, columns in tables.items():
                    column_info = [f"{col['name']} ({col['type']})" for col in columns]
                    schema_parts.append(f"Table {table_name}: {', '.join(column_info)}")
                
                self.schema_context = "Available tables and columns:\n" + "\n".join(schema_parts)
        except Exception as e:
            self.schema_context = f"Error loading schema: {e}"
    
    def _generate_sql_with_openai(self, natural_query: str) -> str:
        """
        Generate SQL using direct OpenAI API.
        
        Args:
            natural_query (str): Natural language query.
            
        Returns:
            str: Generated SQL query.
        """
        if not self.api_key:
            raise Exception("OpenAI API key not available")
        
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
        
        # Prepare request headers
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Prepare request data
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this to SQL: {natural_query}"}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        try:
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            response_data = response.json()
            
            # Extract SQL query
            sql_query = response_data['choices'][0]['message']['content'].strip()
            
            # Clean up the SQL query (remove code blocks if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.startswith('```'):
                sql_query = sql_query[3:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error calling OpenAI API: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected OpenAI API response format: {e}")
        except Exception as e:
            raise Exception(f"Error generating SQL with OpenAI: {e}")
    
    def execute_natural_query(self, natural_query: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Execute a natural language query by converting it to SQL first.
        
        Args:
            natural_query (str): Natural language query.
            verbose (bool): Whether to show generated SQL.
            
        Returns:
            Dict[str, Any]: Query results with metadata.
        """
        if not self.use_ai:
            return {
                "success": False,
                "error": "AI functionality not available. Use execute_sql_query() for direct SQL.",
                "data": None
            }
        
        try:
            # Generate SQL using OpenAI
            sql_query = self._generate_sql_with_openai(natural_query)
            
            if verbose:
                print(f"Generated SQL: {sql_query}")
            
            # Execute the generated SQL
            return self.execute_sql_query(sql_query, natural_query)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing natural language query: {e}",
                "data": None,
                "natural_query": natural_query
            }
    
    def execute_sql_query(self, sql_query: str, natural_query: str = None) -> Dict[str, Any]:
        """
        Execute a SQL query directly.
        
        Args:
            sql_query (str): SQL query to execute.
            natural_query (str): Original natural language query (optional).
            
        Returns:
            Dict[str, Any]: Query results with metadata.
        """
        try:
            with self.db_manager:
                results = self.db_manager.execute_query(sql_query)
                
                return {
                    "success": True,
                    "data": results,
                    "sql_query": sql_query,
                    "natural_query": natural_query,
                    "row_count": len(results) if results else 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Database error: {e}",
                "sql_query": sql_query,
                "natural_query": natural_query,
                "data": None
            }
    
    def get_table_preview(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Get a preview of table data."""
        sql_query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_sql_query(sql_query)
    
    def list_tables(self) -> Dict[str, Any]:
        """List all tables in the database."""
        try:
            with self.db_manager:
                tables = self.db_manager.get_table_info()
                return {
                    "success": True,
                    "data": list(tables.keys()),
                    "table_info": tables
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing tables: {e}",
                "data": None
            }
    
    def format_results(self, results: Dict[str, Any], max_rows: int = 20) -> str:
        """Format query results for display."""
        if not results.get("success"):
            return f"❌ Error: {results.get('error', 'Unknown error')}"
        
        data = results.get("data")
        if not data:
            return "No results found."
        
        # Show only first max_rows
        display_data = data[:max_rows] if len(data) > max_rows else data
        
        if not display_data:
            return "No results to display."
        
        # Get column names
        columns = list(display_data[0].keys())
        
        # Calculate column widths
        col_widths = {}
        for col in columns:
            col_widths[col] = max(len(str(col)), max(len(str(row.get(col, ''))) for row in display_data))
        
        # Format table
        lines = []
        
        # Header
        header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Data rows
        for row in display_data:
            row_str = " | ".join(str(row.get(col, '')).ljust(col_widths[col]) for col in columns)
            lines.append(row_str)
        
        result = "\n".join(lines)
        
        # Add summary
        total_rows = len(data)
        if total_rows > max_rows:
            result += f"\n\n... showing {max_rows} of {total_rows} rows"
        else:
            result += f"\n\nTotal rows: {total_rows}"
        
        return result


def create_openai_sql_engine(api_key: str = None, model: str = "gpt-4", use_ai: bool = True) -> OpenAISQLEngine:
    """
    Factory function to create an OpenAI SQL engine.
    
    Args:
        api_key (str): OpenAI API key. If None, will try to get from environment.
        model (str): OpenAI model to use (default: gpt-4).
        use_ai (bool): Whether to use AI for query generation.
        
    Returns:
        OpenAISQLEngine: Configured OpenAI SQL engine.
    """
    return OpenAISQLEngine(api_key=api_key, model=model, use_ai=use_ai)


# Example usage
if __name__ == "__main__":
    # Test the OpenAI engine
    engine = create_openai_sql_engine()
    
    # Test natural language query
    result = engine.execute_natural_query("How many work orders are there by each org?", verbose=True)
    print(engine.format_results(result))