from logging import getLogger

from flask import Blueprint, jsonify

from models.main_models import Doctor, Patient, SessionLocal

logger = getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/<entity>/all", methods=["GET"])
def get_all_items(entity):
    with SessionLocal() as db_session:
        model_map = {"doctors": Doctor, "patients": Patient}
        model = model_map.get(entity)

        if not model:
            return jsonify({"error": "Invalid entity"}), 400

        doctors = db_session.query(model).all()
    if not doctors:
        return jsonify({"error": "Not found"})
    match entity:
        case "doctors":
            data = [
                {"id": d.id, "name": d.name, "age": d.age, "email": d.email, "contact": d.contact, "specialization": d.specialization or ""}
                for d in doctors
            ]
        case "patients":
            data = [
                {"id": p.id, "name": p.name, "age": p.age, "email": p.email, "contact": p.contact}
                for p in doctors
            ]
    return jsonify(data)

@api_bp.route("/<entity>/<int:item_id>", methods=["DELETE"])
def delete_item(entity, item_id):
    with SessionLocal() as db_session:
        model_map = {"doctor": Doctor, "patient": Patient}
        model = model_map.get(entity)

        if not model:
            return jsonify({"error": "Invalid entity"}), 400

        item = db_session.get(model, item_id)
        if not item:
            return jsonify({"error": "Not found"}), 404

        db_session.delete(item)
        db_session.commit()
    return jsonify({"status": "deleted"})
