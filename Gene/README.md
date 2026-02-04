# Gene SQL Query System

A simple, lightweight SQL query system that converts natural language to SQL queries and executes them on local SQLite databases.

## 🚀 Quick Start

1. **Setup Database**:
   ```bash
   cd Gene
   python main.py setup
   ```

2. **Start Interactive Mode**:
   ```bash
   python main.py interactive
   ```

3. **Run Built-in Examples**:
   ```bash
   python main.py examples
   ```

## 📁 Structure

```
Gene/
├── __init__.py          # Package initialization
├── config.py            # Configuration and settings
├── database.py          # Database operations
├── query_engine.py      # SQL query engine
├── main.py             # Main interactive script with built-in examples
└── README.md           # This file
```

## ✨ Features

- **Natural Language to SQL**: Ask questions in plain English
- **Direct SQL Execution**: Run SQL queries directly when needed
- **Local SQLite Database**: No external database server required
- **Interactive Mode**: Command-line interface for real-time queries
- **Table Management**: Browse tables and preview data
- **Error Handling**: Graceful error handling and user feedback

## 💻 Usage

### Interactive Mode
```bash
python main.py interactive
```

Commands in interactive mode:
- Type any question in natural language
- `tables` - List all available tables
- `preview <table>` - Show preview of a table
- `sql <query>` - Execute SQL directly
- `quit` - Exit

### Programmatic Usage
```python
from Gene import create_sql_engine

# Create engine
engine = create_sql_engine()

# Natural language query
results = engine.execute_natural_query("How many users are there?")
print(engine.format_results(results))

# Direct SQL
results = engine.execute_sql_query("SELECT * FROM users LIMIT 5")
print(engine.format_results(results))
```

### Database Setup
```python
from Gene import DatabaseManager

# Setup database with sample data
db_manager = DatabaseManager()
db_manager.setup_database(with_sample_data=True)
```

## 📊 Sample Data

The system includes sample tables:
- **users**: User information (id, name, email, age, city, country)
- **products**: Product catalog (id, name, category, price, stock)
- **orders**: Order records (id, user_id, product_id, quantity, order_date)

## 🔧 Configuration

Edit `config.py` to customize:
- OpenAI API key and model
- Database file path
- Other settings

## 📝 Example Queries

Natural language queries you can try:
- "How many users are there?"
- "Show me users from USA"
- "What products are in Electronics category?"
- "Which user has the most orders?"
- "What's the average age of users by country?"

## ⚙️ Requirements

Minimal requirements:
- Python 3.7+
- sqlite3 (built-in)
- openai (for natural language queries)

Install OpenAI package:
```bash
pip install openai
```

## 🛠️ Advanced Usage

### Without AI (SQL Only)
```python
# Create engine without AI functionality
engine = create_sql_engine(use_ai=False)

# Only direct SQL works
results = engine.execute_sql_query("SELECT COUNT(*) FROM users")
```

### Custom Database
```python
# Use custom database file
engine = create_sql_engine(db_path="my_custom.db")
```

### Table Information
```python
# List all tables
tables = engine.list_tables()

# Preview table data
preview = engine.get_table_preview("users", limit=10)
```

## 🔍 Troubleshooting

**Common Issues:**

1. **OpenAI API Error**: Check your API key in `config.py`
2. **Database Not Found**: Run `python main.py setup` first
3. **Import Errors**: Make sure you're in the Gene directory
4. **No AI Available**: Install openai package or use `use_ai=False`

## 📄 License

Same as the parent project.