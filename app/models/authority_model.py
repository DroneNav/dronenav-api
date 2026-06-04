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
Authority API object model implementation source file.

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


from sqlalchemy import text

from app.config.database import engine
from app.config.constants import AUTHORITY_STATUS_DELETED


def insert_authority(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO authorities (
                    authority_name,
                    authority_code,
                    authority_type,
                    operational_status,
                    contact_name,
                    contact_email,
                    contact_phone,
                    created_by
                )
                VALUES (
                    :authority_name,
                    :authority_code,
                    :authority_type,
                    :operational_status,
                    :contact_name,
                    :contact_email,
                    :contact_phone,
                    :created_by
                )
                RETURNING authority_id
            """),
            data
        )

        return str(result.scalar())


def select_authority(authority_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    authority_id,
                    authority_name,
                    authority_code,
                    authority_type,
                    operational_status,
                    contact_name,
                    contact_email,
                    contact_phone,
                    created_by,
                    created_at,
                    approved_by,
                    approved_at
                FROM authorities
                WHERE authority_id = :authority_id
                  AND operational_status <> :deleted_status
            """),
            {
                "authority_id": authority_id,
                "deleted_status": AUTHORITY_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_authorities():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    authority_id,
                    authority_name,
                    authority_code,
                    authority_type,
                    operational_status,
                    contact_name,
                    contact_email,
                    contact_phone,
                    created_by,
                    created_at,
                    approved_by,
                    approved_at
                FROM authorities
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": AUTHORITY_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_authority_record(authority_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE authorities
                SET
                    authority_name = :authority_name,
                    authority_code = :authority_code,
                    authority_type = :authority_type,
                    contact_name = :contact_name,
                    contact_email = :contact_email,
                    contact_phone = :contact_phone
                WHERE authority_id = :authority_id
                RETURNING authority_id, authority_name
            """),
            {
                **data,
                "authority_id": authority_id,
            }
        )

        return result.mappings().first()


def soft_delete_authority(authority_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE authorities
                SET
                    operational_status = :deleted_status
                WHERE authority_id = :authority_id
                RETURNING authority_id
            """),
            {
                "authority_id": authority_id,
                "deleted_status": AUTHORITY_STATUS_DELETED,
            }
        )

        return result.mappings().first()
