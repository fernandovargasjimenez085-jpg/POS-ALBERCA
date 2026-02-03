from flask import Flask, request, redirect, jsonify
import sqlite3
import os
from flask import session, flash, redirect, url_for

# Contraseña fija para admin (cámbiala por la que quieras usar)
ADMIN_PASSWORD = "2706"  # ← cámbiala a algo más seguro en producción

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pos_albercas.db")

app = Flask(__name__)

app.secret_key = "albercas-dory-pos-clave-secreta-987654321-cambia-esto"

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

def agregar_producto_a_comanda(comanda_id, producto_id, cantidad=1):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si ya existe el producto en la comanda
    cursor.execute("""
        SELECT id, cantidad, subtotal 
        FROM comanda_detalle 
        WHERE comanda_id = ? AND producto_id = ?
    """, (comanda_id, producto_id))
    existente = cursor.fetchone()

    cursor.execute("SELECT precio FROM productos WHERE id=?", (producto_id,))
    precio = cursor.fetchone()[0]

    if existente:
        detalle_id, cant_actual, subtotal_actual = existente
        nueva_cant = cant_actual + cantidad
        nuevo_subtotal = nueva_cant * precio
        cursor.execute("""
            UPDATE comanda_detalle 
            SET cantidad = ?, subtotal = ? 
            WHERE id = ?
        """, (nueva_cant, nuevo_subtotal, detalle_id))
    else:
        cursor.execute("""
            INSERT INTO comanda_detalle (comanda_id, producto_id, cantidad, subtotal)
            VALUES (?, ?, ?, ?)
        """, (comanda_id, producto_id, cantidad, precio * cantidad))

    # Actualizar total de la comanda
    cursor.execute("""
        UPDATE comandas
        SET total = (SELECT IFNULL(SUM(subtotal), 0) FROM comanda_detalle WHERE comanda_id = ?)
        WHERE id = ?
    """, (comanda_id, comanda_id))

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
    return datos  # Debe retornar algo como: [(5, 'Cerveza', 2, 80.0), ...]

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

def obtener_todos_productos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, precio, categoria FROM productos ORDER BY categoria, nombre")
    productos = cursor.fetchall()
    conn.close()
    return productos

def eliminar_producto(producto_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()
    
@app.route("/")
def inicio():
    return """
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {
            --primary: #00b4d8;
            --primary-dark: #0096c7;
            --accent: #ff9e00;
            --success: #06d6a0;
            --dark: #2d3436;
            --light: #f8f9fa;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--dark);
        }
        .logo {
            font-size: 3.5rem;
            font-weight: 700;
            color: white;
            text-shadow: 0 4px 10px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            text-align: center;
        }
        .subtitle {
            font-size: 1.3rem;
            color: rgba(255,255,255,0.9);
            margin-bottom: 60px;
            text-align: center;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            width: 90%;
            max-width: 900px;
            padding: 0 20px;
        }
        .option-card {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 35px 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            color: var(--dark);
        }
        .option-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,180,216,0.3);
        }
        .icon {
            font-size: 3.5rem;
            margin-bottom: 20px;
            color: var(--primary);
        }
        .title {
            font-size: 1.6rem;
            font-weight: 600;
        }
    </style>
</head>
<body>

<div class="logo">JARDÍN DORY'S</div>
<div class="subtitle">Bienvenido al punto de venta</div>

<div class="grid">
    <a href="/mesero" class="option-card">
        <div class="icon"><i class="fas fa-user-tie"></i></div>
        <div class="title">Soy Mesero</div>
    </a>

    <a href="/caja" class="option-card">
        <div class="icon"><i class="fas fa-cash-register"></i></div>
        <div class="title">Caja</div>
    </a>

    <a href="/productos" class="option-card">
        <div class="icon"><i class="fas fa-boxes"></i></div>
        <div class="title">Admin Productos</div>
    </a>
</div>

</body>
</html>
"""


@app.route("/mesero")
def mesero():
    lista_meseros = obtener_meseros()
    
    if not lista_meseros:
        contenido = '''
        <div style="text-align:center; padding:60px 20px; color:#636e72; font-size:1.3rem;">
            <i class="fas fa-users-slash fa-3x" style="color:#ff9e00; margin-bottom:20px;"></i><br>
            No hay meseros registrados aún
        </div>
        '''
    else:
        tarjetas = ""
        for m in lista_meseros:
            inicial = m[0].upper() if m else "?"
            tarjetas += f'''
            <a href="/mesero/{m}" style="text-decoration:none;">
                <div class="mesero-card">
                    <div class="avatar">{inicial}</div>
                    <div class="nombre">{m}</div>
                </div>
            </a>
            '''
        contenido = f'<div class="grid">{tarjetas}</div>'

    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {{
            --primary: #00b4d8;
            --primary-dark: #0096c7;
            --accent: #ff9e00;
            --light: #f8f9fa;
            --dark: #2d3436;
            --gray: #636e72;
        }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #e0f7fa 0%, #f0f8ff 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            color: var(--dark);
        }}
        .atras {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 16px;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,180,216,0.3);
        }}
        h2 {{
            text-align: center;
            margin: 60px 0 40px;
            font-size: 2rem;
            color: var(--primary-dark);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        .mesero-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .mesero-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 30px rgba(0,180,216,0.2);
        }}
        .avatar {{
            width: 80px;
            height: 80px;
            background: var(--primary);
            color: white;
            font-size: 2.2rem;
            font-weight: 600;
            line-height: 80px;
            border-radius: 50%;
            margin: 0 auto 15px;
        }}
        .nombre {{
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--dark);
        }}
    </style>
