import sqlite3


class DatabaseConnection:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            # If an exception happened, rollback
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()
        # Returning False means exceptions (if any) are not suppressed
        return False


#### Using the custom context manager
with DatabaseConnection("users.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    print(results)
