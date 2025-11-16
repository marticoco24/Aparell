from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
from pathlib import Path
import json

app = Flask(__name__)

# ---------- Estado y persistencia sencilla ----------

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"


def default_state():
    return {
        "next_message_id": 1,
        "messages_state": {
            # Último mensaje que verá el aparato de marti (enviado por ella)
            "marti": None,
            # Último mensaje que verá el aparato de ella (enviado por marti)
            "ella": None,
        },
    }


def load_state():
    if STATE_FILE.exists():
        try:
            with STATE_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # asegurar estructura mínima
            if "next_message_id" not in data or "messages_state" not in data:
                return default_state()
            for d in ("marti", "ella"):
                data["messages_state"].setdefault(d, None)
            return data
        except Exception:
            return default_state()
    else:
        return default_state()


def save_state():
    try:
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "next_message_id": state["next_message_id"],
                    "messages_state": state["messages_state"],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception:
        # en Render el FS puede ser efímero, pero no pasa nada grave
        pass


state = load_state()

# devices_state no se persiste (no hace falta)
devices_state = {
    "marti": {
        "last_seen": None,
        # arrancamos como "no tienes nada pendiente"
        "last_seen_message_id": (
            state["messages_state"]["marti"]["id"]
            if state["messages_state"]["marti"] is not None
            else 0
        ),
    },
    "ella": {
        "last_seen": None,
        "last_seen_message_id": (
            state["messages_state"]["ella"]["id"]
            if state["messages_state"]["ella"] is not None
            else 0
        ),
    },
}


def is_online(last_seen, timeout_seconds=30):
    if last_seen is None:
        return False
    delta = datetime.now(timezone.utc) - last_seen
    return delta.total_seconds() <= timeout_seconds


# ---------- Rutas ----------


@app.route("/")
def index():
    # No mostramos el contenido del mensaje en la web por privacidad
    # pero podríamos pasar meta-info si quisiéramos.
    return render_template("index.html")


@app.route("/mensaje", methods=["POST"])
def nuevo_mensaje():
    """
    Cuerpo esperado (JSON):
    {
      "text": "t'estimo molt",
      "from": "marti" | "ella"
    }
    """
    data = request.get_json(silent=True) or request.form

    text = (data.get("text") or "").strip()
    from_ = (data.get("from") or "marti").strip().lower()

    if not text:
        return jsonify({"status": "error", "error": "Texto vacío"}), 400

    if from_ not in ("marti", "ella"):
        return jsonify({"status": "error", "error": "Campo 'from' inválido"}), 400

    # Destinatario: el otro
    to = "ella" if from_ == "marti" else "marti"

    msg_id = state["next_message_id"]
    state["next_message_id"] += 1

    mensaje = {
        "id": msg_id,
        "text": text,
        "from": from_,
        "to": to,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Guardamos como último mensaje pendiente para ese aparato
    state["messages_state"][to] = mensaje
    save_state()

    # MUY IMPORTANTE:
    # NO marcamos last_seen_message_id aquí -> así el aparato del 'to'
    # verá has_unread = True en /estado hasta que lo marque como visto.
    return jsonify(
        {
            "status": "ok",
            "to": to,
            "message": {
                "id": mensaje["id"],
                "from": mensaje["from"],
                "to": mensaje["to"],
                "timestamp": mensaje["timestamp"],
                # NO devolvemos el texto a la web si no queremos, pero lo dejo
                # por si lo quieres usar en debug (no lo muestra index.html).
                "text": mensaje["text"],
            },
        }
    )


@app.route("/estado")
def estado():
    """
    Endpoint para ESP32.
    GET /estado?device=marti | ella
    """
    device = request.args.get("device", "").strip().lower()
    if device not in ("marti", "ella"):
        return jsonify({"error": "device inválido"}), 400

    now = datetime.now(timezone.utc)
    devices_state[device]["last_seen"] = now

    # Mensaje pendiente para este aparato (buzón)
    mensaje = state["messages_state"].get(device)

    # Cálculo has_unread
    last_seen_id = devices_state[device]["last_seen_message_id"]
    if mensaje is None:
        has_unread = False
    else:
        has_unread = mensaje["id"] > last_seen_id

    # Estado del otro
    other = "ella" if device == "marti" else "marti"
    other_last_seen = devices_state[other]["last_seen"]
    other_online = is_online(other_last_seen, timeout_seconds=30)

    return jsonify(
        {
            "device": device,
            "other_device": other,
            "other_online": other_online,
            "has_unread": has_unread,
            "message": mensaje,  # puede ser None si aún no le han mandado nada
        }
    )


@app.route("/mensaje_visto", methods=["POST"])
def mensaje_visto():
    """
    Cuerpo esperado:
    {
      "device": "marti" | "ella",
      "message_id": 3
    }
    Lo llamará el ESP32 cuando haya mostrado el mensaje y acabado la animación.
    """
    data = request.get_json(silent=True) or {}

    device = (data.get("device") or "").strip().lower()
    if device not in ("marti", "ella"):
        return jsonify({"status": "error", "error": "device inválido"}), 400

    try:
        message_id = int(data.get("message_id"))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "error": "message_id inválido"}), 400

    # Solo actualizamos si ese ID tiene sentido (no hace falta que exista ya,
    # basta con que no sea en el futuro)
    if message_id <= state["next_message_id"]:
        devices_state[device]["last_seen_message_id"] = message_id

    return jsonify(
        {
            "status": "ok",
            "device": device,
            "last_seen_message_id": devices_state[device]["last_seen_message_id"],
        }
    )


if __name__ == "__main__":
    # En local; en Render se usará gunicorn app_v2:app
    app.run(host="0.0.0.0", port=5000, debug=True)
