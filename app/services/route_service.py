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

from app.models.overlay_package_model import (
    get_context_package_record,
)

from app.models.route_model import (
    insert_route,
    select_route,
    select_routes,
    select_routes_by_site_id,
    select_route_segment_conformance,
    select_route_segment_boundary_crossing,
    select_transition_point_containment,
    select_coordinate_distance,
    update_route_record,
    patch_route_record,
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


def validate_route_segment_conformance_payload(data):
    required_fields = [
        "latitude",
        "longitude",
        "start_latitude",
        "start_longitude",
        "end_latitude",
        "end_longitude",
        "route_width_ft",
    ]

    for field in required_fields:
        if field not in data or data[field] is None:
            return f"Missing required field: {field}"

    return None


def normalize_route_segment_conformance_payload(data):
    return {
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "start_latitude": float(data["start_latitude"]),
        "start_longitude": float(data["start_longitude"]),
        "end_latitude": float(data["end_latitude"]),
        "end_longitude": float(data["end_longitude"]),
        "route_width_ft": float(data["route_width_ft"]),
    }


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


def evaluate_route_segment_conformance(data):
    error = validate_route_segment_conformance_payload(data)

    if error:
        return None, error

    normalized_data = normalize_route_segment_conformance_payload(data)

    row = select_route_segment_conformance(normalized_data)

    if row is None:
        return None, "Route segment conformance could not be evaluated"

    return {
        "inside": bool(row["inside"]),
        "distance_ft": round(float(row["distance_ft"]), 3),
        "half_width_ft": round(float(row["half_width_ft"]), 3),
    }, None


def evaluate_route_segment_boundary_crossing(data):
    row = select_route_segment_boundary_crossing(data)

    if row is None:
        return None, "Route segment boundary crossing could not be evaluated"

    return {
        "crossed": bool(row["crossed"]),
    }, None


def evaluate_transition_point_containment(data):
    """Evaluate whether a point is inside a derived transition circle."""

    row = select_transition_point_containment(data)

    return {
        "inside": bool(row["inside"]),
    }, None


def get_coordinate_distance(data):
    """Return the distance between two coordinates in feet."""

    row = select_coordinate_distance(data)

    if row is None:
        return None, "Could not calculate coordinate distance."

    return {
        "distance_ft": round(float(row["distance_ft"]), 3),
    }, None


def validate_route_patch(data):

    if not isinstance(data, dict):
        return "Patch payload must be an object"

    if not data:
        return "Patch payload cannot be empty"

    allowed_fields = {
        "route_name",
        "route_type",
        "minimum_aircraft_weight_lbs",
        "maximum_aircraft_weight_lbs",
        "buffered",
        "direction",
        "segment_attributes",
    }

    for field in data:
        if field not in allowed_fields:
            return f"Unsupported patch field: {field}"

    if "segment_attributes" in data:
        if not isinstance(data["segment_attributes"], list):
            return "segment_attributes must be an array"

    return None


def normalize_route_patch(data):

    allowed_fields = {
        "route_name",
        "route_type",
        "minimum_aircraft_weight_lbs",
        "maximum_aircraft_weight_lbs",
        "buffered",
        "direction",
        "segment_attributes",
    }

    return {
        field: data[field]
        for field in allowed_fields
        if field in data
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


def get_route_context(route_id):

    route = get_route_by_id(route_id)

    if route is None:
        return None, "Route not found"

    origin_site_id = route["origin_site_id"]
    destination_site_id = route["destination_site_id"]

    origin_context, error = get_context_package_record(
        site_id=origin_site_id
    )

    if error:
        return None, error

    packages = [
        format_context_package(origin_context),
    ]

    if origin_site_id != destination_site_id:

        destination_context, error = get_context_package_record(
            site_id=destination_site_id
        )

        if error:
            return None, error

        packages.append(
            format_context_package(destination_context)
        )

    return {
        "packages": packages,
        "selected_route_id": route_id,
    }, None


def format_context_package(context_package):

    if context_package is None:
        return None

    return {
        "site": format_context_site(context_package.get("site")),
        "zones": format_context_zones(context_package.get("zones", [])),
        "droneports": format_context_droneports(context_package.get("droneports", [])),
        "routes": format_context_routes(context_package.get("routes", [])),
    }


def format_context_zones(zones):

    return [format_context_zone(zone) for zone in zones]


def format_context_droneports(droneports):

    return [format_context_droneport(droneport) for droneport in droneports]


def format_context_routes(routes):

    return [format_context_route(route) for route in routes]


def format_context_site(site):

    if site is None:
        return None

    return {
        "site_id": str(site["site_id"]),
        "site_name": site["site_name"],
        "site_type": site["site_type"],
        "geometry": site["geometry"],
    }


def format_context_zone(zone):

    return {
        "zone_id": str(zone["zone_id"]),
        "site_id": str(zone["site_id"]),
        "zone_name": zone["zone_name"],
        "zone_type": zone["zone_type"],
        "geometry": zone["geometry"],
    }


def format_context_droneport(droneport):

    return {
        "droneport_id": str(droneport["droneport_id"]),
        "site_id": str(droneport["site_id"]),
        "droneport_name": droneport["droneport_name"],
        "droneport_type": droneport["droneport_type"],
        "droneport_diameter_ft": droneport["droneport_diameter_ft"],
        "geometry": droneport["geometry"],
    }


def format_context_route(route):

    return {
        "route_id": str(route["route_id"]),
        "origin_site_id": str(route["origin_site_id"]),
        "destination_site_id": str(route["destination_site_id"]),
        "route_name": route["route_name"],
        "route_type": route["route_type"],
        "direction": route["direction"],
        "geometry": route["geometry"],
    }


def get_all_routes(survey_status):
    rows = select_routes(survey_status)
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


def patch_route(route_id, data):
    error = validate_route_patch(data)

    if error:
        return None, error

    normalized_data = normalize_route_patch(data)
    row = patch_route_record(route_id, normalized_data)

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

