import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pos_albercas.db")

productos = [
    ("Michelada", 65, "Bebidas"),
    ("Cerveza", 25, "Bebidas"),
    ("Hamburguesa sencilla con papas", 90, "Comida"),
    ("Pizza jumbo", 290, "Pizzas"),
    ("Entrada adulto", 50, "Extras"),
    ("Hielo", 30, "Extras"),
    ("Renta balón", 25, "Extras"),
    ("Inflable chico", 150, "Inflables")
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for p in productos:
    cursor.execute(
        "INSERT INTO productos (nombre, precio, categoria) VALUES (?, ?, ?)", p
    )

conn.commit()
conn.close()

print("Productos agregados.")
