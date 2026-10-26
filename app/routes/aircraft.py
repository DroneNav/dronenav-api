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
Aircraft API route layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-10-25

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.aircraft_service import (
    create_aircraft,
    get_aircraft_by_id,
    get_aircraft_by_aviator,
    update_aircraft,
    patch_aircraft,
    delete_aircraft,
)

aircraft_bp = Blueprint("aircraft", __name__)

CORS(
    aircraft_bp,
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


@aircraft_bp.route("/api/aircraft", methods=["POST", "OPTIONS"])
def create_aircraft_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_aircraft(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@aircraft_bp.route("/api/aircraft", methods=["GET", "OPTIONS"])
def get_aircraft_list_route():

    if request.method == "OPTIONS":
        return "", 204

    aviator_id = request.args.get("aviator_id")

    if not aviator_id:
        return jsonify({
            "status": "error",
            "message": "Missing required parameter: aviator_id"
        }), 400

    aircraft = get_aircraft_by_aviator(aviator_id)

    return jsonify({
        "aircraft": aircraft
    })


@aircraft_bp.route("/api/aircraft/<aircraft_id>", methods=["GET", "OPTIONS"])
def get_aircraft_route(aircraft_id):

    if request.method == "OPTIONS":
        return "", 204

    aircraft = get_aircraft_by_id(aircraft_id)

    if aircraft is None:
        return jsonify({
            "status": "error",
            "message": "Aircraft not found"
        }), 404

    return jsonify(aircraft)


@aircraft_bp.route("/api/aircraft/<aircraft_id>", methods=["PUT", "OPTIONS"])
def update_aircraft_route(aircraft_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = update_aircraft(aircraft_id, data)

    if error:
        status_code = 404 if error == "Aircraft not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@aircraft_bp.route("/api/aircraft/<aircraft_id>", methods=["PATCH", "OPTIONS"])
def patch_aircraft_route(aircraft_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_aircraft(aircraft_id, data)

    if error:
        status_code = 404 if error == "Aircraft not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@aircraft_bp.route("/api/aircraft/<aircraft_id>", methods=["DELETE", "OPTIONS"])
def delete_aircraft_route(aircraft_id):

    if request.method == "OPTIONS":
        return "", 204

    result, error = delete_aircraft(aircraft_id)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 404

    return jsonify(result)



