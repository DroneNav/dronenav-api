from flask import Blueprint, jsonify, request

from app.services.zone_service import (
    create_zone,
    get_zone_by_id,
    get_all_zones,
    update_zone,
    delete_zone,
)

zones_bp = Blueprint("zones", __name__)


@zones_bp.route("/api/zones", methods=["POST"])
def create_zone_route():
    data = request.get_json()

    result, error = create_zone(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@zones_bp.route("/api/zones", methods=["GET"])
def get_zones_route():
    zones = get_all_zones()

    return jsonify({
        "zones": zones
    })


@zones_bp.route("/api/zones/<zone_id>", methods=["GET"])
def get_zone_route(zone_id):
    zone = get_zone_by_id(zone_id)

    if zone is None:
        return jsonify({
            "status": "error",
            "message": "Zone not found"
        }), 404

    return jsonify(zone)


@zones_bp.route("/api/zones/<zone_id>", methods=["PUT"])
def update_zone_route(zone_id):
    data = request.get_json()

    result, error = update_zone(zone_id, data)

    if error:
        status_code = 404 if error == "Zone not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@zones_bp.route("/api/zones/<zone_id>", methods=["DELETE"])
def delete_zone_route(zone_id):
    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_zone(zone_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Zone not found"
        }), 404

    return jsonify(result)

