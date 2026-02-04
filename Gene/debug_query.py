#!/usr/bin/env python3
"""
Simple test script for specific natural language query
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from query_engine import create_sql_engine


def test_specific_query():
    """Test a specific natural language query to see detailed output."""
    print("🔍 Testing Specific Query")
    print("=" * 40)
    
    try:
        engine = create_sql_engine()
        
        # Test the specific query you're interested in
        query = "How many work orders in BACKOFFICEWORKORDERSYNCSTATUS table per ORGID?"
        print(f"Query: {query}")
        print("-" * 40)
        
        result = engine.execute_natural_query(query, verbose=True)
        
        print("\nFull Result Details:")
        print(f"Success: {result.get('success', 'Unknown')}")
        print(f"SQL Query: {result.get('sql_query', 'Not provided')}")
        print(f"Natural Query: {result.get('natural_query', 'Not provided')}")
        
        if 'results' in result:
            print(f"Results: {result['results']}")
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        
        print("\nFormatted Output:")
        print(engine.format_results(result))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_specific_query()