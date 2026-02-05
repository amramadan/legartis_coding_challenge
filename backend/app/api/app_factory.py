import os

from flask import Flask, jsonify
from sqlalchemy import create_engine

from app.storage_local import LocalFileStorage

from app.api.health import bp as health_bp
from app.api.clause_types import bp as clause_types_bp
from app.api.contracts import bp as contracts_bp


def create_app() -> Flask:
    app = Flask(__name__)

    # DB engine (we already set DATABASE_URL in docker-compose)
    db_url = app.config.get("DATABASE_URL")  # not set by default
    # Prefer env var, fallback to config
    db_url = os.getenv("DATABASE_URL", db_url)
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(db_url, pool_pre_ping=True)
    app.extensions["db_engine"] = engine

    max_upload = int(os.getenv("MAX_UPLOAD_BYTES", "26214400"))
    app.config["MAX_CONTENT_LENGTH"] = max_upload

    storage_dir = os.getenv("CONTRACT_STORAGE_DIR", "./data/contracts")
    app.extensions["storage"] = LocalFileStorage(storage_dir)

    app.register_blueprint(health_bp)
    app.register_blueprint(clause_types_bp, url_prefix="/api/clause-types")
    app.register_blueprint(contracts_bp, url_prefix="/api/contracts")

    return app
