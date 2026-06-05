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
DronePort API business rules layer implementation source file.

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
    DEFAULT_DRONEPORT_STATUS,
    DEFAULT_SURVEY_STATUS,
    DEFAULT_DRONEPORT_DIAMETER_FT,
)

from app.models.droneport_model import (
    insert_droneport,
    select_droneport,
    select_droneports,
    select_droneports_by_site_id,
    update_droneport_record,
    soft_delete_droneport,
    insert_overlay_review,
)


def validate_droneport_payload(data):
    required_fields = [
        "site_id",
        "droneport_name",
        "droneport_type",
        "created_by",
        "geometry"
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    geometry = data["geometry"]

    if geometry.get("type") != "Point":
        return "DronePort geometry must be a Point"

    return None


def normalize_droneport_payload(data):
    return {
        "site_id": data["site_id"],
        "droneport_name": data["droneport_name"],
        "droneport_type": data["droneport_type"],
        "created_by": data["created_by"],
        "operational_status": DEFAULT_DRONEPORT_STATUS,
        "survey_status": DEFAULT_SURVEY_STATUS,
        "droneport_diameter_ft": data.get(
            "droneport_diameter_ft",
            DEFAULT_DRONEPORT_DIAMETER_FT
        ),
        "geometry": data["geometry"],
    }


def format_droneport(row):
    if row is None:
        return None

    return {
        "droneport_id": str(row["droneport_id"]),
        "site_id": str(row["site_id"]),
        "droneport_name": row["droneport_name"],
        "droneport_type": row["droneport_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "last_surveyed_at": row.get("last_surveyed_at").isoformat()
            if row.get("last_surveyed_at") else None,
        "surveyed_by": row.get("surveyed_by"),
        "approved_by": row.get("approved_by"),
        "droneport_diameter_ft": row["droneport_diameter_ft"],
        "geometry": row["geometry"],
    }


def format_droneport_summary(row):
    return {
        "droneport_id": str(row["droneport_id"]),
        "site_id": str(row["site_id"]),
        "droneport_name": row["droneport_name"],
        "droneport_type": row["droneport_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "droneport_diameter_ft": row["droneport_diameter_ft"],
        "geometry": row["geometry"],
    }


def create_droneport(data):
    error = validate_droneport_payload(data)

    if error:
        return None, error

    normalized_data = normalize_droneport_payload(data)
    droneport_id = insert_droneport(normalized_data)

    insert_overlay_review({
        "overlay_type": "droneport",
        "overlay_id": droneport_id,
        "submitted_by": normalized_data["created_by"],
    })

    return {
        "status": "created",
        "droneport_id": droneport_id,
        "droneport_name": normalized_data["droneport_name"],
    }, None


def get_droneport_by_id(droneport_id):
    row = select_droneport(droneport_id)
    return format_droneport(row)


def get_droneports_by_site_id(site_id):
    rows = select_droneports_by_site_id(site_id)
    return [format_droneport_summary(row) for row in rows]


def get_all_droneports():
    rows = select_droneports()
    return [format_droneport_summary(row) for row in rows]


def update_droneport(droneport_id, data):
    error = validate_droneport_payload(data)

    if error:
        return None, error

    normalized_data = normalize_droneport_payload(data)
    row = update_droneport_record(droneport_id, normalized_data)

    if row is None:
        return None, "DronePort not found"

    return {
        "status": "updated",
        "droneport_id": str(row["droneport_id"]),
        "droneport_name": row["droneport_name"],
    }, None


def delete_droneport(droneport_id, deleted_by):
    row = soft_delete_droneport(droneport_id, deleted_by)

    if row is None:
        return None

    return {
        "status": "deleted",
        "droneport_id": str(row["droneport_id"]),
    }