</head>
<body>

<button class="atras" onclick="history.back()"><i class="fas fa-arrow-left"></i> Atrás</button>

<h2>Selecciona tu nombre</h2>

{contenido}

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

    cursor.execute("""
        SELECT id, nombre_mesa
        FROM comandas
        WHERE mesero = ? AND estado = 'abierta'
        ORDER BY id DESC
    """, (nombre,))
    comandas = cursor.fetchall()
    conn.close()

    tarjetas = ""
    if comandas:
        for c in comandas:
            tarjetas += f'''
            <div class="comanda-card" onclick="location.href='/comanda/{c[0]}/{nombre}'">
                <div class="card-header">
                    <div class="mesa-title">Mesa {c[1]}</div>
                    <div class="icon"><i class="fas fa-utensils"></i></div>
                </div>
                <div class="card-footer">
                    <span class="ver-btn">Ver comanda →</span>
                </div>
            </div>
            '''
    else:
        tarjetas = '''
        <div class="empty-state">
            <i class="fas fa-coffee fa-3x" style="color:var(--accent); margin-bottom:15px;"></i><br>
            No tienes comandas abiertas aún
        </div>
        '''

    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {{
            --primary: #00b4d8;
            --primary-dark: #0096c7;
            --accent: #ff9e00;
            --success: #06d6a0;
            --danger: #ef476f;
            --dark: #2d3436;
            --light: #f8f9fa;
            --gray: #636e72;
        }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #e0f7fa 0%, #f0f8ff 100%);
            margin: 0;
            padding: 20px;
            color: var(--dark);
            min-height: 100vh;
        }}
        .top-bar {{
            position: sticky;
            top: 0;
            background: white;
            padding: 15px;
            border-bottom: 3px solid var(--primary);
            box-shadow: 0 4px 15px rgba(0,180,216,0.15);
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .mesero-name {{
            font-size: 1.6rem;
            font-weight: 600;
            color: var(--primary-dark);
        }}
        .atras {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 16px;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,180,216,0.3);
        }}
        h3 {{
            text-align: center;
            margin: 40px 0 30px;
            font-size: 1.8rem;
            color: var(--dark);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }}
        .comanda-card {{
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .comanda-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0,180,216,0.2);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .mesa-title {{
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--dark);
        }}
        .icon {{
            font-size: 1.8rem;
            color: var(--primary);
        }}
        .card-footer {{
            text-align: right;
        }}
        .ver-btn {{
            background: var(--primary);
            color: white;
            padding: 10px 20px;
            border-radius: 12px;
            font-weight: 500;
        }}
        .nueva-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--success);
            color: white;
            border: none;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            font-size: 2.2rem;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(6,214,160,0.3);
            transition: all 0.3s;
        }}
        .nueva-btn:hover {{
            transform: scale(1.1);
        }}
        .empty-state {{
            text-align: center;
            padding: 80px 20px;
            color: var(--gray);
            font-size: 1.4rem;
        }}
        form {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            margin: 30px auto;
            max-width: 500px;
        }}
        input {{
            width: 100%;
            padding: 14px;
            font-size: 1.1rem;
            border: 1px solid #ddd;
            border-radius: 10px;
            margin-bottom: 15px;
        }}
        .submit-btn {{
            width: 100%;
            padding: 16px;
            background: var(--success);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.2rem;
            cursor: pointer;
        }}
    </style>
</head>
<body>

