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

