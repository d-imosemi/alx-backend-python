import time
import sqlite3
import functools


query_cache = {}

#### with_db_connection decorator
def with_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect("users.db")
        try:
            return func(conn, *args, **kwargs)
        finally:
            conn.close()
    return wrapper


#### cache_query decorator
def cache_query(func):
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        query = kwargs.get("query") if "query" in kwargs else (args[0] if args else None)
        if query in query_cache:
            print(f"[CACHE HIT] Returning cached result for query: {query}")
            return query_cache[query]
        else:
            print(f"[CACHE MISS] Executing query: {query}")
            result = func(conn, *args, **kwargs)
            query_cache[query] = result
            return result
    return wrapper


@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")

#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")

print(users_again)
