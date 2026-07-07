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
Flight Band API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-05

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.flight_band_service import (
    create_flight_band,
    get_flight_band_by_id,
    get_all_flight_bands,
    update_flight_band,
    patch_flight_band,
    delete_flight_band,
)


flight_bands_bp = Blueprint("flight_bands", __name__)

CORS(
    flight_bands_bp,
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


@flight_bands_bp.route("/api/flight-bands", methods=["POST", "OPTIONS"])
def create_flight_band_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_flight_band(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@flight_bands_bp.route("/api/flight-bands", methods=["GET", "OPTIONS"])
def get_flight_bands_route():

    if request.method == "OPTIONS":
        return "", 204

    flight_class = request.args.get("flight_class")
    operational_status = request.args.get("operational_status")

    flight_bands = get_all_flight_bands(
        flight_class,
        operational_status
    )

    return jsonify({
        "flight_bands": flight_bands
    })


@flight_bands_bp.route("/api/flight-bands/<flight_band_id>", methods=["GET", "OPTIONS"])
def get_flight_band_route(flight_band_id):

    if request.method == "OPTIONS":
        return "", 204

    flight_band = get_flight_band_by_id(flight_band_id)

    if flight_band is None:
        return jsonify({
            "status": "error",
            "message": "Flight band not found"
        }), 404

    return jsonify(flight_band)


@flight_bands_bp.route("/api/flight-bands/<flight_band_id>", methods=["PUT", "OPTIONS"])
def update_flight_band_route(flight_band_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = update_flight_band(flight_band_id, data)

    if error:
        status_code = 404 if error == "Flight band not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@flight_bands_bp.route("/api/flight-bands/<flight_band_id>", methods=["PATCH", "OPTIONS"])
def patch_flight_band_route(flight_band_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_flight_band(flight_band_id, data)

    if error:
        status_code = 404 if error == "Flight band not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@flight_bands_bp.route("/api/flight-bands/<flight_band_id>", methods=["DELETE", "OPTIONS"])
def delete_flight_band_route(flight_band_id):

    if request.method == "OPTIONS":
        return "", 204

    result = delete_flight_band(flight_band_id)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Flight band not found"
        }), 404

    return jsonify(result)

