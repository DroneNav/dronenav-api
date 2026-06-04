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
Flask route implementation source file to support Authority APIs.

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

from app.services.authority_service import (
    create_authority,
    get_authority_by_id,
    get_all_authorities,
    update_authority,
    delete_authority,
)

authorities_bp = Blueprint("authorities", __name__)


@authorities_bp.route("/api/authorities", methods=["POST"])
def create_authority_route():
    data = request.get_json()

    result, error = create_authority(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@authorities_bp.route("/api/authorities", methods=["GET"])
def get_authorities_route():
    authorities = get_all_authorities()

    return jsonify({
        "authorities": authorities
    })


@authorities_bp.route("/api/authorities/<authority_id>", methods=["GET"])
def get_authority_route(authority_id):
    authority = get_authority_by_id(authority_id)

    if authority is None:
        return jsonify({
            "status": "error",
            "message": "Authority not found"
        }), 404

    return jsonify(authority)


@authorities_bp.route("/api/authorities/<authority_id>", methods=["PUT"])
def update_authority_route(authority_id):
    data = request.get_json()

    result, error = update_authority(authority_id, data)

    if error:
        status_code = 404 if error == "Authority not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@authorities_bp.route("/api/authorities/<authority_id>", methods=["DELETE"])
def delete_authority_route(authority_id):
    result = delete_authority(authority_id)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Authority not found"
        }), 404

    return jsonify(result)

