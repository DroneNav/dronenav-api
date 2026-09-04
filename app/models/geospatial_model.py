from __future__ import annotations

import json

from sqlalchemy import text

from app.config.database import engine


def select_geometry_length_feet(geometry):
    """Return the geodesic length of a GeoJSON geometry in feet."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    ST_Length(
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:geometry),
                            4326
                        )::geography
                    ) / 0.3048 AS length_ft
            """),
            {
                "geometry": json.dumps(geometry),
            },
        )

        return result.mappings().first()


def select_linestring_progress_feet(
    geometry,
    *,
    longitude,
    latitude,
):
    """Return projected distance along a GeoJSON LineString in feet."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                WITH geometries AS (
                    SELECT
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:geometry),
                            4326
                        ) AS line_geometry,
                        ST_SetSRID(
                            ST_MakePoint(
                                :longitude,
                                :latitude
                            ),
                            4326
                        ) AS point_geometry
                ),
                located AS (
                    SELECT
                        line_geometry,
                        ST_LineLocatePoint(
                            line_geometry,
                            point_geometry
                        ) AS fraction
                    FROM geometries
                )
                SELECT
                    ST_Length(
                        ST_LineSubstring(
                            line_geometry,
                            0,
                            fraction
                        )::geography
                    ) / 0.3048 AS distance_ft
                FROM located
            """),
            {
                "geometry": json.dumps(geometry),
                "longitude": longitude,
                "latitude": latitude,
            },
        )

        return result.mappings().first()


def select_geodesic_circle_polygon(
    *,
    longitude,
    latitude,
    radius_nm,
    vertex_count=72,
):
    """Return a GeoJSON polygon approximating a geodesic circle."""

    if vertex_count < 8:
        raise ValueError(
            "Geodesic circle requires at least 8 vertices"
        )

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                WITH parameters AS (
                    SELECT
                        ST_SetSRID(
                            ST_MakePoint(
                                :longitude,
                                :latitude
                            ),
                            4326
                        )::geography AS center,
                        :radius_nm * 1852.0 AS radius_meters
                ),
                points AS (
                    SELECT
                        step,
                        ST_Project(
                            center,
                            radius_meters,
                            radians(
                                step * 360.0 / :vertex_count
                            )
                        )::geometry AS point_geometry
                    FROM parameters
                    CROSS JOIN generate_series(
                        0,
                        :vertex_count
                    ) AS step
                ),
                ring AS (
                    SELECT
                        ST_MakeLine(
                            point_geometry
                            ORDER BY step
                        ) AS ring_geometry
                    FROM points
                )
                SELECT
                    ST_AsGeoJSON(
                        ST_MakePolygon(ring_geometry)
                    ) AS geometry
                FROM ring
            """),
            {
                "longitude": longitude,
                "latitude": latitude,
                "radius_nm": radius_nm,
                "vertex_count": vertex_count,
            },
        )

        row = result.mappings().first()

        if row is None or row["geometry"] is None:
            return None

        return json.loads(row["geometry"])


def select_geodesic_arc_points(
    *,
    start,
    end,
    center,
    radius_nm,
    direction,
    maximum_step_degrees=5.0,
):
    """Return ordered points approximating a geodesic arc."""

    if direction not in {
        "CWA",
        "CCA",
    }:
        raise ValueError(
            f"Unsupported FAA TFR arc direction: {direction}"
        )

    if maximum_step_degrees <= 0:
        raise ValueError(
            "Arc maximum step must be greater than zero"
        )

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                WITH parameters AS (
                    SELECT
                        ST_SetSRID(
                            ST_MakePoint(
                                :center_longitude,
                                :center_latitude
                            ),
                            4326
                        )::geography AS center,
                        ST_SetSRID(
                            ST_MakePoint(
                                :start_longitude,
                                :start_latitude
                            ),
                            4326
                        )::geography AS start_point,
                        ST_SetSRID(
                            ST_MakePoint(
                                :end_longitude,
                                :end_latitude
                            ),
                            4326
                        )::geography AS end_point,
                        :radius_nm * 1852.0 AS radius_meters
                ),
                azimuths AS (
                    SELECT
                        center,
                        radius_meters,
                        degrees(
                            ST_Azimuth(
                                center,
                                start_point
                            )
                        ) AS start_degrees,
                        degrees(
                            ST_Azimuth(
                                center,
                                end_point
                            )
                        ) AS end_degrees
                    FROM parameters
                ),
                sweep AS (
                    SELECT
                        center,
                        radius_meters,
                        start_degrees,
                        CASE
                            WHEN :direction = 'CWA'
                            THEN
                                CASE
                                    WHEN end_degrees >= start_degrees
                                    THEN end_degrees - start_degrees
                                    ELSE end_degrees - start_degrees + 360.0
                                END
                            ELSE
                                CASE
                                    WHEN start_degrees >= end_degrees
                                    THEN start_degrees - end_degrees
                                    ELSE start_degrees - end_degrees + 360.0
                                END
                        END AS sweep_degrees
                    FROM azimuths
                ),
                arc AS (
                    SELECT
                        center,
                        radius_meters,
                        start_degrees,
                        sweep_degrees,
                        GREATEST(
                            1,
                            CEIL(
                                sweep_degrees
                                / :maximum_step_degrees
                            )::integer
                        ) AS step_count
                    FROM sweep
                ),
                points AS (
                    SELECT
                        step,
                        ST_Project(
                            center,
                            radius_meters,
                            radians(
                                CASE
                                    WHEN :direction = 'CWA'
                                    THEN start_degrees
                                        + (
                                            sweep_degrees
                                            * step
                                            / step_count
                                        )
                                    ELSE start_degrees
                                        - (
                                            sweep_degrees
                                            * step
                                            / step_count
                                        )
                                END
                            )
                        )::geometry AS point_geometry
                    FROM arc
                    CROSS JOIN LATERAL generate_series(
                        0,
                        step_count
                    ) AS step
                )
                SELECT
                    json_agg(
                        json_build_array(
                            ST_X(point_geometry),
                            ST_Y(point_geometry)
                        )
                        ORDER BY step
                    ) AS points
                FROM points
            """),
            {
                "start_longitude": start[0],
                "start_latitude": start[1],
                "end_longitude": end[0],
                "end_latitude": end[1],
                "center_longitude": center[0],
                "center_latitude": center[1],
                "radius_nm": radius_nm,
                "direction": direction,
                "maximum_step_degrees": maximum_step_degrees,
            },
        )

        row = result.mappings().first()

        if row is None or row["points"] is None:
            return None

        points = row["points"]

        points[0] = [
            float(start[0]),
            float(start[1]),
        ]

        points[-1] = [
            float(end[0]),
            float(end[1]),
        ]

        return points


