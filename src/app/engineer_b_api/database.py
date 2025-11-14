# src/engineer_b_api/database.py (stub)
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Заглушка для подключения к БД"""
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="crd12",
        user="crd_user",
        password="crd12"
    )
