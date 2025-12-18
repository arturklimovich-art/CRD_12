DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5434,  # Default PostgreSQL port is 5432, check if this is correct
    'database': 'tradlab_db',  # Ensure this is the correct database name
    'user': 'tradlab',
    'password': 'crd12'
}

def get_connection_string():
    return f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
