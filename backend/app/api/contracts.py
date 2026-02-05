from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import selectinload

from app.api._common import db_session, json_error
from app.model import ClauseType, Contract, ContractClause
from app.storage_local import LocalFileStorage

bp = Blueprint("contracts", __name__)

ALLOWED_EXTS = {".txt", ".md", ".markdown"}


def _detect_clause(contract_text: str, patterns) -> bool:
    hay_lower = contract_text.lower()
    for p in patterns:
        if p.is_regex:
            if re.search(p.pattern, contract_text, flags=re.IGNORECASE):
                return True
        else:
            if p.pattern.lower() in hay_lower:
                return True
    return False


def _allowed_filename(name: str) -> bool:
    _, ext = os.path.splitext(name.lower())
    return ext in ALLOWED_EXTS


class ClauseOverrideIn(BaseModel):
    confirmed: bool | None


@bp.post("")
def upload_contract():
    if "file" not in request.files:
        return json_error("missing_file", 400)

    f = request.files["file"]
    original_filename = (f.filename or "").strip()
    if not original_filename:
        return json_error("missing_filename", 400)

    if not _allowed_filename(original_filename):
        return json_error(
            "unsupported_file_type",
            415,
            allowed=sorted(ALLOWED_EXTS),
        )

    # Size guardrail (Flask also enforces MAX_CONTENT_LENGTH if set)
    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH")
    if max_bytes and request.content_length and request.content_length > max_bytes:
        return json_error("file_too_large", 413, max_bytes=max_bytes)

    # UTF-8 + "looks like text" sniff (first 64KB)
    head = f.stream.read(64 * 1024)
    if b"\x00" in head:
        return json_error("binary_file_rejected", 400)
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        return json_error(
            "invalid_encoding",
            400,
            hint="upload UTF-8 text/markdown",
        )

    storage: LocalFileStorage = current_app.extensions["storage"]
    stored = storage.save(f.stream, original_filename=original_filename, first_chunk=head)

    with db_session() as session:
        contract = Contract(
            original_filename=original_filename,
            storage_backend=stored.backend,
            storage_key=stored.key,
            size_bytes=stored.size_bytes,
            sha256_hex=stored.sha256_hex,
            processing_status="processing",
        )
        session.add(contract)
        session.flush()  # obtain contract.id before writing matrix rows

        try:
            clause_types = (
                session.query(ClauseType)
                .options(selectinload(ClauseType.patterns))
                .order_by(ClauseType.id)
                .all()
            )

            with storage.open(stored.key) as fh:
                contract_text = fh.read().decode("utf-8", errors="strict")

            rows: list[ContractClause] = []
            for ct in clause_types:
                detected = _detect_clause(contract_text, ct.patterns) if ct.patterns else False
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

            # best-effort: persist failure state for this contract row
            session.add(contract)
            contract.processing_status = "failed"
            contract.processed_at = datetime.now(timezone.utc)
            contract.error_message = str(e)[:2000]
            session.commit()

            return json_error("processing_failed", 500)

        return jsonify(
            {
                "id": contract.id,
                "original_filename": contract.original_filename,
                "processing_status": contract.processing_status,
                "storage": {
                    "backend": contract.storage_backend,
                    "key": contract.storage_key,
                    "size_bytes": contract.size_bytes,
                    "sha256": contract.sha256_hex,
                },
            }
        ), 201


@bp.get("")
def list_contracts():
    with db_session() as session:
        items = session.query(Contract).order_by(Contract.id.desc()).all()
        return jsonify(
            {
                "items": [
                    {
                        "id": c.id,
                        "original_filename": c.original_filename,
                        "processing_status": c.processing_status,
                        "created_at": c.created_at.isoformat(),
                        "processed_at": c.processed_at.isoformat() if c.processed_at else None,
                    }
                    for c in items
                ]
            }
        ), 200


@bp.get("/<int:contract_id>")
def get_contract(contract_id: int):
    with db_session() as session:
        c = session.get(Contract, contract_id)
        if not c:
            return json_error("contract_not_found", 404)

        clause_types = session.query(ClauseType).order_by(ClauseType.name).all()

        rows = (
            session.query(ContractClause)
            .filter(ContractClause.contract_id == contract_id)
            .all()
        )
        by_ct = {r.clause_type_id: r for r in rows}

        matrix = []
        for ct in clause_types:
            r = by_ct.get(ct.id)
            detected = bool(r.detected) if r else False
            confirmed = r.confirmed if r else None
            effective = confirmed if confirmed is not None else detected

            matrix.append(
                {
                    "clause_type": {"id": ct.id, "name": ct.name},
                    "detected": detected,
                    "confirmed": confirmed,
                    "effective": effective,
                }
            )

        return jsonify(
            {
                "contract": {
                    "id": c.id,
                    "original_filename": c.original_filename,
                    "processing_status": c.processing_status,
                    "created_at": c.created_at.isoformat(),
                    "processed_at": c.processed_at.isoformat() if c.processed_at else None,
                    "error_message": c.error_message,
                },
                "matrix": matrix,
            }
        ), 200


@bp.patch("/<int:contract_id>/clauses/<int:clause_type_id>")
def set_clause_override(contract_id: int, clause_type_id: int):
    try:
        payload = ClauseOverrideIn.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return json_error("validation_error", 400, details=e.errors())

    with db_session() as session:
        c = session.get(Contract, contract_id)
        if not c:
            return json_error("contract_not_found", 404)

        ct = session.get(ClauseType, clause_type_id)
        if not ct:
            return json_error("clause_type_not_found", 404)

        row = (
            session.query(ContractClause)
            .filter(
                ContractClause.contract_id == contract_id,
                ContractClause.clause_type_id == clause_type_id,
            )
            .one_or_none()
        )

        # Should exist if detection ran, but keep it resilient.
        if not row:
            row = ContractClause(
                contract_id=contract_id,
                clause_type_id=clause_type_id,
                detected=False,
                confirmed=None,
            )
            session.add(row)

        row.confirmed = payload.confirmed
        session.commit()

        return jsonify(
            {
                "contract_id": contract_id,
                "clause_type_id": clause_type_id,
                "confirmed": row.confirmed,
            }
        ), 200
