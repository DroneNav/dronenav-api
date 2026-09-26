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
Obstacle API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-09-25

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from app.config.constants import (
    DEFAULT_OBSTACLE_STATUS,
    DEFAULT_SURVEY_STATUS,
    OBSTACLE_TYPES,
)

from app.models.obstacle_model import (
    insert_obstacle,
    select_obstacle,
    select_obstacles,
    select_obstacles_by_site_id,
    patch_obstacle_record,
    soft_delete_obstacle,
    insert_overlay_review,
    insert_obstacle_collection,
    select_obstacle_collection,
    select_obstacle_collections,
    insert_obstacle_membership,
    delete_obstacle_membership,
    select_obstacles_by_collection_id,
    delete_obstacle_collection,
    patch_obstacle_collection,
)


def validate_obstacle_payload(data):
    required_fields = [
        "obstacle_name",
        "obstacle_type",
        "created_by",
        "geometry",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    if data["obstacle_type"] not in OBSTACLE_TYPES:
        return "Invalid obstacle_type"

    geometry = data["geometry"]

    if geometry.get("type") not in (
        "Point",
        "LineString",
        "Polygon",
    ):
        return (
            "Obstacle geometry must be a Point, "
            "LineString, or Polygon"
        )

    return None


def validate_obstacle_patch(data):
    required_fields = [
        "obstacle_name",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    if (
        "obstacle_type" in data
        and data["obstacle_type"] not in OBSTACLE_TYPES
    ):
        return "Invalid obstacle_type"

    return None


def normalize_obstacle_payload(data):
    return {
        "site_id": data.get("site_id"),
        "obstacle_name": data["obstacle_name"],
        "obstacle_type": data["obstacle_type"],
        "created_by": data["created_by"],
        "operational_status": DEFAULT_OBSTACLE_STATUS,
        "survey_status": DEFAULT_SURVEY_STATUS,
        "maximum_height_agl_ft": data.get("maximum_height_agl_ft"),
        "description": data.get("description"),
        "geometry": data["geometry"],
    }


def normalize_obstacle_patch(data):
    return {
        "obstacle_name": data["obstacle_name"],
        "maximum_height_agl_ft": data.get("maximum_height_agl_ft"),
        "description": data.get("description"),
    }


def format_obstacle(row):
    if row is None:
        return None

    return {
        "obstacle_id": str(row["obstacle_id"]),
        "site_id": str(row["site_id"]) if row["site_id"] else None,
        "obstacle_name": row["obstacle_name"],
        "obstacle_type": row["obstacle_type"],
        "source": row["source"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat()
            if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "last_surveyed_at": row.get("last_surveyed_at").isoformat()
            if row.get("last_surveyed_at") else None,
        "surveyed_by": row.get("surveyed_by"),
        "approved_by": row.get("approved_by"),
        "maximum_height_agl_ft": row["maximum_height_agl_ft"],
        "description": row["description"],
        "geometry": row["geometry"],
    }


def format_obstacle_summary(row):
    return {
        "obstacle_id": str(row["obstacle_id"]),
        "site_id": str(row["site_id"]) if row["site_id"] else None,
        "obstacle_name": row["obstacle_name"],
        "obstacle_type": row["obstacle_type"],
        "source": row["source"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat()
            if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "maximum_height_agl_ft": row["maximum_height_agl_ft"],
        "description": row["description"],
        "geometry": row["geometry"],
    }


def create_obstacle(data):
    error = validate_obstacle_payload(data)

    if error:
        return None, error

    normalized_data = normalize_obstacle_payload(data)

    obstacle_id = insert_obstacle(normalized_data)

    insert_overlay_review({
        "overlay_type": "obstacle",
        "overlay_id": obstacle_id,
        "submitted_by": normalized_data["created_by"],
    })

    return {
        "status": "created",
        "obstacle_id": obstacle_id,
        "obstacle_name": normalized_data["obstacle_name"],
    }, None


def get_obstacle_by_id(obstacle_id):
    row = select_obstacle(obstacle_id)
    return format_obstacle(row)


def get_obstacles_by_site_id(site_id):
    rows = select_obstacles_by_site_id(site_id)
    return [format_obstacle_summary(row) for row in rows]


def get_obstacles(survey_status=None):
    rows = select_obstacles(survey_status)
    return [format_obstacle_summary(row) for row in rows]


def patch_obstacle(obstacle_id, data):
    error = validate_obstacle_patch(data)

    if error:
        return None, error

    normalized_data = normalize_obstacle_patch(data)

    row = patch_obstacle_record(
        obstacle_id,
        normalized_data,
    )

    if row is None:
        return None, "Obstacle not found"

    return {
        "status": "updated",
        "obstacle_id": str(row["obstacle_id"]),
        "obstacle_name": row["obstacle_name"],
    }, None


def delete_obstacle(obstacle_id, deleted_by):
    obstacle_id = soft_delete_obstacle(
        obstacle_id,
        deleted_by,
    )

    if obstacle_id is None:
        return None

    return {
        "status": "deleted",
        "obstacle_id": str(obstacle_id),
    }


def validate_obstacle_collection_payload(data):
    if (
        "collection_name" not in data
        or data["collection_name"] in ("", None)
    ):
        return "Missing required field: collection_name"

    return None


def normalize_obstacle_collection_payload(data):
    return {
        "collection_name": data["collection_name"],
        "description": data.get("description"),
    }


def format_obstacle_collection(row):
    if row is None:
        return None

    return {
        "obstacle_collection_id": str(
            row["obstacle_collection_id"]
        ),
        "collection_name": row["collection_name"],
        "description": row["description"],
    }


def create_obstacle_collection(data):
    error = validate_obstacle_collection_payload(data)

    if error:
        return None, error

    normalized_data = normalize_obstacle_collection_payload(data)

    obstacle_collection_id = insert_obstacle_collection(
        normalized_data
    )

    return {
        "status": "created",
        "obstacle_collection_id": obstacle_collection_id,
        "collection_name": normalized_data["collection_name"],
    }, None


def get_obstacle_collection_by_id(obstacle_collection_id):
    row = select_obstacle_collection(
        obstacle_collection_id
    )

    return format_obstacle_collection(row)


def get_obstacle_collections():
    rows = select_obstacle_collections()

    return [
        format_obstacle_collection(row)
        for row in rows
    ]


def patch_obstacle_collection_record(
    obstacle_collection_id,
    data,
):
    error = validate_obstacle_collection_payload(data)

    if error:
        return None, error

    normalized_data = normalize_obstacle_collection_payload(data)

    row = patch_obstacle_collection(
        obstacle_collection_id,
        normalized_data,
    )

    if row is None:
        return None, "Obstacle collection not found"

    return {
        "status": "updated",
        "obstacle_collection_id": str(
            row["obstacle_collection_id"]
        ),
        "collection_name": row["collection_name"],
    }, None


def delete_obstacle_collection_record(obstacle_collection_id):
    deleted_id = delete_obstacle_collection(
        obstacle_collection_id
    )

    if deleted_id is None:
        return None

    return {
        "status": "deleted",
        "obstacle_collection_id": str(deleted_id),
    }


def add_obstacle_to_collection(
    obstacle_collection_id,
    obstacle_id,
):
    insert_obstacle_membership(
        obstacle_collection_id,
        obstacle_id,
    )

    return {
        "status": "created",
        "obstacle_collection_id": str(
            obstacle_collection_id
        ),
        "obstacle_id": str(obstacle_id),
    }


def remove_obstacle_from_collection(
    obstacle_collection_id,
    obstacle_id,
):
    delete_obstacle_membership(
        obstacle_collection_id,
        obstacle_id,
    )

    return {
        "status": "deleted",
        "obstacle_collection_id": str(
            obstacle_collection_id
        ),
        "obstacle_id": str(obstacle_id),
    }


def get_obstacles_by_collection_id(obstacle_collection_id):
    rows = select_obstacles_by_collection_id(
        obstacle_collection_id
    )

    return [
        format_obstacle_summary(row)
        for row in rows
    ]


