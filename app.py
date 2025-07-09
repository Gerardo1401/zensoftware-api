from flask import Flask, request, jsonify
import sqlite3
import os
import random
import smtplib
from datetime import datetime
from email.message import EmailMessage

# ✅ Cargar .env solo si no existen variables del entorno
def cargar_env_local():
    if not os.environ.get("EMAIL_REMITENTE") or not os.environ.get("EMAIL_CONTRASENA"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os.environ[key.strip()] = value.strip()
            print("✅ Variables de entorno cargadas desde .env")
        except FileNotFoundError:
            print("⚠️ No se encontró .env. Asegúrate de tener variables configuradas en el entorno.")

cargar_env_local()

app = Flask(__name__)
DB_PATH = "usuarios.db"

# 🔧 Conexión a base de datos
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 🚀 Registro de empresa + usuario + dispositivo
@app.route("/api/registro", methods=["POST"])
def registrar_empresa():
    try:
        data = request.get_json()

        required_empresa = ["nombre_empresa", "telefono", "correo", "hardware_id"]
        required_usuario = ["nombre_usuario", "correo_usuario", "telefono_usuario", "contrasena"]
        if not all(key in data for key in required_empresa + required_usuario):
            return jsonify({"success": False, "message": "Faltan datos requeridos."}), 400

        nombre_empresa = data["nombre_empresa"]
        rfc = data.get("rfc", "")
        direccion = data.get("direccion", "")
        telefono = data["telefono"]
        correo = data["correo"]
        hardware_id = data["hardware_id"]

        nombre_usuario = data["nombre_usuario"]
        correo_usuario = data["correo_usuario"]
        telefono_usuario = data["telefono_usuario"]
        contrasena = data["contrasena"]
        plan = data.get("plan", "pendiente")

        conn = get_db()
        cur = conn.cursor()

        # Verificar si ese hardware_id ya está en uso
        cur.execute("SELECT * FROM dispositivos WHERE hardware_id = ?", (hardware_id,))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Este equipo ya está registrado por otra empresa."}), 403

        # Verificar si ya existe la empresa o el usuario
        cur.execute("SELECT * FROM empresas WHERE correo = ?", (correo,))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Ya existe una empresa con ese correo."}), 409

        cur.execute("SELECT * FROM usuarios WHERE correo = ?", (correo_usuario,))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Ya existe un usuario con ese correo."}), 409

        # Registrar empresa
        cur.execute("""
            INSERT INTO empresas (nombre, rfc, direccion, telefono, correo, plan, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre_empresa, rfc, direccion, telefono, correo, plan, "pendiente"))
        empresa_id = cur.lastrowid

        # Registrar usuario administrador
        cur.execute("""
            INSERT INTO usuarios (empresa_id, nombre, correo, telefono, contrasena, rol)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (empresa_id, nombre_usuario, correo_usuario, telefono_usuario, contrasena, "administrador"))

        # Registrar dispositivo
        nombre_pc = os.environ.get("COMPUTERNAME", "PC-ZenCore")
        fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("""
            INSERT INTO dispositivos (empresa_id, hardware_id, nombre_pc, fecha_registro)
            VALUES (?, ?, ?, ?)
        """, (empresa_id, hardware_id, nombre_pc, fecha_registro))

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

# 🔍 Verificación previa del hardware ID
@app.route("/api/verificar-dispositivo", methods=["POST"])
def verificar_dispositivo():
    try:
        data = request.get_json()
        hardware_id = data.get("hardware_id")

        if not hardware_id:
            return jsonify({"success": False, "message": "Hardware ID no proporcionado."}), 400

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT empresas.nombre, empresas.id
            FROM dispositivos
            INNER JOIN empresas ON dispositivos.empresa_id = empresas.id
            WHERE dispositivos.hardware_id = ?
        """, (hardware_id,))
        resultado = cur.fetchone()

        if resultado:
            return jsonify({
                "success": True,
                "registrado": True,
                "empresa": resultado["nombre"],
                "empresa_id": resultado["id"]
            }), 200
        else:
            return jsonify({
                "success": True,
                "registrado": False
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error interno al verificar: {str(e)}"
        }), 500

# ✉️ Envío de código de verificación por correo
@app.route("/api/verificar-correo", methods=["POST"])
def enviar_codigo_verificacion():
    try:
        data = request.get_json()
        correo = data.get("correo")

        if not correo:
            return jsonify({"success": False, "message": "Correo no proporcionado."}), 400

        codigo = str(random.randint(100000, 999999))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO verificacion (correo, codigo) VALUES (?, ?)", (correo, codigo))
        conn.commit()

        msg = EmailMessage()
        msg.set_content(f"Tu código de verificación es: {codigo}")
        msg['Subject'] = "Código de verificación – Zen Software"
        msg['From'] = os.environ.get("EMAIL_REMITENTE", "noreply@zensoftware.mx")
        msg['To'] = correo

        smtp_user = os.environ.get("EMAIL_REMITENTE")
        smtp_pass = os.environ.get("EMAIL_CONTRASENA")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)

        return jsonify({"success": True, "message": "Código enviado correctamente."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error al enviar código: {str(e)}"}), 500

# ✅ Validación del código
@app.route("/api/validar-codigo", methods=["POST"])
def validar_codigo():
    try:
        data = request.get_json()
        correo = data.get("correo")
        codigo = data.get("codigo")

        if not correo or not codigo:
            return jsonify({"success": False, "message": "Correo o código faltante."}), 400

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM verificacion WHERE correo = ? AND codigo = ?", (correo, codigo))
        resultado = cur.fetchone()

        if resultado:
            cur.execute("DELETE FROM verificacion WHERE correo = ?", (correo,))
            conn.commit()
            return jsonify({"success": True, "message": "Código válido."}), 200
        else:
            return jsonify({"success": False, "message": "Código incorrecto o expirado."}), 401

    except Exception as e:
        return jsonify({"success": False, "message": f"Error al validar código: {str(e)}"}), 500

# 🟢 Ejecutar app localmente
if __name__ == "__main__":
    app.run(debug=True)