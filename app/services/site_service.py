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
Site API business rules layer implementation source file.

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
    DEFAULT_OPERATIONAL_STATUS,
    DEFAULT_SURVEY_STATUS,
    DEFAULT_REVIEW_STATUS,
)

from app.models.site_model import (
    insert_site,
    select_site,
    select_sites,
    update_site_record,
    patch_site_record,
    soft_delete_site,
    insert_overlay_review,
)


def validate_site_payload(data):
    required_fields = [
        "authority_id",
        "site_name",
        "site_type",
        "created_by",
        "geometry",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    geometry = data["geometry"]

    if geometry.get("type") != "Polygon":
        return "Site geometry must be a Polygon"

    return None


def validate_site_patch(data):
    required_fields = [
        "description",
        "minimum_altitude_ft",
        "maximum_altitude_ft",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    return None


def normalize_site_payload(data):
    return {
        "authority_id": data["authority_id"],
        "site_name": data["site_name"],
        "site_type": data["site_type"],
        "created_by": data["created_by"],
        "operational_status": DEFAULT_OPERATIONAL_STATUS,
        "survey_status": DEFAULT_SURVEY_STATUS,
        "description": data.get("description", None),
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


def normalize_site_patch(data):
    return {
        "description": data.get("description", None),
        "minimum_altitude_ft": data.get(
            "minimum_altitude_ft",
            DEFAULT_MINIMUM_ALTITUDE_FT
        ),
        "maximum_altitude_ft": data.get(
            "maximum_altitude_ft",
            DEFAULT_MAXIMUM_ALTITUDE_FT
        ),
    }


def format_site(row):
    if row is None:
        return None

    return {
        "site_id": str(row["site_id"]),
        "authority_id": str(row["authority_id"]),
        "site_name": row["site_name"],
        "site_type": row["site_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "description": row["description"] if row["description"] else None,
        "survey_status": row["survey_status"],
        "last_surveyed_at": row.get("last_surveyed_at").isoformat()
            if row.get("last_surveyed_at") else None,
        "surveyed_by": row.get("surveyed_by"),
        "approved_by": row.get("approved_by"),
        "minimum_altitude_ft": row["minimum_altitude_ft"],
        "maximum_altitude_ft": row["maximum_altitude_ft"],
        "geometry": row["geometry"],
    }


def format_site_summary(row):
    return {
        "site_id": str(row["site_id"]),
        "authority_id": str(row["authority_id"]),
        "site_name": row["site_name"],
        "site_type": row["site_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "description": row["description"] if row["description"] else None,
        "survey_status": row["survey_status"],
        "minimum_altitude_ft": row["minimum_altitude_ft"],
        "maximum_altitude_ft": row["maximum_altitude_ft"],
        "geometry": row["geometry"],
    }


def create_site(data):
    error = validate_site_payload(data)

    if error:
        return None, error

    normalized_data = normalize_site_payload(data)
    site_id = insert_site(normalized_data)

    insert_overlay_review({
        "overlay_type": "site",
        "overlay_id": site_id,
        "submitted_by": normalized_data["created_by"],
    })

    return {
        "status": "created",
        "site_id": site_id,
        "site_name": normalized_data["site_name"],
    }, None


def get_site_by_id(site_id):
    row = select_site(site_id)
    return format_site(row)


def get_all_sites(survey_status):
    rows = select_sites(survey_status)
    return [format_site_summary(row) for row in rows]


def update_site(site_id, data):
    error = validate_site_payload(data)

    if error:
        return None, error

    normalized_data = normalize_site_payload(data)
    row = update_site_record(site_id, normalized_data)

    if row is None:
        return None, "Site not found"

    return {
        "status": "updated",
        "site_id": str(row["site_id"]),
        "site_name": row["site_name"],
    }, None


def patch_site(site_id, data):
    error = validate_site_patch(data)

    if error:
        return None, error

    normalized_data = normalize_site_patch(data)
    row = patch_site_record(site_id, normalized_data)

    if row is None:
        return None, "Site not found"

    return {
        "status": "updated",
        "site_id": str(row["site_id"]),
        "site_name": row["site_name"],
    }, None


def delete_site(site_id, deleted_by):
    row = soft_delete_site(site_id, deleted_by)

    if row is None:
        return None

    return {
        "status": "deleted",
        "site_id": str(row["site_id"]),
    }

