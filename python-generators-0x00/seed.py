import mysql.connector
import os
import uuid
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from .env

def connect_db():
    """Connects to MySQL server (not a specific database)."""
    return mysql.connector.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        host=os.getenv('MYSQL_HOST', 'localhost'),
        unix_socket=os.getenv('MYSQL_SOCKET', '/opt/homebrew/var/mysql/mysql.sock')
    )

def create_database(connection):
    """Creates the ALX_prodev database if it does not exist."""
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
    cursor.close()

def connect_to_prodev():
    """Connects to the ALX_prodev database."""
    return mysql.connector.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        host=os.getenv('MYSQL_HOST', 'localhost'),
        unix_socket=os.getenv('MYSQL_SOCKET', '/opt/homebrew/var/mysql/mysql.sock'),
        database='ALX_prodev'
    )

def create_table(connection):
    """Creates the user_data table with user_id as UUID Primary Key and Indexed."""
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            user_id CHAR(36) PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            age INT,
            INDEX(user_id)
        )
    """)
    cursor.close()

def insert_data(connection, csv_path):
    """Inserts data from CSV into user_data table if email does not exist."""
    import csv
    cursor = connection.cursor()
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            if len(row) != 3:
                print(f"Skipping malformed row: {row}")
                continue
            name, email, age = row
            try:
                age_int = int(age)
            except ValueError:
                print(f"Skipping row with invalid age: {row}")
                continue
            cursor.execute("SELECT COUNT(*) FROM user_data WHERE email = %s", (email,))
            if cursor.fetchone()[0] == 0:
                user_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO user_data (user_id, name, email, age) VALUES (%s, %s, %s, %s)",
                    (user_id, name, email, age_int)
                )
    cursor.close()

if __name__ == "__main__":
    # Step 1: Connect to MySQL server and create database
    conn = connect_db()
    create_database(conn)
    conn.close()

    # Step 2: Connect to ALX_prodev and create table
    conn = connect_to_prodev()
    create_table(conn)

    # Step 3: Read CSV and insert data
    insert_data(conn, 'user_data.csv')

    conn.commit()
    conn.close()
