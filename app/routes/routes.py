"""
DroneNav - Drone Navigation Network System
Copyright (C) 2026 DroneNav Project

This file is part of DroneNav.

DroneNav is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

DroneNav is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with DroneNav. If not, see https://www.gnu.org/licenses/.

Project:
DroneNav - Drone Navigation Network System

Repository:
https://github.com/DroneNav

License:
GNU Affero General Public License v3.0 (AGPL-3.0-or-later)

Purpose:
Flask route implementation source file to support Route APIs.

Author:
DroneNav Project Contributors

Created:
2026-06-04

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.route_service import (
    create_route,
    get_route_by_id,
    get_all_routes,
    update_route,
    patch_route,
    delete_route,
)

routes_bp = Blueprint("routes", __name__)

CORS(
    routes_bp,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


@routes_bp.route("/api/routes", methods=["POST", "OPTIONS"])
def create_route_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_route(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@routes_bp.route("/api/routes", methods=["GET", "OPTIONS"])
def get_routes_route():

    if request.method == "OPTIONS":
        return "", 204

    routes = get_all_routes()

    return jsonify({
        "routes": routes
    })


@routes_bp.route("/api/routes/<route_id>", methods=["GET", "OPTIONS"])
def get_route_route(route_id):

    if request.method == "OPTIONS":
        return "", 204

    route = get_route_by_id(route_id)

    if route is None:
        return jsonify({
            "status": "error",
            "message": "Route not found"
        }), 404

    return jsonify(route)


@routes_bp.route("/api/routes/<route_id>", methods=["PUT", "OPTIONS"])
def update_route_route(route_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = update_route(route_id, data)

    if error:
        status_code = 404 if error == "Route not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@routes_bp.route("/api/routes/<route_id>", methods=["PATCH", "OPTIONS"])
def patch_route_route(route_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_route(route_id, data)

    if error:
        status_code = 404 if error == "Route not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@routes_bp.route("/api/routes/<route_id>", methods=["DELETE", "OPTIONS"])
def delete_route_route(route_id):

    if request.method == "OPTIONS":
        return "", 204

    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_route(route_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Route not found"
        }), 404

    return jsonify(result)

