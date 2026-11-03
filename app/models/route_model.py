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
import math

from sqlalchemy import text

from app.config.constants import (
    DEFAULT_SRID,
    SITE_STATUS_DELETED,
    ROUTE_STATUS_DELETED,
    ROUTE_STATUS_INACTIVE,
    ROUTE_STATUS_ACTIVE,
    SURVEY_STATUS_APPROVED,
    SURVEY_STATUS_NOT_SURVEYED,
    MINIMUM_ENDPOINT_SEGMENT_LENGTH_FT,
    MINIMUM_INTERMEDIATE_SEGMENT_LENGTH_FT,
)

from app.config.database import engine


def resolve_or_create_route_node(
    connection,
    longitude,
    latitude,
):
    existing_result = connection.execute(
        text("""
            SELECT
                route_node_id,
                site_id
            FROM route_nodes
            WHERE ST_DWithin(
                geometry::geography,
                ST_SetSRID(
                    ST_MakePoint(
                        :longitude,
                        :latitude
                    ),
                    :srid
                )::geography,
                :snap_distance_meters
            )
        """),
        {
            "longitude": longitude,
            "latitude": latitude,
            "srid": DEFAULT_SRID,
            "snap_distance_meters": 0.1,
        },
    )

    existing_nodes = existing_result.mappings().all()

    if len(existing_nodes) > 1:
        raise RuntimeError(
            "Multiple Route Nodes exist at the same endpoint coordinate."
        )

    if len(existing_nodes) == 1:
        return (
            str(existing_nodes[0]["route_node_id"]),
            existing_nodes[0]["site_id"],
        )

    site_result = connection.execute(
        text("""
            WITH point AS (
                SELECT ST_SetSRID(
                    ST_MakePoint(
                        :longitude,
                        :latitude
                    ),
                    :srid
                ) AS geometry
            )
            SELECT
                site_id
            FROM sites
            CROSS JOIN point
            WHERE ST_Covers(
                sites.geometry,
                point.geometry
            )
              AND sites.operational_status != :deleted_status
        """),
        {
            "longitude": longitude,
            "latitude": latitude,
            "srid": DEFAULT_SRID,
            "deleted_status": SITE_STATUS_DELETED,
        },
    )

    containing_sites = site_result.mappings().all()

    if len(containing_sites) > 1:
        raise RuntimeError(
            "Route endpoint is contained by multiple Sites."
        )

    site_id = (
        containing_sites[0]["site_id"]
        if len(containing_sites) == 1
        else None
    )

    result = connection.execute(
        text("""
            INSERT INTO route_nodes (
                site_id,
                geometry
            )
            VALUES (
                :site_id,
                ST_SetSRID(
                    ST_MakePoint(
                        :longitude,
                        :latitude
                    ),
                    :srid
                )
            )
            RETURNING route_node_id
        """),
        {
            "site_id": site_id,
            "longitude": longitude,
            "latitude": latitude,
            "srid": DEFAULT_SRID,
        },
    )

    return (
        str(result.scalar()),
        site_id,
    )


