import sqlite3

# Conexión
conn = sqlite3.connect("usuarios.db")
cur = conn.cursor()

# Tabla de empresas
cur.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    rfc TEXT,
    direccion TEXT,
    telefono TEXT,
    correo TEXT UNIQUE NOT NULL,
    plan TEXT,
    estado TEXT DEFAULT 'activo'
)
""")

# Tabla de usuarios
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    correo TEXT UNIQUE NOT NULL,
    telefono TEXT,
    contrasena TEXT NOT NULL,
    rol TEXT NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
)
""")

# Tabla de verificación de códigos enviados por correo
cur.execute("""
CREATE TABLE IF NOT EXISTS verificacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    correo TEXT NOT NULL,
    codigo TEXT NOT NULL
)
""")

# Tabla de dispositivos vinculados a cada empresa
cur.execute("""
CREATE TABLE IF NOT EXISTS dispositivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER NOT NULL,
    hardware_id TEXT UNIQUE NOT NULL,
    nombre_pc TEXT,
    fecha_registro TEXT,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
)
""")

# Guardar y cerrar
conn.commit()
conn.close()
print("✅ Base de datos 'usuarios.db' creada correctamente con todas las tablas necesarias.")