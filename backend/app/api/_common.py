from __future__ import annotations

from contextlib import contextmanager
from flask import current_app, jsonify
from sqlalchemy.orm import Session


def json_error(code: str, status: int, **extra):
    payload = {"error": code}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


@contextmanager
def db_session():
    engine = current_app.extensions["db_engine"]
    with Session(engine) as session:
        yield session
