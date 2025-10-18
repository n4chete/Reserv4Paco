from flask import Flask, request, render_template, jsonify
import requests
import threading

from reserva_core import hacer_reserva  # Asegúrate de que este módulo esté presente

app = Flask(__name__, static_folder='static', template_folder='templates')

# 🧠 Sesión global para login anticipado
session_guardada = None

# ✅ Ruta principal
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Ruta dummy para probar conexión backend
@app.route('/ping', methods=['POST'])
def ping():
    return "✅ Backend activo"

# ✅ Ruta para login anticipado
@app.route('/prelogin', methods=['POST'])
def prelogin():
    global session_guardada
    usuario = request.form.get("usuario")
    password = request.form.get("password")

    session = requests.Session()
    login_payload = {
        "name": usuario,
        "pass": password,
        "form_id": "user_login_block",
        "op": "Entra"
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    login_url = "https://laietania.miclubonline.net/"
    response = session.post(login_url, data=login_payload, headers=headers)

    if response.ok and "logout" in response.text.lower():
        session_guardada = session
        return jsonify({"status": "✅ Login exitoso"})
    else:
        return jsonify({"status": "❌ Error de login"})

# ✅ Función para ejecutar la reserva en segundo plano
def ejecutar_reserva_en_segundo_plano(data, session):
    try:
        resultado = hacer_reserva(data, session)
        print(f"[RESERVA] Resultado: {resultado}", flush=True)
    except Exception as e:
        print(f"[ERROR] Reserva fallida: {str(e)}", flush=True)

# ✅ Ruta para lanzar la reserva
@app.route('/run-script', methods=['POST'])
def run_script():
    global session_guardada
    session = session_guardada or requests.Session()

    data = {
        "usuario": request.form.get("usuario"),
        "password": request.form.get("password"),
        "fecha": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "pista": request.form.get("pista"),
        "part2": request.form.get("part2", ""),
        "part3": request.form.get("part3", ""),
        "part4": request.form.get("part4", ""),
        "deporte": request.form.get("deporte", "padel")
    }

    print("[DEBUG] Datos recibidos:", data, flush=True)

    hilo = threading.Thread(target=ejecutar_reserva_en_segundo_plano, args=(data, session))
    hilo.start()

    return "⏳ Reserva en curso…"

# ✅ Ejecutar localmente si se desea
if __name__ == "__main__":
    app.run(debug=True)
