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
Flight Band API business rules layer implementation source file.

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

from datetime import datetime

from app.models.flight_band_model import (
    insert_flight_band_record,
    select_flight_band_record,
    select_flight_band_records,
    update_flight_band_record,
    patch_flight_band_record,
    delete_flight_band_record,
)

from app.config.constants import (
    DEFAULT_MINIMUM_ALTITUDE_FT,
    DEFAULT_MAXIMUM_ALTITUDE_FT,
    DEFAULT_START_TIME,
    DEFAULT_END_TIME,
    DEFAULT_ALLDAYS,
    VALID_FLIGHT_CLASSES,
)

DEFAULT_OPERATIONAL_STATUS = "active"
VALID_OPERATIONAL_STATUSES = ("active", "inactive")


def normalize_time(value):
    if value is None:
        return None

    if not isinstance(value, str):
        return None

    value = value.strip()

    try:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.strftime("%H:%M")
    except ValueError:
        return None


def validate_flight_band_payload(data):
    required_fields = [
        "flight_class",
        "band_name",
        "created_by",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    return validate_flight_band_values(data)


def validate_flight_band_update(data):
    required_fields = [
        "flight_class",
        "band_name",
        "updated_by",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    return validate_flight_band_values(data)


def validate_flight_band_patch(data):
    if not data:
        return None

    if "updated_by" not in data or data["updated_by"] in ("", None):
        return "Missing required field: updated_by"

    allowed_fields = {
        "flight_class",
        "band_name",
        "min_agl_ft",
        "max_agl_ft",
        "start_time",
        "end_time",
        "operational_status",
        "updated_by",
        "days",
    }

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for patch: {field}"

    return validate_flight_band_values(data)


def validate_flight_band_values(data):
    if "flight_class" in data:
        if data["flight_class"] not in VALID_FLIGHT_CLASSES:
            return "flight_class is not valid"

    min_agl_ft = data.get("min_agl_ft", DEFAULT_MINIMUM_ALTITUDE_FT)
    max_agl_ft = data.get("max_agl_ft", DEFAULT_MAXIMUM_ALTITUDE_FT)

    if min_agl_ft < 0:
        return "min_agl_ft must be greater than or equal to 0"

    if max_agl_ft <= min_agl_ft:
        return "max_agl_ft must be greater than min_agl_ft"

    start_time = data.get("start_time", DEFAULT_START_TIME)
    end_time = data.get("end_time", DEFAULT_END_TIME)

    normalized_start_time = normalize_time(start_time)
    normalized_end_time = normalize_time(end_time)

    if normalized_start_time is None:
        return "start_time must be in HH:MM format"

    if normalized_end_time is None:
        return "end_time must be in HH:MM format"

    if normalized_start_time >= normalized_end_time:
        return "start_time must be earlier than end_time"

    operational_status = data.get(
        "operational_status",
        DEFAULT_OPERATIONAL_STATUS
    )

    if operational_status not in VALID_OPERATIONAL_STATUSES:
        return "operational_status must be active or inactive"

    if "days" in data:
        error = validate_days(data["days"])
        if error:
            return error

    return None


def validate_days(days):
    if not isinstance(days, list):
        return "days must be an array"

    if len(days) == 0:
        return "days must contain at least one day"

    if len(days) != len(set(days)):
        return "days must not contain duplicate values"

    for day in days:
        if not isinstance(day, int):
            return "day_of_week values must be integers"

        if day < 0 or day > 6:
            return "day_of_week values must be between 0 and 6"

    return None


def normalize_flight_band_payload(data):
    return {
        "flight_class": data["flight_class"],
        "band_name": data["band_name"],
        "min_agl_ft": data.get("min_agl_ft", DEFAULT_MINIMUM_ALTITUDE_FT),
        "max_agl_ft": data.get("max_agl_ft", DEFAULT_MAXIMUM_ALTITUDE_FT),
        "start_time": normalize_time(data.get("start_time", DEFAULT_START_TIME)),
        "end_time": normalize_time(data.get("end_time", DEFAULT_END_TIME)),
        "operational_status": data.get(
            "operational_status",
            DEFAULT_OPERATIONAL_STATUS
        ),
        "created_by": data["created_by"],
        "updated_by": data.get("updated_by"),
        "days": data.get("days", list(DEFAULT_ALLDAYS)),
    }


def normalize_flight_band_update(data):
    return {
        "flight_class": data["flight_class"],
        "band_name": data["band_name"],
        "min_agl_ft": data.get("min_agl_ft", DEFAULT_MINIMUM_ALTITUDE_FT),
        "max_agl_ft": data.get("max_agl_ft", DEFAULT_MAXIMUM_ALTITUDE_FT),
        "start_time": normalize_time(data.get("start_time", DEFAULT_START_TIME)),
        "end_time": normalize_time(data.get("end_time", DEFAULT_END_TIME)),
        "operational_status": data.get(
            "operational_status",
            DEFAULT_OPERATIONAL_STATUS
        ),
        "updated_by": data["updated_by"],
        "days": data.get("days", list(DEFAULT_ALLDAYS)),
    }


def normalize_flight_band_patch(data):
    normalized_data = {}

    for field in [
        "flight_class",
        "band_name",
        "min_agl_ft",
        "max_agl_ft",
        "operational_status",
        "updated_by",
        "days",
    ]:
        if field in data:
            normalized_data[field] = data[field]

    if "start_time" in data:
        normalized_data["start_time"] = normalize_time(data["start_time"])

    if "end_time" in data:
        normalized_data["end_time"] = normalize_time(data["end_time"])

    return normalized_data


def format_time(value):
    if value is None:
        return None

    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    return str(value)[:5]


def format_flight_band(row):
    if row is None:
        return None

    return {
        "flight_band_id": str(row["flight_band_id"]),
        "flight_class": row["flight_class"],
        "band_name": row["band_name"],
        "min_agl_ft": row["min_agl_ft"],
        "max_agl_ft": row["max_agl_ft"],
        "start_time": format_time(row["start_time"]),
        "end_time": format_time(row["end_time"]),
        "operational_status": row["operational_status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "created_by": row["created_by"],
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        "updated_by": row["updated_by"],
        "days": list(row["days"]) if row["days"] else [],
    }


def create_flight_band(data):
    error = validate_flight_band_payload(data)

    if error:
        return None, error

    normalized_data = normalize_flight_band_payload(data)
    flight_band_id = insert_flight_band_record(normalized_data)

    return {
        "status": "created",
        "flight_band_id": flight_band_id,
        "flight_class": normalized_data["flight_class"],
        "band_name": normalized_data["band_name"],
    }, None


def get_flight_band_by_id(flight_band_id):
    row = select_flight_band_record(flight_band_id)
    return format_flight_band(row)


def get_all_flight_bands(flight_class=None, operational_status=None):
    rows = select_flight_band_records(flight_class, operational_status)
    return [format_flight_band(row) for row in rows]


def update_flight_band(flight_band_id, data):
    error = validate_flight_band_update(data)

    if error:
        return None, error

    normalized_data = normalize_flight_band_update(data)
    row = update_flight_band_record(flight_band_id, normalized_data)

    if row is None:
        return None, "Flight band not found"

    return {
        "status": "updated",
        "flight_band_id": str(row["flight_band_id"]),
    }, None


def patch_flight_band(flight_band_id, data):
    error = validate_flight_band_patch(data)

    if error:
        return None, error

    normalized_data = normalize_flight_band_patch(data)
    row = patch_flight_band_record(flight_band_id, normalized_data)

    if row is None:
        return None, "Flight band not found"

    return {
        "status": "updated",
        "flight_band_id": str(row["flight_band_id"]),
    }, None


def delete_flight_band(flight_band_id):
    row = delete_flight_band_record(flight_band_id)

    if row is None:
        return None

    return {
        "status": "deleted",
        "flight_band_id": str(row["flight_band_id"]),
    }

