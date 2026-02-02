import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pos_albercas.db")

meseros = ["Fernando", "Sergio"]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for m in meseros:
    cursor.execute("INSERT INTO meseros (nombre) VALUES (?)", (m,))

conn.commit()
conn.close()

print("Meseros agregados.")
