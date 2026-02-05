from flask import Blueprint, jsonify, request, current_app
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.model import ClauseType

bp = Blueprint("clause_types", __name__)


class ClauseTypeIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


@bp.get("")
def list_clause_types():
    engine = current_app.extensions["db_engine"]

    with Session(engine) as session:
        items = session.query(ClauseType).order_by(ClauseType.name).all()
        return jsonify({"items": [{"id": x.id, "name": x.name} for x in items]}), 200


@bp.post("")
def create_clause_type():
    engine = current_app.extensions["db_engine"]

    try:
        payload = ClauseTypeIn.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": e.errors()}), 400

    with Session(engine) as session:
        ct = ClauseType(name=payload.name.strip())
        session.add(ct)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return jsonify({"error": "clause_type_name_exists"}), 409

        return jsonify({"id": ct.id, "name": ct.name}), 201
