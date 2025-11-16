from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json
import os

app = Flask(__name__)

DATA_FILE = "mensaje.json"

# Cargar último mensaje si existe, si no crear uno por defecto
def load_message():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        msg = {
            "id": 0,
            "text": "Encara no hi ha cap missatge 💌",
            "timestamp": datetime.utcnow().isoformat(),
            "is_read": False
        }
        save_message(msg)
        return msg

def save_message(msg_dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(msg_dict, f, ensure_ascii=False, indent=2)

# Lo guardamos en memoria para ir rápido
mensaje_actual = load_message()


@app.route("/")
def index():
    # Página con el formulario para enviar mensajes
    return render_template("index.html", mensaje=mensaje_actual)


@app.route("/mensaje", methods=["POST"])
def nuevo_mensaje():
    global mensaje_actual

    data = request.get_json() if request.is_json else request.form
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Mensaje vacío"}), 400

    # Incrementamos el id del mensaje
    mensaje_actual["id"] = mensaje_actual.get("id", 0) + 1
    mensaje_actual["text"] = text
    mensaje_actual["timestamp"] = datetime.utcnow().isoformat()
    mensaje_actual["is_read"] = False

    save_message(mensaje_actual)

    return jsonify({"status": "ok", "mensaje": mensaje_actual})


@app.route("/ultimo_mensaje", methods=["GET"])
def ultimo_mensaje():
    # Endpoint que luego consumirá el ESP32
    return jsonify(mensaje_actual)


if __name__ == "__main__":
    # host="0.0.0.0" para poder entrar desde el mòbil en la mateixa WiFi
    app.run(host="0.0.0.0", port=5000, debug=True)
