seed = __import__('seed')

def stream_users():
    """Generator function that yields user data row by row from user_data table."""
    connection = seed.connect_db()
    if connection:
        seed.create_database(connection)
        connection.close()
        print(f"connection successful")

        connection = seed.connect_to_prodev()

        if connection:
            seed.create_table(connection)
            seed.insert_data(connection, 'user_data.csv')
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM user_data;")
            for row in cursor:
                yield row
            cursor.close()
            connection.close()

# Expose the generator function for import
__all__ = ['stream_users']
