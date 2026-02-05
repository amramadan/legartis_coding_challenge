from flask import Flask, jsonify
from sqlalchemy import create_engine

from app.api.clause_types import bp as clause_types_bp
from app.model import Base


def create_app() -> Flask:
    app = Flask(__name__)

    # DB engine (we already set DATABASE_URL in docker-compose)
    db_url = app.config.get("DATABASE_URL")  # not set by default
    # Prefer env var, fallback to config
    import os
    db_url = os.getenv("DATABASE_URL", db_url)
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(db_url, pool_pre_ping=True)
    app.extensions["db_engine"] = engine

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/health/db")
    def health_db():
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return jsonify({"db": "ok"}), 200
        except Exception:
            return jsonify({"db": "down"}), 503

    app.register_blueprint(clause_types_bp, url_prefix="/api/clause-types")

    return app
