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
Zone API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-06-04

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from app.config.constants import (
    DEFAULT_MINIMUM_ALTITUDE_FT,
    DEFAULT_MAXIMUM_ALTITUDE_FT,
    DEFAULT_ZONE_STATUS,
    DEFAULT_SURVEY_STATUS,
)

from app.models.zone_model import (
    insert_zone,
    select_zone,
    select_zones,
    select_zones_by_site_id,
    update_zone_record,
    soft_delete_zone,
    insert_overlay_review,
)


def validate_zone_payload(data):
    required_fields = [
        "site_id",
        "zone_name",
        "zone_type",
        "created_by",
        "geometry",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    geometry = data["geometry"]

    if geometry.get("type") != "Polygon":
        return "Zone geometry must be a Polygon"

    return None


def normalize_zone_payload(data):
    return {
        "site_id": data["site_id"],
        "zone_name": data["zone_name"],
        "zone_type": data["zone_type"],
        "created_by": data["created_by"],
        "operational_status": DEFAULT_ZONE_STATUS,
        "survey_status": DEFAULT_SURVEY_STATUS,
        "minimum_altitude_ft": data.get(
            "minimum_altitude_ft",
            DEFAULT_MINIMUM_ALTITUDE_FT
        ),
        "maximum_altitude_ft": data.get(
            "maximum_altitude_ft",
            DEFAULT_MAXIMUM_ALTITUDE_FT
        ),
        "geometry": data["geometry"],
    }


def format_zone(row):
    if row is None:
        return None

    return {
        "zone_id": str(row["zone_id"]),
        "site_id": str(row["site_id"]),
        "zone_name": row["zone_name"],
        "zone_type": row["zone_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "last_surveyed_at": row.get("last_surveyed_at").isoformat()
            if row.get("last_surveyed_at") else None,
        "surveyed_by": row.get("surveyed_by"),
        "approved_by": row.get("approved_by"),
        "minimum_altitude_ft": row["minimum_altitude_ft"],
        "maximum_altitude_ft": row["maximum_altitude_ft"],
        "geometry": row["geometry"],
    }


def format_zone_summary(row):
    return {
        "zone_id": str(row["zone_id"]),
        "site_id": str(row["site_id"]),
        "zone_name": row["zone_name"],
        "zone_type": row["zone_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "minimum_altitude_ft": row["minimum_altitude_ft"],
        "maximum_altitude_ft": row["maximum_altitude_ft"],
        "geometry": row["geometry"],
    }


def create_zone(data):
    error = validate_zone_payload(data)

    if error:
        return None, error

    normalized_data = normalize_zone_payload(data)
    zone_id = insert_zone(normalized_data)

    insert_overlay_review({
        "overlay_type": "zone",
        "overlay_id": zone_id,
        "submitted_by": normalized_data["created_by"],
    })

    return {
        "status": "created",
        "zone_id": zone_id,
        "zone_name": normalized_data["zone_name"],
    }, None


def get_zone_by_id(zone_id):
    row = select_zone(zone_id)
    return format_zone(row)


def get_zones_by_site_id(site_id):
    rows = select_zones_by_site_id(site_id)
    return [format_zone_summary(row) for row in rows]


def get_all_zones():
    rows = select_zones()
    return [format_zone_summary(row) for row in rows]


def update_zone(zone_id, data):
    error = validate_zone_payload(data)

    if error:
        return None, error

    normalized_data = normalize_zone_payload(data)
    row = update_zone_record(zone_id, normalized_data)

    if row is None:
        return None, "Zone not found"

    return {
        "status": "updated",
        "zone_id": str(row["zone_id"]),
        "zone_name": row["zone_name"],
    }, None


def delete_zone(zone_id, deleted_by):
    row = soft_delete_zone(zone_id, deleted_by)

    if row is None:
        return None

    return {
        "status": "deleted",
        "zone_id": str(row["zone_id"]),
    }