<div class="top-bar">
    <button class="atras" onclick="history.back()"><i class="fas fa-arrow-left"></i> Atrás</button>
    <div class="mesero-name">Mesero: {nombre}</div>
</div>

<h3>Mis comandas abiertas</h3>

<div class="grid">
    {tarjetas}
</div>

<form method="POST">
    <input type="text" name="nombre_mesa" placeholder="Nombre o número de la mesa" required>
    <button type="submit" class="submit-btn">+ Nueva Comanda</button>
</form>

<button class="nueva-btn" onclick="document.querySelector('form').scrollIntoView({{behavior: 'smooth'}})">
    <i class="fas fa-plus"></i>
</button>

</body>
</html>
"""

@app.route("/comanda/<int:comanda_id>/<nombre>")
def ver_comanda(comanda_id, nombre):
    productos = obtener_productos()
    total = obtener_total_comanda(comanda_id)
    detalle = obtener_detalle_comanda(comanda_id)

    tabs = ""
    bloques = ""
    primera_cat = ""

    if productos:
        primera_cat = list(productos.keys())[0]
        for cat, lista in productos.items():
            tabs += f'<button class="cat-tab" onclick="mostrarCategoria(\'{cat}\')">{cat}</button>'
            botones = ""
            for p in lista:
                botones += f'''
                <div class="producto-card" onclick="agregarProducto({p[0]})">
                    <div class="prod-nombre">{p[1]}</div>
                    <div class="prod-precio">${p[2]:.2f}</div>
                </div>
                '''
            bloques += f'<div class="productos-grid" id="cat_{cat}" style="display:none;">{botones}</div>'

    lista_html = ""
    for item in detalle:
        detalle_id = item[0]
        nombre_producto = item[1]
        cantidad = item[2]
        subtotal = item[3]
        lista_html += f'''
        <div class="item-comanda">
            <div class="item-info">
                <span class="cantidad">{cantidad} ×</span> {nombre_producto}
                <span class="subtotal">${subtotal:.2f}</span>
            </div>
            <div class="item-controles">
                <button class="btn-circle menos" onclick="cambiarCantidad({detalle_id}, -1)">−</button>
                <button class="btn-circle mas" onclick="cambiarCantidad({detalle_id}, 1)">+</button>
            </div>
        </div>
        '''

    if not lista_html:
        lista_html = '<div class="empty-state">Aún no hay productos en esta comanda</div>'

    # Siempre retornamos HTML, incluso si algo falla
    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {{
            --primary: #00b4d8;
            --primary-dark: #0096c7;
            --accent: #ff9e00;
            --success: #06d6a0;
            --danger: #ef476f;
            --dark: #2d3436;
            --light: #f8f9fa;
            --gray: #636e72;
        }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #e0f7fa 0%, #f0f8ff 100%);
            margin: 0;
            color: var(--dark);
            min-height: 100vh;
        }}
        .top-bar {{
            position: sticky;
            top: 0;
            background: white;
            padding: 15px;
            border-bottom: 3px solid var(--primary);
            box-shadow: 0 4px 15px rgba(0,180,216,0.15);
            z-index: 100;
            text-align: center;
        }}
        .atras {{
            position: absolute;
            left: 15px;
            top: 15px;
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 16px;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,180,216,0.3);
        }}
        .total-display {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--success);
            margin: 10px 0;
        }}
        .categorias {{
            display: flex;
            overflow-x: auto;
            padding: 10px;
            background: white;
            border-bottom: 1px solid #eee;
        }}
        .cat-tab {{
            background: var(--primary);
            color: white;
            margin: 0 6px;
            padding: 12px 20px;
            border-radius: 30px;
            white-space: nowrap;
            font-weight: 500;
            flex-shrink: 0;
            border: none;
            cursor: pointer;
        }}
        .cat-tab.active {{
            background: var(--primary-dark);
        }}
        .productos-grid {{
            display: none;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 15px;
            padding: 20px;
        }}
        .producto-card {{
            background: white;
            border-radius: 16px;
            padding: 20px 10px;
            text-align: center;
            box-shadow: 0 6px 15px rgba(0,0,0,0.08);
            transition: all 0.25s ease;
            cursor: pointer;
        }}
        .producto-card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 12px 25px rgba(0,180,216,0.2);
        }}
        .prod-nombre {{
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 8px;
        }}
        .prod-precio {{
            color: var(--accent);
            font-size: 1.3rem;
            font-weight: 700;
        }}
        .lista-comanda {{
            padding: 15px;
            background: white;
            min-height: 150px;
            max-height: 40vh;
            overflow-y: auto;
        }}
        .item-comanda {{
            background: var(--light);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .item-info {{
            flex: 1;
        }}
        .cantidad {{
            font-weight: 700;
            color: var(--primary);
            margin-right: 8px;
        }}
        .subtotal {{
            float: right;
            color: var(--success);
            font-weight: 600;
        }}
        .item-controles {{
            display: flex;
            gap: 12px;
        }}
        .btn-circle {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            font-size: 1.5rem;
            line-height: 44px;
            text-align: center;
            color: white;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .menos {{ background: var(--danger); }}
        .mas {{ background: var(--success); }}
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--gray);
            font-size: 1.3rem;
        }}
        .acciones {{
            position: sticky;
            bottom: 0;
            background: white;
            padding: 15px;
            border-top: 2px solid #eee;
            box-shadow: 0 -4px 15px rgba(0,0,0,0.1);
        }}
        .cerrar-btn {{
            background: var(--danger);
            color: white;
            width: 100%;
            padding: 16px;
            font-size: 1.3rem;
            border-radius: 12px;
            border: none;
            cursor: pointer;
        }}
    </style>
</head>
<body>

<div class="top-bar">
    <button class="atras" onclick="history.back()"><i class="fas fa-arrow-left"></i> Atrás</button>
    <div>Mesa: <strong>{nombre}</strong></div>
    <div class="total-display">$ <span id="total">{total:.2f}</span></div>
</div>

<div class="categorias">
    {tabs}
</div>

<div id="productos-container">
    {bloques}
</div>

<div class="lista-comanda" id="lista">
    {lista_html}
</div>

<div class="acciones">
    <button class="cerrar-btn" onclick="if(confirm('¿Cerrar esta comanda?')) location.href='/cerrar/{comanda_id}/{nombre}'">
        <i class="fas fa-check-circle"></i> CERRAR COMANDA
    </button>
</div>

<script>
function mostrarCategoria(cat) {{
    document.querySelectorAll('.productos-grid').forEach(function(el) {{
        el.style.display = 'none';
    }});
    var target = document.getElementById('cat_' + cat);
    if (target) {{
        target.style.display = 'grid';
    }}
    document.querySelectorAll('.cat-tab').forEach(function(btn) {{
        btn.classList.remove('active');
    }});
    var activeBtn = Array.from(document.querySelectorAll('.cat-tab')).find(function(btn) {{
        return btn.textContent === cat;
    }});
    if (activeBtn) activeBtn.classList.add('active');
}}

function agregarProducto(producto_id) {{
    fetch("/api/agregar_producto", {{
        method: "POST",
        headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
        body: "comanda_id={comanda_id}&producto_id=" + producto_id
    }})
    .then(r => r.json())
    .then(data => actualizarVista(data))
    .catch(err => console.error(err));
}}

function cambiarCantidad(detalle_id, delta) {{
    fetch("/api/cambiar_cantidad", {{
        method: "POST",
        headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
        body: "detalle_id=" + detalle_id + "&delta=" + delta
    }})
    .then(r => r.json())
    .then(data => actualizarVista(data))
    .catch(err => console.error(err));
}}

function actualizarVista(data) {{
    if (!data || typeof data.total !== 'number') {{
        console.warn("Respuesta inválida:", data);
        return;
    }}
    document.getElementById("total").innerText = Number(data.total).toFixed(2);
    
    var html = "";
    if (Array.isArray(data.detalle)) {{
        data.detalle.forEach(function(item) {{
            if (Array.isArray(item) && item.length >= 4) {{
                html += '<div class="item-comanda">' +
                    '<div class="item-info">' +
                        '<span class="cantidad">' + item[2] + ' ×</span> ' + item[1] +
                        '<span class="subtotal">$' + Number(item[3]).toFixed(2) + '</span>' +
                    '</div>' +
                    '<div class="item-controles">' +
                        '<button class="btn-circle menos" onclick="cambiarCantidad(' + item[0] + ', -1)">−</button>' +
                        '<button class="btn-circle mas" onclick="cambiarCantidad(' + item[0] + ', 1)">+</button>' +
                    '</div>' +
                '</div>';
            }}
        }});
    }} else {{
        html = '<div class="empty-state">Aún no hay productos en esta comanda</div>';
    }}
    document.getElementById("lista").innerHTML = html;
}}

// Inicializar
""" + (f"mostrarCategoria('{primera_cat}');" if primera_cat else "") + """
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
    cursor.execute("""
        SELECT id, nombre_mesa 
        FROM comandas 
        WHERE estado = 'abierta' 
        ORDER BY id DESC
    """)
    comandas = cursor.fetchall()
    conn.close()

    tarjetas = ""
    if not comandas:
        tarjetas = '''
        <div style="text-align:center; padding:80px 20px; color:var(--gray); font-size:1.4rem;">
            <i class="fas fa-inbox fa-4x" style="color:var(--accent); margin-bottom:20px; opacity:0.6;"></i><br>
            No hay comandas abiertas en este momento
        </div>
        '''
    else:
        for com in comandas:
            comanda_id, mesa = com
            total = obtener_total_comanda(comanda_id)
            tarjetas += f'''
            <div class="comanda-card">
                <div class="card-header">
                    <div class="mesa-nombre">Mesa {mesa}</div>
                    <div class="total-card">${total:.2f}</div>
                </div>
                <div class="card-actions">
                    <button class="btn-ver" onclick="location.href='/ticket/{comanda_id}'">
                        <i class="fas fa-eye"></i> Ver Cuenta
                    </button>
                    <button class="btn-cerrar" onclick="if(confirm('¿Cerrar comanda?')) location.href='/cerrar/{comanda_id}/CAJA'">
                        <i class="fas fa-times-circle"></i> Cerrar
                    </button>
                </div>
            </div>
            '''

    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {{
            --primary: #00b4d8;
            --primary-dark: #0096c7;
            --accent: #ff9e00;
            --success: #06d6a0;
            --danger: #ef476f;
            --dark: #2d3436;
            --light: #f8f9fa;
            --gray: #636e72;
        }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #e0f7fa 0%, #f0f8ff 100%);
            margin: 0;
            padding: 20px;
            color: var(--dark);
            min-height: 100vh;
        }}
        .atras {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 16px;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,180,216,0.3);
        }}
        h1 {{
            text-align: center;
            margin: 60px 0 40px;
            font-size: 2.2rem;
            color: var(--primary-dark);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .comanda-card {{
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }}
        .comanda-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0,180,216,0.2);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .mesa-nombre {{
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--dark);
        }}
        .total-card {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--success);
            background: rgba(6,214,160,0.1);
            padding: 8px 16px;
            border-radius: 12px;
        }}
        .card-actions {{
            display: flex;
            gap: 15px;
        }}
        .btn-ver, .btn-cerrar {{
            flex: 1;
            padding: 14px;
            font-size: 1.1rem;
            border-radius: 12px;
            color: white;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-ver {{
            background: var(--primary);
        }}
        .btn-cerrar {{
            background: var(--danger);
        }}
        .btn-ver:hover, .btn-cerrar:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
        }}
    </style>
</head>
<body>

<button class="atras" onclick="history.back()"><i class="fas fa-arrow-left"></i> Atrás</button>

<h1>Comandas Abiertas - Caja</h1>

<div class="grid">
    {tarjetas}
</div>

</body>
</html>
"""

