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
Flight Execution Actual Path API object model implementation source file.

Author:
DroneNav Project Contributors

Created: 2026-08-12

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.

DroneNav - Flight Actual Path persistence model.

A Flight Actual Path captures realtime telemetry samples 
to support UI operations for the aviator.
"""

import json

from sqlalchemy import text

from app.config.database import engine



def upsert_flight_actual_path(
    flight_execution_id,
    data,
):
    coordinates = data["geometry"]["coordinates"]

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO flight_execution_actual_paths (
                    flight_execution_id,
                    flight_id,
                    geometry,
                    point_count,
                    status
                )
                VALUES (
                    :flight_execution_id,
                    :flight_id,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        4326
                    ),
                    :point_count,
                    :status
                )
                ON CONFLICT (flight_execution_id)
                DO UPDATE SET
                    flight_id = EXCLUDED.flight_id,
                    geometry = EXCLUDED.geometry,
                    point_count = EXCLUDED.point_count,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                RETURNING
                    flight_execution_id,
                    flight_id,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    point_count,
                    status,
                    created_at,
                    updated_at
            """),
            {
                "flight_execution_id": flight_execution_id,
                "flight_id": data["flight_id"],
                "geometry": json.dumps(data["geometry"]),
                "point_count": len(coordinates),
                "status": data.get(
                    "status",
                    "recording",
                ),
            },
        )

        return dict(result.mappings().one())


def select_flight_actual_path(flight_execution_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    flight_execution_id,
                    flight_id,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    point_count,
                    status,
                    created_at,
                    updated_at
                FROM flight_execution_actual_paths
                WHERE flight_execution_id = :flight_execution_id
            """),
            {
                "flight_execution_id": flight_execution_id,
            },
        )

        return result.mappings().first()


def append_flight_actual_path_points(
    flight_execution_id,
    data,
):
    coordinates = data["coordinates"]

    if len(coordinates) == 1:
        longitude, latitude = coordinates[0]

        sql = text("""
            UPDATE flight_execution_actual_paths
            SET
                geometry = ST_AddPoint(
                    geometry,
                    ST_SetSRID(
                        ST_MakePoint(:longitude, :latitude),
                        4326
                    )
                ),
                point_count = point_count + 1,
                updated_at = NOW()
            WHERE flight_execution_id = :flight_execution_id
              AND flight_id = :flight_id
              AND status = 'recording'
            RETURNING
                flight_execution_id,
                flight_id,
                ST_AsGeoJSON(geometry)::json AS geometry,
                point_count,
                status,
                created_at,
                updated_at
        """)

        params = {
            "flight_execution_id": flight_execution_id,
            "flight_id": data["flight_id"],
            "longitude": longitude,
            "latitude": latitude,
        }

    else:
        append_geometry = {
            "type": "LineString",
            "coordinates": coordinates,
        }

        sql = text("""
            UPDATE flight_execution_actual_paths
            SET
                geometry = ST_MakeLine(
                    geometry,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        4326
                    )
                ),
                point_count = point_count + :point_count,
                updated_at = NOW()
            WHERE flight_execution_id = :flight_execution_id
              AND flight_id = :flight_id
              AND status = 'recording'
            RETURNING
                flight_execution_id,
                flight_id,
                ST_AsGeoJSON(geometry)::json AS geometry,
                point_count,
                status,
                created_at,
                updated_at
        """)

        params = {
            "flight_execution_id": flight_execution_id,
            "flight_id": data["flight_id"],
            "geometry": json.dumps(append_geometry),
            "point_count": len(coordinates),
        }

    with engine.begin() as connection:
        result = connection.execute(sql, params)
        row = result.mappings().first()

        return dict(row) if row else None


def complete_flight_actual_path(
    flight_execution_id,
    flight_id,
):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_execution_actual_paths
                SET
                    status = 'complete',
                    updated_at = NOW()
                WHERE flight_execution_id = :flight_execution_id
                  AND flight_id = :flight_id
                  AND status = 'recording'
                RETURNING
                    flight_execution_id,
                    flight_id,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    point_count,
                    status,
                    created_at,
                    updated_at
            """),
            {
                "flight_execution_id": flight_execution_id,
                "flight_id": flight_id,
            },
        )

        row = result.mappings().first()

        return dict(row) if row else None


