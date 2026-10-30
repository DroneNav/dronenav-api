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
Aircraft Profile API business rules layer implementation source file.

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

from uuid import UUID
from sqlalchemy.exc import IntegrityError

from app.models.aircraft_calibration_profile_model import (
    insert_aircraft_calibration_profile_record,
    select_aircraft_calibration_profile_records,
    patch_aircraft_calibration_profile_record,
    delete_aircraft_calibration_profile_record,
)


def validate_calibration_profile_values(data):
    numeric_fields = [
        "cruise_speed_ft_s",
        "planned_deceleration_ft_s2",
    ]

    for field in numeric_fields:
        if field not in data:
            continue

        value = data[field]

        if field == "planned_deceleration_ft_s2" and value is None:
            continue

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value <= 0
        ):
            return f"{field} must be a positive number"

    if "deceleration_verified" in data:
        if not isinstance(data["deceleration_verified"], bool):
            return "deceleration_verified must be a boolean"

    if "sample_count" in data:
        value = data["sample_count"]

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            return "sample_count must be a non-negative integer"

    if "calibration_flight_execution_id" in data:
        value = data["calibration_flight_execution_id"]

        if value is not None:
            try:
                UUID(str(value))
            except (ValueError, TypeError, AttributeError):
                return (
                    "calibration_flight_execution_id "
                    "must be a valid UUID"
                )

    if "updated_by" in data:
        value = data["updated_by"]

        if not isinstance(value, str) or not value.strip():
            return "updated_by must be a non-empty string"

    return None


def validate_calibration_profile_create(data):
    required_fields = [
        "cruise_speed_ft_s",
        "updated_by",
    ]

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            return f"Missing required field: {field}"

    allowed_fields = {
        "cruise_speed_ft_s",
        "planned_deceleration_ft_s2",
        "updated_by",
    }

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for create: {field}"

    return validate_calibration_profile_values(data)


def validate_calibration_profile_patch(data):
    if not data:
        return "PATCH payload cannot be empty"

    if "updated_by" not in data:
        return "Missing required field: updated_by"

    allowed_fields = {
        "cruise_speed_ft_s",
        "planned_deceleration_ft_s2",
        "deceleration_verified",
        "calibration_flight_execution_id",
        "sample_count",
        "updated_by",
    }

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for patch: {field}"

    return validate_calibration_profile_values(data)


def format_calibration_profile(row):
    if row is None:
        return None

    return {
        "profile_id": str(row["profile_id"]),
        "aircraft_id": str(row["aircraft_id"]),
        "cruise_speed_ft_s": float(row["cruise_speed_ft_s"]),
        "planned_deceleration_ft_s2": (
            float(row["planned_deceleration_ft_s2"])
            if row["planned_deceleration_ft_s2"] is not None
            else None
        ),
        "deceleration_verified": row["deceleration_verified"],
        "calibrated_at": (
            row["calibrated_at"].isoformat()
            if row["calibrated_at"] is not None
            else None
        ),
        "calibration_flight_execution_id": (
            str(row["calibration_flight_execution_id"])
            if row["calibration_flight_execution_id"] is not None
            else None
        ),
        "sample_count": row["sample_count"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "updated_by": row["updated_by"],
    }


def create_calibration_profile(aircraft_id, data):
    error = validate_calibration_profile_create(data)

    if error:
        return None, error

    try:
        profile_id = insert_aircraft_calibration_profile_record(
            aircraft_id, data
        )
    except IntegrityError as exc:
        if (
            getattr(exc.orig, "pgcode", None) == "23505"
            and exc.orig.diag.constraint_name
            == "uq_aircraft_calibration_speed"
        ):
            return None, (
                "A calibration profile already exists for "
                "this aircraft and cruise speed."
            )

        raise

    return {
        "status": "created",
        "profile_id": str(profile_id),
        "aircraft_id": str(aircraft_id),
    }, None


def get_calibration_profiles(aircraft_id, cruise_speed_ft_s=None):
    try:
        UUID(str(aircraft_id))
    except (ValueError, TypeError, AttributeError):
        return None, "aircraft_id must be a valid UUID"

    if cruise_speed_ft_s is not None:
        try:
            cruise_speed_ft_s = float(cruise_speed_ft_s)
        except (ValueError, TypeError, OverflowError):
            return None, "cruise_speed_ft_s must be a positive number"

        if (
            not 0 < cruise_speed_ft_s < float("inf")
        ):
            return None, "cruise_speed_ft_s must be a positive number"

    rows = select_aircraft_calibration_profile_records(
        aircraft_id, cruise_speed_ft_s
    )

    return [format_calibration_profile(row) for row in rows], None


def patch_calibration_profile(
    aircraft_id, profile_id, data, calibration_result=False
):
    if calibration_result:
        if not isinstance(data, dict):
            return None, "Invalid calibration data"

        if not isinstance(data.get("calibration_success"), bool):
            return None, "calibration_success must be true or false"

        data = data.copy()
        success = data.pop("calibration_success")

        data["deceleration_verified"] = success

        if success:
            required_fields = (
                "planned_deceleration_ft_s2",
                "calibration_flight_execution_id",
                "sample_count",
            )

            for field in required_fields:
                if data.get(field) is None:
                    return None, (
                        f"{field} is required for successful calibration"
                    )

            sample_count = data["sample_count"]

            if (
                isinstance(sample_count, bool)
                or not isinstance(sample_count, int)
                or sample_count <= 0
            ):
                return None, (
                    "sample_count must be a positive integer"
                )

        else:
            for field in (
                "planned_deceleration_ft_s2",
                "calibration_flight_execution_id",
                "sample_count",
            ):
                data.pop(field, None)

    error = validate_calibration_profile_patch(data)

    if error:
        return None, error

    if not calibration_result:
        restricted_fields = {
            "deceleration_verified",
            "calibrated_at",
            "calibration_flight_execution_id",
            "sample_count",
        }

        for field in restricted_fields:
            if field in data:
                return None, (
                    f"{field} cannot be changed by an administrator"
                )

    row = patch_aircraft_calibration_profile_record(
        aircraft_id,
        profile_id,
        data,
        calibration_result=calibration_result,
    )

    if row is None:
        return None, "Calibration profile not found"

    return {
        "status": "updated",
        "profile_id": str(row["profile_id"]),
        "aircraft_id": str(aircraft_id),
    }, None


def delete_calibration_profile(aircraft_id, profile_id):
    row = delete_aircraft_calibration_profile_record(
        aircraft_id,
        profile_id,
    )

    if row is None:
        return None, "Calibration profile not found"

    return {
        "status": "deleted",
        "profile_id": str(row["profile_id"]),
        "aircraft_id": str(aircraft_id),
    }, None



