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
Flight Execution API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-08

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

import uuid
from app.config.constants import VALID_FLIGHT_CLASSES
from app.models.flight_band_model import select_active_flight_band_records_by_class


def create_flight_execution(data):
    if data.get("force_reject") is True:
        return rejected_response([
            {
                "field": "flight_class",
                "code": "flight_band_unavailable",
                "message": "No active Flight Band is available for this flight class at the requested execution time.",
            }
        ])

    errors = validate_flight_execution_submission(data)

    if errors:
        return rejected_response(errors)

    return accepted_response()


def validate_flight_execution_submission(data):
    errors = []

    required_fields = [
        "flight_plan_id",
        "authority_id",
        "aviator_id",
        "aircraft_id",
        "flight_class",
        "origin_site_id",
        "destination_site_id",
        "requested_departure_datetime",
        "departure_droneport_id",
        "arrival_droneport_id",
        "flight_path_ids",
        "submitted_by",
    ]

    for field in required_fields:
        if field not in data:
            errors.append({
                "field": field,
                "code": "missing_required_field",
                "message": f"Missing required field: {field}.",
            })

    if errors:
        return errors

    if data["flight_class"] not in VALID_FLIGHT_CLASSES:
        errors.append({
            "field": "flight_class",
            "code": "invalid_flight_class",
            "message": "flight_class is not valid.",
        })

    active_flight_bands = select_active_flight_band_records_by_class(data["flight_class"])

    if not active_flight_bands:
        errors.append({
            "field": "flight_class",
            "code": "flight_band_unavailable",
            "message": "No active Flight Band is available for this flight class.",
        })

    nullable_fields = [
        "requested_departure_datetime",
        "departure_droneport_id",
        "arrival_droneport_id",
    ]

    for field in nullable_fields:
        if field in data and data[field] == "":
            errors.append({
                "field": field,
                "code": "invalid_null_value",
                "message": f"{field} must be null or a valid value, not an empty string.",
            })

    if not isinstance(data["flight_path_ids"], list):
        errors.append({
            "field": "flight_path_ids",
            "code": "invalid_list",
            "message": "flight_path_ids must be an array.",
        })
    else:
        for flight_path_id in data["flight_path_ids"]:
            if flight_path_id in ("", None):
                errors.append({
                    "field": "flight_path_ids",
                    "code": "invalid_route_id",
                    "message": "flight_path_ids must contain only non-empty route IDs.",
                })

    return errors


def accepted_response():
    return {
        "status": "accepted",
        "message": "Flight plan accepted.",
        "flight_execution_record_id": str(uuid.uuid4()),
        "flight_plan_status": "submitted",
    }, 201


def rejected_response(errors):
    return {
        "status": "rejected",
        "message": "Flight plan rejected.",
        "flight_plan_status": "draft",
        "errors": errors,
    }, 422

