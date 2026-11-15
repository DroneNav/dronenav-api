
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
Residential Destination API route layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-11-15
"""

from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.residential_destination_service import (
    create_residential_destination,
    get_residential_destination_by_id,
    get_residential_destinations_by_site,
    patch_residential_destination,
    verify_residential_destination,
    delete_residential_destination,
)


residential_destinations_bp = Blueprint(
    "residential_destinations",
    __name__,
)

CORS(
    residential_destinations_bp,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


def valid_uuid(value):
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def error_response(message, status_code):
    return jsonify({
        "status": "error",
        "message": message,
    }), status_code


@residential_destinations_bp.route(
    "/api/residential-destinations",
    methods=["POST", "OPTIONS"],
)
def create_residential_destination_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response("A JSON object is required", 400)

    result, error = create_residential_destination(data)

    if error:
        return error_response(error, 400)

    return jsonify(result), 201


@residential_destinations_bp.route(
    "/api/residential-destinations",
    methods=["GET", "OPTIONS"],
)
def get_residential_destination_list_route():

    if request.method == "OPTIONS":
        return "", 204

    site_id = request.args.get("site_id")

    if not site_id:
        return error_response(
            "Missing required parameter: site_id",
            400,
        )

    if not valid_uuid(site_id):
        return error_response(
            "site_id must be a valid UUID",
            400,
        )

    destinations = get_residential_destinations_by_site(site_id)

    return jsonify({
        "residential_destinations": destinations,
    })


@residential_destinations_bp.route(
    "/api/residential-destinations/<destination_id>",
    methods=["GET", "OPTIONS"],
)
def get_residential_destination_route(destination_id):

    if request.method == "OPTIONS":
        return "", 204

    if not valid_uuid(destination_id):
        return error_response(
            "destination_id must be a valid UUID",
            400,
        )

    destination = get_residential_destination_by_id(destination_id)

    if destination is None:
        return error_response("Residential destination not found", 404)

    return jsonify(destination)


@residential_destinations_bp.route(
    "/api/residential-destinations/<destination_id>",
    methods=["PATCH", "OPTIONS"],
)
def patch_residential_destination_route(destination_id):

    if request.method == "OPTIONS":
        return "", 204

    if not valid_uuid(destination_id):
        return error_response(
            "destination_id must be a valid UUID",
            400,
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response("A JSON object is required", 400)

    result, error = patch_residential_destination(
        destination_id,
        data,
    )

    if error:
        status_code = (
            404 if error == "Residential destination not found" else 400
        )
        return error_response(error, status_code)

    return jsonify(result)


@residential_destinations_bp.route(
    "/api/residential-destinations/<destination_id>/verify",
    methods=["POST", "OPTIONS"],
)
def verify_residential_destination_route(destination_id):

    if request.method == "OPTIONS":
        return "", 204

    if not valid_uuid(destination_id):
        return error_response(
            "destination_id must be a valid UUID",
            400,
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response("A JSON object is required", 400)

    # Manual satellite-image review must precede this request.
    # Authentication and authorization must be enforced before
    # this endpoint is enabled for operational use.
    result, error = verify_residential_destination(
        destination_id,
        data,
    )

    if error:
        status_code = (
            404 if error == "Residential destination not found" else 400
        )
        return error_response(error, status_code)

    return jsonify(result)


@residential_destinations_bp.route(
    "/api/residential-destinations/<destination_id>",
    methods=["DELETE", "OPTIONS"],
)
def delete_residential_destination_route(destination_id):

    if request.method == "OPTIONS":
        return "", 204

    if not valid_uuid(destination_id):
        return error_response(
            "destination_id must be a valid UUID",
            400,
        )

    result, error = delete_residential_destination(destination_id)

    if error:
        return error_response(error, 404)

    return jsonify(result)

