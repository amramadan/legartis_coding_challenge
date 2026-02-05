from __future__ import annotations

import os
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.orm import Session

from app.model import Contract
from app.storage_local import LocalFileStorage

bp = Blueprint("contracts", __name__)

ALLOWED_EXTS = {".txt", ".md", ".markdown"}


def _allowed_filename(name: str) -> bool:
    _, ext = os.path.splitext(name.lower())
    return ext in ALLOWED_EXTS


@bp.post("")
def upload_contract():
    if "file" not in request.files:
        return jsonify({"error": "missing_file"}), 400

    f = request.files["file"]
    original_filename = (f.filename or "").strip()
    if not original_filename:
        return jsonify({"error": "missing_filename"}), 400

    if not _allowed_filename(original_filename):
        return jsonify({"error": "unsupported_file_type", "allowed": sorted(ALLOWED_EXTS)}), 415

    # Size guardrail (Flask also enforces MAX_CONTENT_LENGTH if set)
    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH")
    if max_bytes and request.content_length and request.content_length > max_bytes:
        return jsonify({"error": "file_too_large", "max_bytes": max_bytes}), 413

    # UTF-8 + "looks like text" sniff (first 64KB)
    head = f.stream.read(64 * 1024)
    if b"\x00" in head:
        return jsonify({"error": "binary_file_rejected"}), 400
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "invalid_encoding", "hint": "upload UTF-8 text/markdown"}), 400

    storage: LocalFileStorage = current_app.extensions["storage"]
    stored = storage.save(f.stream, original_filename=original_filename, first_chunk=head)

    engine = current_app.extensions["db_engine"]
    with Session(engine) as session:
        contract = Contract(
            original_filename=original_filename,
            storage_backend=stored.backend,
            storage_key=stored.key,
            size_bytes=stored.size_bytes,
            sha256_hex=stored.sha256_hex,
            processing_status="uploaded",
        )
        session.add(contract)
        session.commit()

        return jsonify({
            "id": contract.id,
            "original_filename": contract.original_filename,
            "processing_status": contract.processing_status,
            "storage": {
                "backend": contract.storage_backend,
                "key": contract.storage_key,
                "size_bytes": contract.size_bytes,
                "sha256": contract.sha256_hex,
            },
        }), 201
