from flask import Blueprint, jsonify, request, current_app
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.model import ClauseType, ClausePattern

bp = Blueprint("clause_types", __name__)


class ClausePatternIn(BaseModel):
    pattern: str = Field(min_length=1, max_length=500)
    is_regex: bool = False

class ClauseTypeIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    patterns: list[ClausePatternIn] = Field(default_factory=list)

@bp.get("")
def list_clause_types():
    engine = current_app.extensions["db_engine"]

    with Session(engine) as session:
        items = (
            session.query(ClauseType)
            .options(selectinload(ClauseType.patterns))
            .order_by(ClauseType.name)
            .all()
        )

        return jsonify({
            "items": [
                {
                    "id": x.id,
                    "name": x.name,
                    "patterns": [
                        {"pattern": p.pattern, "is_regex": p.is_regex}
                        for p in x.patterns
                    ],
                }
                for x in items
            ]
        }), 200

@bp.post("")
def create_clause_type():
    engine = current_app.extensions["db_engine"]

    try:
        payload = ClauseTypeIn.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": e.errors()}), 400

    with Session(engine) as session:
        ct = ClauseType(name=payload.name.strip())

        for p in payload.patterns:
            ct.patterns.append(
                ClausePattern(pattern=p.pattern.strip(), is_regex=p.is_regex)
            )

        session.add(ct)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return jsonify({"error": "clause_type_name_exists"}), 409

        return jsonify({
            "id": ct.id,
            "name": ct.name,
            "patterns": [{"pattern": p.pattern, "is_regex": p.is_regex} for p in ct.patterns],
        }), 201
