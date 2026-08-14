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
Flask route implementation source file for support of Zone APIs.

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

from app.services.zone_service import (
    create_zone,
    get_zone_by_id,
    get_all_zones,
    update_zone,
    patch_zone,
    delete_zone,
    evaluate_point_in_zone,
)

zones_bp = Blueprint("zones", __name__)

CORS(
    zones_bp,
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


@zones_bp.route("/api/zones", methods=["POST", "OPTIONS"])
def create_zone_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_zone(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@zones_bp.route("/api/zones", methods=["GET", "OPTIONS"])
def get_zones_route():

    if request.method == "OPTIONS":
        return "", 204

    survey_status = request.args.get("survey_status")

    zones = get_all_zones(survey_status)

    return jsonify({
        "zones": zones
    })


@zones_bp.route("/api/zones/<zone_id>", methods=["GET", "OPTIONS"])
def get_zone_route(zone_id):

    if request.method == "OPTIONS":
        return "", 204

    zone = get_zone_by_id(zone_id)

    if zone is None:
        return jsonify({
            "status": "error",
            "message": "Zone not found"
        }), 404

    return jsonify(zone)


@zones_bp.route("/api/zones/<zone_id>", methods=["PUT", "OPTIONS"])
def update_zone_route(zone_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = update_zone(zone_id, data)

    if error:
        status_code = 404 if error == "Zone not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@zones_bp.route("/api/zones/<zone_id>", methods=["PATCH", "OPTIONS"])
def patch_zone_route(zone_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_zone(zone_id, data)

    if error:
        status_code = 404 if error == "Zone not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@zones_bp.route("/api/zones/<zone_id>", methods=["DELETE", "OPTIONS"])
def delete_zone_route(zone_id):

    if request.method == "OPTIONS":
        return "", 204

    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_zone(zone_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Zone not found"
        }), 404

    return jsonify(result)


@zones_bp.route(
    "/api/zones/<zone_id>/point-containment",
    methods=["POST", "OPTIONS"],
)
def evaluate_point_in_zone_route(zone_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}

    result, error = evaluate_point_in_zone(
        zone_id,
        data,
    )

    if error:
        status_code = 404 if error == "Zone not found" else 400

        return jsonify({
            "status": "error",
            "message": error,
        }), status_code

    return jsonify(result)

