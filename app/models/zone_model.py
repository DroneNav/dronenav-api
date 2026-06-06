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
Zone API object model implementation source file.

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
    ZONE_STATUS_DELETED,
    ZONE_STATUS_INACTIVE,
    ZONE_STATUS_ACTIVE
)

from app.config.database import engine


def insert_zone(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO zones (
                    site_id,
                    zone_name,
                    zone_type,
                    created_by,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    geometry
                )
                VALUES (
                    :site_id,
                    :zone_name,
                    :zone_type,
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
                RETURNING zone_id
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


def select_zone(zone_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    zone_id,
                    site_id,
                    zone_name,
                    zone_type,
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
                FROM zones 
                WHERE zone_id = :zone_id
                  AND operational_status <> :deleted_status
            """),
            {
                "zone_id": zone_id,
                "deleted_status": ZONE_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_zones():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    zone_id,
                    site_id,
                    zone_name,
                    zone_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM zones
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": ZONE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def select_zones_by_site_id(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    zone_id,
                    site_id,
                    zone_name,
                    zone_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM zones
                WHERE operational_status <> :deleted_status
                  AND site_id = :site_id
                ORDER BY created_at DESC
            """),
            {
                "site_id": site_id,
                "deleted_status": ZONE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_zone_record(zone_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE zones
                SET
                    site_id = :site_id,
                    zone_name = :zone_name,
                    zone_type = :zone_type,
                    created_by = :created_by,
                    minimum_altitude_ft = :minimum_altitude_ft,
                    maximum_altitude_ft = :maximum_altitude_ft,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                WHERE zone_id = :zone_id
                RETURNING zone_id, zone_name
            """),
            {
                **data,
                "zone_id": zone_id,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def soft_delete_zone(zone_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE zones
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE zone_id = :zone_id
                RETURNING zone_id
            """),
            {
                "zone_id": zone_id,
                "status": ZONE_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()


def approve_zone(zone_id, approved_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE zones
                SET
                    operational_status = :status,
                    approved_by = :approved_by
                WHERE zone_id = :zone_id
                RETURNING zone_id, approved_by
            """),
            {
                "zone_id": zone_id,
                "approved_by": approved_by,
                "status": ZONE_STATUS_ACTIVE
            }
        )

        return result.mappings().first()


def reject_zone(zone_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE zones 
                SET
                    operational_status = :status,
                    approved_by = NULL
                WHERE zone_id = :zone_id
                RETURNING zone_id
            """),
            {
                "zone_id": zone_id,
                "status": ZONE_STATUS_INACTIVE
            }
        )

        return result.mappings().first()


def request_changes_to_zone(zone_id):
    return reject_zone(zone_id)

