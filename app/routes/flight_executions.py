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
Flight Executions API business rules layer implementation source file.

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

from app.services.flight_execution_service import (
    create_flight_execution,
    launch_reusable_flight_execution,
    release_scheduled_flight_execution_service,
    cancel_flight_execution_service,
    list_flight_executions,
    get_flight_execution,
)

flight_executions_bp = Blueprint("flight_executions", __name__)

CORS(
    flight_executions_bp,
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


@flight_executions_bp.route("/api/flight-executions", methods=["POST", "OPTIONS"])
def create_flight_execution_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}

    result, status_code = create_flight_execution(data)

    return jsonify(result), status_code


@flight_executions_bp.route(
    "/api/flight-executions/<flight_execution_id>/launch",
    methods=["POST", "OPTIONS"],
)
def launch_flight_execution_route(flight_execution_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}

    aviator_id = data.get("aviator_id")
    aircraft_id = data.get("aircraft_id")

    if not aviator_id:
        return jsonify({
            "error": "aviator_id is required."
        }), 400

    if not aircraft_id:
        return jsonify({
            "error": "aircraft_id is required."
        }), 400

    result, status_code = launch_reusable_flight_execution(
        flight_execution_id,
        aviator_id,
        aircraft_id,
    )

    return jsonify(result), status_code


@flight_executions_bp.route("/api/flight-executions", methods=["GET", "OPTIONS"])
def list_flight_executions_route():

    if request.method == "OPTIONS":
        return "", 204

    requested_departure_datetime = request.args.get(
        "requested_departure_datetime"
    )

    response, status = list_flight_executions(
        requested_departure_datetime
    )

    return jsonify(response), status


@flight_executions_bp.route("/api/flight-executions/<flight_execution_id>", methods=["GET", "OPTIONS"])
def get_flight_execution_route(
    flight_execution_id,
):
    if request.method == "OPTIONS":
        return "", 204

    response, status_code = get_flight_execution(
        flight_execution_id
    )

    return jsonify(response), status_code


@flight_executions_bp.route("/api/flight-executions/<flight_execution_id>/release",
  methods=["POST", "OPTIONS"])
def release_flight_execution_route(
    flight_execution_id,
):
    """
    Return a preflight-failed scheduled Flight Execution to active status.
    """

    if request.method == "OPTIONS":
        return "", 204

    response, status_code = (
        release_scheduled_flight_execution_service(
            flight_execution_id
        )
    )

    return jsonify(response), status_code


@flight_executions_bp.route("/api/flight-executions/<flight_execution_id>/cancel",
  methods=["POST", "OPTIONS"])
def cancel_flight_execution_route(
    flight_execution_id,
):
    """
    Cancels a Flight Execution Record.
    """

    if request.method == "OPTIONS":
        return "", 204

    response, status_code = (
        cancel_flight_execution_service(
            flight_execution_id
        )
    )

    return jsonify(response), status_code

