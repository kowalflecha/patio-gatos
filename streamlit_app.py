import streamlit as st
import sqlite3
from datetime import datetime

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect("gatos_paseos_v4.db")
    cursor = conn.cursor()
    # Crear tabla de gatos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE
        )
    """)
    # Crear tabla de paseos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paseos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gato_id INTEGER,
            inicio_paseo TEXT,
            fin_paseo TEXT,
            FOREIGN KEY (gato_id) REFERENCES gatos (id)
        )
    """)
    conn.commit()
    return conn

# Funciones para manejar datos
def agregar_gato(conn, nombre):
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO gatos (nombre) VALUES (?)", (nombre,))
        conn.commit()
    except sqlite3.IntegrityError:
        st.warning("El gato ya está registrado.")

def obtener_gatos(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM gatos")
    return cursor.fetchall()

def iniciar_paseo(conn, gato_id):
    cursor = conn.cursor()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO paseos (gato_id, inicio_paseo) VALUES (?, ?)", (gato_id, ahora))
    conn.commit()

def finalizar_paseo(conn, gato_id):
    cursor = conn.cursor()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE paseos
        SET fin_paseo = ?
        WHERE gato_id = ? AND fin_paseo IS NULL
    """, (ahora, gato_id))
    conn.commit()

def obtener_paseos(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.nombre, p.inicio_paseo, p.fin_paseo
        FROM paseos p
        JOIN gatos g ON p.gato_id = g.id
        ORDER BY p.inicio_paseo DESC
    """)
    return cursor.fetchall()

def eliminar_datos(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM paseos")
    cursor.execute("DELETE FROM gatos")
    conn.commit()

# Iniciar conexión
conn = init_db()

# Interfaz de usuario
st.header("🐈 Seguimiento de paseos de los gatos")

# Agregar un nuevo gato
nuevo_gato = st.text_input("Agregar un nuevo gato:")
if st.button("Añadir gato") and nuevo_gato:
    agregar_gato(conn, nuevo_gato)
    st.success(f"Se agregó a {nuevo_gato}.")

# Mostrar lista de gatos
gatos = obtener_gatos(conn)
st.subheader("Estado de paseos")
for gato_id, nombre in gatos:
    # Verificar si el gato está actualmente paseando
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM paseos
        WHERE gato_id = ? AND fin_paseo IS NULL
    """, (gato_id,))
    paseando = cursor.fetchone() is not None

    # Checkbox dinámico con mensaje según estado
    if paseando:
        checkbox_label = f"{nombre} está paseando"
    else:
        checkbox_label = f"{nombre} no está paseando"

    if st.checkbox(checkbox_label, key=nombre, value=paseando):
        if not paseando:  # Si el checkbox cambia a True
            iniciar_paseo(conn, gato_id)
            st.success(f"{nombre} comenzó a pasear.")
    else:
        if paseando:  # Si el checkbox cambia a False
            finalizar_paseo(conn, gato_id)
            st.info(f"{nombre} dejó de pasear.")

# Historial de paseos
st.subheader("Historial de paseos")
todos_paseos = obtener_paseos(conn)
if todos_paseos:
    for nombre, inicio, fin in todos_paseos:
        st.write(f"**{nombre}**: {inicio} - {fin or 'En paseo...'}")
else:
    st.write("No hay paseos registrados.")

# Botón para reiniciar datos
if st.button("Reiniciar datos"):
    eliminar_datos(conn)
    st.success("Datos reiniciados.")
