
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
    delete_residential_destination_record,
)

from app.services.elevation_service import (
    resolve_coordinate_elevations,
)

from app.services.site_service import evaluate_point_in_site


def validate_residential_destination_values(data):
    text_fields = [
        "street_address",
    ]

    for field in text_fields:
        if field in data:
            value = data[field]

            if not isinstance(value, str) or not value.strip():
                return f"{field} must be a non-empty string"

    coordinate_fields = {
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
        "latitude",
        "longitude",
    }

    for field in data:
        if field not in allowed_fields:
            return f"Invalid field for patch: {field}"

    return validate_residential_destination_values(data)


def format_residential_destination(row):
    if row is None:
        return None

    return {
        "destination_id": str(row["destination_id"]),
        "site_id": str(row["site_id"]),
        "street_address": row["street_address"],
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "ground_elevation_ft": row["ground_elevation_ft"],
    }


def create_residential_destination(data):

    error = validate_residential_destination_payload(data)

    if error:
        return None, error

    containment, error = evaluate_point_in_site(
        data["site_id"],
        {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
        },
    )

    if error:
        return None, error

    if not (
        containment["inside"]
        or containment["on_boundary"]
    ):
        return None, "Residential destination must be within the Site boundary"

    data = enrich_residential_destination_elevation(data)

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

    existing = select_residential_destination_record(destination_id)

    if existing is None:
        return None, "Residential destination not found"

    latitude = data.get("latitude", existing["latitude"])
    longitude = data.get("longitude", existing["longitude"])

    containment, error = evaluate_point_in_site(
        str(existing["site_id"]),
        {
            "latitude": latitude,
            "longitude": longitude,
        },
    )

    if error:
        return None, error

    if not (
        containment["inside"]
        or containment["on_boundary"]
    ):
        return None, "Residential destination must be within the Site boundary"

    if (
        latitude != existing["latitude"]
        or longitude != existing["longitude"]
    ):
        data["latitude"] = latitude
        data["longitude"] = longitude

        data = enrich_residential_destination_elevation(data)

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


def delete_residential_destination(destination_id):
    row = delete_residential_destination_record(destination_id)

    if row is None:
        return None, "Residential destination not found"

    return {
        "status": "deleted",
        "destination_id": str(row["destination_id"]),
    }, None


def enrich_residential_destination_elevation(data):
    coordinates = [
        [data["longitude"], data["latitude"]]
    ]

    elevations = resolve_coordinate_elevations(coordinates)

    if elevations and elevations[0] is not None:
        data["ground_elevation_ft"] = round(
            elevations[0]["ground_elevation_ft"]
        )

    return data

