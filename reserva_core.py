import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

def hacer_reserva(data: dict, session: requests.Session) -> str:
    usuario = data["usuario"]
    password = data["password"]
    fecha = data["fecha"]
    hora = data["hora"]
    pista_raw = data["pista"]
    deporte = data.get("deporte", "padel")

    # ?? Configuracion por deporte
    if deporte == "tenis":
        pista_map = {str(i): f"{i:02}" for i in range(1, 7)}  # pistas 01 a 06
        endpoint = "01"
        pista = pista_map.get(pista_raw, pista_raw)
        tiempo_reserva = "5"  # duracion fija 1h15
        max_jugadores = "2"
        partes = {
            "part1": f"[{usuario}] (jo)",
            "part2": data.get("part2", "[Invitacio sense carrec]")
        }
    else:
        pista_map = {str(i): str(19 + i) for i in range(1, 8)}  # pistas 20 a 26
        endpoint = "02"
        pista = pista_map.get(pista_raw, pista_raw)
        partido_datetime = datetime.strptime(f"{fecha} {hora}", "%Y%m%d %H%M")
        dia_semana = partido_datetime.weekday()
        horas_1h15 = {"1600", "1715", "1830", "1945", "2100"}
        tiempo_reserva = "5" if dia_semana < 5 and hora in horas_1h15 else "6"
        max_jugadores = "4"
        partes = {
            "part1": f"[{usuario}] (jo)",
            "part2": data.get("part2", "[Invitacio sense carrec]"),
            "part3": data.get("part3", "[Invitacio sense carrec]"),
            "part4": data.get("part4", "[14429]")
        }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
        "Referer": "https://laietania.miclubonline.net/",
        "Origin": "https://laietania.miclubonline.net",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    login_payload = {
        "name": usuario,
        "pass": password,
        "form_id": "user_login_block",
        "op": "Entra"
    }

    login_url = "https://laietania.miclubonline.net/"
    login_response = session.post(login_url, data=login_payload, headers=headers)
    if not login_response.ok or "logout" not in login_response.text.lower():
        return "? Error de login"

    reserva_url = f"https://laietania.miclubonline.net/infopistas/{endpoint}/{fecha}/{pista}/{hora}"
    reserva_response = session.get(reserva_url, headers=headers)
    if not reserva_response.ok:
        return "? Error al cargar la pagina de reserva"

    soup = BeautifulSoup(reserva_response.text, "html.parser")
    form_build_id = soup.find("input", {"name": "form_build_id"})
    form_token = soup.find("input", {"name": "form_token"})
    form_id = soup.find("input", {"name": "form_id"})
    if not (form_build_id and form_token and form_id):
        return "? Tokens no encontrados"

    reserva_payload = {
        "total": "0",
        "max": max_jugadores,
        "mixto": "1",
        "add": "",
        "invitation-group": "none",
        "tiempo": tiempo_reserva,
        "reserva": "Reserva",
        "form_build_id": form_build_id.get("value"),
        "form_token": form_token.get("value"),
        "form_id": form_id.get("value")
    }
    reserva_payload.update(partes)

    confirm_response = session.post(reserva_url, data=reserva_payload, headers=headers)

    debug_path = os.path.join(os.getcwd(), "reserva_debug.html")
    try:
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(confirm_response.text)
        print(f"?? HTML de confirmacion guardado en: {debug_path}", flush=True)
    except Exception as e:
        print(f"?? Error al guardar HTML: {e}", flush=True)

    soup = BeautifulSoup(confirm_response.text, "html.parser")
    alert_div = soup.find("div", class_="alert-success")
    if alert_div:
        for tag in alert_div.find_all(["a", "h4"]):
            tag.decompose()
        mensaje = alert_div.get_text(strip=True)
        return f"? {mensaje}"
    else:
        return "? Fallo al realizar la reserva"
