#!/usr/bin/env python3
"""
Enhanced test script for Gene SQL Query System
Supports runtime queries via command line arguments
"""

import sys
import os
import argparse
import json
from typing import List, Optional

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from query_engine import create_sql_engine
from database import DatabaseManager


def test_database_connection():
    """Test database connection."""
    print("1. Testing database connection...")
    db_manager = DatabaseManager()
    with db_manager:
        tables = db_manager.get_table_info()
        print(f"✅ Connected! Found {len(tables)} tables")
    return True


def test_engine_creation():
    """Test SQL engine creation."""
    print("\n2. Creating SQL engine...")
    engine = create_sql_engine()
    print("✅ SQL engine created successfully")
    return engine


def test_table_listing(engine):
    """Test table listing functionality."""
    print("\n3. Testing table listing...")
    tables_result = engine.list_tables()
    tables_dict = {}
    if tables_result.get("success"):
        tables_dict = tables_result["tables"]
        print(f"✅ Engine found {len(tables_dict)} tables")
        
        # Show a sample table structure
        if tables_dict:
            sample_table = list(tables_dict.keys())[0]
            columns = tables_dict[sample_table]
            print(f"   Sample table '{sample_table}' has {len(columns)} columns")
    
    return tables_dict


def test_direct_sql_query(engine, sql_query: Optional[str] = None, tables_dict: dict = None):
    """Test direct SQL query execution."""
    print("\n4. Testing direct SQL query...")
    
    if sql_query:
        print(f"   Executing custom query: {sql_query}")
    else:
        # Use default query if no custom query provided
        if tables_dict:
            sample_table = list(tables_dict.keys())[0]
            sql_query = f"SELECT COUNT(*) as record_count FROM {sample_table}"
            print(f"   Executing default query: {sql_query}")
        else:
            print("❌ No query provided and no tables available for default query")
            return False
    
    try:
        sql_result = engine.execute_sql_query(sql_query)
        print(f"✅ SQL query executed successfully")
        print(f"   Result: {engine.format_results(sql_result)}")
        return True
    except Exception as e:
        print(f"❌ SQL query failed: {e}")
        return False


def test_natural_language_query(engine, nl_query: Optional[str] = None, tables_dict: dict = None):
    """Test natural language query execution."""
    print("\n5. Testing natural language query...")
    
    if nl_query:
        print(f"   Natural language: '{nl_query}'")
    else:
        # Use default query if no custom query provided
        available_tables = list(tables_dict.keys()) if tables_dict else []
        workorder_tables = [t for t in available_tables if 'WORKORDER' in t.upper()]
        
        if workorder_tables:
            nl_query = f"How many work orders in WORKORDER table per ORGID?"
        elif available_tables:
            nl_query = f"How many records are in the {available_tables[0]} table?"
        else:
            nl_query = "Show me all available tables"
        
        print(f"   Natural language (default): '{nl_query}'")
    
    try:
        nl_result = engine.execute_natural_query(nl_query, verbose=True)
        print("✅ Natural language query working!")
        print(f"   Result: {engine.format_results(nl_result)}")
        return True
    except Exception as e:
        print(f"⚠️ Natural language query failed: {e}")
        print("💡 This might be due to AI Gateway authentication")
        print("💡 Direct SQL queries still work fine!")
        return False


def run_interactive_query_test(engine):
    """Run interactive query testing mode."""
    print("\n🎮 Interactive Query Test Mode")
    print("=" * 40)
    print("Enter your queries (type 'quit' to exit)")
    print("Prefix with 'sql:' for direct SQL or 'nl:' for natural language")
    print("Examples:")
    print("  sql: SELECT COUNT(*) FROM WORKORDER")
    print("  nl: How many work orders are there?")
    print()
    
    while True:
        try:
            query = input("Query> ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Exiting interactive mode")
                break
            
            if not query:
                continue
            
            if query.lower().startswith('sql:'):
                sql_query = query[4:].strip()
                print(f"\n🔄 Executing SQL: {sql_query}")
                try:
                    result = engine.execute_sql_query(sql_query)
                    print(f"✅ Result: {engine.format_results(result)}")
                except Exception as e:
                    print(f"❌ SQL Error: {e}")
            
            elif query.lower().startswith('nl:'):
                nl_query = query[3:].strip()
                print(f"\n🔄 Executing NL: {nl_query}")
                try:
                    result = engine.execute_natural_query(nl_query, verbose=True)
                    print(f"✅ Result: {engine.format_results(result)}")
                except Exception as e:
                    print(f"❌ NL Error: {e}")
            
            else:
                # Auto-detect query type
                if query.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE')):
                    print(f"\n🔄 Auto-detected SQL: {query}")
                    try:
                        result = engine.execute_sql_query(query)
                        print(f"✅ Result: {engine.format_results(result)}")
                    except Exception as e:
                        print(f"❌ SQL Error: {e}")
                else:
                    print(f"\n🔄 Auto-detected NL: {query}")
                    try:
                        result = engine.execute_natural_query(query, verbose=True)
                        print(f"✅ Result: {engine.format_results(result)}")
                    except Exception as e:
                        print(f"❌ NL Error: {e}")
                        
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Exiting interactive mode")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


