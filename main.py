from flask import Flask, request, redirect, jsonify
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pos_albercas.db")

app = Flask(__name__)

def obtener_meseros():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM meseros")
    meseros = cursor.fetchall()
    conn.close()
    return [m[0] for m in meseros]

def obtener_productos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, precio, categoria FROM productos")
    datos = cursor.fetchall()
    conn.close()

    productos = {}
    for p in datos:
        categoria = p[3]
        if categoria not in productos:
            productos[categoria] = []
        productos[categoria].append(p)

    return productos

def agregar_producto_a_comanda(comanda_id, producto_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT precio FROM productos WHERE id=?", (producto_id,))
    precio = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO comanda_detalle (comanda_id, producto_id, cantidad, subtotal)
        VALUES (?, ?, ?, ?)
    """, (comanda_id, producto_id, 1, precio))

    cursor.execute("""
        UPDATE comandas
        SET total = total + ?
        WHERE id = ?
    """, (precio, comanda_id))

    conn.commit()
    conn.close()

def obtener_detalle_comanda(comanda_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.id, p.nombre, d.cantidad, d.subtotal
        FROM comanda_detalle d
        JOIN productos p ON d.producto_id = p.id
        WHERE d.comanda_id = ?
    """, (comanda_id,))

    datos = cursor.fetchall()
    conn.close()
    return datos

def quitar_item(detalle_id, comanda_id, subtotal):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM comanda_detalle WHERE id=?", (detalle_id,))
    cursor.execute(
        "UPDATE comandas SET total = total - ? WHERE id=?",
        (subtotal, comanda_id)
    )

    conn.commit()
    conn.close()

def obtener_total_comanda(comanda_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT IFNULL(SUM(subtotal), 0)
        FROM comanda_detalle
        WHERE comanda_id = ?
    """, (comanda_id,))

    total = cursor.fetchone()[0]
    conn.close()

    return total


def obtener_categorias():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categoria FROM productos")
    cats = [c[0] for c in cursor.fetchall()]
    conn.close()
    return cats

@app.route("/")
def inicio():
    return """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
    font-family: Arial;
    background: #f2f2f2;
    display: flex;
    height: 100vh;
    justify-content: center;
    align-items: center;
    margin: 0;
}

.contenedor {
    text-align: center;
}

h1 {
    margin-bottom: 50px;
}

button {
    width: 280px;
    padding: 30px;
    font-size: 28px;
    margin: 20px;
    border: none;
    border-radius: 12px;
    color: white;
}

