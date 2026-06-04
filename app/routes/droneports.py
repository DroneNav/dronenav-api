from flask import Blueprint, jsonify, request

from app.services.droneport_service import (
    create_droneport,
    get_droneport_by_id,
    get_all_droneports,
    update_droneport,
    delete_droneport,
)

droneports_bp = Blueprint("droneports", __name__)


@droneports_bp.route("/api/droneports", methods=["POST"])
def create_droneport_route():
    data = request.get_json()

    result, error = create_droneport(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@droneports_bp.route("/api/droneports", methods=["GET"])
def get_droneports_route():
    droneports = get_all_droneports()

    return jsonify({
        "droneports": droneports
    })


@droneports_bp.route("/api/droneports/<droneport_id>", methods=["GET"])
def get_droneport_route(droneport_id):
    droneport = get_droneport_by_id(droneport_id)

    if droneport is None:
        return jsonify({
            "status": "error",
            "message": "DronePort not found"
        }), 404

    return jsonify(droneport)


@droneports_bp.route("/api/droneports/<droneport_id>", methods=["PUT"])
def update_droneport_route(droneport_id):
    data = request.get_json()

    result, error = update_droneport(droneport_id, data)

    if error:
        status_code = 404 if error == "DronePort not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@droneports_bp.route("/api/droneports/<droneport_id>", methods=["DELETE"])
def delete_droneport_route(droneport_id):
    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_droneport(droneport_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "DronePort not found"
        }), 404

    return jsonify(result)

