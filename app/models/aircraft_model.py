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
Aircraft API object model implentation source file.

Author:
DroneNav Project Contributors

Created: 2026-10-25

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from sqlalchemy import text

from app.config.database import engine


def insert_aircraft_record(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO aircraft (
                    aviator_id,
                    aircraft_name,
                    manufacturer,
                    model,
                    aircraft_type,
                    length_cm,
                    width_cm,
                    height_cm,
                    maximum_takeoff_weight_kg,
                    maximum_speed_ft_s,
                    planned_deceleration_ft_s2,
                    deceleration_verified,
                    operational_status,
                    created_by
                )
                VALUES (
                    :aviator_id,
                    :aircraft_name,
                    :manufacturer,
                    :model,
                    :aircraft_type,
                    :length_cm,
                    :width_cm,
                    :height_cm,
                    :maximum_takeoff_weight_kg,
                    :maximum_speed_ft_s,
                    :planned_deceleration_ft_s2,
                    :deceleration_verified,
                    :operational_status,
                    :created_by
                )
                RETURNING aircraft_id
            """),
            {
                "aviator_id": data["aviator_id"],
                "aircraft_name": data["aircraft_name"],
                "manufacturer": data.get("manufacturer"),
                "model": data["model"],
                "aircraft_type": data["aircraft_type"],
                "length_cm": data["length_cm"],
                "width_cm": data["width_cm"],
                "height_cm": data["height_cm"],
                "maximum_takeoff_weight_kg": data["maximum_takeoff_weight_kg"],
                "maximum_speed_ft_s": data["maximum_speed_ft_s"],
                "planned_deceleration_ft_s2": data.get("planned_deceleration_ft_s2"),
                "deceleration_verified": data.get("deceleration_verified", False),
                "operational_status": data.get("operational_status", "active"),
                "created_by": data["created_by"],
            }
        )

        return str(result.scalar())


def select_aircraft_record(aircraft_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    aircraft_id,
                    aviator_id,
                    aircraft_name,
                    manufacturer,
                    model,
                    aircraft_type,
                    length_cm,
                    width_cm,
                    height_cm,
                    maximum_takeoff_weight_kg,
                    maximum_speed_ft_s,
                    planned_deceleration_ft_s2,
                    deceleration_verified,
                    operational_status,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by
                FROM aircraft
                WHERE aircraft_id = :aircraft_id
            """),
            {"aircraft_id": aircraft_id}
        )

        return result.mappings().first()


def select_aircraft_records(aviator_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    aircraft_id,
                    aviator_id,
                    aircraft_name,
                    manufacturer,
                    model,
                    aircraft_type,
                    length_cm,
                    width_cm,
                    height_cm,
                    maximum_takeoff_weight_kg,
                    maximum_speed_ft_s,
                    planned_deceleration_ft_s2,
                    deceleration_verified,
                    operational_status,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by
                FROM aircraft
                WHERE aviator_id = :aviator_id
                ORDER BY aircraft_name, model
            """),
            {"aviator_id": aviator_id}
        )

        return result.mappings().all()


def update_aircraft_record(aircraft_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE aircraft
                SET
                    aircraft_name = :aircraft_name,
                    manufacturer = :manufacturer,
                    model = :model,
                    aircraft_type = :aircraft_type,
                    length_cm = :length_cm,
                    width_cm = :width_cm,
                    height_cm = :height_cm,
                    maximum_takeoff_weight_kg = :maximum_takeoff_weight_kg,
                    maximum_speed_ft_s = :maximum_speed_ft_s,
                    planned_deceleration_ft_s2 = CASE
                        WHEN :planned_deceleration_ft_s2 IS NULL
                        THEN planned_deceleration_ft_s2
                        ELSE :planned_deceleration_ft_s2
                    END,
                    deceleration_verified = COALESCE(
                        :deceleration_verified,
                        deceleration_verified
                    ),
                    operational_status = :operational_status,
                    updated_at = now(),
                    updated_by = :updated_by
                WHERE aircraft_id = :aircraft_id
                RETURNING aircraft_id
            """),
            {
                "aircraft_id": aircraft_id,
                "aircraft_name": data["aircraft_name"],
                "manufacturer": data.get("manufacturer"),
                "model": data["model"],
                "aircraft_type": data["aircraft_type"],
                "length_cm": data["length_cm"],
                "width_cm": data["width_cm"],
                "height_cm": data["height_cm"],
                "maximum_takeoff_weight_kg": data["maximum_takeoff_weight_kg"],
                "maximum_speed_ft_s": data["maximum_speed_ft_s"],
                "planned_deceleration_ft_s2": data.get("planned_deceleration_ft_s2"),
                "deceleration_verified": data.get("deceleration_verified"),
                "operational_status": data.get("operational_status", "active"),
                "updated_by": data["updated_by"],
            }
        )

        return result.mappings().first()


def patch_aircraft_record(aircraft_id, data):
    allowed_fields = [
        "aircraft_name",
        "manufacturer",
        "model",
        "aircraft_type",
        "length_cm",
        "width_cm",
        "height_cm",
        "maximum_takeoff_weight_kg",
        "maximum_speed_ft_s",
        "planned_deceleration_ft_s2",
        "deceleration_verified",
        "operational_status",
    ]

    set_clauses = []
    params = {
        "aircraft_id": aircraft_id,
        "updated_by": data["updated_by"],
    }

    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = :{field}")
            params[field] = data[field]

    if not set_clauses:
        return None

    with engine.begin() as connection:
        result = connection.execute(
            text(f"""
                UPDATE aircraft
                SET
                    {", ".join(set_clauses)},
                    updated_at = now(),
                    updated_by = :updated_by
                WHERE aircraft_id = :aircraft_id
                RETURNING aircraft_id
            """),
            params
        )

        return result.mappings().first()


def delete_aircraft_record(aircraft_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM aircraft
                WHERE aircraft_id = :aircraft_id
                RETURNING aircraft_id
            """),
            {"aircraft_id": aircraft_id}
        )

        return result.mappings().first()


