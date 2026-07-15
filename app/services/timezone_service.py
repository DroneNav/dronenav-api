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


from collections import Counter

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

def resolve_authoritative_site_timezone(site, droneports):
    """
    Resolve the authoritative Site timezone from contained DronePorts.

    Returns:
        (timezone, condition)

    condition is one of:
        persisted_site_fallback
        single_timezone
        majority_timezone
        tied_timezone
    """

    valid_droneports = [
        droneport
        for droneport in droneports
        if droneport.get("timezone")
    ]

    if not valid_droneports:
        return resolve_site_timezone(site), "persisted_site_fallback"

    timezone_counts = Counter(
        droneport["timezone"]
        for droneport in valid_droneports
    )

    highest_count = max(timezone_counts.values())

    winning_timezones = {
        timezone
        for timezone, count in timezone_counts.items()
        if count == highest_count
    }

    if len(winning_timezones) == 1:
        selected_timezone = next(iter(winning_timezones))

        condition = (
            "single_timezone"
            if len(timezone_counts) == 1
            else "majority_timezone"
        )

        return selected_timezone, condition

    # No primary DronePort exists yet. Use the earliest-created
    # DronePort whose timezone is among the tied winners.
    tied_droneports = [
        droneport
        for droneport in valid_droneports
        if droneport["timezone"] in winning_timezones
    ]

    earliest_droneport = min(
        tied_droneports,
        key=lambda droneport: droneport["created_at"],
    )

    return earliest_droneport["timezone"], "tied_timezone"