@app.route("/productos/login", methods=["GET", "POST"])
def productos_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_authenticated"] = True
            return redirect("/productos")
        else:
            error = "Contraseña incorrecta"
    else:
        error = ""

    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {{
            --primary: #00b4d8;
            --primary-dark: #0096c7;
            --accent: #ff9e00;
            --success: #06d6a0;
            --danger: #ef476f;
            --dark: #2d3436;
            --light: #f8f9fa;
            --gray: #636e72;
        }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #e0f7fa 0%, #f0f8ff 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 420px;
            text-align: center;
        }}
        h2 {{
            color: var(--primary);
            margin-bottom: 30px;
        }}
        input {{
            width: 100%;
            padding: 14px;
            margin: 12px 0;
            border: 1px solid #ddd;
            border-radius: 10px;
            font-size: 1.1rem;
        }}
        button {{
            width: 100%;
            padding: 14px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.2rem;
            cursor: pointer;
            transition: background 0.2s;
        }}
        button:hover {{
            background: var(--primary-dark);
        }}
        .error {{
            color: var(--danger);
            margin-top: 15px;
            font-weight: 500;
        }}
        .atras {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 16px;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
        }}
    </style>
</head>
<body>

<button class="atras" onclick="history.back()"><i class="fas fa-arrow-left"></i> Atrás</button>