.mesero { background: #2196F3; }
.caja { background: #4CAF50; }
.productos { background: #FF9800; }
</style>
</head>

<body>
    <div class="contenedor">
        <h1>POS JARDIN DORY'S</h1>

        <a href="/mesero">
            <button class="mesero">SOY MESERO</button>
        </a><br>

        <a href="/caja">
            <button class="caja">CAJA</button>
        </a><br>

        <a href="/productos">
            <button class="productos">ADMIN PRODUCTOS</button>
        </a>
    </div>
</body>
</html>
"""


@app.route("/mesero")
def mesero():
    lista_meseros = obtener_meseros()
    botones = ""
    for m in lista_meseros:
        botones += f'<a href="/mesero/{m}"><button style="font-size:25px;margin:10px;">{m}</button></a><br>'
    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
    font-family: Arial;
    background: #f2f2f2;
    margin: 0;
    padding: 20px;
    text-align: center;
}}

h2 {{
    margin-bottom: 30px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}}

button {{
    padding: 30px;
    font-size: 26px;
    border: none;
    border-radius: 12px;
    background: #2196F3;
    color: white;
}}
</style>
</head>

<body>
    <h2>Selecciona tu nombre</h2>
    <div class="grid">
        {''.join([f"<a href='/mesero/{m}'><button>{m}</button></a>" for m in obtener_meseros()])}
    </div>
</body>
</html>
"""

@app.route("/mesero/<nombre>", methods=["GET", "POST"])
def pantalla_mesero(nombre):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == "POST":
        nombre_mesa = request.form["nombre_mesa"]

        cursor.execute("""
            INSERT INTO comandas (nombre_mesa, mesero, estado)
            VALUES (?, ?, 'abierta')
        """, (nombre_mesa, nombre))

        comanda_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return redirect(f"/comanda/{comanda_id}/{nombre}")

    cursor.execute("""
        SELECT id, nombre_mesa
        FROM comandas
        WHERE mesero = ? AND estado = 'abierta'
        ORDER BY id DESC
    """, (nombre,))
    comandas = cursor.fetchall()
    conn.close()

    lista = ""
    for c in comandas:
        lista += f'''
        <div class="comanda"
             onclick="window.location.href='/comanda/{c[0]}/{nombre}'">
            Mesa: <b>{c[1]}</b>
        </div>
        '''

    return f'''
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
    font-family: Arial;
    margin: 0;
    background: #f2f2f2;
}}

.top {{
    background: white;
    padding: 20px;
    font-size: 26px;
    text-align: center;
    border-bottom: 3px solid black;
}}

.lista {{
    padding: 20px;
}}

.comanda {{
    background: white;
    padding: 20px;
    margin-bottom: 10px;
    border-radius: 10px;
    font-size: 22px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}}

form {{
    padding: 20px;
    background: white;
    margin: 20px;
    border-radius: 10px;
}}

input {{
    width: 100%;
    padding: 15px;
    font-size: 22px;
    margin-bottom: 15px;
}}

.nueva {{
    width: 100%;
    background: #4CAF50;
    color: white;
    font-size: 26px;
    padding: 20px;
    border: none;
    border-radius: 10px;
}}
</style>
</head>

<body>

<div class="top">
    Mesero: <b>{nombre}</b>
</div>

<div class="lista">
    <h3>Comandas abiertas</h3>
    {lista}
</div>

<form method="POST">
    <input type="text" name="nombre_mesa" placeholder="Nombre de la nueva mesa" required>
    <button class="nueva" type="submit">+ NUEVA COMANDA</button>
</form>

</body>
</html>
'''

@app.route("/comanda/<int:comanda_id>/<nombre>")
def ver_comanda(comanda_id, nombre):
    productos = obtener_productos()
    total = obtener_total_comanda(comanda_id)
    detalle = obtener_detalle_comanda(comanda_id)

    # ---------- Categorías ----------
    tabs = ""
    bloques = ""

    for cat, lista in productos.items():
        tabs += f"<button onclick=\"mostrarCategoria('{cat}')\">{cat}</button>"

        botones = ""
        for p in lista:
            botones += f"""
            <button class="producto" onclick="agregarProducto({p[0]})">
                {p[1]}<br>${p[2]}
            </button>
            """

        bloques += f"""
        <div class="productos" id="cat_{cat}">
            {botones}
        </div>
        """

    # ---------- Lista de productos agregados ----------
    lista_html = ""
    for item in detalle:
        # item = (detalle_id, nombre, cantidad, subtotal)
        lista_html += f"""
        <div onclick="quitarProducto({item[0]})"
             style="padding:8px; border-bottom:1px solid #ccc;">
            {item[2]} x {item[1]} ❌
        </div>
        """

    primera_cat = list(productos.keys())[0]

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
    font-family: Arial;
    margin: 0;
    background: #f2f2f2;
}}

.top {{
    position: sticky;
    top: 0;
    background: white;
    padding: 10px;
    border-bottom: 3px solid black;
    text-align: center;
}}

.total {{
    font-size: 34px;
    font-weight: bold;
    color: green;
}}

.lista {{
    background: white;
    padding: 10px;
    height: 130px;
    overflow-y: auto;
    border-bottom: 3px solid black;
}}

.categorias {{
    display: flex;
    background: #222;
}}

.categorias button {{
    flex: 1;
    padding: 15px;
    font-size: 18px;
    border: none;
    background: #333;
    color: white;
}}

.productos {{
    display: none;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    padding: 10px;
}}

.producto {{
    padding: 20px;
    font-size: 18px;
    border: none;
    border-radius: 10px;
    background: #2196F3;
    color: white;
}}

.acciones {{
    position: sticky;
    bottom: 0;
    display: flex;
}}

.acciones button {{
    flex: 1;
    font-size: 22px;
    padding: 15px;
    border: none;
    color: white;
}}

.ver {{ background: orange; }}
.cerrar {{ background: red; }}
</style>
</head>

<body>

<div class="top">
    Mesa: {nombre}<br>
    <div class="total">$ <span id="total">{total}</span></div>
</div>

<div class="lista" id="lista">
    {lista_html}
</div>

<div class="categorias">
    {tabs}
</div>

{bloques}

<div class="acciones">
    <button class="ver"
        onclick="window.location.href='/ticket/{comanda_id}'">
        VER CUENTA
    </button>
    <button class="cerrar"
        onclick="window.location.href='/cerrar/{comanda_id}/{nombre}'">
        CERRAR
    </button>
</div>

<script>
function agregarProducto(producto_id) {{
    fetch("/api/agregar_producto", {{
        method: "POST",
        headers: {{
            "Content-Type": "application/x-www-form-urlencoded"
        }},
        body: `comanda_id={comanda_id}&producto_id=${{producto_id}}`
    }})
    .then(res => res.json())
    .then(data => {{
        actualizarVista(data);
    }});
}}

function quitarProducto(detalle_id) {{
    fetch("/api/quitar_producto", {{
        method: "POST",
        headers: {{
            "Content-Type": "application/x-www-form-urlencoded"
        }},
        body: `detalle_id=${{detalle_id}}`
    }})
    .then(res => res.json())
    .then(data => {{
        actualizarVista(data);
    }});
}}

function actualizarVista(data) {{
    document.getElementById("total").innerText = data.total;

    let lista = "";
    data.detalle.forEach(item => {{
        lista += `<div onclick="quitarProducto(${{item[0]}})"
                     style="padding:8px;border-bottom:1px solid #ccc;">
                     ${{item[2]}} x ${{item[1]}} ❌
                  </div>`;
    }});
    document.getElementById("lista").innerHTML = lista;
}}

function mostrarCategoria(cat) {{
    document.querySelectorAll('.productos').forEach(p => p.style.display = 'none');
    document.getElementById('cat_' + cat).style.display = 'grid';
}}

mostrarCategoria("{primera_cat}");
</script>

</body>
</html>
"""




@app.route("/cerrar/<int:comanda_id>/<nombre>")
def cerrar_comanda(comanda_id, nombre):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE comandas SET estado='cerrada' WHERE id=?", (comanda_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/caja")
def caja():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_mesa FROM comandas WHERE estado='abierta'")
    comandas = cursor.fetchall()
    conn.close()

    filas = ""
    for c in comandas:
        total = obtener_total_comanda(c[0])
        filas += f"""
        <div>
            <b>{c[1]}</b> - ${total}
            <button onclick="window.location.href='/ticket/{c[0]}'">VER</button>
            <button onclick="window.location.href='/cerrar/{c[0]}/CAJA'">CERRAR</button>
        </div>
        """

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
    font-family: Arial;
    background: #f2f2f2;
    margin: 0;
    padding: 20px;
}}

h1 {{
    text-align: center;
    margin-bottom: 30px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
}}

.card {{
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.2);
    text-align: center;
}}

.mesa {{
    font-size: 24px;
    margin-bottom: 10px;
}}

.total {{
    font-size: 20px;
    margin-bottom: 15px;
    color: green;
}}

button {{
    width: 45%;
    padding: 15px;
    font-size: 18px;
    border: none;
    border-radius: 8px;
    margin: 5px;
    color: white;
}}

.ver {{ background: #2196F3; }}
.cerrar {{ background: #f44336; }}
</style>
</head>

<body>

<h1>COMANDAS ABIERTAS</h1>

<div class="grid">
    {''.join([f"""
        <div class='card'>
            <div class='mesa'>{c[1]}</div>
            <div class='total'>Total: ${obtener_total_comanda(c[0])}</div>
            <button class='ver' onclick="location.href='/ticket/{c[0]}'">VER</button>
            <button class='cerrar' onclick="location.href='/cerrar/{c[0]}/CAJA'">CERRAR</button>
        </div>
    """ for c in comandas])}
</div>

</body>
</html>
"""
@app.route("/productos", methods=["GET", "POST"])
def productos_admin():
    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        categoria = request.form["categoria"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO productos (nombre, precio, categoria)
            VALUES (?, ?, ?)
        """, (nombre, precio, categoria))
        conn.commit()
        conn.close()

        return redirect("/productos")

    categorias = obtener_categorias()

    opciones = ""
    for c in categorias:
        opciones += f"<option value='{c}'>{c}</option>"

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body {{
        font-family: Arial;
        background: #f2f2f2;
        padding: 20px;
    }}
    input, select {{
        width: 100%;
        padding: 15px;
        font-size: 18px;
        margin-bottom: 15px;
    }}
    button {{
        width: 100%;
        padding: 15px;
        font-size: 20px;
        background: #2196F3;
        color: white;
        border: none;
        border-radius: 10px;
    }}
    </style>
    </head>
    <body>

    <h2>Agregar Producto</h2>

    <form method="POST">
        <input type="text" name="nombre" placeholder="Nombre del producto" required>
        <input type="number" step="0.01" name="precio" placeholder="Precio" required>
        <select name="categoria">
            {opciones}
        </select>
        <button type="submit">Guardar Producto</button>
    </form>

    </body>
    </html>
    """


@app.route("/api/agregar_producto", methods=["POST"])
def api_agregar_producto():
    comanda_id = request.form["comanda_id"]
    producto_id = request.form["producto_id"]

    agregar_producto_a_comanda(comanda_id, producto_id)

    total = obtener_total_comanda(comanda_id)
    detalle = obtener_detalle_comanda(comanda_id)

    return jsonify({
        "total": total,
        "detalle": detalle
    })

@app.route("/api/quitar_producto", methods=["POST"])
def api_quitar_producto():
    detalle_id = request.form["detalle_id"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener datos del item
    cursor.execute("""
        SELECT comanda_id, producto_id, cantidad
        FROM comanda_detalle
        WHERE id = ?
    """, (detalle_id,))
    comanda_id, producto_id, cantidad = cursor.fetchone()

    # Obtener precio
    cursor.execute("SELECT precio FROM productos WHERE id=?", (producto_id,))
    precio = cursor.fetchone()[0]

    if cantidad > 1:
        cursor.execute("""
            UPDATE comanda_detalle
            SET cantidad = cantidad - 1,
                subtotal = subtotal - ?
            WHERE id = ?
        """, (precio, detalle_id))
    else:
        cursor.execute("DELETE FROM comanda_detalle WHERE id=?", (detalle_id,))

    conn.commit()
    conn.close()

    total = obtener_total_comanda(comanda_id)
    detalle = obtener_detalle_comanda(comanda_id)

    return jsonify({
        "total": total,
        "detalle": detalle
    })

@app.route("/ticket/<int:comanda_id>")
def ticket(comanda_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre_mesa, mesero
        FROM comandas
        WHERE id=?
    """, (comanda_id,))
    mesa, mesero = cursor.fetchone()

    cursor.execute("""
        SELECT productos.nombre, comanda_detalle.cantidad, productos.precio
        FROM comanda_detalle
        JOIN productos ON productos.id = comanda_detalle.producto_id
        WHERE comanda_detalle.comanda_id = ?
    """, (comanda_id,))
    items = cursor.fetchall()

    conn.close()

    lineas = ""
    total = 0

    for nombre, cantidad, precio in items:
        subtotal = cantidad * precio
        total += subtotal
        lineas += f"""
        <div class="linea">
            <span>{cantidad} x {nombre}</span>
            <span>${subtotal}</span>
        </div>
        """

    return f"""
<html>
<head>
<style>
body {{
    font-family: monospace;
    width: 280px;
}}

.linea {{
    display: flex;
    justify-content: space-between;
}}

.total {{
    border-top: 1px dashed black;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    font-size: 18px;
}}

@media print {{
    button {{ display: none; }}
}}
</style>
</head>

<body onload="window.print()">

<h3>JARDIN DORY'S</h3>
Mesa: {mesa}<br>
Mesero: {mesero}
<hr>

{lineas}

<div class="total">
TOTAL: ${total}
</div>

<br><br>
<button onclick="window.print()">Imprimir</button>

</body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True)
