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

from app.config.constants import DEFAULT_SRID, SITE_STATUS_DELETED
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


def select_sites():
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
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM sites
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": SITE_STATUS_DELETED,
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
