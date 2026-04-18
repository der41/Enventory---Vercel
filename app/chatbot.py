from flask import Blueprint, request, jsonify
from flask_login import current_user

from .models.chatbot import ask_bot

bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


@bp.route("/message", methods=["POST"])
def message():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"reply": "Please type something."}), 400

    uid = current_user.id if current_user.is_authenticated else None
    reply = ask_bot(text, uid)
    return jsonify({"reply": reply})