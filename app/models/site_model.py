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
Site API object model implentation source file.

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
    SITE_STATUS_DELETED,
    SITE_STATUS_ACTIVE,
    SITE_STATUS_INACTIVE,
    SURVEY_STATUS_APPROVED,
    SURVEY_STATUS_NOT_SURVEYED
)

from app.config.database import engine


def insert_site(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO sites (
                    authority_id,
                    site_name,
                    site_type,
                    created_by,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    description,
                    timezone,
                    geometry
                )
                VALUES (
                    :authority_id,
                    :site_name,
                    :site_type,
                    :created_by,
                    :operational_status,
                    :survey_status,
                    :minimum_altitude_ft,
                    :maximum_altitude_ft,
                    :description,
                    :timezone,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                )
                RETURNING site_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
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


def select_site(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    site_id,
                    authority_id,
                    site_name,
                    site_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    last_surveyed_at,
                    surveyed_by,
                    approved_by,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    description,
                    timezone,
                    ST_X(ST_PointOnSurface(geometry)) AS timezone_longitude,
                    ST_Y(ST_PointOnSurface(geometry)) AS timezone_latitude,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM sites
                WHERE site_id = :site_id
                  AND operational_status <> :deleted_status
            """),
            {
                "site_id": site_id,
                "deleted_status": SITE_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_sites(survey_status=None):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    site_id,
                    authority_id,
                    site_name,
                    site_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    description,
                    timezone,
                    ST_X(ST_PointOnSurface(geometry)) AS timezone_longitude,
                    ST_Y(ST_PointOnSurface(geometry)) AS timezone_latitude,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM sites
                WHERE operational_status <> :deleted_status
                  AND (
                      :survey_status IS NULL
                      OR survey_status = :survey_status
                  )
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": SITE_STATUS_DELETED,
                "survey_status": survey_status,
            }
        )

        return result.mappings().all()


def update_site_record(site_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET
                    authority_id = :authority_id,
                    site_name = :site_name,
                    site_type = :site_type,
                    created_by = :created_by,
                    minimum_altitude_ft = :minimum_altitude_ft,
                    maximum_altitude_ft = :maximum_altitude_ft,
                    description = :description,
                    timezone = :timezone,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                WHERE site_id = :site_id
                RETURNING site_id, site_name
            """),
            {
                **data,
                "site_id": site_id,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def patch_site_record(site_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET
                    description = :description,
                    minimum_altitude_ft = :minimum_altitude_ft,
                    maximum_altitude_ft = :maximum_altitude_ft
                WHERE site_id = :site_id
                RETURNING site_id, site_name
            """),
            {
                **data,
                "site_id": site_id,
            }
        )

        return result.mappings().first()


def patch_timezone_record(site_id, timezone):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET timezone = :timezone
                WHERE site_id = :site_id
                RETURNING site_id, timezone
            """),
            {
                "site_id": site_id,
                "timezone": timezone,
            }
        )

        return result.mappings().first()


def soft_delete_site(site_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE site_id = :site_id
                RETURNING site_id
            """),
            {
                "site_id": site_id,
                "status": SITE_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()


def approve_site(site_id, approved_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET
                    survey_status = :status,
                    approved_by = :approved_by 
                WHERE site_id = :site_id
                RETURNING site_id, approved_by
            """),
            {
                "site_id": site_id,
                "approved_by": approved_by,
                "status": SURVEY_STATUS_APPROVED
            }
        )

        return result.mappings().first()


def reject_site(site_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET
                    survey_status = :status,
                    approved_by = NULL
                WHERE site_id = :site_id
                RETURNING site_id
            """),
            {
                "site_id": site_id,
                "status": SURVEY_STATUS_NOT_SURVEYED
            }
        )

        return result.mappings().first()


def request_site_changes(site_id):
    return reject_site(site_id)


def submit_site(site_id):
    return reject_site(site_id)


def compute_point_on_surface_from_geojson(geometry, srid=4326):
    """
    Use PostGIS to calculate a representative point guaranteed to lie
    within the submitted Site polygon.
    """

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    ST_X(point_geometry) AS longitude,
                    ST_Y(point_geometry) AS latitude
                FROM (
                    SELECT ST_PointOnSurface(
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:geometry),
                            :srid
                        )
                    ) AS point_geometry
                ) AS point_result
            """),
            {
                "geometry": json.dumps(geometry),
                "srid": srid,
            },
        )

        return result.mappings().first()


def update_site_timezone_record(site_id, timezone):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET timezone = :timezone
                WHERE site_id = :site_id
                RETURNING
                    site_id,
                    timezone
            """),
            {
                "site_id": site_id,
                "timezone": timezone,
            },
        )

        record = result.mappings().first()

        if record is None:
            return None, "Site not found"

        return dict(record), None


def select_site_point_containment(
    site_id,
    data,
):
    with engine.connect() as connection:
        result = connection.execute(
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
                    s.site_id,
                    ST_Covers(
                        s.geometry,
                        point.geometry
                    ) AS inside,
                    ST_Touches(
                        s.geometry,
                        point.geometry
                    ) AS on_boundary
                FROM sites AS s
                CROSS JOIN point
                WHERE s.site_id = :site_id
                  AND s.operational_status != :deleted_status
            """),
            {
                "site_id": site_id,
                "longitude": data["longitude"],
                "latitude": data["latitude"],
                "srid": DEFAULT_SRID,
                "deleted_status": SITE_STATUS_DELETED,
            },
        )

        return result.mappings().first()