<div class="container">
    <h2>Acceso Administrador</h2>
    <form method="POST">
        <input type="password" name="password" placeholder="Contraseña" required autofocus>
        <button type="submit">Entrar</button>
    </form>
    {f'<div class="error">{error}</div>' if error else ''}
</div>

</body>
</html>
"""


@app.route("/productos", methods=["GET", "POST"])
def productos_admin():
    if not session.get("admin_authenticated"):
        return redirect("/productos/login")

    mensaje = ""
    tipo_mensaje = "success"

    accion = request.args.get("accion", "")
    producto_id = request.args.get("id", type=int)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Eliminar producto
    if accion == "eliminar" and producto_id:
        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()
        mensaje = "Producto eliminado correctamente"
        tipo_mensaje = "success"

    # Agregar o editar producto
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        precio_str = request.form.get("precio", "").strip()
        categoria = request.form.get("categoria", "").strip()  # ← viene del input (escrito o seleccionado)
        edit_id = request.form.get("edit_id", type=int)

        if not nombre or not categoria or not precio_str:
            mensaje = "Completa todos los campos"
            tipo_mensaje = "error"
        else:
            try:
                precio = float(precio_str)
                if precio <= 0:
                    mensaje = "El precio debe ser mayor a 0"
                    tipo_mensaje = "error"
                else:
                    if edit_id:
                        cursor.execute("""
                            UPDATE productos 
                            SET nombre = ?, precio = ?, categoria = ? 
                            WHERE id = ?
                        """, (nombre, precio, categoria, edit_id))
                        mensaje = "Producto actualizado correctamente"
                    else:
                        cursor.execute("""
                            INSERT INTO productos (nombre, precio, categoria) 
                            VALUES (?, ?, ?)
                        """, (nombre, precio, categoria))
                        mensaje = "Producto agregado correctamente"
                    conn.commit()
                    tipo_mensaje = "success"
            except ValueError:
                mensaje = "El precio debe ser un número válido"
                tipo_mensaje = "error"

    # Obtener productos
    cursor.execute("SELECT id, nombre, precio, categoria FROM productos ORDER BY categoria, nombre")
    productos = cursor.fetchall()

    # Categorías existentes
    cursor.execute("SELECT DISTINCT categoria FROM productos ORDER BY categoria")
    categorias = [row[0] for row in cursor.fetchall()]

    conn.close()

    # Producto a editar
    producto_edit = None
    if accion == "editar" and producto_id:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, precio, categoria FROM productos WHERE id = ?", (producto_id,))
        row = cursor.fetchone()
        if row:
            producto_edit = row
        conn.close()

    opciones_cat = ''.join(f'<option value="{c}">{c}</option>' for c in categorias)

    # Tabla HTML
    tabla_html = ""
    if productos:
        for p in productos:
            tabla_html += f'''
            <tr class="row-hover">
                <td>{p[1]}</td>
                <td>${p[2]:.2f}</td>
                <td>{p[3]}</td>
                <td class="actions">
                    <a href="/productos?accion=editar&id={p[0]}" class="btn-edit"><i class="fas fa-edit"></i> Editar</a>
                    <a href="/productos?accion=eliminar&id={p[0]}" onclick="return confirm('¿Eliminar {p[1]}?');" class="btn-delete"><i class="fas fa-trash"></i> Eliminar</a>
                </td>
            </tr>
            '''
    else:
        tabla_html = '<tr><td colspan="4" class="empty">No hay productos registrados</td></tr>'

    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {{
            --primary: #00b4d8;
            --primary-dark: #0096c7;
            --accent: #ff9e00;
            --success: #06d6a0;
            --danger: #ef476f;
            --dark: #2d3436;
            --light: #f8f9fa;
            --gray: #636e72;
        }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #e0f7fa 0%, #f0f8ff 100%);
            margin: 0;
            padding: 20px;
            color: var(--dark);
            min-height: 100vh;
        }}
        .atras {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 16px;
            font-size: 1.1rem;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,180,216,0.3);
        }}
        h2 {{
            text-align: center;
            margin: 60px 0 30px;
            font-size: 2.2rem;
            color: var(--primary-dark);
        }}
        form {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            max-width: 600px;
            margin: 0 auto 50px;
        }}
        label {{
            display: block;
            margin: 15px 0 8px;
            font-weight: 600;
            color: var(--dark);
        }}
        .categoria-group {{
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }}
        .categoria-group select, .categoria-group input {{
            flex: 1;
            padding: 14px;
            font-size: 1rem;
            border: 1px solid #ddd;
            border-radius: 10px;
            box-sizing: border-box;
        }}
        input, select {{
            width: 100%;
            padding: 14px;
            font-size: 1rem;
            border: 1px solid #ddd;
            border-radius: 10px;
            box-sizing: border-box;
        }}
        button {{
            width: 100%;
            padding: 16px;
            font-size: 1.2rem;
            background: var(--success);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.2s;
        }}
        button:hover {{
            background: #05c08e;
            transform: translateY(-2px);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        }}
        th, td {{
            padding: 16px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: var(--primary);
            color: white;
            font-weight: 600;
        }}
        .row-hover:hover {{
            background: rgba(0,180,216,0.05);
        }}
        .actions a {{
            margin-right: 15px;
            text-decoration: none;
            font-weight: 500;
        }}
        .btn-edit {{ color: var(--primary); }}
        .btn-delete {{ color: var(--danger); }}
        .mensaje {{
            padding: 15px;
            border-radius: 12px;
            margin: 20px auto;
            max-width: 600px;
            text-align: center;
            font-weight: 500;
        }}
        .success {{ background: rgba(6,214,160,0.15); color: var(--success); }}
        .error {{ background: rgba(239,71,111,0.15); color: var(--danger); }}
        .empty {{ text-align: center; padding: 30px; color: var(--gray); }}
    </style>
</head>
<body>

<button class="atras" onclick="history.back()"><i class="fas fa-arrow-left"></i> Atrás</button>

<h2>Administrar Productos</h2>

{mensaje and f'<div class="mensaje {tipo_mensaje}">{mensaje}</div>' or ''}

<form method="POST">
    {f'<input type="hidden" name="edit_id" value="{producto_edit[0]}">' if producto_edit else ''}
    <label>Nombre del producto</label>
    <input type="text" name="nombre" value="{producto_edit[1] if producto_edit else ''}" required placeholder="Ej: Pelota de playa">

    <label>Precio ($)</label>
    <input type="number" name="precio" step="0.01" value="{producto_edit[2] if producto_edit else ''}" required placeholder="Ej: 150.00">

    <label>Categoría</label>
    <div class="categoria-group">
        <select name="categoria_select" id="categoria_select" onchange="document.getElementById('categoria_input').value = this.value;">
            <option value="">-- Selecciona una existente --</option>
            {opciones_cat}
        </select>
        <input type="text" name="categoria" id="categoria_input" value="{producto_edit[3] if producto_edit else ''}" placeholder="O escribe una nueva" required>
    </div>

    <button type="submit">
        {'Actualizar Producto' if producto_edit else 'Agregar Producto'}
    </button>
</form>

<h3>Productos registrados ({len(productos)})</h3>

<table>
    <thead>
        <tr>
            <th>Nombre</th>
            <th>Precio</th>
            <th>Categoría</th>
            <th>Acciones</th>
        </tr>
    </thead>
    <tbody>
        {tabla_html}
    </tbody>
</table>

</body>
</html>
"""


