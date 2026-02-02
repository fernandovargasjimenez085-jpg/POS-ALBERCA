import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pos_albercas.db")

def crear_bd():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla de meseros
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meseros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
    """)

    # Tabla de productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL,
        categoria TEXT NOT NULL
    )
    """)

    # Tabla de comandas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comandas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_mesa TEXT NOT NULL,
        mesero TEXT NOT NULL,
        estado TEXT NOT NULL,
        total REAL DEFAULT 0
    )
    """)

    # Productos dentro de la comanda
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comanda_productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comanda_id INTEGER,
        producto TEXT,
        precio REAL,
        FOREIGN KEY (comanda_id) REFERENCES comandas(id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    crear_bd()
    print("Base de datos creada correctamente.")
