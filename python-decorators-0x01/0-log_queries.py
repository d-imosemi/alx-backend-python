import sqlite3
import functools
from datetime import datetime

#### decorator to log SQL queries
def log_queries(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract query argument from kwargs or args
        query = kwargs.get("query") if "query" in kwargs else (args[0] if args else None)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if query:
            print(f"[{timestamp}] Executing SQL Query: {query}")
        else:
            print(f"[{timestamp}] No SQL query found.")
        return func(*args, **kwargs)
    return wrapper


@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")
print(users)