def insert_route(data):

    with engine.begin() as connection:
        coordinates = data["geometry"]["coordinates"]

        origin_longitude, origin_latitude = coordinates[0]
        destination_longitude, destination_latitude = coordinates[-1]

        origin_route_node_id, origin_site_id = (
            resolve_or_create_route_node(
                connection,
                origin_longitude,
                origin_latitude,
            )
        )

        destination_route_node_id, destination_site_id = (
            resolve_or_create_route_node(
                connection,
                destination_longitude,
                destination_latitude,
            )
        )

        result = connection.execute(
            text("""
                INSERT INTO routes (
                    origin_site_id,
                    destination_site_id,
                    origin_route_node_id,
                    destination_route_node_id,
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
                    :origin_route_node_id,
                    :destination_route_node_id,
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
                "origin_site_id": origin_site_id,
                "destination_site_id": destination_site_id,
                "origin_route_node_id": origin_route_node_id,
                "destination_route_node_id": destination_route_node_id,
                "geometry": json.dumps(data["geometry"]),
                "segment_attributes": json.dumps(data["segment_attributes"]),
                "srid": DEFAULT_SRID,
            }
        )

        route_id = str(result.scalar())

        connection.execute(
            text("""
                INSERT INTO route_node_connections (
                    route_id,
                    route_node_id,
                    waypoint_index
                )
                VALUES
                    (
                        :route_id,
                        :origin_route_node_id,
                        0
                    ),
                    (
                        :route_id,
                        :destination_route_node_id,
                        :destination_waypoint_index
                    )
            """),
            {
                "route_id": route_id,
                "origin_route_node_id": origin_route_node_id,
                "destination_route_node_id": destination_route_node_id,
                "destination_waypoint_index": len(coordinates) - 1,
            }
        )

        return route_id


def insert_route_node_connection(
    connection,
    route_id,
    route_node_id,
    waypoint_index,
):
    result = connection.execute(
        text("""
            SELECT
                ST_NPoints(r.geometry) AS waypoint_count,
                ST_Distance(
                    ST_PointN(
                        r.geometry,
                        :point_number
                    )::geography,
                    rn.geometry::geography
                ) AS distance_meters
            FROM routes r
            CROSS JOIN route_nodes rn
            WHERE r.route_id = :route_id
              AND rn.route_node_id = :route_node_id
              AND r.operational_status <> :deleted_status
            FOR UPDATE OF r
        """),
        {
            "route_id": route_id,
            "route_node_id": route_node_id,
            "point_number": waypoint_index + 1,
            "deleted_status": ROUTE_STATUS_DELETED,
        },
    )

    row = result.mappings().first()

    if row is None:
        raise ValueError(
            "Route or Route Node not found."
        )

    if (
        waypoint_index < 0
        or waypoint_index >= row["waypoint_count"]
    ):
        raise ValueError(
            "Waypoint index is outside the Route geometry."
        )

    if (
        row["distance_meters"] is None
        or row["distance_meters"] > 0.1
    ):
        raise ValueError(
            "Route Node does not match the selected waypoint."
        )

    existing = connection.execute(
        text("""
            SELECT
                route_node_id,
                waypoint_index
            FROM route_node_connections
            WHERE route_id = :route_id
              AND (
                  route_node_id = :route_node_id
                  OR waypoint_index = :waypoint_index
              )
        """),
        {
            "route_id": route_id,
            "route_node_id": route_node_id,
            "waypoint_index": waypoint_index,
        },
    ).mappings().first()

    if existing is not None:
        if (
            str(existing["route_node_id"]) == str(route_node_id)
            and existing["waypoint_index"] == waypoint_index
        ):
            return {
                "route_id": str(route_id),
                "route_node_id": str(route_node_id),
                "waypoint_index": waypoint_index,
                "already_connected": True,
            }

        raise ValueError(
            "Route Node or waypoint is already connected elsewhere."
        )

    connection.execute(
        text("""
            INSERT INTO route_node_connections (
                route_id,
                route_node_id,
                waypoint_index
            )
            VALUES (
                :route_id,
                :route_node_id,
                :waypoint_index
            )
        """),
        {
            "route_id": route_id,
            "route_node_id": route_node_id,
            "waypoint_index": waypoint_index,
        },
    )

    return {
        "route_id": str(route_id),
        "route_node_id": str(route_node_id),
        "waypoint_index": waypoint_index,
    }


def validate_route_segment_split(
    geometry,
    segment_index,
    longitude,
    latitude,
):
    coordinates = geometry.get("coordinates", [])

    if (
        geometry.get("type") != "LineString"
        or not isinstance(coordinates, list)
        or len(coordinates) < 2
    ):
        raise ValueError("Invalid Route geometry.")

    segment_count = len(coordinates) - 1

    if (
        isinstance(segment_index, bool)
        or not isinstance(segment_index, int)
        or segment_index < 0
        or segment_index >= segment_count
    ):
        raise ValueError("Invalid segment index.")

    for value, minimum, maximum in (
        (longitude, -180, 180),
        (latitude, -90, 90),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not minimum <= value <= maximum
        ):
            raise ValueError("Invalid insertion coordinate.")

    start = coordinates[segment_index]
    end = coordinates[segment_index + 1]

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                WITH segment AS (
                    SELECT
                        ST_SetSRID(
                            ST_MakeLine(
                                ST_MakePoint(:start_lon, :start_lat),
                                ST_MakePoint(:end_lon, :end_lat)
                            ),
                            4326
                        ) AS geom
                ),
                proposed AS (
                    SELECT
                        ST_SetSRID(
                            ST_MakePoint(:longitude, :latitude),
                            4326
                        ) AS geom
                ),
                projected AS (
                    SELECT
                        ST_LineInterpolatePoint(
                            segment.geom,
                            ST_LineLocatePoint(
                                segment.geom,
                                proposed.geom
                            )
                        ) AS geom,
                        segment.geom AS segment_geom,
                        proposed.geom AS proposed_geom
                    FROM segment, proposed
                )
                SELECT
                    ST_Distance(
                        proposed_geom::geography,
                        geom::geography
                    ) AS offset_meters,
                    ST_Length(
                        ST_MakeLine(
                            ST_StartPoint(segment_geom),
                            geom
                        )::geography
                    ) / 0.3048 AS first_length_ft,
                    ST_Length(
                        ST_MakeLine(
                            geom,
                            ST_EndPoint(segment_geom)
                        )::geography
                    ) / 0.3048 AS second_length_ft,
                    ST_X(geom) AS longitude,
                    ST_Y(geom) AS latitude
                FROM projected
            """),
            {
                "start_lon": start[0],
                "start_lat": start[1],
                "end_lon": end[0],
                "end_lat": end[1],
                "longitude": longitude,
                "latitude": latitude,
            },
        )

        row = result.mappings().first()

    if row is None:
        raise ValueError(
            "Unable to validate segment split."
        )

    if row["offset_meters"] > 0.1:
        raise ValueError(
            "Insertion coordinate is not on the selected segment."
        )

    first_minimum = (
        MINIMUM_ENDPOINT_SEGMENT_LENGTH_FT
        if segment_index == 0
        else MINIMUM_INTERMEDIATE_SEGMENT_LENGTH_FT
    )

    second_minimum = (
        MINIMUM_ENDPOINT_SEGMENT_LENGTH_FT
        if segment_index == segment_count - 1
        else MINIMUM_INTERMEDIATE_SEGMENT_LENGTH_FT
    )

    first_length = row["first_length_ft"]
    second_length = row["second_length_ft"]

    if (
        first_length <= first_minimum
        if segment_index == 0
        else first_length < first_minimum
    ):
        raise ValueError(
            "First resulting segment is too short."
        )

    if (
        second_length <= second_minimum
        if segment_index == segment_count - 1
        else second_length < second_minimum
    ):
        raise ValueError(
            "Second resulting segment is too short."
        )

    return {
        "segment_index": segment_index,
        "longitude": row["longitude"],
        "latitude": row["latitude"],
        "first_length_ft": first_length,
        "second_length_ft": second_length,
    }


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
                    routes.route_id,
                    routes.origin_site_id,
                    routes.destination_site_id,
                    routes.origin_route_node_id,
                    routes.destination_route_node_id,
                    routes.route_name,
                    routes.route_type,
                    routes.created_by,
                    routes.created_at,
                    routes.operational_status,
                    routes.survey_status,
                    routes.last_surveyed_at,
                    routes.surveyed_by,
                    routes.approved_by,
                    routes.minimum_aircraft_weight_lbs,
                    routes.maximum_aircraft_weight_lbs,
                    routes.direction,
                    routes.maximum_aircraft_capacity,
                    ST_AsGeoJSON(routes.geometry)::json AS geometry,
                    routes.segment_attributes
                FROM routes
                WHERE routes.route_id = :route_id
                  AND routes.operational_status <> :deleted_status
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
                    routes.route_id,
                    routes.origin_site_id,
                    routes.destination_site_id,
                    routes.origin_route_node_id,
                    routes.destination_route_node_id,
                    routes.route_name,
                    routes.route_type,
                    routes.created_by,
                    routes.created_at,
                    routes.operational_status,
                    routes.survey_status,
                    routes.minimum_aircraft_weight_lbs,
                    routes.maximum_aircraft_weight_lbs,
                    routes.direction,
                    routes.maximum_aircraft_capacity,
                    ST_AsGeoJSON(routes.geometry)::json AS geometry,
                    routes.segment_attributes
                FROM routes
                WHERE routes.operational_status <> :deleted_status
                  AND (
                        :survey_status IS NULL
                        OR routes.survey_status = :survey_status
                  )
                ORDER BY routes.created_at DESC
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
                    routes.route_id,
                    routes.origin_site_id,
                    routes.destination_site_id,
                    routes.origin_route_node_id,
                    routes.destination_route_node_id,
                    routes.route_name,
                    routes.route_type,
                    routes.created_by,
                    routes.created_at,
                    routes.operational_status,
                    routes.survey_status,
                    routes.minimum_aircraft_weight_lbs,
                    routes.maximum_aircraft_weight_lbs,
                    routes.direction,
                    routes.maximum_aircraft_capacity,
                    ST_AsGeoJSON(routes.geometry)::json AS geometry,
                    routes.segment_attributes
                FROM routes
                WHERE routes.operational_status <> :deleted_status
                  AND (
                        routes.origin_site_id = :site_id
                        OR routes.destination_site_id = :site_id
                  )
                ORDER BY routes.created_at DESC
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


