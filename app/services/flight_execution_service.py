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

from app.services.geospatial_validation_service import (
    validate_operational_geospatial_data,
)
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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

    # This early return is intentional because later code accesses
    # required dictionary keys directly.
    if errors:
        return errors

    if data["flight_class"] not in VALID_FLIGHT_CLASSES:
        errors.append({
            "field": "flight_class",
            "code": "invalid_flight_class",
            "message": "flight_class is not valid.",
        })

    active_flight_bands = select_active_flight_band_records_by_class(
        data["flight_class"]
    )

    if not active_flight_bands:
        errors.append({
            "field": "flight_class",
            "code": "flight_band_unavailable",
            "message": (
                "No active Flight Band is available for this "
                "flight class."
            ),
        })
    else:
        departure_error = validate_requested_departure_datetime(
            data["requested_departure_datetime"],
            active_flight_bands,
        )

        if departure_error:
            errors.append(departure_error)

    nullable_fields = [
        "requested_departure_datetime",
        "departure_droneport_id",
        "arrival_droneport_id",
    ]

    for field in nullable_fields:
        if data[field] == "":
            errors.append({
                "field": field,
                "code": "invalid_null_value",
                "message": (
                    f"{field} must be null or a valid value, "
                    "not an empty string."
                ),
            })

    if not isinstance(data["flight_path_ids"], list):
        errors.append({
            "field": "flight_path_ids",
            "code": "invalid_list",
            "message": "flight_path_ids must be an array.",
        })
    else:
        for route_id in data["flight_path_ids"]:
            if route_id in ("", None):
                errors.append({
                    "field": "flight_path_ids",
                    "code": "invalid_route_id",
                    "message": (
                        "flight_path_ids must contain only "
                        "non-empty Route IDs."
                    ),
                })

    # Do not run database relationship validation when the payload shape
    # is already invalid.
    if errors:
        return errors

    geospatial_errors = validate_operational_geospatial_data(data)
    errors.extend(geospatial_errors)

    # This is the final return.
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

def validate_requested_departure_datetime(
    requested_departure_datetime,
    active_flight_bands,
):
    """
    Validate an optional requested departure against active Flight Bands.

    A null value means no specific departure time was requested. The Flight
    Execution may be scheduled whenever an active Flight Band permits it.
    """

    if requested_departure_datetime is None:
        return None

    requested_datetime = _parse_requested_departure_datetime(
        requested_departure_datetime
    )

    if requested_datetime is None:
        return {
            "field": "requested_departure_datetime",
            "code": "invalid_departure_datetime",
            "message": (
                "requested_departure_datetime must be a valid "
                "ISO 8601 datetime with a timezone offset."
            ),
        }

    for flight_band in active_flight_bands:
        if _requested_departure_matches_band(
            requested_datetime,
            flight_band,
        ):
            return None

    return {
        "field": "requested_departure_datetime",
        "code": "outside_flight_band_window",
        "message": (
            "The requested departure datetime is outside every active "
            "Flight Band window for this flight class."
        ),
    }


def _parse_requested_departure_datetime(value):
    if not isinstance(value, str):
        return None

    normalized_value = value.strip()

    if not normalized_value:
        return None

    # Python 3.11 accepts ISO 8601 offsets through fromisoformat().
    # Normalize a trailing Z to the equivalent UTC offset.
    if normalized_value.endswith("Z"):
        normalized_value = normalized_value[:-1] + "+00:00"

    try:
        parsed_datetime = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None

    # Require an aware datetime so its meaning is unambiguous when converted
    # into each Flight Band's configured timezone.
    if (
        parsed_datetime.tzinfo is None
        or parsed_datetime.utcoffset() is None
    ):
        return None

    return parsed_datetime


def _requested_departure_matches_band(
    requested_datetime,
    flight_band,
):
    timezone_name = flight_band["timezone"]

    try:
        flight_band_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return False

    local_datetime = requested_datetime.astimezone(
        flight_band_timezone
    )

    day_of_week = _to_flight_band_day_of_week(local_datetime)

    allowed_days = {
        int(day)
        for day in flight_band["days"]
    }

    if day_of_week not in allowed_days:
        return False

    requested_time = local_datetime.time().replace(
        second=0,
        microsecond=0,
        tzinfo=None,
    )

    start_time = flight_band["start_time"]
    end_time = flight_band["end_time"]

    return start_time <= requested_time <= end_time


def _to_flight_band_day_of_week(value):
    """
    Convert Python weekday numbering to DroneNav numbering.

    Python:
        Monday = 0
        Sunday = 6

    DroneNav:
        Sunday = 0
        Monday = 1
        Saturday = 6
    """

    return (value.weekday() + 1) % 7

