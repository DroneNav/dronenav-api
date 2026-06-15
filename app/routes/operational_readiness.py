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
Flask route implementation source file for operational readiness status of overlays.

Author:
DroneNav Project Contributors

Created:
2026-06-14

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.operational_readiness_service import (
    activate_overlay,
    deactivate_overlay_package,
    deactivate_overlay,
)


operational_readiness_bp = Blueprint("operational_readiness", __name__)

CORS(
    operational_readiness_bp,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": ["POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


@operational_readiness_bp.route("/api/governance/overlays/<overlay_type>/<overlay_id>/activate", methods=["POST", "OPTIONS"])
def activate_overlay_route(overlay_type, overlay_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}

    result, error = activate_overlay(overlay_type, overlay_id, data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 200

@operational_readiness_bp.route("/api/governance/sites/<site_id>/deactivate-package", methods=["POST", "OPTIONS"])
def deactivate_package_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    result, error = deactivate_overlay_package(site_id)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 200


@operational_readiness_bp.route("/api/governance/overlays/<overlay_type>/<overlay_id>/deactivate", methods=["POST", "OPTIONS"])
def deactivate_overlay_route(overlay_type, overlay_id):

    if request.method == "OPTIONS":
        return "", 204

    result, error = deactivate_overlay(overlay_type, overlay_id)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 200


