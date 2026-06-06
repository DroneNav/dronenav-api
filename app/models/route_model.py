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
    ROUTE_STATUS_ACTIVE
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
                    buffered,
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
                    :buffered,
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
                    buffered,
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


def select_routes():
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
                    buffered,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    segment_attributes
                FROM routes
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": ROUTE_STATUS_DELETED,
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
                    buffered,
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
                    buffered = :buffered,
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
                    operational_status = :status,
                    approved_by = :approved_by
                WHERE route_id = :route_id
                RETURNING route_id, approved_by
            """),
            {
                "route_id": route_id,
                "approved_by": approved_by,
                "status": ROUTE_STATUS_ACTIVE
            }
        )

        return result.mappings().first()


def reject_route(route_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    operational_status = :status,
                    approved_by = NULL
                WHERE route_id = :route_id
                RETURNING route_id
            """),
            {
                "route_id": route_id,
                "status": ROUTE_STATUS_INACTIVE
            }
        )

        return result.mappings().first()


def request_changes_to_route(route_id):
    return reject_route(route_id)

