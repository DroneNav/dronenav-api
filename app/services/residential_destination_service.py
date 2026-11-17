
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
Residential Destination API business rules layer.

Author:
DroneNav Project Contributors

Created:
2026-11-15
"""

from math import isfinite
from uuid import UUID

from app.models.residential_destination_model import (
    insert_residential_destination_record,
    select_residential_destination_record,
    select_residential_destination_records,
    patch_residential_destination_record,
    verify_residential_destination_record,
    delete_residential_destination_record,
)


def validate_residential_destination_values(data):
    text_fields = [
        "street_address",
        "normalized_address",
    ]

    for field in text_fields:
        if field in data:
            value = data[field]

            if not isinstance(value, str) or not value.strip():
                return f"{field} must be a non-empty string"

    coordinate_fields = {
        "geocoded_latitude": (-90, 90),
        "geocoded_longitude": (-180, 180),
        "latitude": (-90, 90),
        "longitude": (-180, 180),
    }

    for field, (minimum, maximum) in coordinate_fields.items():
        if field not in data:
            continue

        value = data[field]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or not minimum <= value <= maximum
        ):
            return f"{field} must be a number between {minimum} and {maximum}"

    return None


def validate_residential_destination_payload(data):
    required_fields = [
        "site_id",
        "street_address",
        "normalized_address",
        "geocoded_latitude",
        "geocoded_longitude",
        "latitude",
        "longitude",
    ]

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            return f"Missing required field: {field}"

    try:
        UUID(str(data["site_id"]))
    except (ValueError, TypeError, AttributeError):
        return "site_id must be a valid UUID"

    allowed_fields = set(required_fields)

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for creation: {field}"

    return validate_residential_destination_values(data)


def validate_residential_destination_patch(data):
    if not data:
        return "PATCH payload cannot be empty"

    allowed_fields = {
        "street_address",
        "normalized_address",
        "geocoded_latitude",
        "geocoded_longitude",
        "latitude",
        "longitude",
    }

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for patch: {field}"

    return validate_residential_destination_values(data)


def validate_residential_destination_verification(data):
    required_fields = [
        "latitude",
        "longitude",
        "verified_by",
    ]

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            return f"Missing required field: {field}"

    if (
        not isinstance(data["verified_by"], str)
        or not data["verified_by"].strip()
    ):
        return "verified_by must be a non-empty string"

    allowed_fields = set(required_fields)

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for verification: {field}"

    return validate_residential_destination_values(data)


def format_residential_destination(row):
    if row is None:
        return None

    return {
        "destination_id": str(row["destination_id"]),
        "site_id": str(row["site_id"]),
        "street_address": row["street_address"],
        "normalized_address": row["normalized_address"],
        "geocoded_latitude": (
          float(row["geocoded_latitude"])
          if row["geocoded_latitude"] is not None
          else None
        ),
        "geocoded_longitude": (
          float(row["geocoded_longitude"])
          if row["geocoded_longitude"] is not None
          else None
        ),
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "geocode_verified": row["geocode_verified"],
        "verified_by": row["verified_by"],
        "verified_at": (
            row["verified_at"].isoformat()
            if row["verified_at"] else None
        ),
    }


def create_residential_destination(data):
    error = validate_residential_destination_payload(data)

    if error:
        return None, error

    destination_id = insert_residential_destination_record(data)

    return {
        "status": "created",
        "destination_id": destination_id,
    }, None


def get_residential_destination_by_id(destination_id):
    row = select_residential_destination_record(destination_id)

    return format_residential_destination(row)


def get_residential_destinations_by_site(site_id):
    rows = select_residential_destination_records(site_id)

    return [format_residential_destination(row) for row in rows]


def patch_residential_destination(destination_id, data):
    error = validate_residential_destination_patch(data)

    if error:
        return None, error

    row = patch_residential_destination_record(
        destination_id,
        data,
    )

    if row is None:
        return None, "Residential destination not found"

    return {
        "status": "updated",
        "destination_id": str(row["destination_id"]),
    }, None


def verify_residential_destination(destination_id, data):
    error = validate_residential_destination_verification(data)

    if error:
        return None, error

    row = verify_residential_destination_record(
        destination_id,
        data["latitude"],
        data["longitude"],
        data["verified_by"],
    )

    if row is None:
        return None, "Residential destination not found"

    return {
        "status": (
            "verified"
            if row["geocode_verified"]
            else "unverified"
        ),
        "destination_id": str(row["destination_id"]),
        "geocode_verified": row["geocode_verified"],
    }, None


def delete_residential_destination(destination_id):
    row = delete_residential_destination_record(destination_id)

    if row is None:
        return None, "Residential destination not found"

    return {
        "status": "deleted",
        "destination_id": str(row["destination_id"]),
    }, None


