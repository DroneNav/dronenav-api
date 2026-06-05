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
Route API business rules layer implementation source file.

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
    DEFAULT_MINIMUM_AIRCRAFT_WEIGHT_LBS,
    DEFAULT_MAXIMUM_AIRCRAFT_WEIGHT_LBS,
    DEFAULT_MINIMUM_SEGMENT_COUNT,
    DEFAULT_ROUTE_DIRECTION,
    DEFAULT_ROUTE_BUFFERED,
    DEFAULT_ROUTE_STATUS,
    DEFAULT_SURVEY_STATUS,
)

from app.models.route_model import (
    insert_route,
    select_route,
    select_routes,
    select_routes_by_site_id,
    update_route_record,
    soft_delete_route,
    insert_overlay_review,
)


def validate_route_payload(data):
    required_fields = [
        "origin_site_id",
        "destination_site_id",
        "origin_droneport_id",
        "destination_droneport_id",
        "route_name",
        "route_type",
        "created_by",
        "geometry",
        "segment_attributes",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    if not isinstance(data["segment_attributes"], list):
        return "segment_attributes must be an array"

    geometry = data["geometry"]

    if geometry.get("type") != "LineString":
        return "Route geometry must be a LineString"

    coordinates = geometry.get("coordinates", [])

    if not isinstance(coordinates, list):
        return "Route coordinates must be an array"

    segment_count = len(coordinates) - 1

    if segment_count < DEFAULT_MINIMUM_SEGMENT_COUNT:
        return (
            f"Route must contain at least "
            f"{DEFAULT_MINIMUM_SEGMENT_COUNT} segments"
        )

    if len(data["segment_attributes"]) != segment_count:
        return (
            f"segment_attributes must contain "
            f"{segment_count} entries"
        )

    return None


def normalize_route_payload(data):
    return {
        "origin_site_id": data["origin_site_id"],
        "destination_site_id": data["destination_site_id"],
        "origin_droneport_id": data["origin_droneport_id"],
        "destination_droneport_id": data["destination_droneport_id"],
        "route_name": data["route_name"],
        "route_type": data["route_type"],
        "created_by": data["created_by"],
        "operational_status": DEFAULT_ROUTE_STATUS,
        "survey_status": DEFAULT_SURVEY_STATUS,
	"minimum_aircraft_weight_lbs": data.get(
	    "minimum_aircraft_weight_lbs",
	    DEFAULT_MINIMUM_AIRCRAFT_WEIGHT_LBS
	),
	"maximum_aircraft_weight_lbs": data.get(
	    "maximum_aircraft_weight_lbs",
	    DEFAULT_MAXIMUM_AIRCRAFT_WEIGHT_LBS
	),
	"direction": data.get(
	    "direction",
	    DEFAULT_ROUTE_DIRECTION
	),
	"buffered": data.get(
	    "buffered",
	    DEFAULT_ROUTE_BUFFERED
	),
	"geometry": data["geometry"],
	"segment_attributes": data["segment_attributes"],
    }


def format_route(row):
    if row is None:
        return None

    return {
        "route_id": str(row["route_id"]),
        "origin_site_id": str(row["origin_site_id"]),
        "destination_site_id": str(row["destination_site_id"]),
        "origin_droneport_id": str(row["origin_droneport_id"]),
        "destination_droneport_id": str(row["destination_droneport_id"]),
        "route_name": row["route_name"],
        "route_type": row["route_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "last_surveyed_at": row.get("last_surveyed_at").isoformat()
            if row.get("last_surveyed_at") else None,
        "surveyed_by": row.get("surveyed_by"),
        "approved_by": row.get("approved_by"),
        "minimum_aircraft_weight_lbs": row["minimum_aircraft_weight_lbs"],
        "maximum_aircraft_weight_lbs": row["maximum_aircraft_weight_lbs"],
        "direction": row["direction"],
        "buffered": row["buffered"],
        "geometry": row["geometry"],
        "segment_attributes": row["segment_attributes"],
    }


def format_route_summary(row):
    return {
        "route_id": str(row["route_id"]),
        "origin_site_id": str(row["origin_site_id"]),
        "destination_site_id": str(row["destination_site_id"]),
        "origin_droneport_id": str(row["origin_droneport_id"]),
        "destination_droneport_id": str(row["destination_droneport_id"]),
        "route_name": row["route_name"],
        "route_type": row["route_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "minimum_aircraft_weight_lbs": row["minimum_aircraft_weight_lbs"],
        "maximum_aircraft_weight_lbs": row["maximum_aircraft_weight_lbs"],
        "direction": row["direction"],
        "buffered": row["buffered"],
        "geometry": row["geometry"],
        "segment_attributes": row["segment_attributes"],
    }


def create_route(data):
    error = validate_route_payload(data)

    if error:
        return None, error

    normalized_data = normalize_route_payload(data)
    route_id = insert_route(normalized_data)

    insert_overlay_review({
        "overlay_type": "route",
        "overlay_id": route_id,
        "submitted_by": normalized_data["created_by"],
    })

    return {
        "status": "created",
        "route_id": route_id,
        "route_name": normalized_data["route_name"],
    }, None


def get_route_by_id(route_id):
    row = select_route(route_id)
    return format_route(row)


def get_routes_by_site_id(site_id):
    rows = select_routes_by_site_id(site_id)
    return [format_route_summary(row) for row in rows]


def get_all_routes():
    rows = select_routes()
    return [format_route_summary(row) for row in rows]


def update_route(route_id, data):
    error = validate_route_payload(data)

    if error:
        return None, error

    normalized_data = normalize_route_payload(data)
    row = update_route_record(route_id, normalized_data)

    if row is None:
        return None, "Route not found"

    return {
        "status": "updated",
        "route_id": str(row["route_id"]),
        "route_name": row["route_name"],
    }, None


def delete_route(route_id, deleted_by):
    row = soft_delete_route(route_id, deleted_by)

    if row is None:
        return None

    return {
        "status": "deleted",
        "route_id": str(row["route_id"]),
    }

