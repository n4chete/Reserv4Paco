from flask import Flask, request, render_template, jsonify
from reserva_core import hacer_reserva
import time
import requests

app = Flask(__name__, static_folder='static', template_folder='templates')

# 🧠 Sesión global para login anticipado
session_guardada = None

@app.route('/')
def home():
    return render_template('index.html')

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

@app.route('/run-script', methods=['POST'])
def run_script():
    global session_guardada
    session = session_guardada or requests.Session()

    # 🧩 Recogida de datos del formulario
    data = {
        "usuario": request.form.get("usuario"),
        "password": request.form.get("password"),
        "fecha": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "pista": request.form.get("pista"),
        "part2": request.form.get("part2", ""),
        "part3": request.form.get("part3", ""),
        "part4": request.form.get("part4", ""),
        "deporte": request.form.get("deporte", "padel")  # ✅ nuevo campo para lógica condicional
    }

    resultados = []

    pistas_raw = request.form.get("pistas_multis", "").strip()
    pistas_activadas = bool(pistas_raw)

    if pistas_activadas:
        try:
            intervalo = float(request.form.get("intervalo", 0))
        except ValueError:
            return "❌ Error en intervalo"

        pistas = [p.strip() for p in pistas_raw.split(",") if p.strip().isdigit()]
        if not pistas:
            return "❌ No se han especificado pistas válidas"

        for i, pista in enumerate(pistas):
            data["pista"] = pista
            resultado = hacer_reserva(data, session)
            resultados.append(f"Pista {pista}: {resultado}")
            if i < len(pistas) - 1:
                print(f"[DEBUG] Esperando {intervalo} segundos...")
                time.sleep(intervalo)

    else:
        try:
            cantidad = int(request.form.get("cantidad", 1))
            intervalo = float(request.form.get("intervalo", 0))
        except ValueError:
            return "❌ Error en cantidad o intervalo"

        for i in range(cantidad):
            resultado = hacer_reserva(data, session)
            resultados.append(f"Reserva {i+1}: {resultado}")
            if i < cantidad - 1:
                time.sleep(intervalo)

    return "\n".join(resultados)

if __name__ == '__main__':
    app.run(debug=True)
