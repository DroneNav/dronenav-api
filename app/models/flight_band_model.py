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
Flight Band API object model implentation source file.

Author:
DroneNav Project Contributors

Created: 2026-07-05

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from sqlalchemy import text

from app.config.database import engine

from app.config.constants import (
    DEFAULT_ALLDAYS,
    DEFAULT_TIMEZONE,
    DEFAULT_MINIMUM_ALTITUDE_FT,
    DEFAULT_MAXIMUM_ALTITUDE_FT,
    DEFAULT_START_TIME,
    DEFAULT_END_TIME
)


def insert_flight_band_record(data):
    days = data.get("days", DEFAULT_ALLDAYS)

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO flight_bands (
                    flight_class,
                    band_name,
                    min_agl_ft,
                    max_agl_ft,
                    start_time,
                    end_time,
                    timezone,
                    operational_status,
                    created_by
                )
                VALUES (
                    :flight_class,
                    :band_name,
                    :min_agl_ft,
                    :max_agl_ft,
                    :start_time,
                    :end_time,
                    :timezone,
                    :operational_status,
                    :created_by
                )
                RETURNING flight_band_id
            """),
            {
                "flight_class": data["flight_class"],
                "band_name": data["band_name"],
                "min_agl_ft": data.get("min_agl_ft", DEFAULT_MINIMUM_ALTITUDE_FT),
                "max_agl_ft": data.get("max_agl_ft", DEFAULT_MAXIMUM_ALTITUDE_FT),
                "start_time": data.get("start_time", DEFAULT_START_TIME),
                "end_time": data.get("end_time", DEFAULT_END_TIME),
                "timezone": data.get("timezone", DEFAULT_TIMEZONE),
                "operational_status": data.get("operational_status", "active"),
                "created_by": data.get("created_by"),
            }
        )

        flight_band_id = str(result.scalar())

        _insert_flight_band_days(connection, flight_band_id, days)

        return flight_band_id


def select_flight_band_record(flight_band_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    fb.flight_band_id,
                    fb.flight_class,
                    fb.band_name,
                    fb.min_agl_ft,
                    fb.max_agl_ft,
                    fb.start_time,
                    fb.end_time,
                    fb.timezone,
                    fb.operational_status,
                    fb.created_at,
                    fb.created_by,
                    fb.updated_at,
                    fb.updated_by,
                    COALESCE(
                        array_agg(fbd.day_of_week ORDER BY fbd.day_of_week)
                        FILTER (WHERE fbd.day_of_week IS NOT NULL),
                        '{}'
                    ) AS days
                FROM flight_bands fb
                LEFT JOIN flight_band_days fbd
                    ON fb.flight_band_id = fbd.flight_band_id
                WHERE fb.flight_band_id = :flight_band_id
                GROUP BY fb.flight_band_id
            """),
            {"flight_band_id": flight_band_id}
        )

        return result.mappings().first()


def select_flight_band_records(flight_class=None, operational_status=None):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    fb.flight_band_id,
                    fb.flight_class,
                    fb.band_name,
                    fb.min_agl_ft,
                    fb.max_agl_ft,
                    fb.start_time,
                    fb.end_time,
                    fb.timezone,
                    fb.operational_status,
                    fb.created_at,
                    fb.created_by,
                    fb.updated_at,
                    fb.updated_by,
                    COALESCE(
                        array_agg(fbd.day_of_week ORDER BY fbd.day_of_week)
                        FILTER (WHERE fbd.day_of_week IS NOT NULL),
                        '{}'
                    ) AS days
                FROM flight_bands fb
                LEFT JOIN flight_band_days fbd
                    ON fb.flight_band_id = fbd.flight_band_id
                WHERE (
                    :flight_class IS NULL
                    OR fb.flight_class = :flight_class
                )
                AND (
                    :operational_status IS NULL
                    OR fb.operational_status = :operational_status
                )
                GROUP BY fb.flight_band_id
                ORDER BY fb.flight_class, fb.band_name
            """),
            {
                "flight_class": flight_class,
                "operational_status": operational_status,
            }
        )

        return result.mappings().all()


def update_flight_band_record(flight_band_id, data):
    days = data.get("days", DEFAULT_ALLDAYS)

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_bands
                SET
                    flight_class = :flight_class,
                    band_name = :band_name,
                    min_agl_ft = :min_agl_ft,
                    max_agl_ft = :max_agl_ft,
                    start_time = :start_time,
                    end_time = :end_time,
                    timezone = :timezone,
                    operational_status = :operational_status,
                    updated_at = now(),
                    updated_by = :updated_by
                WHERE flight_band_id = :flight_band_id
                RETURNING flight_band_id
            """),
            {
                "flight_band_id": flight_band_id,
                "flight_class": data["flight_class"],
                "band_name": data["band_name"],
                "min_agl_ft": data.get("min_agl_ft", DEFAULT_MINIMUM_ALTITUDE_FT),
                "max_agl_ft": data.get("max_agl_ft", DEFAULT_MAXIMUM_ALTITUDE_FT),
                "start_time": data.get("start_time", DEFAULT_START_TIME),
                "end_time": data.get("end_time", DEFAULT_END_TIME),
                "timezone": data.get("timezone", DEFAULT_TIMEZONE),
                "operational_status": data.get("operational_status", "active"),
                "updated_by": data.get("updated_by"),
            }
        )

        row = result.mappings().first()

        if not row:
            return None

        _replace_flight_band_days(connection, flight_band_id, days)

        return row


