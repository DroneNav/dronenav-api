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
Obstacle API object model implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-09-26

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
    OBSTACLE_STATUS_DELETED,
    SURVEY_STATUS_APPROVED,
    SURVEY_STATUS_NOT_SURVEYED,
)

from app.config.database import engine


def insert_obstacle(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO obstacles (
                    site_id,
                    obstacle_name,
                    obstacle_type,
                    created_by,
                    operational_status,
                    survey_status,
                    maximum_height_agl_ft,
                    description,
                    geometry
                )
                VALUES (
                    :site_id,
                    :obstacle_name,
                    :obstacle_type,
                    :created_by,
                    :operational_status,
                    :survey_status,
                    :maximum_height_agl_ft,
                    :description,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                )
                RETURNING obstacle_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return str(result.scalar())


def select_obstacle(obstacle_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    obstacle_id,
                    site_id,
                    obstacle_name,
                    obstacle_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    last_surveyed_at,
                    surveyed_by,
                    approved_by,
                    maximum_height_agl_ft,
                    description,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM obstacles
                WHERE obstacle_id = :obstacle_id
                  AND operational_status <> :deleted_status
            """),
            {
                "obstacle_id": obstacle_id,
                "deleted_status": OBSTACLE_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_obstacles(survey_status=None):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    obstacle_id,
                    site_id,
                    obstacle_name,
                    obstacle_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    maximum_height_agl_ft,
                    description,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM obstacles
                WHERE operational_status <> :deleted_status
                  AND (
                      :survey_status IS NULL
                      OR survey_status = :survey_status
                  )
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": OBSTACLE_STATUS_DELETED,
                "survey_status": survey_status,
            }
        )

        return result.mappings().all()


def select_obstacles_by_site_id(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    obstacle_id,
                    site_id,
                    obstacle_name,
                    obstacle_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    maximum_height_agl_ft,
                    description,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM obstacles
                WHERE operational_status <> :deleted_status
                  AND site_id = :site_id
                ORDER BY created_at DESC
            """),
            {
                "site_id": site_id,
                "deleted_status": OBSTACLE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def patch_obstacle_record(obstacle_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE obstacles
                SET
                    obstacle_name = :obstacle_name,
                    obstacle_type = :obstacle_type,
                    maximum_height_agl_ft = :maximum_height_agl_ft,
                    description = :description
                WHERE obstacle_id = :obstacle_id
                RETURNING obstacle_id, obstacle_name
            """),
            {
                **data,
                "obstacle_id": obstacle_id,
            }
        )

        return result.mappings().first()


def soft_delete_obstacle(obstacle_id, deleted_by):
    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM obstacle_membership
                WHERE obstacle_id = :obstacle_id
            """),
            {
                "obstacle_id": obstacle_id,
            }
        )

        result = connection.execute(
            text("""
                UPDATE obstacles
                SET
                    operational_status = :deleted_status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE obstacle_id = :obstacle_id
                RETURNING obstacle_id
            """),
            {
                "obstacle_id": obstacle_id,
                "deleted_status": OBSTACLE_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.scalar()


def approve_obstacle(obstacle_id, approved_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE obstacles
                SET
                    survey_status = :survey_status,
                    approved_by = :approved_by
                WHERE obstacle_id = :obstacle_id
                RETURNING obstacle_id
            """),
            {
                "obstacle_id": obstacle_id,
                "survey_status": SURVEY_STATUS_APPROVED,
                "approved_by": approved_by,
            }
        )

        return result.scalar()


def reject_obstacle(obstacle_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE obstacles
                SET
                    survey_status = :status,
                    approved_by = NULL
                WHERE obstacle_id = :obstacle_id
                RETURNING obstacle_id
            """),
            {
                "obstacle_id": obstacle_id,
                "status": SURVEY_STATUS_NOT_SURVEYED,
            }
        )

        return result.mappings().first()

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


def request_obstacle_changes(obstacle_id):
    return reject_obstacle(obstacle_id)


def submit_obstacle(obstacle_id):
    return reject_obstacle(obstacle_id)


def insert_obstacle_collection(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO obstacle_collections (
                    collection_name,
                    description
                )
                VALUES (
                    :collection_name,
                    :description
                )
                RETURNING obstacle_collection_id
            """),
            data
        )

        return str(result.scalar())


def select_obstacle_collection(obstacle_collection_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    obstacle_collection_id,
                    collection_name,
                    description
                FROM obstacle_collections
                WHERE obstacle_collection_id = :obstacle_collection_id
            """),
            {
                "obstacle_collection_id": obstacle_collection_id,
            }
        )

        return result.mappings().first()


def select_obstacle_collections():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    obstacle_collection_id,
                    collection_name,
                    description
                FROM obstacle_collections
                ORDER BY collection_name
            """)
        )

        return result.mappings().all()


def insert_obstacle_membership(obstacle_collection_id, obstacle_id):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO obstacle_membership (
                    obstacle_collection_id,
                    obstacle_id
                )
                VALUES (
                    :obstacle_collection_id,
                    :obstacle_id
                )
            """),
            {
                "obstacle_collection_id": obstacle_collection_id,
                "obstacle_id": obstacle_id,
            }
        )


def delete_obstacle_membership(obstacle_collection_id, obstacle_id):
    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM obstacle_membership
                WHERE obstacle_collection_id = :obstacle_collection_id
                  AND obstacle_id = :obstacle_id
            """),
            {
                "obstacle_collection_id": obstacle_collection_id,
                "obstacle_id": obstacle_id,
            }
        )


def select_obstacles_by_collection_id(obstacle_collection_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    o.obstacle_id,
                    o.site_id,
                    o.obstacle_name,
                    o.obstacle_type,
                    o.created_by,
                    o.created_at,
                    o.operational_status,
                    o.survey_status,
                    o.maximum_height_agl_ft,
                    o.description,
                    ST_AsGeoJSON(o.geometry)::json AS geometry
                FROM obstacles o
                JOIN obstacle_membership om
                  ON om.obstacle_id = o.obstacle_id
                WHERE om.obstacle_collection_id = :obstacle_collection_id
                  AND o.operational_status <> :deleted_status
                ORDER BY o.created_at DESC
            """),
            {
                "obstacle_collection_id": obstacle_collection_id,
                "deleted_status": OBSTACLE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def delete_obstacle_collection(obstacle_collection_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM obstacle_collections
                WHERE obstacle_collection_id = :obstacle_collection_id
                RETURNING obstacle_collection_id
            """),
            {
                "obstacle_collection_id": obstacle_collection_id,
            }
        )

        return result.scalar()


def patch_obstacle_collection(obstacle_collection_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE obstacle_collections
                SET
                    collection_name = :collection_name,
                    description = :description
                WHERE obstacle_collection_id = :obstacle_collection_id
                RETURNING obstacle_collection_id, collection_name
            """),
            {
                **data,
                "obstacle_collection_id": obstacle_collection_id,
            }
        )

        return result.mappings().first()



