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
"""

import json

from sqlalchemy import text

from app.config.constants import DEFAULT_SRID
from app.config.database import engine


def insert_droneport_landing_space(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO droneport_landing_spaces (
                    droneport_id,
                    geometry,
                    heading_degrees,
                    charging_capable,
                    operational_status,
                    created_by
                )
                VALUES (
                    :droneport_id,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    ),
                    :heading_degrees,
                    :charging_capable,
                    :operational_status,
                    :created_by
                )
                RETURNING landing_space_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            },
        )

        return str(result.scalar())


def select_droneport_landing_space(landing_space_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    landing_space_id,
                    droneport_id,
                    heading_degrees,
                    charging_capable,
                    operational_status,
                    created_by,
                    created_at,
                    ST_X(geometry) AS longitude,
                    ST_Y(geometry) AS latitude,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneport_landing_spaces
                WHERE landing_space_id = :landing_space_id
            """),
            {
                "landing_space_id": landing_space_id,
            },
        )

        return result.mappings().first()


def select_droneport_landing_spaces(
    droneport_id=None,
    operational_status=None,
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    landing_space_id,
                    droneport_id,
                    heading_degrees,
                    charging_capable,
                    operational_status,
                    created_by,
                    created_at,
                    ST_X(geometry) AS longitude,
                    ST_Y(geometry) AS latitude,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneport_landing_spaces
                WHERE (
                    :droneport_id IS NULL
                    OR droneport_id = :droneport_id
                )
                AND (
                    :operational_status IS NULL
                    OR operational_status = :operational_status
                )
                ORDER BY created_at ASC
            """),
            {
                "droneport_id": droneport_id,
                "operational_status": operational_status,
            },
        )

        return result.mappings().all()


def select_duplicate_droneport_landing_space(
    droneport_id,
    geometry,
    exclude_landing_space_id=None,
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    landing_space_id
                FROM droneport_landing_spaces
                WHERE droneport_id = :droneport_id
                  AND (
                      :exclude_landing_space_id IS NULL
                      OR landing_space_id != :exclude_landing_space_id
                  )
                  AND ST_DWithin(
                      geometry::geography,
                      ST_SetSRID(
                          ST_GeomFromGeoJSON(:geometry),
                          :srid
                      )::geography,
                      0.1
                  )
                LIMIT 1
            """),
            {
                "droneport_id": droneport_id,
                "geometry": json.dumps(geometry),
                "exclude_landing_space_id": exclude_landing_space_id,
                "srid": DEFAULT_SRID,
            },
        )

        return result.mappings().first()


def patch_droneport_landing_space(
    landing_space_id,
    data,
):
    allowed_fields = {
        "geometry",
        "heading_degrees",
        "charging_capable",
        "operational_status",
    }

    assignments = []
    parameters = {
        "landing_space_id": landing_space_id,
        "srid": DEFAULT_SRID,
    }

    for field in allowed_fields:
        if field not in data:
            continue

        if field == "geometry":
            assignments.append(
                """
                geometry = ST_SetSRID(
                    ST_GeomFromGeoJSON(:geometry),
                    :srid
                )
                """
            )
            parameters["geometry"] = json.dumps(
                data["geometry"]
            )
        else:
            assignments.append(f"{field} = :{field}")
            parameters[field] = data[field]

    if not assignments:
        return select_droneport_landing_space(
            landing_space_id
        )

    statement = text(
        f"""
        UPDATE droneport_landing_spaces
        SET
            {", ".join(assignments)}
        WHERE landing_space_id = :landing_space_id
        RETURNING landing_space_id
        """
    )

    with engine.begin() as connection:
        result = connection.execute(
            statement,
            parameters,
        )

        updated = result.scalar()

    if updated is None:
        return None

    return select_droneport_landing_space(
        landing_space_id
    )


def select_droneport_landing_space_counts(
    droneport_id,
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    COUNT(*) AS total_count,
                    COUNT(*) FILTER (
                        WHERE operational_status = 'active'
                    ) AS active_count
                FROM droneport_landing_spaces
                WHERE droneport_id = :droneport_id
            """),
            {
                "droneport_id": droneport_id,
            },
        )

        return result.mappings().first()


