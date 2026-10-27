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
Aircraft API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-10-25

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from uuid import UUID

from app.models.aircraft_model import (
    insert_aircraft_record,
    select_aircraft_record,
    select_aircraft_records,
    update_aircraft_record,
    patch_aircraft_record,
    delete_aircraft_record,
)


def validate_aircraft_payload(data):
    required_fields = [
        "aviator_id",
        "aircraft_name",
        "model",
        "aircraft_type",
        "length_cm",
        "width_cm",
        "height_cm",
        "maximum_takeoff_weight_kg",
        "maximum_speed_ft_s",
        "created_by",
    ]

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            return f"Missing required field: {field}"

    try:
        UUID(str(data["aviator_id"]))
    except (ValueError, TypeError, AttributeError):
        return "aviator_id must be a valid UUID"

    return validate_aircraft_values(data)


def validate_aircraft_values(data):
    numeric_fields = [
        "length_cm",
        "width_cm",
        "height_cm",
        "maximum_takeoff_weight_kg",
        "maximum_speed_ft_s",
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
            or not 0 < value
        ):
            return f"{field} must be a positive number"

    text_fields = [
        "aircraft_name",
        "model",
        "aircraft_type",
    ]

    for field in text_fields:
        if field in data:
            value = data[field]

            if not isinstance(value, str) or not value.strip():
                return f"{field} must be a non-empty string"

    if "operational_status" in data:
        if data["operational_status"] not in ("active", "inactive"):
            return "operational_status must be active or inactive"

    if "deceleration_verified" in data:
        if not isinstance(data["deceleration_verified"], bool):
            return "deceleration_verified must be a boolean"

    return None


def validate_aircraft_update(data):
    required_fields = [
        "aircraft_name",
        "model",
        "aircraft_type",
        "length_cm",
        "width_cm",
        "height_cm",
        "maximum_takeoff_weight_kg",
        "maximum_speed_ft_s",
        "updated_by",
    ]

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            return f"Missing required field: {field}"

    return validate_aircraft_values(data)


def validate_aircraft_patch(data):
    if not data:
        return "PATCH payload cannot be empty"

    if "updated_by" not in data or data["updated_by"] in ("", None):
        return "Missing required field: updated_by"

    allowed_fields = {
        "aircraft_name",
        "manufacturer",
        "model",
        "aircraft_type",
        "length_cm",
        "width_cm",
        "height_cm",
        "maximum_takeoff_weight_kg",
        "maximum_speed_ft_s",
        "planned_deceleration_ft_s2",
        "deceleration_verified",
        "operational_status",
        "updated_by",
    }

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for patch: {field}"

    return validate_aircraft_values(data)


def format_aircraft(row):
    if row is None:
        return None

    return {
        "aircraft_id": str(row["aircraft_id"]),
        "aviator_id": str(row["aviator_id"]),
        "aircraft_name": row["aircraft_name"],
        "manufacturer": row["manufacturer"],
        "model": row["model"],
        "aircraft_type": row["aircraft_type"],
        "length_cm": float(row["length_cm"]),
        "width_cm": float(row["width_cm"]),
        "height_cm": float(row["height_cm"]),
        "maximum_takeoff_weight_kg": float(
            row["maximum_takeoff_weight_kg"]
        ),
        "maximum_speed_ft_s": float(row["maximum_speed_ft_s"]),
        "planned_deceleration_ft_s2": (
            float(row["planned_deceleration_ft_s2"])
            if row["planned_deceleration_ft_s2"] is not None
            else None
        ),
        "deceleration_verified": row["deceleration_verified"],
        "operational_status": row["operational_status"],
        "created_at": (
            row["created_at"].isoformat()
            if row["created_at"] else None
        ),
        "created_by": row["created_by"],
        "updated_at": (
            row["updated_at"].isoformat()
            if row["updated_at"] else None
        ),
        "updated_by": row["updated_by"],
    }


def create_aircraft(data):
    error = validate_aircraft_payload(data)

    if error:
        return None, error

    aircraft_id = insert_aircraft_record(data)

    return {
        "status": "created",
        "aircraft_id": str(aircraft_id),
    }, None


def get_aircraft_by_id(aircraft_id):
    row = select_aircraft_record(aircraft_id)

    return format_aircraft(row)


def get_aircraft_by_aviator(aviator_id):
    rows = select_aircraft_records(aviator_id)

    return [format_aircraft(row) for row in rows]


def update_aircraft(aircraft_id, data):
    error = validate_aircraft_update(data)

    if error:
        return None, error

    row = update_aircraft_record(aircraft_id, data)

    if row is None:
        return None, "Aircraft not found"

    return {
        "status": "updated",
        "aircraft_id": str(row["aircraft_id"]),
    }, None


def patch_aircraft(aircraft_id, data):
    error = validate_aircraft_patch(data)

    if error:
        return None, error

    row = patch_aircraft_record(aircraft_id, data)

    if row is None:
        return None, "Aircraft not found"

    return {
        "status": "updated",
        "aircraft_id": str(row["aircraft_id"]),
    }, None


def delete_aircraft(aircraft_id):
    row = delete_aircraft_record(aircraft_id)

    if row is None:
        return None, "Aircraft not found"

    return {
        "status": "deleted",
        "aircraft_id": str(row["aircraft_id"]),
    }, None



