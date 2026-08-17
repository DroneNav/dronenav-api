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
Elevation Service API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-08-17

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""
import requests

from app.config.constants import EPQS_URL


def resolve_coordinate_elevation(
    longitude,
    latitude,
):
    response = requests.get(
        EPQS_URL,
        params={
            "x": longitude,
            "y": latitude,
            "units": "Feet",
            "wkid": 4326,
            "includeDate": "False",
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    return {
        "longitude": longitude,
        "latitude": latitude,
        "ground_elevation_ft": round(float(data["value"]), 1),
        "raster_id": data.get("rasterId"),
        "resolution": data.get("resolution"),
    }


def resolve_coordinate_elevations(coordinates):
    results = []
    resolved = {}

    for coordinate in coordinates:
        longitude = coordinate[0]
        latitude = coordinate[1]

        key = (
            longitude,
            latitude,
        )

        if key not in resolved:
            resolved[key] = resolve_coordinate_elevation(
                longitude,
                latitude,
            )

        results.append(resolved[key])

    return results
