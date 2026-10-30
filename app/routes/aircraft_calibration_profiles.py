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
Aircraft Profiles API route layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-10-29

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from flask import jsonify, request

from app.routes.aircraft import aircraft_bp

from app.services.aircraft_calibration_profile_service import (
    create_calibration_profile,
    get_calibration_profiles,
    patch_calibration_profile,
    delete_calibration_profile,
)



@aircraft_bp.route(
    "/api/aircraft/<aircraft_id>/deceleration-profiles",
    methods=["GET", "OPTIONS"]
)
def get_calibration_profiles_route(aircraft_id):

    if request.method == "OPTIONS":
        return "", 204

    cruise_speed = request.args.get("cruise_speed_ft_s")

    profiles, error = get_calibration_profiles(
        aircraft_id, cruise_speed
    )

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify({"profiles": profiles})


@aircraft_bp.route(
    "/api/aircraft/<aircraft_id>/deceleration-profiles",
    methods=["POST", "OPTIONS"]
)
def create_calibration_profile_route(aircraft_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_calibration_profile(
        aircraft_id, data
    )

    if error:
        status_code = 409 if (
            error == "A calibration profile already exists for "
            "this aircraft and cruise speed."
        ) else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result), 201


@aircraft_bp.route(
    "/api/aircraft/<aircraft_id>/deceleration-profiles/<profile_id>",
    methods=["PATCH", "OPTIONS"]
)
def patch_calibration_profile_route(aircraft_id, profile_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    calibration_result = request.args.get(
        "calibration_result"
    ) == "true"

    result, error = patch_calibration_profile(
        aircraft_id,
        profile_id,
        data,
        calibration_result=calibration_result,
    )

    if error:
        status_code = (
            404 if error == "Calibration profile not found" else 400
        )

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@aircraft_bp.route(
    "/api/aircraft/<aircraft_id>/deceleration-profiles/<profile_id>",
    methods=["DELETE", "OPTIONS"]
)
def delete_calibration_profile_route(aircraft_id, profile_id):

    if request.method == "OPTIONS":
        return "", 204

    result, error = delete_calibration_profile(
        aircraft_id,
        profile_id,
    )

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 404

    return jsonify(result)


