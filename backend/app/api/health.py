from __future__ import annotations

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

bp = Blueprint("health", __name__)

@bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@bp.get("/health/db")
def health_db():
    engine = current_app.extensions["db_engine"]
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"db": "ok"}), 200
    except Exception:
        return jsonify({"db": "down"}), 503
