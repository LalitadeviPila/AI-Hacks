#!/usr/bin/env python3
"""
Gene SQL Query System - Main Script

Simple command-line interface for natural language SQL queries.
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from query_engine import create_sql_engine
from database import DatabaseManager


def check_database_connection():
    print("Checking database connection...")
    
    try:
        db_manager = DatabaseManager()
        with db_manager:
            tables = db_manager.get_table_info()
            print(f"Connected to database successfully!")
            print(f"Found {len(tables)} tables: {', '.join(list(tables.keys())[:5])}{'...' if len(tables) > 5 else ''}")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def run_interactive_mode():
    """Run interactive query mode."""
    print("Gene SQL Query System - Interactive Mode")
    print("=" * 50)
    print("Type your questions in natural language, or:")
    print("  'tables' - List all tables")
    print("  'preview <table>' - Show table preview") 
    print("  'sql <query>' - Execute SQL directly")
    print("  'quit' - Exit")
    print("-" * 50)
    
    # Create SQL engine
    engine = create_sql_engine()
    
    while True:
        try:
            user_input = input("\nAsk me: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == 'tables':
                # List tables
                results = engine.list_tables()
                if results.get("success"):
                    print("\nAvailable Tables:")
                    for table, columns in results["tables"].items():
                        print(f"  {table}: {', '.join(columns)}")
                else:
                    print(f"Error: {results.get('error')}")
            
            elif user_input.lower().startswith('preview '):
                # Table preview
                table_name = user_input[8:].strip()
                if table_name:
                    results = engine.get_table_preview(table_name)
                    print(engine.format_results(results))
                else:
                    print("Please specify a table name: preview <table>")
            
            elif user_input.lower().startswith('sql '):
                # Direct SQL
                sql_query = user_input[4:].strip()
                if sql_query:
                    results = engine.execute_sql_query(sql_query)
                    print(engine.format_results(results))
                else:
                    print("Please provide a SQL query: sql <query>")
            
            else:
                # Natural language query
                print("Processing your query...")
                results = engine.execute_natural_query(user_input, verbose=True)
                print(engine.format_results(results))
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_example_queries():
    """Run some example queries to demonstrate functionality."""
    print("Running Example Queries")
    print("=" * 40)
    
    engine = create_sql_engine()
    
    example_queries = [
        "How many OPEN work ordeers are there?",
        "Show me orgs and their recent work orders",
        "Which org has the most work orders?"
    ]
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n{i}. {query}")
        print("-" * 30)
        results = engine.execute_natural_query(query, verbose=True)
        print(engine.format_results(results))
        
        if i < len(example_queries):
            input("\nPress Enter for next example...")



def main():
    """Main entry point."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ['interactive']
    
    if 'check' in args:
        check_database_connection()
    
    elif 'examples' in args:
        run_example_queries()
    
    elif 'interactive' in args:
        run_interactive_mode()
    
    else:
        print("Unknown command. Use 'help' for usage information.")


if __name__ == "__main__":
    main()