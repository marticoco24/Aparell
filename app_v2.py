from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
import json
import os

app = Flask(__name__)

DATA_FILE = "mensaje.json"

# -------------------------------
# Carga y guardado del mensaje
# -------------------------------
def load_message():
    """Carga el último mensaje desde disco o crea uno por defecto."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        msg = {
            "id": 0,
            "text": "Encara no hi ha cap missatge 💌",
            "from": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        save_message(msg)
        return msg


def save_message(msg_dict):
    """Guarda el mensaje actual en disco."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(msg_dict, f, ensure_ascii=False, indent=2)


# Mensaje actual (compartido por la parella)
mensaje_actual = load_message()

# -------------------------------
# Estado de los dos aparatos
# -------------------------------
# Tendremos dos "devices": marti y ella
# Al iniciar, asumimos que ambos han visto el mensaje actual (si existe)
devices_state = {
    "marti": {
        "last_seen": None,                     # última vez que su ESP32 ha contactado
        "last_seen_message_id": mensaje_actual["id"]
    },
    "ella": {
        "last_seen": None,
        "last_seen_message_id": mensaje_actual["id"]
    }
}


def get_other_device(device):
    if device == "marti":
        return "ella"
    elif device == "ella":
        return "marti"
    else:
        return None


def is_online(last_seen, timeout_seconds=30):
    """Devuelve True si last_seen fue hace menos de timeout_seconds."""
    if last_seen is None:
        return False
    now = datetime.now(timezone.utc)
    delta = (now - last_seen).total_seconds()
    return delta < timeout_seconds


# -------------------------------
# Rutas web
# -------------------------------

@app.route("/")
def index():
    """Página para enviar mensajes (frontend humano)."""
    # Pasamos el mensaje completo al template
    return render_template("index.html", mensaje=mensaje_actual)


@app.route("/mensaje", methods=["POST"])
def nuevo_mensaje():
    """
    Crea un mensaje nuevo.
    De momento asumimos que lo envía 'marti' por defecto.
    Más adelante podremos dejar que el front indique 'from'.
    """
    global mensaje_actual

    data = request.get_json() if request.is_json else request.form
    text = data.get("text", "").strip()
    from_device = data.get("from", "marti")  # por defecto, tú

    if not text:
        return jsonify({"error": "Mensaje vacío"}), 400

    # Creamos mensaje nuevo
    new_id = mensaje_actual.get("id", 0) + 1
    mensaje_actual = {
        "id": new_id,
        "text": text,
        "from": from_device,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    save_message(mensaje_actual)

    # No tocamos last_seen_message_id aquí:
    # así, para cualquier device cuyo last_seen_message_id < new_id,
    # has_unread será True hasta que llame a /mensaje_visto

    return jsonify({"status": "ok", "mensaje": mensaje_actual})


@app.route("/estado", methods=["GET"])
def estado():
    """
    Endpoint pensado para el ESP32.
    Ejemplo: /estado?device=marti

    Devuelve:
    - message: último mensaje (id, text, from, timestamp)
    - has_unread: si este device tiene mensaje nuevo
    - other_online: si el otro device ha enviado ping recientemente
    """
    global mensaje_actual, devices_state

    device = request.args.get("device", "").strip().lower()
    if device not in devices_state:
        return jsonify({"error": "device inválido, usa 'marti' o 'ella'"}), 400

    now = datetime.now(timezone.utc)

    # Marcamos que este device "se ha visto" ahora
    devices_state[device]["last_seen"] = now

    # Calculamos si tiene mensaje nuevo
    last_seen_msg_id = devices_state[device]["last_seen_message_id"]
    has_unread = mensaje_actual["id"] > last_seen_msg_id

    # Calculamos si el otro está online
    other = get_other_device(device)
    other_online = is_online(devices_state[other]["last_seen"])

    # Construimos la respuesta
    response = {
        "device": device,
        "other_device": other,
        "other_online": other_online,
        "has_unread": has_unread,
        "message": mensaje_actual
    }
    return jsonify(response)


@app.route("/mensaje_visto", methods=["POST"])
def mensaje_visto():
    """
    Endpoint para que el ESP32 marque el mensaje como visto.
    Body JSON: { "device": "marti", "message_id": 3 }
    """
    global devices_state, mensaje_actual

    data = request.get_json(force=True)
    device = data.get("device", "").strip().lower()
    msg_id = data.get("message_id")

    if device not in devices_state:
        return jsonify({"error": "device inválido"}), 400

    if not isinstance(msg_id, int):
        return jsonify({"error": "message_id debe ser int"}), 400

    # Solo actualizamos si coincide con el mensaje actual o uno anterior
    if msg_id <= mensaje_actual["id"]:
        devices_state[device]["last_seen_message_id"] = msg_id

    return jsonify({
        "status": "ok",
        "device": device,
        "last_seen_message_id": devices_state[device]["last_seen_message_id"]
    })


if __name__ == "__main__":
    # host="0.0.0.0" para poder entrar desde el mòbil en la mateixa WiFi
    app.run(host="0.0.0.0", port=5000, debug=True)
