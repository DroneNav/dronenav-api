from flask import Blueprint, jsonify, request

from app.services.authority_service import (
    create_authority,
    get_authority_by_id,
    get_all_authorities,
    update_authority,
    delete_authority,
)

authorities_bp = Blueprint("authorities", __name__)


@authorities_bp.route("/api/authorities", methods=["POST"])
def create_authority_route():
    data = request.get_json()

    result, error = create_authority(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@authorities_bp.route("/api/authorities", methods=["GET"])
def get_authorities_route():
    authorities = get_all_authorities()

    return jsonify({
        "authorities": authorities
    })


@authorities_bp.route("/api/authorities/<authority_id>", methods=["GET"])
def get_authority_route(authority_id):
    authority = get_authority_by_id(authority_id)

    if authority is None:
        return jsonify({
            "status": "error",
            "message": "Authority not found"
        }), 404

    return jsonify(authority)


@authorities_bp.route("/api/authorities/<authority_id>", methods=["PUT"])
def update_authority_route(authority_id):
    data = request.get_json()

    result, error = update_authority(authority_id, data)

    if error:
        status_code = 404 if error == "Authority not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@authorities_bp.route("/api/authorities/<authority_id>", methods=["DELETE"])
def delete_authority_route(authority_id):
    result = delete_authority(authority_id)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Authority not found"
        }), 404

    return jsonify(result)

