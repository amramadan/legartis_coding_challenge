from flask import Flask, jsonify

from app.db import get_engine, ping_db

def create_app() -> Flask:
    app = Flask(__name__)
    engine = get_engine()

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/health/db")
    def health_db():
        ok = ping_db(engine)
        return jsonify({"db": "ok" if ok else "down"}), (200 if ok else 503)

    return app