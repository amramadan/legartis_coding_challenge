from __future__ import annotations

import os

from flask import Flask
from sqlalchemy import create_engine

from app.api.clause_types import bp as clause_types_bp
from app.api.contracts import bp as contracts_bp
from app.api.health import bp as health_bp
from app.storage_local import LocalFileStorage


def create_app() -> Flask:
    app = Flask(__name__)

    db_url = os.getenv("DATABASE_URL") or app.config.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    app.config["DATABASE_URL"] = db_url

    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_BYTES", "26214400"))
    storage_dir = os.getenv("CONTRACT_STORAGE_DIR", "./data/contracts")

    engine = create_engine(db_url, pool_pre_ping=True)
    app.extensions["db_engine"] = engine
    app.extensions["storage"] = LocalFileStorage(storage_dir)

    app.register_blueprint(health_bp)  # /health, /health/db
    app.register_blueprint(clause_types_bp, url_prefix="/api/clause-types")
    app.register_blueprint(contracts_bp, url_prefix="/api/contracts")

    return app
