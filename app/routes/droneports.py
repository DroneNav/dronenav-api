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
Flask route implementation source file for support of DronePort APIs.

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

from app.services.droneport_service import (
    create_droneport,
    get_droneport_by_id,
    get_all_droneports,
    update_droneport,
    patch_droneport,
    delete_droneport,
)

droneports_bp = Blueprint("droneports", __name__)

CORS(
    droneports_bp,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


@droneports_bp.route("/api/droneports", methods=["POST", "OPTIONS"])
def create_droneport_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_droneport(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@droneports_bp.route("/api/droneports", methods=["GET", "OPTIONS"])
def get_droneports_route():

    if request.method == "OPTIONS":
        return "", 204

    droneports = get_all_droneports()

    return jsonify({
        "droneports": droneports
    })


@droneports_bp.route("/api/droneports/<droneport_id>", methods=["GET", "OPTIONS"])
def get_droneport_route(droneport_id):

    if request.method == "OPTIONS":
        return "", 204

    droneport = get_droneport_by_id(droneport_id)

    if droneport is None:
        return jsonify({
            "status": "error",
            "message": "DronePort not found"
        }), 404

    return jsonify(droneport)


@droneports_bp.route("/api/droneports/<droneport_id>", methods=["PUT", "OPTIONS"])
def update_droneport_route(droneport_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = update_droneport(droneport_id, data)

    if error:
        status_code = 404 if error == "DronePort not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@droneports_bp.route("/api/droneports/<droneport_id>", methods=["PATCH", "OPTIONS"])
def patch_droneport_route(droneport_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_droneport(droneport_id, data)

    if error:
        status_code = 404 if error == "DronePort not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@droneports_bp.route("/api/droneports/<droneport_id>", methods=["DELETE", "OPTIONS"])
def delete_droneport_route(droneport_id):

    if request.method == "OPTIONS":
        return "", 204

    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_droneport(droneport_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "DronePort not found"
        }), 404

    return jsonify(result)

