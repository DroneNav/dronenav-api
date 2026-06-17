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
DronePort API oject model implementation source file.

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
    DRONEPORT_STATUS_DELETED,
    DRONEPORT_STATUS_INACTIVE,
    DRONEPORT_STATUS_ACTIVE
)

from app.config.database import engine 

def insert_droneport(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO droneports (
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    operational_status,
                    survey_status,
                    droneport_diameter_ft,
                    geometry 
                )
                VALUES (
                    :site_id,
                    :droneport_name,
                    :droneport_type,
                    :created_by,
                    :operational_status,
                    :survey_status,
                    :droneport_diameter_ft,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                )
                RETURNING droneport_id
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


def select_droneport(droneport_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    droneport_id,
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    last_surveyed_at,
                    surveyed_by,
                    approved_by,
                    droneport_diameter_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneports 
                WHERE droneport_id = :droneport_id
                  AND operational_status <> :deleted_status
            """),
            {
                "droneport_id": droneport_id,
                "deleted_status": DRONEPORT_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_droneports(survey_status=None):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    droneport_id,
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    droneport_diameter_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneports
                WHERE operational_status <> :deleted_status
                  AND (
                      :survey_status IS NULL
                      OR survey_status = :survey_status
                  )
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": DRONEPORT_STATUS_DELETED,
                "survey_status": survey_status,
            }
        )

        return result.mappings().all()


def select_droneports_by_site_id(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    droneport_id,
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    droneport_diameter_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneports
                WHERE operational_status <> :deleted_status
                  AND site_id = :site_id
                ORDER BY created_at DESC
            """),
            {
                "site_id": site_id,
                "deleted_status": DRONEPORT_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_droneport_record(droneport_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE droneports
                SET
                    site_id = :site_id,
                    droneport_name = :droneport_name,
                    droneport_type = :droneport_type,
                    created_by = :created_by,
                    droneport_diameter_ft = :droneport_diameter_ft,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                WHERE droneport_id = :droneport_id
                RETURNING droneport_id, droneport_name
            """),
            {
                **data,
                "droneport_id": droneport_id,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def patch_droneport_record(droneport_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE droneports
                SET
                    droneport_name = :droneport_name,
                    droneport_type = :droneport_type,
                    droneport_diameter_ft = :droneport_diameter_ft
                WHERE droneport_id = :droneport_id
                RETURNING droneport_id, droneport_name
            """),
            {
                **data,
                "droneport_id": droneport_id,
            }
        )

        return result.mappings().first()


def soft_delete_droneport(droneport_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE droneports
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE droneport_id = :droneport_id
                RETURNING droneport_id
            """),
            {
                "droneport_id": droneport_id,
                "status": DRONEPORT_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()


def approve_droneport(droneport_id, approved_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE droneports
                SET
                    operational_status = :status,
                    approved_by = :approved_by
                WHERE droneport_id = :droneport_id
                RETURNING droneport_id, approved_by
            """),
            {
                "droneport_id": droneport_id,
                "approved_by": approved_by,
                "status": DRONEPORT_STATUS_ACTIVE
            }
        )

        return result.mappings().first()


def reject_droneport(droneport_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE droneports
                SET
                    operational_status = :status,
                    approved_by = NULL
                WHERE droneport_id = :droneport_id
                RETURNING droneport_id
            """),
            {
                "droneport_id": droneport_id,
                "status": DRONEPORT_STATUS_INACTIVE
            }
        )

        return result.mappings().first()


def request_droneport_changes(droneport_id):
    return reject_droneport(droneport_id)


def submit_droneport(droneport_id):
    return reject_droneport(droneport_id)

