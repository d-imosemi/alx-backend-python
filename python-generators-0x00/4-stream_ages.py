seed = __import__('seed')

def stream_user_ages():
    """Generator function that yields user ages one by one."""
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
            cursor.execute("SELECT age FROM user_data;")
            for row in cursor:
                yield row[0]
            cursor.close()
            connection.close()

def average_user_age():
    """Calculates and returns the average age without loading the entire dataset into memory"""
    total_age = 0
    count = 0
    for age in stream_user_ages():
        total_age += age
        count += 1
    return total_age / count if count > 0 else 0
print(f"Average age of users: {average_user_age()}")
