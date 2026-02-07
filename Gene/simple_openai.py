#!/usr/bin/env python3
"""
Test script for OpenAI SQL Query Engine
Supports runtime queries via command line arguments using direct OpenAI API
"""

import sys
import os
import argparse
import json
from typing import List, Optional

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from query_engine import create_openai_sql_engine


def test_openai_natural_language_query(engine, nl_query: Optional[str] = None):
    """Test natural language query execution with OpenAI."""
    print("\nTesting OpenAI natural language query...")
    
    if nl_query:
        print(f"   Natural language: '{nl_query}'")
    
    try:
        nl_result = engine.execute_natural_query(nl_query, verbose=True)
        print("OpenAI natural language query working!")
        print(f"   Result: {engine.format_results(nl_result)}")
        return True
    except Exception as e:
        print(f"OpenAI natural language query failed: {e}")
        print("Make sure you have set OPENAI_API_KEY environment variable")
        print("Or ensure you have sufficient OpenAI API credits")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="OpenAI SQL Query Engine Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python simple_openai.py --nl "How many work orders are there?"
    python simple_openai.py --nl "Show me work orders by org"
    python simple_openai.py --api-key YOUR_KEY --nl "Count all users"
    
Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key
        """
    )
    
    parser.add_argument('--nl', type=str, help='Execute a natural language query')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (optional if set in environment)')
    parser.add_argument('--model', type=str, default='gpt-4', 
                       help='OpenAI model to use (default: gpt-4, alternatives: gpt-3.5-turbo)')
    
    args = parser.parse_args()
    
    if not args.nl:
        print("Please provide a natural language query with --nl")
        parser.print_help()
        return False
    
    try:
        # Initialize OpenAI engine
        print(f"Initializing OpenAI engine with model: {args.model}")
        engine = create_openai_sql_engine(
            api_key=args.api_key,
            model=args.model,
            use_ai=True
        )
        
        # Test natural language query
        success = test_openai_natural_language_query(engine, args.nl)
        return success
        
    except Exception as e:
        print(f"Error during OpenAI test: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)