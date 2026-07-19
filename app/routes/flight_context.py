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
Flight Context API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-18

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.flight_context_service import get_flight_context

flight_context_bp = Blueprint("flight_context", __name__)

CORS(
    flight_context_bp,
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

@flight_context_bp.route("/api/flight-context", methods=["POST", "OPTIONS"])
def get_flight_context_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    if data is None:
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON."
        }), 400

    context, error = get_flight_context(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(context), 200

