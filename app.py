from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "usuarios.db"

# 🔧 Conexión a base de datos
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder por nombre
    return conn

# 🚀 Endpoint para registro de empresa + usuario
@app.route("/api/registro", methods=["POST"])
def registrar_empresa():
    try:
        data = request.get_json()

        # Validaciones mínimas
        required_empresa = ["nombre_empresa", "telefono", "correo"]
        required_usuario = ["nombre_usuario", "correo_usuario", "telefono_usuario", "contrasena"]
        if not all(key in data for key in required_empresa + required_usuario):
            return jsonify({"success": False, "message": "Faltan datos requeridos."}), 400

        # Extrae los datos
        nombre_empresa = data["nombre_empresa"]
        rfc = data.get("rfc", "")
        direccion = data.get("direccion", "")
        telefono = data["telefono"]
        correo = data["correo"]

        nombre_usuario = data["nombre_usuario"]
        correo_usuario = data["correo_usuario"]
        telefono_usuario = data["telefono_usuario"]
        contrasena = data["contrasena"]
        plan = data.get("plan", "pendiente")

        conn = get_db()
        cur = conn.cursor()

        # Verifica si ya existe la empresa
        cur.execute("SELECT * FROM empresas WHERE correo = ?", (correo,))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Ya existe una empresa con ese correo."}), 409

        # Verifica si ya existe el usuario
        cur.execute("SELECT * FROM usuarios WHERE correo = ?", (correo_usuario,))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Ya existe un usuario con ese correo."}), 409

        # Inserta empresa
        cur.execute("""
            INSERT INTO empresas (nombre, rfc, direccion, telefono, correo, plan, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre_empresa, rfc, direccion, telefono, correo, plan, "pendiente"))

        empresa_id = cur.lastrowid

        # Inserta usuario administrador
        cur.execute("""
            INSERT INTO usuarios (empresa_id, nombre, correo, telefono, contrasena, rol)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (empresa_id, nombre_usuario, correo_usuario, telefono_usuario, contrasena, "administrador"))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Registro exitoso. Cuenta creada en modo pendiente.",
            "empresa_id": empresa_id
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error interno en el servidor: {str(e)}"
        }), 500

# ✅ Esto asegura que el servidor se inicie al ejecutar "python app.py"
if __name__ == "__main__":
    app.run(debug=True)