def run_batch_query_test(engine, queries: List[str]):
    """Run batch query testing."""
    print(f"\n📊 Batch Query Test - {len(queries)} queries")
    print("=" * 40)
    
    results = []
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}/{len(queries)} ---")
        
        try:
            # Auto-detect query type
            if query.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE')):
                print(f"SQL: {query}")
                result = engine.execute_sql_query(query)
                print(f"✅ Success: {engine.format_results(result)}")
                results.append({"query": query, "type": "sql", "success": True, "result": result})
            else:
                print(f"NL: {query}")
                result = engine.execute_natural_query(query, verbose=False)
                print(f"✅ Success: {engine.format_results(result)}")
                results.append({"query": query, "type": "nl", "success": True, "result": result})
                
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({"query": query, "type": "unknown", "success": False, "error": str(e)})
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n📈 Batch Results: {successful}/{len(queries)} successful")
    
    return results


def quick_test():
    """Quick test of the system with default queries."""
    print("🧪 Quick Test - Gene SQL Query System")
    print("=" * 40)
    
    try:
        # Test basic functionality
        test_database_connection()
        engine = test_engine_creation()
        tables_dict = test_table_listing(engine)
        test_direct_sql_query(engine, tables_dict=tables_dict)
        test_natural_language_query(engine, tables_dict=tables_dict)
        
        print("\n🎉 Basic functionality test completed successfully!")
        print("\n📝 Next steps:")
        print("   • Use 'python test.py --interactive' for interactive query testing")
        print("   • Use 'python test.py --sql \"YOUR_QUERY\"' for single SQL test")
        print("   • Use 'python test.py --nl \"YOUR_QUERY\"' for single NL test")
        print("   • Use 'python main.py interactive' for full interactive mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Check your database connection settings in config.py")
        print("   • Verify your network connection to the MySQL database")
        print("   • Make sure all required packages are installed")
        return False


def main():
    """Enhanced main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced Gene SQL Query System Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test.py                                    # Run quick test
  python test.py --sql "SELECT COUNT(*) FROM WORKORDER"  # Test SQL query
  python test.py --nl "How many work orders are there?"  # Test natural language
  python test.py --interactive                     # Interactive mode
  python test.py --batch "query1" "query2" "query3"     # Batch testing
  python test.py --file queries.txt                # Load queries from file
        """
    )
    
    parser.add_argument('--sql', type=str, help='Execute a direct SQL query')
    parser.add_argument('--nl', type=str, help='Execute a natural language query')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--batch', nargs='+', help='Run multiple queries in batch')
    parser.add_argument('--file', type=str, help='Load queries from file (one per line)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # If no arguments provided, run quick test
    if len(sys.argv) == 1:
        return quick_test()
    
    try:
        # Initialize engine
        engine = test_engine_creation()
        tables_dict = test_table_listing(engine) if args.verbose else {}
        
        # Handle different modes
        if args.interactive:
            run_interactive_query_test(engine)
        
        elif args.sql:
            test_direct_sql_query(engine, args.sql)
        
        elif args.nl:
            test_natural_language_query(engine, args.nl)
        
        elif args.batch:
            run_batch_query_test(engine, args.batch)
        
        elif args.file:
            if not os.path.exists(args.file):
                print(f"❌ File not found: {args.file}")
                return False
            
            with open(args.file, 'r', encoding='utf-8') as f:
                queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not queries:
                print(f"❌ No queries found in file: {args.file}")
                return False
            
            run_batch_query_test(engine, queries)
        
        else:
            print("❌ No valid option provided. Use --help for usage information.")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during enhanced test: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)