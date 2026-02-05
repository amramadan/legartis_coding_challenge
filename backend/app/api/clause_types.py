from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.api._common import db_session, json_error
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
    with db_session() as session:
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
    try:
        payload = ClauseTypeIn.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return json_error("validation_error", 400, details=e.errors())

    with db_session() as session:
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
            return json_error("clause_type_name_exists", 409)

        return jsonify({
            "id": ct.id,
            "name": ct.name,
            "patterns": [{"pattern": p.pattern, "is_regex": p.is_regex} for p in ct.patterns],
        }), 201