def patch_flight_band_record(flight_band_id, data):
    allowed_fields = [
        "flight_class",
        "band_name",
        "min_agl_ft",
        "max_agl_ft",
        "start_time",
        "end_time",
        "timezone",
        "operational_status",
        "updated_by",
    ]

    set_clauses = []
    params = {"flight_band_id": flight_band_id}

    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = :{field}")
            params[field] = data[field]

    with engine.begin() as connection:
        if set_clauses:
            sql = f"""
                UPDATE flight_bands
                SET
                    {", ".join(set_clauses)},
                    updated_at = now()
                WHERE flight_band_id = :flight_band_id
                RETURNING flight_band_id
            """

            result = connection.execute(text(sql), params)
            row = result.mappings().first()

            if not row:
                return None
        else:
            result = connection.execute(
                text("""
                    SELECT flight_band_id
                    FROM flight_bands
                    WHERE flight_band_id = :flight_band_id
                """),
                {"flight_band_id": flight_band_id}
            )

            row = result.mappings().first()

            if not row:
                return None

        if "days" in data:
            _replace_flight_band_days(connection, flight_band_id, data["days"])

        return row


def delete_flight_band_record(flight_band_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM flight_bands
                WHERE flight_band_id = :flight_band_id
                RETURNING flight_band_id
            """),
            {"flight_band_id": flight_band_id}
        )

        return result.mappings().first()


def _insert_flight_band_days(connection, flight_band_id, days):
    for day in days:
        connection.execute(
            text("""
                INSERT INTO flight_band_days (
                    flight_band_id,
                    day_of_week
                )
                VALUES (
                    :flight_band_id,
                    :day_of_week
                )
            """),
            {
                "flight_band_id": flight_band_id,
                "day_of_week": day,
            }
        )


def _replace_flight_band_days(connection, flight_band_id, days):
    connection.execute(
        text("""
            DELETE FROM flight_band_days
            WHERE flight_band_id = :flight_band_id
        """),
        {"flight_band_id": flight_band_id}
    )

    _insert_flight_band_days(connection, flight_band_id, days)


def select_active_flight_band_records_by_class(flight_class):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    fb.flight_band_id,
                    fb.flight_class,
                    fb.band_name,
                    fb.min_agl_ft,
                    fb.max_agl_ft,
                    fb.start_time,
                    fb.end_time,
                    fb.timezone,
                    fb.operational_status,
                    COALESCE(
                        array_agg(fbd.day_of_week ORDER BY fbd.day_of_week)
                        FILTER (WHERE fbd.day_of_week IS NOT NULL),
                        '{}'
                    ) AS days
                FROM flight_bands fb
                LEFT JOIN flight_band_days fbd
                    ON fb.flight_band_id = fbd.flight_band_id
                WHERE fb.flight_class = :flight_class
                  AND fb.operational_status = 'active'
                GROUP BY fb.flight_band_id
                ORDER BY fb.start_time, fb.end_time
            """),
            {
                "flight_class": flight_class,
            }
        )

        return result.mappings().all()

