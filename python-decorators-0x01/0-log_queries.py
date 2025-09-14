import sqlite3
import functools


""" YOUR CODE GOES HERE"""


# decorator to log SQL queries
def log_queries(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        #check if query is passed as a positional or keyboard argument
        if args:
            query = args[0]
        else:
            query = kwargs.get('query', '')
         # log the query
        print(f"[LOG] Executing SQL Query: {query}")
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
