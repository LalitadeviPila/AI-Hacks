#!/usr/bin/env python3
"""
OpenAI Gene SQL Query System - Main Script

Simple command-line interface for natural language SQL queries using direct OpenAI API.
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from query_engine_openai import create_openai_sql_engine
from database import DatabaseManager


def check_database_connection():
    """Check database connectivity."""
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


def check_openai_setup():
    """Check OpenAI API setup."""
    print("Checking OpenAI API setup...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY environment variable not set")
        print("💡 Set it with: set OPENAI_API_KEY=your_api_key")
        return False
    
    print("✅ OpenAI API key found")
    return True


def run_interactive_mode():
    """Run interactive query mode with OpenAI."""
    print("OpenAI Gene SQL Query System - Interactive Mode")
    print("=" * 60)
    print("Type your questions in natural language, or:")
    print("  'tables' - List all tables")
    print("  'preview <table>' - Show table preview") 
    print("  'sql <query>' - Execute SQL directly")
    print("  'quit' - Exit")
    print("-" * 60)
    
    # Check OpenAI setup
    if not check_openai_setup():
        print("❌ OpenAI setup incomplete. Exiting.")
        return
    
    # Create OpenAI SQL engine
    try:
        engine = create_openai_sql_engine()
        print("✅ OpenAI engine initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI engine: {e}")
        return
    
    while True:
        try:
            user_input = input("\n🤖 Ask me (OpenAI): ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == 'tables':
                # List tables
                results = engine.list_tables()
                if results.get("success"):
                    tables = results.get("data", [])
                    print(f"Available tables ({len(tables)}): {', '.join(tables)}")
                else:
                    print(f"Error listing tables: {results.get('error')}")
            
            elif user_input.lower().startswith('preview '):
                # Table preview
                table_name = user_input[8:].strip()
                results = engine.get_table_preview(table_name, limit=5)
                print(engine.format_results(results))
            
            elif user_input.lower().startswith('sql '):
                # Direct SQL query
                sql_query = user_input[4:].strip()
                results = engine.execute_sql_query(sql_query)
                print(engine.format_results(results))
            
            else:
                # Natural language query using OpenAI
                print("🔄 Processing with OpenAI...")
                results = engine.execute_natural_query(user_input, verbose=True)
                print(engine.format_results(results))
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_example_queries():
    """Run example queries using OpenAI."""
    print("Running Example Queries with OpenAI")
    print("=" * 50)
    
    # Check OpenAI setup
    if not check_openai_setup():
        print("❌ OpenAI setup incomplete. Exiting.")
        return
    
    try:
        engine = create_openai_sql_engine()
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI engine: {e}")
        return
    
    example_queries = [
        "How many work orders are there?",
        "Show me work orders grouped by org",
        "Which org has the most work orders?"
    ]
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n{i}. {query}")
        print("-" * 40)
        print("🔄 Processing with OpenAI...")
        results = engine.execute_natural_query(query, verbose=True)
        print(engine.format_results(results))
        
        if i < len(example_queries):
            input("\nPress Enter for next example...")


def show_help():
    """Show help information."""
    print("OpenAI Gene SQL Query System")
    print("=" * 40)
    print("Commands:")
    print("  python main_openai.py                  - Interactive mode")
    print("  python main_openai.py interactive      - Interactive mode")
    print("  python main_openai.py check           - Check database connection")
    print("  python main_openai.py examples        - Run example queries")
    print("  python main_openai.py help            - Show this help")
    print("")
    print("Requirements:")
    print("  - Set OPENAI_API_KEY environment variable")
    print("  - Configure database connection in config.py")
    print("")
    print("Example:")
    print("  set OPENAI_API_KEY=your_openai_api_key")
    print("  python main_openai.py interactive")


def main():
    """Main entry point."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ['interactive']
    
    if 'check' in args:
        check_database_connection()
    
    elif 'examples' in args:
        run_example_queries()
    
    elif 'interactive' in args:
        run_interactive_mode()
    
    elif 'help' in args:
        show_help()
    
    else:
        print("Unknown command. Use 'help' for usage information.")
        show_help()


if __name__ == "__main__":
    main()