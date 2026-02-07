# Gene SQL Query System

A simple, lightweight SQL query system that converts natural language to SQL queries and executes them against local MySQL databases using direct OpenAI API integration.

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   cd Gene
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Set OpenAI API Key**:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   ```

3. **Test Natural Language Query**:
   ```bash
   python simple_openai.py --nl "how many work orders are there by each org"
   ```

4. **Run Interactive Mode**:
   ```bash
   python main.py interactive
   ```

## 📁 Structure

```
Gene/
├── __init__.py              # Package initialization
├── config_local.py          # Local database configuration
├── database_local.py        # Local MySQL database operations
├── query_engine.py         # SQL query engine with OpenAI integration
├── main.py                 # Interactive CLI script
├── simple_openai.py        # Simplified test script
├── test.py                 # Test utilities
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## ✨ Features

- **Natural Language to SQL**: Ask questions in plain English using OpenAI's GPT models
- **Local MySQL Database**: Works with local MySQL database setup
- **Direct OpenAI Integration**: No external gateway dependencies
- **Simplified Configuration**: Easy setup with local database
- **Error Handling**: Graceful error handling and user feedback
- **AI-Powered**: Leverages GPT-4 for intelligent query generation

## 💻 Usage

### Simple Natural Language Query
```bash
# Test a natural language query with OpenAI
python simple_openai.py --nl "how many work orders are there by each org"
python simple_openai.py --nl "show me all users from California"
python simple_openai.py --nl "what is the average price by category"
```

### Interactive Mode
```bash
python main.py interactive
```

Commands in interactive mode:
- Type any question in natural language
- `tables` - List all tables
- `preview <table>` - Preview table data
- `sql <query>` - Execute direct SQL
- `quit` - Exit

### Programmatic Usage
```python
from Gene import create_openai_sql_engine

# Create OpenAI engine
engine = create_openai_sql_engine()

# Natural language query
results = engine.execute_natural_query("How many work orders are there?")
print(engine.format_results(results))
```

## 🧪 Testing with simple_openai.py

The simplified `simple_openai.py` script provides easy testing for natural language queries using direct OpenAI API.

### Prerequisites

1. **Database Connection**: Ensure your local MySQL database connection is configured in [`config_local.py`](config_local.py)
2. **OpenAI API Key**: Set your OpenAI API key in environment variables
3. **Local MySQL**: Have a local MySQL server running

### Usage Examples

**Natural Language Queries**:
```bash
python simple_openai.py --nl "how many work orders are there by each org"
python simple_openai.py --nl "show me all open work orders"
python simple_openai.py --nl "what is the total count by status"
```

### Command Line Options

- `--nl`: Execute a natural language query
- `--api-key`: Specify OpenAI API key (optional if set in environment)

### Example Output

```
🤖 Testing OpenAI natural language query...
   Natural language: 'how many work orders are there by each org'
Generated SQL: SELECT ORGID, COUNT(*) AS work_order_count FROM WORKORDER GROUP BY ORGID;
✅ OpenAI natural language query working!
   Result: 
ORGID           | work_order_count
----------------------------------
0               | 1
1223            | 1
2101            | 1212
...
Total rows: 79
```

## 🔧 Configuration

The system connects to a local MySQL database. Update your [`config_local.py`](config_local.py) with:
- Local database connection settings
- OpenAI API configuration

Example configuration:
```python
DB_HOST = "127.0.0.1"  # localhost
DB_USER = "newuser"     # Your database username
DB_PASSWORD = ""       # Your database password
DB_NAME = "dispatchwork"  # Your database name
```

## 📝 Example Queries

Natural language queries you can try:
- "How many work orders are there by each org?"
- "Show me all open work orders"
- "What is the total count by status?"
- "Which org has the most work orders?"
- "Show me work orders from the last 30 days"

## ⚙️ Requirements

- Python 3.7+
- mysql-connector-python
- requests
- python-dotenv
- OpenAI API key
- Local MySQL database

## 🛠️ Advanced Usage

### Without AI (SQL Only)
```python
# Create engine without AI functionality
engine = create_openai_sql_engine(use_ai=False)

# Only direct SQL works
results = engine.execute_sql_query("SELECT COUNT(*) FROM WORKORDER")
```

### Table Information
```python
# List all tables
tables = engine.list_tables()

# Preview table data
preview = engine.get_table_preview("WORKORDER", limit=10)
```

## 🔍 Troubleshooting

**Common Issues:**

1. **OpenAI API Error**: Check your OpenAI API key and ensure sufficient credits
2. **Database Connection Error**: Verify MySQL connection settings in [`config_local.py`](config_local.py)
3. **Import Errors**: Make sure you're in the Gene directory and have installed requirements
4. **Environment Variables**: Ensure OPENAI_API_KEY is properly set

**Debug Steps:**
1. Test database connection: `python main.py check`
2. Verify OpenAI API key is set
3. Check local MySQL server is running
4. Use verbose mode for detailed error information

## 📄 License

Same as the parent project.