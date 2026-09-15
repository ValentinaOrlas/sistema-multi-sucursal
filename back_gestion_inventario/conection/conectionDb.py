import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
from sqlalchemy.orm import sessionmaker

# Se obtiene la URL de conexión desde el entorno configurada en Docker
DATABASE_URL = os.getenv("DATABASE_URL")

# se crea el motor
engine = create_engine(DATABASE_URL)

# Cada petición HTTP abrirá una sesión independiente para hacer consultas
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Clase base de la cual heredarán todos los modelos (tablas)
Base = declarative_base()

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # cerrar la conexión