import sqlite3

conn = sqlite3.connect("usuarios.db")
cur = conn.cursor()

# Empresas
cur.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    rfc TEXT,
    direccion TEXT,
    telefono TEXT,
    correo TEXT UNIQUE,
    plan TEXT,
    estado TEXT
)
""")

# Usuarios
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    nombre TEXT,
    correo TEXT UNIQUE,
    telefono TEXT,
    contrasena TEXT,
    rol TEXT,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
)
""")

# Verificación
cur.execute("""
CREATE TABLE IF NOT EXISTS verificacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    correo TEXT NOT NULL,
    codigo TEXT NOT NULL
)
""")

conn.commit()
conn.close()
print("✅ Base de datos 'usuarios.db' creada correctamente con todas las tablas.")