from flask import Blueprint, jsonify, request

from app.services.route_service import (
    create_route,
    get_route_by_id,
    get_all_routes,
    update_route,
    delete_route,
)

routes_bp = Blueprint("routes", __name__)


@routes_bp.route("/api/routes", methods=["POST"])
def create_route_route():
    data = request.get_json()

    result, error = create_route(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@routes_bp.route("/api/routes", methods=["GET"])
def get_routes_route():
    routes = get_all_routes()

    return jsonify({
        "routes": routes
    })


@routes_bp.route("/api/routes/<route_id>", methods=["GET"])
def get_route_route(route_id):
    route = get_route_by_id(route_id)

    if route is None:
        return jsonify({
            "status": "error",
            "message": "Route not found"
        }), 404

    return jsonify(route)


@routes_bp.route("/api/routes/<route_id>", methods=["PUT"])
def update_route_route(route_id):
    data = request.get_json()

    result, error = update_route(route_id, data)

    if error:
        status_code = 404 if error == "Route not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@routes_bp.route("/api/routes/<route_id>", methods=["DELETE"])
def delete_route_route(route_id):
    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_route(route_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Route not found"
        }), 404

    return jsonify(result)