@app.route("/api/agregar_producto", methods=["POST"])
def api_agregar_producto():
    comanda_id = int(request.form["comanda_id"])
    producto_id = int(request.form["producto_id"])
    cantidad = int(request.form.get("cantidad", 1))  # default 1

    agregar_producto_a_comanda(comanda_id, producto_id, cantidad)

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

@app.route("/api/cambiar_cantidad", methods=["POST"])
def api_cambiar_cantidad():
    detalle_id = int(request.form["detalle_id"])
    delta = int(request.form["delta"])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT comanda_id, cantidad, subtotal, producto_id
        FROM comanda_detalle
        WHERE id = ?
    """, (detalle_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Item no encontrado"}), 404

    comanda_id, cant_actual, subtotal_actual, producto_id = row

    cursor.execute("SELECT precio FROM productos WHERE id=?", (producto_id,))
    precio = cursor.fetchone()[0]

    nueva_cant = cant_actual + delta
    if nueva_cant <= 0:
        cursor.execute("DELETE FROM comanda_detalle WHERE id = ?", (detalle_id,))
    else:
        nuevo_subtotal = nueva_cant * precio
        cursor.execute("""
            UPDATE comanda_detalle 
            SET cantidad = ?, subtotal = ? 
            WHERE id = ?
        """, (nueva_cant, nuevo_subtotal, detalle_id))

    conn.commit()
    conn.close()

    total = obtener_total_comanda(comanda_id)
    detalle = obtener_detalle_comanda(comanda_id)

    return jsonify({"total": total, "detalle": detalle})

@app.route("/ver_comanda/<int:comanda_id>")
def ver_comanda_solo_lectura(comanda_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT nombre_mesa, mesero FROM comandas WHERE id=?", (comanda_id,))
    mesa, mesero = cursor.fetchone()

    cursor.execute("""
        SELECT p.nombre, d.cantidad, p.precio
        FROM comanda_detalle d
        JOIN productos p ON d.producto_id = p.id
        WHERE d.comanda_id = ?
    """, (comanda_id,))
    items = cursor.fetchall()

    conn.close()

    lineas = ""
    total = 0
    for nombre, cant, precio in items:
        subtotal = cant * precio
        total += subtotal
        lineas += f"<div>{cant} × {nombre:.<30} ${subtotal:>8.2f}</div>"

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            body {{ font-family: Arial; padding: 15px; background: #f8f8f8; }}
            h2 {{ text-align: center; }}
            .total {{ font-size: 24px; font-weight: bold; text-align: right; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h2>JARDIN DORY'S - Cuenta</h2>
        Mesa: {mesa}<br>
        Mesero: {mesero}<br><br>
        <hr>
        {lineas}
        <div class="total">TOTAL: ${total:.2f}</div>
        <br><br>
        <button onclick="history.back()">← Regresar</button>
    </body>
    </html>
    """
    
