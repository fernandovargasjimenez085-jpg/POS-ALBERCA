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
    ("Inflable chico", 150, "Juguetes"),
    ("Pizza mediana", 160, "Pizzas"),
    ("Pizza personal", 100, "Pizzas"),
    ("Hot dog", 40, "Comida"),
    ("Sincronizadas", 45, "Comida"),
    ("Hamburguesa sencilla sin papas", 60, "Comida"),
    ("Hamburguesa hawaiana con papas", 110, "Comida"),
    ("Hamburguesa hawaiana sin papas", 70, "Comida"),
    ("Piña colada", 55, "Bebidas"),
    ("Frappé moka", 55, "Bebidas"),
    ("Frappé Oreo", 55, "Bebidas"),
    ("Orden picadas (frijol)", 40, "Comida"),
    ("Orden picadas (guiso)", 60, "Comida"),
    ("Orden quesadillas", 30, "Comida"),
    ("Orden pescadillas", 70, "Comida"),
    ("Orden papas a la francesa", 50, "Comida"),
    ("Orden nuggets", 65, "Comida"),
    ("Pechuga asada", 125, "Comida"),
    ("Caldo de camarón", 150, "Comida"),
    ("Camarón a la diabla", 150, "Comida"),
    ("Camarón al mojo de ajo", 150, "Comida"),
    ("Refresco 500ML", 25, "Bebidas"),
    ("Refresco 600ML", 30, "Bebidas"),
    ("Agua de sabor 500ML", 20, "Bebidas"),
    ("Agua de sabor 1L", 40, "Bebidas"),
    ("Agua natural 500ML", 10, "Bebidas"),
    ("Agua natural 1L", 15, "Bebidas"),
    ("Mango spicy", 65, "Bebidas")
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
