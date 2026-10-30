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
Aircraft Profile API object model implentation source file.

Author:
DroneNav Project Contributors

Created: 2026-10-29

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from sqlalchemy import text

from app.config.database import engine


def insert_aircraft_calibration_profile_record(aircraft_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO aircraft_calibration_profiles (
                    aircraft_id,
                    cruise_speed_ft_s,
                    planned_deceleration_ft_s2,
                    deceleration_verified,
                    calibrated_at,
                    calibration_flight_execution_id,
                    sample_count,
                    updated_by
                )
                VALUES (
                    :aircraft_id,
                    :cruise_speed_ft_s,
                    :planned_deceleration_ft_s2,
                    :deceleration_verified,
                    :calibrated_at,
                    :calibration_flight_execution_id,
                    :sample_count,
                    :updated_by
                )
                RETURNING profile_id
            """),
            {
                "aircraft_id": aircraft_id,
                "cruise_speed_ft_s": data["cruise_speed_ft_s"],
                "planned_deceleration_ft_s2": data.get(
                    "planned_deceleration_ft_s2"
                ),
                "deceleration_verified": data.get(
                    "deceleration_verified", False
                ),
                "calibrated_at": data.get("calibrated_at"),
                "calibration_flight_execution_id": data.get(
                    "calibration_flight_execution_id"
                ),
                "sample_count": data.get("sample_count", 0),
                "updated_by": data["updated_by"],
            }
        )

        return str(result.scalar())


def select_aircraft_calibration_profile_records(
    aircraft_id, cruise_speed_ft_s=None
):
    params = {"aircraft_id": aircraft_id}

    speed_filter = ""

    if cruise_speed_ft_s is not None:
        speed_filter = """
            AND cruise_speed_ft_s = :cruise_speed_ft_s
        """
        params["cruise_speed_ft_s"] = cruise_speed_ft_s

    with engine.connect() as connection:
        result = connection.execute(
            text(f"""
                SELECT
                    profile_id,
                    aircraft_id,
                    cruise_speed_ft_s,
                    planned_deceleration_ft_s2,
                    deceleration_verified,
                    calibrated_at,
                    calibration_flight_execution_id,
                    sample_count,
                    created_at,
                    updated_at,
                    updated_by
                FROM aircraft_calibration_profiles
                WHERE aircraft_id = :aircraft_id
                {speed_filter}
                ORDER BY cruise_speed_ft_s
            """),
            params
        )

        return result.mappings().all()


def patch_aircraft_calibration_profile_record(
    aircraft_id, profile_id, data, calibration_result=False
):
    allowed_fields = [
        "cruise_speed_ft_s",
        "planned_deceleration_ft_s2",
        "deceleration_verified",
        "calibration_flight_execution_id",
        "sample_count",
    ]

    set_clauses = []
    params = {
        "aircraft_id": aircraft_id,
        "profile_id": profile_id,
        "updated_by": data["updated_by"],
    }

    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = :{field}")
            params[field] = data[field]

    if not set_clauses:
        return None

    if calibration_result and data.get("deceleration_verified") is True:
        set_clauses = [
            clause for clause in set_clauses
            if clause.split(" = ")[0] != "calibrated_at"
        ]

        set_clauses.append("calibrated_at = NOW()")

    if (
        "cruise_speed_ft_s" in data
        or "planned_deceleration_ft_s2" in data
    ) and not calibration_result:
        set_clauses = [
            clause for clause in set_clauses
            if clause.split(" = ")[0] not in (
                "deceleration_verified",
                "calibrated_at",
                "calibration_flight_execution_id",
            )
        ]

        set_clauses.extend([
            "deceleration_verified = FALSE",
            "calibrated_at = NULL",
            "calibration_flight_execution_id = NULL",
        ])

    with engine.begin() as connection:
        result = connection.execute(
            text(f"""
                UPDATE aircraft_calibration_profiles
                SET
                    {", ".join(set_clauses)},
                    updated_at = now(),
                    updated_by = :updated_by
                WHERE aircraft_id = :aircraft_id
                  AND profile_id = :profile_id
                RETURNING profile_id
            """),
            params
        )

        return result.mappings().first()


def delete_aircraft_calibration_profile_record(
    aircraft_id, profile_id
):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM aircraft_calibration_profiles
                WHERE aircraft_id = :aircraft_id
                  AND profile_id = :profile_id
                RETURNING profile_id
            """),
            {
                "aircraft_id": aircraft_id,
                "profile_id": profile_id,
            }
        )

        return result.mappings().first()

