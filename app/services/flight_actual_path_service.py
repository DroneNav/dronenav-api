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
Flight Actual Path API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-08-12

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from app.models.flight_actual_path_model import (
    upsert_flight_actual_path,
    select_flight_actual_path,
    append_flight_actual_path_points,
    complete_flight_actual_path,
)

def _validate_coordinate(coordinate):
    if not isinstance(coordinate, (list, tuple)):
        raise ValueError("Coordinate must be an array.")

    if len(coordinate) != 2:
        raise ValueError(
            "Coordinate must contain longitude and latitude."
        )

    longitude, latitude = coordinate

    if not isinstance(longitude, (int, float)):
        raise ValueError("Longitude must be numeric.")

    if not isinstance(latitude, (int, float)):
        raise ValueError("Latitude must be numeric.")

    if longitude < -180 or longitude > 180:
        raise ValueError("Longitude must be between -180 and 180.")

    if latitude < -90 or latitude > 90:
        raise ValueError("Latitude must be between -90 and 90.")


def _validate_coordinates(coordinates, minimum_points=1):
    if not isinstance(coordinates, list):
        raise ValueError("Coordinates must be an array.")

    if len(coordinates) < minimum_points:
        raise ValueError(
            f"At least {minimum_points} coordinate(s) required."
        )

    for coordinate in coordinates:
        _validate_coordinate(coordinate)


def _validate_post_payload(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    if not data.get("flight_id"):
        raise ValueError("flight_id is required.")

    geometry = data.get("geometry")

    if not isinstance(geometry, dict):
        raise ValueError("geometry is required.")

    if geometry.get("type") != "LineString":
        raise ValueError("geometry type must be LineString.")

    coordinates = geometry.get("coordinates")

    _validate_coordinates(
        coordinates,
        minimum_points=2,
    )

def format_flight_actual_path(row):
    if row is None:
        return None

    return {
        "flight_execution_id": str(
            row["flight_execution_id"]
        ),
        "flight_id": str(
            row["flight_id"]
        ),
        "geometry": row["geometry"],
        "point_count": row["point_count"],
        "status": row["status"],
        "created_at": (
            row["created_at"].isoformat()
            if row["created_at"]
            else None
        ),
        "updated_at": (
            row["updated_at"].isoformat()
            if row["updated_at"]
            else None
        ),
    }

def create_flight_actual_path(
    flight_execution_id,
    data,
):
    _validate_post_payload(data)

    normalized_data = {
        "flight_id": data["flight_id"],
        "geometry": data["geometry"],
        "status": "recording",
    }

    row = upsert_flight_actual_path(
        flight_execution_id,
        normalized_data,
    )

    return format_flight_actual_path(row)

def _validate_patch_payload(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    if not data.get("flight_id"):
        raise ValueError("flight_id is required.")

    coordinates = data.get("coordinates")
    status = data.get("status")

    if coordinates is None and status is None:
        raise ValueError(
            "coordinates or status is required."
        )

    if coordinates is not None:
        _validate_coordinates(
            coordinates,
            minimum_points=1,
        )

    if status is not None and status != "complete":
        raise ValueError(
            "PATCH status must be complete."
        )

def update_flight_actual_path(
    flight_execution_id,
    data,
):
    _validate_patch_payload(data)

    row = None

    coordinates = data.get("coordinates")

    if coordinates is not None:
        row = append_flight_actual_path_points(
            flight_execution_id,
            {
                "flight_id": data["flight_id"],
                "coordinates": coordinates,
            },
        )

        if row is None:
            return None

    if data.get("status") == "complete":
        row = complete_flight_actual_path(
            flight_execution_id,
            data["flight_id"],
        )

        if row is None:
            return None

    return format_flight_actual_path(row)


def get_flight_actual_path(
    flight_execution_id,
):
    row = select_flight_actual_path(
        flight_execution_id
    )

    return format_flight_actual_path(row)


