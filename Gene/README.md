# Gene SQL Query System

A simple, lightweight SQL query system that converts natural language to SQL queries and executes them against MySQL databases using Deere AI Gateway.

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   cd Gene
   # Ensure you're using the project's virtual environment
   C:/Users/ABGNBXP/mywork/isg-pro-dispatch-support-tool-agent/.venv/Scripts/python.exe
   ```

2. **Test Natural Language Query**:
   ```bash
   python simple.py --nl "how many work orders are there by each org"
   ```

3. **Run Interactive Mode** (using main.py):
   ```bash
   python main.py interactive
   ```

## 📁 Structure

```
Gene/
├── __init__.py          # Package initialization
├── config.py            # Configuration and database settings
├── database.py          # MySQL database operations
├── query_engine.py      # SQL query engine with AI integration
├── main.py             # Full interactive script
├── simple.py           # Simplified test script (new)
└── README.md           # This file
```

## ✨ Features

- **Natural Language to SQL**: Ask questions in plain English using Deere AI Gateway
- **MySQL Database Integration**: Direct connection to remote MySQL database
- **Simplified Testing**: Easy-to-use command line interface
- **Error Handling**: Graceful error handling and user feedback
- **AI-Powered**: Leverages GPT-4 through Deere AI Gateway for query generation

## 💻 Usage

### Simple Natural Language Query
```bash
# Test a natural language query
python simple.py --nl "how many work orders are there by each org"
python simple.py --nl "show me all users from California"
python simple.py --nl "what is the average price by category"
```

### Interactive Mode (Full Features)
```bash
python main.py interactive
```

Commands in interactive mode:
- Type any question in natural language
- `quit` - Exit

### Programmatic Usage
```python
from Gene import create_sql_engine

# Create engine
engine = create_sql_engine()

# Natural language query
results = engine.execute_natural_query("How many work orders are there?")
print(engine.format_results(results))
```

## 🧪 Testing with simple.py

The simplified `simple.py` script provides easy testing for natural language queries.

### Prerequisites

1. **Database Connection**: Ensure your MySQL database connection is configured in [`config.py`](config/config.py)
2. **Environment Variables**: Set up Deere AI Gateway credentials
3. **Virtual Environment**: Use the project's virtual environment

### Usage Examples

**Natural Language Queries**:
```bash
python simple.py --nl "how many work orders are there by each org"
python simple.py --nl "show me all open work orders"
python simple.py --nl "what is the total count by status"
```

### Command Line Options

- `--nl`: Execute a natural language query

### Example Output

```
. Testing natural language query...
   Natural language: 'how many work orders are there by each org'
Generated SQL: SELECT ORGID, COUNT(*) AS work_order_count FROM WORKORDER GROUP BY ORGID;
✅ Natural language query working!
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

The system connects to a remote MySQL database. Ensure your [`config.py`](config/config.py) has:
- Database connection settings
- Deere AI Gateway configuration
- Authentication credentials

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
- Access to Deere AI Gateway
- MySQL database connection

## 🛠️ Advanced Usage

### Without AI (SQL Only)
```python
# Create engine without AI functionality
engine = create_sql_engine(use_ai=False)

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

1. **AI Gateway Error**: Check your Deere AI Gateway credentials and registration ID
2. **Database Connection Error**: Verify MySQL connection settings in [`config.py`](config/config.py)
3. **Import Errors**: Make sure you're in the Gene directory and using the correct virtual environment
4. **No AI Available**: Check auth_helper import and authentication setup

**Debug Steps:**
1. Test database connection first
2. Verify AI Gateway authentication
3. Check environment variables
4. Use verbose mode for detailed error information

## 📄 License

Same as the parent project.