from __future__ import annotations

from sqlalchemy import text

from app.config.database import engine


def assign_droneport_landing_space(
    *,
    flight_execution_id: str,
) -> tuple[dict, int]:
    """
    Assign an active landing space for the current Flight.

    Assignment is serialized by locking the arrival DronePort row.

    A Flight receives at most one landing-space assignment. If the
    assignment already exists, the existing assignment is returned.

    Otherwise:
      - never-used active spaces are preferred;
      - then the least-recently-used active space is selected.

    The assignment is recorded in flight_log.
    """

    with engine.begin() as connection:
        execution = connection.execute(
            text(
                """
                SELECT
                    fe.flight_execution_id,
                    fe.arrival_droneport_id,
                    f.flight_id
                FROM flight_executions AS fe
                JOIN flight AS f
                  ON f.flight_execution_id = fe.flight_execution_id
                WHERE fe.flight_execution_id = :flight_execution_id
                ORDER BY f.created_at DESC
                LIMIT 1
                """
            ),
            {
                "flight_execution_id": flight_execution_id,
            },
        ).mappings().first()

        if execution is None:
            return {
                "error": "Flight Execution or Flight was not found."
            }, 404

        arrival_droneport_id = execution["arrival_droneport_id"]
        flight_id = execution["flight_id"]

        if arrival_droneport_id is None:
            return {
                "error": "Flight Execution has no arrival DronePort."
            }, 400

        droneport = connection.execute(
            text(
                """
                SELECT droneport_id
                FROM droneports
                WHERE droneport_id = :droneport_id
                FOR UPDATE
                """
            ),
            {
                "droneport_id": arrival_droneport_id,
            },
        ).first()

        if droneport is None:
            return {
                "error": "Arrival DronePort was not found."
            }, 404

        existing = connection.execute(
            text(
                """
                SELECT
                    ls.landing_space_id,
                    ST_X(ls.geometry) AS longitude,
                    ST_Y(ls.geometry) AS latitude,
                    ls.heading_degrees,
                    ls.charging_capable
                FROM flight_log AS fl
                JOIN droneport_landing_spaces AS ls
                  ON ls.landing_space_id = CAST(
                      fl.details ->> 'landing_space_id'
                      AS uuid
                  )
                WHERE fl.flight_id = :flight_id
                  AND fl.event_type = 'landing_space_assigned'
                ORDER BY fl.occurred_at DESC
                LIMIT 1
                """
            ),
            {
                "flight_id": flight_id,
            },
        ).mappings().first()

        if existing is not None:
            return {
                "assigned": True,
                "landing_space_id": str(
                    existing["landing_space_id"]
                ),
                "arrival_droneport_id": str(
                    arrival_droneport_id
                ),
                "longitude": float(
                    existing["longitude"]
                ),
                "latitude": float(
                    existing["latitude"]
                ),
                "heading_degrees": float(
                    existing["heading_degrees"]
                ),
                "charging_capable": bool(
                    existing["charging_capable"]
                ),
            }, 200

        landing_space = connection.execute(
            text(
                """
                SELECT
                    ls.landing_space_id,
                    ST_X(ls.geometry) AS longitude,
                    ST_Y(ls.geometry) AS latitude,
                    ls.heading_degrees,
                    ls.charging_capable,
                    MAX(fl.occurred_at) AS last_assigned_at
                FROM droneport_landing_spaces AS ls
                LEFT JOIN flight_log AS fl
                  ON fl.event_type = 'landing_space_assigned'
                 AND fl.details ->> 'landing_space_id'
                     = CAST(ls.landing_space_id AS text)
                WHERE ls.droneport_id = :arrival_droneport_id
                  AND ls.operational_status = 'active'
                GROUP BY
                    ls.landing_space_id,
                    ls.geometry,
                    ls.heading_degrees,
                    ls.charging_capable
                ORDER BY
                    MAX(fl.occurred_at) ASC NULLS FIRST,
                    ls.created_at ASC
                LIMIT 1
                """
            ),
            {
                "arrival_droneport_id": arrival_droneport_id,
            },
        ).mappings().first()

        if landing_space is None:
            return {
                "error": (
                    "Arrival DronePort has no active landing space."
                )
            }, 409

        connection.execute(
            text(
                """
                INSERT INTO flight_log (
                    flight_id,
                    flight_execution_id,
                    lifecycle_phase,
                    event_type,
                    event_status,
                    message,
                    details
                )
                VALUES (
                    :flight_id,
                    :flight_execution_id,
                    'pre_flight',
                    'landing_space_assigned',
                    'assigned',
                    'Landing space assigned at arrival DronePort.',
                    jsonb_build_object(
                        'arrival_droneport_id',
                        CAST(:arrival_droneport_id AS text),
                        'landing_space_id',
                        CAST(:landing_space_id AS text)
                    )
                )
                """
            ),
            {
                "flight_id": flight_id,
                "flight_execution_id": flight_execution_id,
                "arrival_droneport_id": arrival_droneport_id,
                "landing_space_id": (
                    landing_space["landing_space_id"]
                ),
            },
        )

        return {
            "assigned": True,
            "landing_space_id": str(
                landing_space["landing_space_id"]
            ),
            "arrival_droneport_id": str(
                arrival_droneport_id
            ),
            "longitude": float(
                landing_space["longitude"]
            ),
            "latitude": float(
                landing_space["latitude"]
            ),
            "heading_degrees": float(
                landing_space["heading_degrees"]
            ),
            "charging_capable": bool(
                landing_space["charging_capable"]
            ),
        }, 200