from datetime import datetime  # asegúrate de tener esta import al inicio del archivo

from datetime import datetime  # Asegúrate de tener esta import al inicio del archivo

@app.route("/ticket/<int:comanda_id>")
def ticket(comanda_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre_mesa, mesero
        FROM comandas
        WHERE id = ?
    """, (comanda_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "Comanda no encontrada", 404

    mesa, mesero = row

    cursor.execute("""
        SELECT p.nombre, d.cantidad, p.precio, d.subtotal
        FROM comanda_detalle d
        JOIN productos p ON d.producto_id = p.id
        WHERE d.comanda_id = ?
        ORDER BY d.id
    """, (comanda_id,))
    items = cursor.fetchall()

    conn.close()

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    lineas = ""
    total = 0.0
    for nombre, cantidad, precio, subtotal in items:
        total += subtotal
        lineas += f'''
        <div class="ticket-line">
            <span class="qty">{cantidad} ×</span>
            <span class="prod-name">{nombre}</span>
            <span class="subtotal">${subtotal:.2f}</span>
        </div>
        '''

    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket - Jardín Dory's</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Poppins', sans-serif;
            width: 80mm;
            margin: 0 auto;
            padding: 10mm 5mm;
            font-size: 12pt;
            line-height: 1.4;
            color: #000;
            background: white;
        }}
        .header {{
            text-align: center;
            margin-bottom: 8mm;
        }}
        .logo {{
            font-size: 20pt;
            font-weight: 700;
            color: #00b4d8;
            margin: 0;
        }}
        .info {{
            text-align: center;
            font-size: 11pt;
            margin-bottom: 6mm;
            color: #444;
        }}
        .divider {{
            border-top: 1px dashed #000;
            margin: 4mm 0;
        }}
        .ticket-line {{
            display: flex;
            justify-content: space-between;
            margin: 2mm 0;
            font-size: 11pt;
        }}
        .qty {{
            width: 15%;
            text-align: left;
        }}
        .prod-name {{
            flex: 1;
            text-align: left;
        }}
        .subtotal {{
            width: 30%;
            text-align: right;
            font-weight: 600;
        }}
        .total-section {{
            margin-top: 8mm;
            padding-top: 4mm;
            border-top: 2px dashed #000;
            text-align: right;
            font-size: 14pt;
            font-weight: 700;
        }}
        .gracias {{
            text-align: center;
            margin-top: 10mm;
            font-style: italic;
            color: #555;
            font-size: 11pt;
        }}
        .print-btn {{
            display: block;
            margin: 20px auto;
            padding: 12px 30px;
            font-size: 14pt;
            background: #00b4d8;
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; margin: 0; }}
        }}
    </style>
</head>
<body onload="window.print()">

<div class="header">
    <div class="logo">JARDÍN DORY'S</div>
    <div style="font-size:10pt; color:#666;">Albercas & Comida</div>
</div>

<div class="info">
    Mesa: <strong>{mesa}</strong><br>
    Mesero: <strong>{mesero}</strong><br>
    Fecha: {ahora}
</div>

<div class="divider"></div>

{lineas}

<div class="total-section">
    TOTAL: ${total:.2f}
</div>

<div class="divider"></div>

<div class="gracias">
    ¡Gracias por su visita!<br>
    ¡Vuelva pronto! 🌴🍹
</div>

<button class="print-btn" onclick="window.print()">Imprimir de nuevo</button>

</body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True)
