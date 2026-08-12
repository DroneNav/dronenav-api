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
Flight Actual Path API route layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-08-12

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.flight_actual_path_service import (
    create_flight_actual_path,
    update_flight_actual_path,
    get_flight_actual_path,
)

flight_actual_path_bp = Blueprint("flight_actual_path", __name__)

CORS(
    flight_actual_path_bp,
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


@flight_actual_path_bp.route(
    "/api/actual-paths/<flight_execution_id>",
    methods=["POST", "OPTIONS"],
)
def create_flight_actual_path_route(
    flight_execution_id,
):
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}

    try:
        result = create_flight_actual_path(
            flight_execution_id,
            data,
        )
    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400

    return jsonify(result), 201


@flight_actual_path_bp.route(
    "/api/actual-paths/<flight_execution_id>",
    methods=["PATCH", "OPTIONS"],
)
def update_flight_actual_path_route(
    flight_execution_id,
):
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}

    try:
        result = update_flight_actual_path(
            flight_execution_id,
            data,
        )
    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400

    if result is None:
        return jsonify({
            "status": "error",
            "message": (
                "Actual path not found, flight_id does not match, "
                "or path is already complete."
            ),
        }), 404

    return jsonify(result)


@flight_actual_path_bp.route(
    "/api/actual-paths/<flight_execution_id>",
    methods=["GET", "OPTIONS"],
)
def get_flight_actual_path_route(
    flight_execution_id,
):
    if request.method == "OPTIONS":
        return "", 204

    result = get_flight_actual_path(
        flight_execution_id
    )

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Actual path not found.",
        }), 404

    return jsonify(result)

