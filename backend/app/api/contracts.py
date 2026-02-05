from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.orm import Session, selectinload

from app.model import Contract, ClauseType, ContractClause
from app.storage_local import LocalFileStorage

bp = Blueprint("contracts", __name__)

ALLOWED_EXTS = {".txt", ".md", ".markdown"}

def _detect_clause(text: str, patterns) -> bool:
    hay_lower = text.lower()
    for p in patterns:
        if p.is_regex:
            if re.search(p.pattern, text, flags=re.IGNORECASE):
                return True
        else:
            if p.pattern.lower() in hay_lower:
                return True
    return False

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
            processing_status="processing",
        )
        session.add(contract)
        session.flush()  

        try:
            clause_types = (
                session.query(ClauseType)
                .options(selectinload(ClauseType.patterns))
                .order_by(ClauseType.id)
                .all()
            )

            with storage.open(stored.key) as fh:
                text = fh.read().decode("utf-8", errors="strict")

            # Build matrix rows: one per clause type
            rows: list[ContractClause] = []
            for ct in clause_types:
                detected = _detect_clause(text, ct.patterns) if ct.patterns else False
                rows.append(
                    ContractClause(
                        contract_id=contract.id,
                        clause_type_id=ct.id,
                        detected=detected,
                        confirmed=None,
                    )
                )

            session.add_all(rows)

            contract.processing_status = "processed"
            contract.processed_at = datetime.now(timezone.utc)
            contract.error_message = None

            session.commit()

        except Exception as e:
            session.rollback()
            session.add(contract)
            contract.processing_status = "failed"
            contract.processed_at = datetime.now(timezone.utc)
            contract.error_message = str(e)[:2000]
            session.commit()
            return jsonify({"error": "processing_failed"}), 500

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
