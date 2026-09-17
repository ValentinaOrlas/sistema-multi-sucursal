import os
import psycopg
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

def obtener_conexion():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

# Decorador que maneja la conexión y el cursor automáticamente
def con_cursor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with obtener_conexion() as conn:
            with conn.cursor() as cur:
                # Le pasa el 'cur' a la función del repositorio como primer argumento extra
                return func(cur, *args, **kwargs)
    return wrapper