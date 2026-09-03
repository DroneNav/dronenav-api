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
TFR API route layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-09-01

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.tfr_service import (
    get_tfrs,
    get_tfrs_for_geometry,
)

tfrs_bp = Blueprint("tfrs", __name__)

CORS(
    tfrs_bp,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


@tfrs_bp.route("/api/tfrs", methods=["GET", "OPTIONS"])
def get_tfrs_route():

    if request.method == "OPTIONS":
        return "", 204

    tfrs = get_tfrs()

    return jsonify({
        "tfrs": tfrs
    })


@tfrs_bp.route("/api/tfrs/applicability", methods=["POST", "OPTIONS"])
def get_tfr_applicability_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}

    geometry = data.get("geometry")

    if geometry is None:
        return jsonify({
            "error": "Missing geometry"
        }), 400

    try:
        tfrs = get_tfrs_for_geometry(
            geometry
        )
    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify({
        "tfrs": tfrs
    })