def select_geometry_difference(
    base_geometry,
    subtract_geometries,
):
    """Return GeoJSON for base geometry minus zero or more geometries."""

    if not subtract_geometries:
        return base_geometry

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                WITH base AS (
                    SELECT
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:base_geometry),
                            4326
                        ) AS geometry
                ),
                subtract AS (
                    SELECT
                        ST_UnaryUnion(
                            ST_Collect(
                                ST_SetSRID(
                                    ST_GeomFromGeoJSON(value),
                                    4326
                                )
                            )
                        ) AS geometry
                    FROM jsonb_array_elements_text(
                        CAST(:subtract_geometries AS jsonb)
                    )
                )
                SELECT
                    ST_AsGeoJSON(
                        ST_Difference(
                            base.geometry,
                            subtract.geometry
                        )
                    ) AS geometry
                FROM base
                CROSS JOIN subtract
            """),
            {
                "base_geometry": json.dumps(
                    base_geometry
                ),
                "subtract_geometries": json.dumps(
                    [
                        json.dumps(geometry)
                        for geometry in subtract_geometries
                    ]
                ),
            },
        )

        row = result.mappings().first()

        if row is None or row["geometry"] is None:
            return None

        return json.loads(row["geometry"])


def select_geometries_intersect(
    geometry_a,
    geometry_b,
):
    """Return whether two GeoJSON geometries intersect."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    ST_Intersects(
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:geometry_a),
                            4326
                        ),
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:geometry_b),
                            4326
                        )
                    ) AS intersects
            """),
            {
                "geometry_a": json.dumps(
                    geometry_a
                ),
                "geometry_b": json.dumps(
                    geometry_b
                ),
            },
        )

        row = result.mappings().first()

        if row is None:
            return None

        return bool(row["intersects"])


def select_geodesic_buffer_geometry(
    geometry,
    buffer_feet,
):
    """Return GeoJSON geometry buffered geodesically by feet."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    ST_AsGeoJSON(
                        ST_Buffer(
                            ST_SetSRID(
                                ST_GeomFromGeoJSON(:geometry),
                                4326
                            )::geography,
                            :buffer_feet * 0.3048
                        )::geometry
                    )::json AS geometry
            """),
            {
                "geometry": json.dumps(geometry),
                "buffer_feet": buffer_feet,
            },
        )

        row = result.mappings().first()

        if row is None or row["geometry"] is None:
            return None

        return row["geometry"]