def select_route_waypoint_for_update(
    connection,
    route_id,
    waypoint_index,
):
    if (
        isinstance(waypoint_index, bool)
        or not isinstance(waypoint_index, int)
        or waypoint_index < 0
    ):
        raise ValueError("Invalid waypoint index.")

    result = connection.execute(
        text("""
            SELECT
                ST_NPoints(geometry) AS waypoint_count,
                ST_X(
                    ST_PointN(geometry, :point_number)
                ) AS longitude,
                ST_Y(
                    ST_PointN(geometry, :point_number)
                ) AS latitude
            FROM routes
            WHERE route_id = :route_id
              AND operational_status <> :deleted_status
            FOR UPDATE
        """),
        {
            "route_id": route_id,
            "point_number": waypoint_index + 1,
            "deleted_status": ROUTE_STATUS_DELETED,
        },
    )

    row = result.mappings().first()

    if row is None:
        raise ValueError("Route not found.")

    if waypoint_index >= row["waypoint_count"]:
        raise ValueError(
            "Waypoint index is outside the Route geometry."
        )

    return (
        row["longitude"],
        row["latitude"],
    )


def update_route_record(route_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    origin_site_id = :origin_site_id,
                    destination_site_id = :destination_site_id,
                    origin_route_node_id = :origin_route_node_id,
                    destination_route_node_id = :destination_route_node_id,
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


def count_routes_for_route_node(route_node_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM routes
                WHERE origin_route_node_id = :route_node_id
                   OR destination_route_node_id = :route_node_id
            """),
            {
                "route_node_id": route_node_id,
            },
        )

        return result.scalar_one()


def select_shared_route_node(
    from_route_id,
    to_route_id,
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT route_node_id
                FROM (
                    SELECT origin_route_node_id AS route_node_id
                    FROM routes
                    WHERE route_id = :from_route_id

                    UNION

                    SELECT destination_route_node_id AS route_node_id
                    FROM routes
                    WHERE route_id = :from_route_id
                ) AS from_nodes
                WHERE route_node_id IN (
                    SELECT origin_route_node_id
                    FROM routes
                    WHERE route_id = :to_route_id

                    UNION

                    SELECT destination_route_node_id
                    FROM routes
                    WHERE route_id = :to_route_id
                )
            """),
            {
                "from_route_id": from_route_id,
                "to_route_id": to_route_id,
            },
        )

        return result.scalar_one_or_none()


def select_orphaned_route_nodes():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    rn.route_node_id,
                    rn.site_id,
                    ST_AsGeoJSON(rn.geometry)::json AS geometry
                FROM route_nodes AS rn
                LEFT JOIN droneports AS d
                    ON d.route_node_id = rn.route_node_id
                LEFT JOIN routes AS r_origin
                    ON r_origin.origin_route_node_id = rn.route_node_id
                LEFT JOIN routes AS r_destination
                    ON r_destination.destination_route_node_id = rn.route_node_id
                WHERE d.route_node_id IS NULL
                  AND r_origin.route_id IS NULL
                  AND r_destination.route_id IS NULL
                ORDER BY rn.route_node_id
            """)
        )

        return [dict(row) for row in result.mappings().all()]


def delete_orphaned_route_nodes():
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM route_nodes AS rn
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM droneports AS d
                    WHERE d.route_node_id = rn.route_node_id
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM routes AS r
                    WHERE r.origin_route_node_id = rn.route_node_id
                       OR r.destination_route_node_id = rn.route_node_id
                )
                RETURNING
                    rn.route_node_id,
                    rn.site_id
            """)
        )

        return [dict(row) for row in result.mappings().all()]


