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
Route API object model implementation source file.

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


import json

from sqlalchemy import text

from app.config.constants import (
    DEFAULT_SRID,
    ROUTE_STATUS_DELETED,
    ROUTE_STATUS_INACTIVE,
    ROUTE_STATUS_ACTIVE,
    SURVEY_STATUS_APPROVED,
    SURVEY_STATUS_NOT_SURVEYED
)

from app.config.database import engine


def insert_route(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO routes (
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    operational_status,
                    survey_status,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    maximum_aircraft_capacity,
                    geometry,
                    segment_attributes
                )
                VALUES (
                    :origin_site_id,
                    :destination_site_id,
                    :origin_droneport_id,
                    :destination_droneport_id,
                    :route_name,
                    :route_type,
                    :created_by,
                    :operational_status,
                    :survey_status,
                    :minimum_aircraft_weight_lbs,
                    :maximum_aircraft_weight_lbs,
                    :direction,
                    :maximum_aircraft_capacity,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    ),
                    CAST(:segment_attributes AS jsonb)
                )
                RETURNING route_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
                "segment_attributes": json.dumps(data["segment_attributes"]),
                "srid": DEFAULT_SRID,
            }
        )

        return str(result.scalar())


def insert_overlay_review(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO overlay_reviews (
                    overlay_type,
                    overlay_id,
                    submitted_by
                )
                VALUES (
                    :overlay_type,
                    :overlay_id,
                    :submitted_by
                )
                RETURNING review_id
            """),
            data
        )

        return str(result.scalar())


def select_route(route_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    route_id,
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    last_surveyed_at,
                    surveyed_by,
                    approved_by,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    maximum_aircraft_capacity,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    segment_attributes
                FROM routes 
                WHERE route_id = :route_id
                  AND operational_status <> :deleted_status
            """),
            {
                "route_id": route_id,
                "deleted_status": ROUTE_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_routes(survey_status=None):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    route_id,
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    maximum_aircraft_capacity,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    segment_attributes
                FROM routes
                WHERE operational_status <> :deleted_status
                  AND (
                      :survey_status IS NULL
                      OR survey_status = :survey_status
                  )
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": ROUTE_STATUS_DELETED,
                "survey_status": survey_status,
            }
        )

        return result.mappings().all()


def select_routes_by_site_id(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    route_id,
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    maximum_aircraft_capacity,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    segment_attributes
                FROM routes
                WHERE operational_status <> :deleted_status
                  AND (origin_site_id = :site_id OR destination_site_id = :site_id)
                ORDER BY created_at DESC
            """),
            {
                "site_id": site_id,
                "deleted_status": ROUTE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def select_route_segment_conformance(data):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                WITH geometries AS (
                    SELECT
                        ST_SetSRID(
                            ST_MakePoint(
                                :longitude,
                                :latitude
                            ),
                            :srid
                        ) AS point_geometry,
                        ST_SetSRID(
                            ST_MakeLine(
                                ST_MakePoint(
                                    :start_longitude,
                                    :start_latitude
                                ),
                                ST_MakePoint(
                                    :end_longitude,
                                    :end_latitude
                                )
                            ),
                            :srid
                        ) AS segment_geometry
                )
                SELECT
                    ST_DWithin(
                        point_geometry::geography,
                        segment_geometry::geography,
                        (:route_width_ft / 2.0) * 0.3048
                    ) AS inside,
                    ST_Distance(
                        point_geometry::geography,
                        segment_geometry::geography
                    ) / 0.3048 AS distance_ft,
                    :route_width_ft / 2.0 AS half_width_ft
                FROM geometries
            """),
            {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "start_latitude": data["start_latitude"],
                "start_longitude": data["start_longitude"],
                "end_latitude": data["end_latitude"],
                "end_longitude": data["end_longitude"],
                "route_width_ft": data["route_width_ft"],
                "srid": 4326,
            },
        )

        return result.mappings().first()


