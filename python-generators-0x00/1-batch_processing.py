seed = __import__('seed')

def stream_users_in_batches(batch_size):
    """Generator function that yields user data in batches from user_data table."""
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
            while True:
                batch = cursor.fetchmany(batch_size)
                if not batch:
                    break
                yield batch
            cursor.close()
            connection.close()

def batch_processing(batch_size):
    """processes each batch to filter users over the age of 25"""
    for batch in stream_users_in_batches(batch_size):
        for user in batch:
            if user[3] > 25:
                return(user)
