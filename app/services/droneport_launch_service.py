from __future__ import annotations

from sqlalchemy import text

from app.config.database import engine

from app.config.constants import (
    DRONEPORT_LAUNCH_SEPARATION_SECONDS,
)


def request_droneport_launch_authorization(
    *,
    flight_execution_id: str,
) -> tuple[dict, int]:
    """
    Atomically authorize launch from a Flight Execution's departure DronePort.

    Authorization is serialized by locking the departure DronePort row.
    A granted authorization is recorded in flight_log before the aircraft
    is permitted to arm.
    """

    with engine.begin() as connection:
        execution = connection.execute(
            text(
                """
                SELECT
                    fe.flight_execution_id,
                    fe.departure_droneport_id,
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

        departure_droneport_id = execution["departure_droneport_id"]

        if departure_droneport_id is None:
            return {
                "error": "Flight Execution has no departure DronePort."
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
                "droneport_id": departure_droneport_id,
            },
        ).first()

        if droneport is None:
            return {
                "error": "Departure DronePort was not found."
            }, 404

        previous = connection.execute(
            text(
                """
                SELECT fl.occurred_at
                FROM flight_log AS fl
                JOIN flight_executions AS fe
                  ON fe.flight_execution_id = fl.flight_execution_id
                WHERE fe.departure_droneport_id = :departure_droneport_id
                  AND fl.event_type = 'launch_authorized'
                ORDER BY fl.occurred_at DESC
                LIMIT 1
                """
            ),
            {
                "departure_droneport_id": departure_droneport_id,
            },
        ).mappings().first()

        if previous is not None:
            separation = connection.execute(
                text(
                    """
                    SELECT EXTRACT(
                        EPOCH FROM (
                            CURRENT_TIMESTAMP - :previous_occurred_at
                        )
                    )
                    """
                ),
                {
                    "previous_occurred_at": previous["occurred_at"],
                },
            ).scalar_one()

            elapsed_seconds = float(separation)

            if elapsed_seconds < DRONEPORT_LAUNCH_SEPARATION_SECONDS:
                retry_after_seconds = max(
                    1,
                    int(
                        DRONEPORT_LAUNCH_SEPARATION_SECONDS
                        - elapsed_seconds
                    ),
                )

                return {
                    "authorized": False,
                    "departure_droneport_id": str(
                        departure_droneport_id
                    ),
                    "retry_after_seconds": retry_after_seconds,
                }, 200

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
                    'launch_authorized',
                    'granted',
                    'Launch authorized from departure DronePort.',
                    jsonb_build_object(
                        'departure_droneport_id',
                        CAST(:departure_droneport_id AS text),
                        'minimum_separation_seconds',
                        :minimum_separation_seconds
                    )
                )
                """
            ),
            {
                "flight_id": execution["flight_id"],
                "flight_execution_id": flight_execution_id,
                "departure_droneport_id": departure_droneport_id,
                "minimum_separation_seconds":
                    DRONEPORT_LAUNCH_SEPARATION_SECONDS,
            },
        )

        return {
            "authorized": True,
            "departure_droneport_id": str(
                departure_droneport_id
            ),
            "retry_after_seconds": 0,
        }, 200

