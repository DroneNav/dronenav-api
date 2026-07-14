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
timezone calculation services implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-13

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.


Operational timezone resolution service.

This service owns coordinate-based IANA timezone resolution for DroneNav.
"""

from timezonefinder import timezone_at_land


def derive_timezone_from_coordinates(longitude, latitude):
    """
    Resolve an IANA timezone from WGS84 longitude and latitude.

    Returns None when coordinates are missing, invalid, outside valid ranges,
    or cannot be resolved to a land timezone.
    """

    try:
        longitude = float(longitude)
        latitude = float(latitude)
    except (TypeError, ValueError):
        return None

    if not -180.0 <= longitude <= 180.0:
        return None

    if not -90.0 <= latitude <= 90.0:
        return None

    return timezone_at_land(
        lng=longitude,
        lat=latitude,
    )


def resolve_droneport_timezone(droneport):
    """
    Return the persisted DronePort timezone or derive it from its coordinates.
    """

    if droneport is None:
        return None

    if droneport.get("timezone"):
        return droneport["timezone"]

    return derive_timezone_from_coordinates(
        longitude=droneport.get("longitude"),
        latitude=droneport.get("latitude"),
    )


def resolve_site_timezone(site):
    """
    Return the persisted Site timezone or derive it from its representative
    PointOnSurface coordinates.
    """

    if site is None:
        return None

    if site.get("timezone"):
        return site["timezone"]

    return derive_timezone_from_coordinates(
        longitude=site.get("timezone_longitude"),
        latitude=site.get("timezone_latitude"),
    )