def select_route_segment_boundary_crossing(data):
    """Determine whether a point crossed a Route segment's forward boundary."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                WITH geometries AS (
                    SELECT
                        ST_SetSRID(
                            ST_MakePoint(
                                :start_longitude,
                                :start_latitude
                            ),
                            :srid
                        ) AS start_geometry,
                        ST_SetSRID(
                            ST_MakePoint(
                                :end_longitude,
                                :end_latitude
                            ),
                            :srid
                        ) AS end_geometry,
                        ST_SetSRID(
                            ST_MakePoint(
                                :longitude,
                                :latitude
                            ),
                            :srid
                        ) AS point_geometry
                    ),
                    projected AS (
                        SELECT
                            ST_Transform(start_geometry, 3857) AS start_geometry,
                            ST_Transform(end_geometry, 3857) AS end_geometry,
                            ST_Transform(point_geometry, 3857) AS point_geometry
                        FROM geometries
                    )
                    SELECT
                        (
                            (
                                ST_X(end_geometry) - ST_X(start_geometry)
                            ) * (
                                ST_X(point_geometry) - ST_X(end_geometry)
                            )
                            +
                            (
                                ST_Y(end_geometry) - ST_Y(start_geometry)
                            ) * (
                                ST_Y(point_geometry) - ST_Y(end_geometry)
                            )
                        ) >= 0 AS crossed
                    FROM projected
            """),
            {
                "start_latitude": data["start_latitude"],
                "start_longitude": data["start_longitude"],
                "end_latitude": data["end_latitude"],
                "end_longitude": data["end_longitude"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "srid": 4326,
            },
        )

        return result.mappings().first()


def select_transition_point_containment(data):
    """Determine whether a point is inside a derived transition circle."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT ST_DWithin(
                    ST_SetSRID(
                        ST_MakePoint(:longitude, :latitude),
                        4326
                    )::geography,
                    ST_SetSRID(
                        ST_MakePoint(:center_longitude, :center_latitude),
                        4326
                    )::geography,
                    :radius_meters
                ) AS inside
            """),
            {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "center_latitude": data["center_latitude"],
                "center_longitude": data["center_longitude"],
                "radius_meters": (
                    data["diameter_ft"] / 2.0
                ) * 0.3048,
            },

        )

        return result.mappings().first()


def select_coordinate_distance(data):
    """Return the distance between two coordinates in feet."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    ST_Distance(
                        ST_SetSRID(
                            ST_MakePoint(
                                :first_longitude,
                                :first_latitude
                            ),
                            4326
                        )::geography,
                        ST_SetSRID(
                            ST_MakePoint(
                                :second_longitude,
                                :second_latitude
                            ),
                            4326
                        )::geography
                    ) / 0.3048 AS distance_ft
            """),
            {
                "first_latitude": data["first_latitude"],
                "first_longitude": data["first_longitude"],
                "second_latitude": data["second_latitude"],
                "second_longitude": data["second_longitude"],
            },
        )

        return result.mappings().first()


def update_route_record(route_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    origin_site_id = :origin_site_id,
                    destination_site_id = :destination_site_id,
                    origin_droneport_id = :origin_droneport_id,
                    destination_droneport_id = :destination_droneport_id,
                    route_name = :route_name,
                    route_type = :route_type,
                    created_by = :created_by,
                    minimum_aircraft_weight_lbs = :minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs = :maximum_aircraft_weight_lbs,
                    direction = :direction,
                    maximum_aircraft_capacity = :maximum_aircraft_capacity,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    ),
                    segment_attributes = CAST(:segment_attributes AS jsonb)
                WHERE route_id = :route_id
                RETURNING route_id, route_name
            """),
            {
                **data,
                "route_id": route_id,
                "geometry": json.dumps(data["geometry"]),
                "segment_attributes": json.dumps(data["segment_attributes"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def patch_route_record(route_id, data):

    if not data:
        return None

    set_clauses = []
    params = {
        "route_id": route_id,
    }

    for field, value in data.items():

        if field == "segment_attributes":
            set_clauses.append("segment_attributes = CAST(:segment_attributes AS jsonb)")
            params["segment_attributes"] = json.dumps(value)
        else:
            set_clauses.append(f"{field} = :{field}")
            params[field] = value

    sql = f"""
        UPDATE routes
        SET
            {", ".join(set_clauses)}
        WHERE route_id = :route_id
        RETURNING route_id, route_name
    """

    with engine.begin() as connection:
        result = connection.execute(
            text(sql),
            params
        )

        return result.mappings().first()


def soft_delete_route(route_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE route_id = :route_id
                RETURNING route_id
            """),
            {
                "route_id": route_id,
                "status": ROUTE_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()


def approve_route(route_id, approved_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    survey_status = :status,
                    approved_by = :approved_by
                WHERE route_id = :route_id
                RETURNING route_id, approved_by
            """),
            {
                "route_id": route_id,
                "approved_by": approved_by,
                "status": SURVEY_STATUS_APPROVED
            }
        )

        return result.mappings().first()


def reject_route(route_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    survey_status = :status,
                    approved_by = NULL
                WHERE route_id = :route_id
                RETURNING route_id
            """),
            {
                "route_id": route_id,
                "status": SURVEY_STATUS_NOT_SURVEYED
            }
        )

        return result.mappings().first()


def request_route_changes(route_id):
    return reject_route(route_id)


def submit_route(route_id):
    return reject_route(route_id)

