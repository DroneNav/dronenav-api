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
Flight Execution API object model implementation source file.

Author:
DroneNav Project Contributors

Created: 2026-07-15

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.

DroneNav - Flight Execution persistence model.

A Flight Execution Record is the single concise, machine-readable
translation of one immutable Drupal Flight Plan. NAVProxy is its
exclusive consumer.
"""

from sqlalchemy import bindparam, text

from app.config.database import engine

from app.models.route_occupancy_state_model import (
    insert_route_occupancy_state,
)

from app.config.constants import (
    EXECUTION_STATUS_ACTIVE,
    EXECUTION_STATUS_COMPLETED,
    EXECUTION_STATUS_DISPATCHED,
    EXECUTION_STATUS_EXPIRED,
    EXECUTION_STATUS_REVOKED,
    EXECUTION_STATUS_SUSPENDED,
    EXECUTION_STATUS_CANCELLED,
)

EXECUTION_STATUSES = {
    EXECUTION_STATUS_ACTIVE,
    EXECUTION_STATUS_COMPLETED,
    EXECUTION_STATUS_DISPATCHED,
    EXECUTION_STATUS_EXPIRED,
    EXECUTION_STATUS_SUSPENDED,
    EXECUTION_STATUS_REVOKED,
    EXECUTION_STATUS_CANCELLED,
}


def insert_flight_execution_record(data, planned_route_occupancy=None):

    route_ids = _normalize_route_ids(data.get("route_ids", []))

    planned_route_occupancy = (
        planned_route_occupancy or []
    )

    execution_status = data.get(
        "execution_status",
        EXECUTION_STATUS_ACTIVE,
    )

    _validate_execution_status(execution_status)

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO flight_executions (
                    flight_plan_id,
                    authority_id,
                    aviator_id,
                    aircraft_id,
                    flight_class,
                    origin_site_id,
                    destination_site_id,
                    departure_droneport_id,
                    arrival_droneport_id,
                    requested_departure_datetime,
                    flight_termination_datetime,
                    operational_timezone,
                    execution_status
                )
                VALUES (
                    :flight_plan_id,
                    :authority_id,
                    :aviator_id,
                    :aircraft_id,
                    :flight_class,
                    :origin_site_id,
                    :destination_site_id,
                    :departure_droneport_id,
                    :arrival_droneport_id,
                    :requested_departure_datetime,
                    :flight_termination_datetime,
                    :operational_timezone,
                    :execution_status
                )
                RETURNING
                    flight_execution_id,
                    flight_plan_id,
                    authority_id,
                    aviator_id,
                    aircraft_id,
                    flight_class,
                    origin_site_id,
                    destination_site_id,
                    departure_droneport_id,
                    arrival_droneport_id,
                    requested_departure_datetime,
                    flight_termination_datetime,
                    operational_timezone,
                    execution_status,
                    created_at,
                    updated_at
            """),
            {
                "flight_plan_id": data["flight_plan_id"],
                "authority_id": data["authority_id"],
                "aviator_id": data["aviator_id"],
                "aircraft_id": data["aircraft_id"],
                "flight_class": data["flight_class"],
                "origin_site_id": data["origin_site_id"],
                "destination_site_id": data["destination_site_id"],
                "departure_droneport_id":
                    data.get("departure_droneport_id"),
                "arrival_droneport_id":
                    data.get("arrival_droneport_id"),
                "requested_departure_datetime":
                    data.get("requested_departure_datetime"),
                "flight_termination_datetime":
                    data.get("flight_termination_datetime"),
                "operational_timezone":
                    data["operational_timezone"],
                "execution_status": execution_status,
            },
        )

        record = dict(result.mappings().one())

        _insert_flight_execution_routes(
            connection,
            record["flight_execution_id"],
            route_ids,
        )

        for occupancy in planned_route_occupancy:
            insert_route_occupancy_state(
                connection,
                route_id=occupancy["route_id"],
                flight_band_id=occupancy["flight_band_id"],
                flight_execution_id=record[
                    "flight_execution_id"
                ],
                aircraft_id=occupancy["aircraft_id"],
                planned_entry_time=occupancy[
                    "planned_entry_time"
                ],
                planned_exit_time=occupancy[
                    "planned_exit_time"
                ],
            )

        record["route_ids"] = route_ids

        return record


def select_flight_execution(flight_execution_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    flight_execution_id,
                    flight_plan_id,
                    authority_id,
                    aviator_id,
                    aircraft_id,
                    flight_class,
                    origin_site_id,
                    destination_site_id,
                    departure_droneport_id,
                    arrival_droneport_id,
                    requested_departure_datetime,
                    flight_termination_datetime,
                    operational_timezone,
                    execution_status,
                    created_at,
                    updated_at
                FROM flight_executions
                WHERE flight_execution_id = :flight_execution_id
            """),
            {"flight_execution_id": flight_execution_id},
        )

        row = result.mappings().first()
        if row is None:
            return None

        record = dict(row)
        record["route_ids"] = _select_flight_execution_routes(
            connection,
            flight_execution_id,
        )
        return record


def select_flight_execution_by_flight_plan(flight_plan_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    flight_execution_id,
                    flight_plan_id,
                    authority_id,
                    aviator_id,
                    aircraft_id,
                    flight_class,
                    origin_site_id,
                    destination_site_id,
                    departure_droneport_id,
                    arrival_droneport_id,
                    requested_departure_datetime,
                    flight_termination_datetime,
                    operational_timezone,
                    execution_status,
                    created_at,
                    updated_at
                FROM flight_executions
                WHERE flight_plan_id = :flight_plan_id
            """),
            {"flight_plan_id": flight_plan_id},
        )

        row = result.mappings().first()
        if row is None:
            return None

        record = dict(row)
        record["route_ids"] = _select_flight_execution_routes(
            connection,
            record["flight_execution_id"],
        )
        return record


def select_flight_executions(
    authority_id=None,
    execution_status=None,
    requested_departure_datetime=None,
):
    if execution_status is not None:
        _validate_execution_status(execution_status)

    if requested_departure_datetime not in (None, "null", "not_null"):
        raise ValueError(
            "requested_departure_datetime must be null or not_null"
        )

    departure_filter = ""
    if requested_departure_datetime == "null":
        departure_filter = (
            "AND requested_departure_datetime IS NULL"
        )
    elif requested_departure_datetime == "not_null":
        departure_filter = (
            "AND requested_departure_datetime IS NOT NULL "
            "AND requested_departure_datetime >= NOW()"
        )

    query = text(f"""
        SELECT
            flight_execution_id,
            flight_plan_id,
            authority_id,
            aviator_id,
            aircraft_id,
            flight_class,
            origin_site_id,
            destination_site_id,
            departure_droneport_id,
            arrival_droneport_id,
            requested_departure_datetime,
            flight_termination_datetime,
            operational_timezone,
            execution_status,
            created_at,
            updated_at
        FROM flight_executions
        WHERE (
            :authority_id IS NULL
            OR authority_id = :authority_id
        )
          AND (
            :execution_status IS NULL
            OR execution_status = :execution_status
          )
          {departure_filter}
        ORDER BY
            requested_departure_datetime NULLS FIRST,
            created_at DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {
                "authority_id": authority_id,
                "execution_status": execution_status,
            },
        )

        records = [dict(row) for row in result.mappings().all()]
        route_map = _select_routes_for_flight_executions(
            connection,
            [record["flight_execution_id"] for record in records],
        )

        for record in records:
            record["route_ids"] = route_map.get(
                record["flight_execution_id"],
                [],
            )

        return records


def update_flight_execution_status(
    flight_execution_id,
    execution_status,
):
    _validate_execution_status(execution_status)

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_executions
                SET
                    execution_status = :execution_status,
                    updated_at = NOW()
                WHERE flight_execution_id = :flight_execution_id
                RETURNING
                    flight_execution_id,
                    execution_status,
                    updated_at
            """),
            {
                "flight_execution_id": flight_execution_id,
                "execution_status": execution_status,
            },
        )

        row = result.mappings().first()
        return dict(row) if row is not None else None


def update_flight_termination_datetime(
    flight_execution_id,
    flight_termination_datetime,
):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_executions
                SET
                    flight_termination_datetime =
                        :flight_termination_datetime,
                    updated_at = NOW()
                WHERE flight_execution_id = :flight_execution_id
                RETURNING
                    flight_execution_id,
                    flight_termination_datetime,
                    updated_at
            """),
            {
                "flight_execution_id": flight_execution_id,
                "flight_termination_datetime":
                    flight_termination_datetime,
            },
        )

        row = result.mappings().first()
        return dict(row) if row is not None else None


def complete_scheduled_flight_execution(
    flight_execution_id,
    flight_termination_datetime,
):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_executions
                SET
                    flight_termination_datetime =
                        :flight_termination_datetime,
                    execution_status = :completed_status,
                    updated_at = NOW()
                WHERE flight_execution_id = :flight_execution_id
                  AND requested_departure_datetime IS NOT NULL
                  AND execution_status = :dispatched_status
                RETURNING
                    flight_execution_id,
                    execution_status,
                    flight_termination_datetime,
                    updated_at
            """),
            {
                "flight_execution_id": flight_execution_id,
                "flight_termination_datetime":
                    flight_termination_datetime,
                "completed_status": EXECUTION_STATUS_COMPLETED,
                "dispatched_status": EXECUTION_STATUS_DISPATCHED,
            },
        )

        row = result.mappings().first()
        return dict(row) if row is not None else None


def select_flight_executions_ready_for_dispatch(
    preflight_window_minutes,
    expiration_grace_minutes,
):
    preflight_window_minutes = int(preflight_window_minutes)
    expiration_grace_minutes = int(expiration_grace_minutes)

    if preflight_window_minutes < 0:
        raise ValueError(
            "preflight_window_minutes must not be negative"
        )

    if expiration_grace_minutes < 0:
        raise ValueError(
            "expiration_grace_minutes must not be negative"
        )

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    flight_execution_id,
                    flight_plan_id,
                    aviator_id,
                    aircraft_id,
                    requested_departure_datetime
                FROM flight_executions
                WHERE requested_departure_datetime IS NOT NULL
                  AND flight_termination_datetime IS NULL
                  AND execution_status = :active_status
                  AND requested_departure_datetime
                      <= NOW()
                         + (
                             :preflight_window_minutes
                             * INTERVAL '1 minute'
                         )
                  AND requested_departure_datetime
                      > NOW()
                        - (
                            :expiration_grace_minutes
                            * INTERVAL '1 minute'
                        )
                ORDER BY
                    requested_departure_datetime,
                    flight_execution_id
            """),
            {
                "active_status": EXECUTION_STATUS_ACTIVE,
                "preflight_window_minutes":
                    preflight_window_minutes,
                "expiration_grace_minutes":
                    expiration_grace_minutes,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]


def _create_flight(
    connection,
    flight_execution_id,
    aviator_id,
    aircraft_id,
    scheduled_departure_utc,
):
    """
    Create and return the Flight anchor for a claimed Flight Execution.

    The caller must already hold the Flight Execution row lock.
    """

    result = connection.execute(
        text("""
            INSERT INTO flight (
                flight_execution_id,
                aviator_id,
                aircraft_id,
                scheduled_departure_utc
            )
            VALUES (
                :flight_execution_id,
                :aviator_id,
                :aircraft_id,
                :scheduled_departure_utc
            )
            RETURNING
                flight_id,
                flight_execution_id,
                aviator_id,
                aircraft_id,
                scheduled_departure_utc,
                created_at
        """),
        {
            "flight_execution_id": flight_execution_id,
            "aviator_id": aviator_id,
            "aircraft_id": aircraft_id,
            "scheduled_departure_utc": scheduled_departure_utc,
        },
    )

    return dict(result.mappings().one())


def _create_initial_flight_log(
    connection,
    flight,
):
    """
    Append the initial Flight Log entry before NAVProxy is launched.
    """

    result = connection.execute(
        text("""
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
                'flight_created',
                'started',
                'Flight created and prepared for NAVProxy execution.',
                NULL
            )
            RETURNING flight_log_id
        """),
        {
            "flight_id": flight["flight_id"],
            "flight_execution_id": flight["flight_execution_id"],
        },
    )

    return str(result.scalar_one())


def claim_scheduled_flight_execution(
    flight_execution_id,
    aviator_id,
    aircraft_id,
):
    """
    Atomically claim a scheduled Flight Execution.


    A scheduled Flight Execution may be dispatched only once.
    Returns the created Flight, or None when the execution is
    no longer eligible.
    """

    with engine.begin() as connection:

        execution_result = connection.execute(
            text("""
                UPDATE flight_executions
                SET
                    execution_status = :dispatched_status,
                    updated_at = NOW()
                WHERE flight_execution_id =
                    :flight_execution_id
                  AND execution_status =
                    :active_status
                  AND requested_departure_datetime
                    IS NOT NULL
                  AND flight_termination_datetime
                    IS NULL
                RETURNING
                    flight_execution_id,
                    requested_departure_datetime
                        AS scheduled_departure_utc
            """),
            {
                "flight_execution_id":
                    flight_execution_id,
                "active_status":
                    EXECUTION_STATUS_ACTIVE,
                "dispatched_status":
                    EXECUTION_STATUS_DISPATCHED,
            },
        )

        execution = execution_result.mappings().first()

        if execution is None:
            return None

        flight = _create_flight(
            connection=connection,
            flight_execution_id=execution["flight_execution_id"],
            aviator_id=aviator_id,
            aircraft_id=aircraft_id,
            scheduled_departure_utc=execution["scheduled_departure_utc"],
        )

        flight["initial_flight_log_id"] = _create_initial_flight_log(
            connection=connection,
            flight=flight,
        )

        return flight

def release_scheduled_flight_execution(
    flight_execution_id,
):
    """
    Return a preflight-failed scheduled Flight Execution to active status.

    Only a dispatched, unterminated scheduled execution may be released.
    """

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_executions
                SET
                    execution_status = :active_status,
                    updated_at = NOW()
                WHERE flight_execution_id = :flight_execution_id
                  AND requested_departure_datetime IS NOT NULL
                  AND flight_termination_datetime IS NULL
                  AND execution_status = :dispatched_status
                RETURNING
                    flight_execution_id,
                    execution_status,
                    updated_at
            """),
            {
                "flight_execution_id": flight_execution_id,
                "active_status": EXECUTION_STATUS_ACTIVE,
                "dispatched_status": EXECUTION_STATUS_DISPATCHED,
            },
        )

        row = result.mappings().first()

        return dict(row) if row is not None else None


def cancel_flight_execution(
    flight_execution_id,
):
    """
    Cancel a Flight Execution Record.

    Only an active record can be cancelled.
    """

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_executions
                SET
                    execution_status = :cancelled_status,
                    updated_at = NOW()
                WHERE flight_execution_id = :flight_execution_id
                  AND flight_termination_datetime IS NULL
                  AND execution_status = :active_status
                RETURNING
                    flight_execution_id,
                    execution_status,
                    updated_at
            """),
            {
                "flight_execution_id": flight_execution_id,
                "cancelled_status": EXECUTION_STATUS_CANCELLED,
                "active_status": EXECUTION_STATUS_ACTIVE,
            },
        )

        row = result.mappings().first()

        return dict(row) if row is not None else None


def claim_reusable_flight_execution(
    flight_execution_id,
    aviator_id,
    aircraft_id,
):
    """
    Atomically claim a reusable Flight Execution.

    A reusable Flight Execution may create multiple Flights.
    Returns the created Flight, or None when the execution is
    no longer eligible.
    """

    with engine.begin() as connection:

        execution_result = connection.execute(
            text("""
                SELECT
                    flight_execution_id,
                    NOW() AS scheduled_departure_utc
                FROM flight_executions
                WHERE flight_execution_id =
                    :flight_execution_id
                  AND execution_status =
                    :execution_status
                  AND requested_departure_datetime
                    IS NULL
                  AND flight_termination_datetime
                    IS NULL
                FOR UPDATE SKIP LOCKED
            """),
            {
                "flight_execution_id":
                    flight_execution_id,
                "execution_status":
                    EXECUTION_STATUS_ACTIVE,
            },
        )

        execution = execution_result.mappings().first()

        if execution is None:
            return None

        flight = _create_flight(
            connection=connection,
            flight_execution_id=execution["flight_execution_id"],
            aviator_id=aviator_id,
            aircraft_id=aircraft_id,
            scheduled_departure_utc=execution["scheduled_departure_utc"],
        )

        flight["initial_flight_log_id"] = _create_initial_flight_log(
            connection=connection,
            flight=flight,
        )

        return flight


def expire_scheduled_flight_executions(late_launch_minutes):
    late_launch_minutes = int(late_launch_minutes)
    if late_launch_minutes < 0:
        raise ValueError(
            "late_launch_minutes must not be negative"
        )

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_executions
                SET
                    execution_status = :expired_status,
                    updated_at = NOW()
                WHERE requested_departure_datetime IS NOT NULL
                  AND flight_termination_datetime IS NULL
                  AND execution_status IN (
                      :active_status,
                      :suspended_status
                  )
                  AND requested_departure_datetime
                      + (
                          :late_launch_minutes
                          * INTERVAL '1 minute'
                      ) <= NOW()
                RETURNING flight_execution_id
            """),
            {
                "expired_status": EXECUTION_STATUS_EXPIRED,
                "active_status": EXECUTION_STATUS_ACTIVE,
                "suspended_status":
                    EXECUTION_STATUS_SUSPENDED,
                "late_launch_minutes": late_launch_minutes,
            },
        )

        return [
            row["flight_execution_id"]
            for row in result.mappings().all()
        ]


def delete_flight_execution(flight_execution_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM flight_executions
                WHERE flight_execution_id = :flight_execution_id
                RETURNING flight_execution_id
            """),
            {"flight_execution_id": flight_execution_id},
        )

        return result.scalar_one_or_none() is not None


def _insert_flight_execution_routes(
    connection,
    flight_execution_id,
    route_ids,
):
    for sequence_number, route_id in enumerate(
        route_ids,
        start=1,
    ):
        connection.execute(
            text("""
                INSERT INTO flight_execution_routes (
                    flight_execution_id,
                    sequence_number,
                    route_id
                )
                VALUES (
                    :flight_execution_id,
                    :sequence_number,
                    :route_id
                )
            """),
            {
                "flight_execution_id": flight_execution_id,
                "sequence_number": sequence_number,
                "route_id": route_id,
            },
        )


def _select_flight_execution_routes(
    connection,
    flight_execution_id,
):
    result = connection.execute(
        text("""
            SELECT route_id
            FROM flight_execution_routes
            WHERE flight_execution_id = :flight_execution_id
            ORDER BY sequence_number
        """),
        {"flight_execution_id": flight_execution_id},
    )

    return [
        row["route_id"]
        for row in result.mappings().all()
    ]


def update_flight_execution_route_mission_ranges(
    flight_execution_id,
    route_ranges,
):
    with engine.begin() as connection:
        for route_range in route_ranges:
            connection.execute(
                text("""
                    UPDATE flight_execution_routes
                    SET
                        start_mission_sequence =
                            :start_mission_sequence,
                        end_mission_sequence =
                            :end_mission_sequence,
                        segment_mission_sequences =
                            :segment_mission_sequences
                    WHERE flight_execution_id = :flight_execution_id
                      AND sequence_number = :sequence_number
                """),
                {
                    "flight_execution_id": flight_execution_id,
                    "sequence_number": (
                        route_range["route_index"] + 1
                    ),
                    "start_mission_sequence": (
                        route_range["start_mission_sequence"]
                    ),
                    "end_mission_sequence": (
                        route_range["end_mission_sequence"]
                    ),
                    "segment_mission_sequences": (
                        route_range["segment_mission_sequences"]
                    ),
                },
            )


def select_flight_execution_route_ranges(
    flight_execution_id,
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    sequence_number,
                    route_id,
                    start_mission_sequence,
                    end_mission_sequence,
                    segment_mission_sequences
                FROM flight_execution_routes
                WHERE flight_execution_id = :flight_execution_id
                ORDER BY sequence_number
            """),
            {
                "flight_execution_id": flight_execution_id,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]


def _select_routes_for_flight_executions(
    connection,
    flight_execution_ids,
):
    if not flight_execution_ids:
        return {}

    result = connection.execute(
        text("""
            SELECT
                flight_execution_id,
                route_id
            FROM flight_execution_routes
            WHERE flight_execution_id IN :flight_execution_ids
            ORDER BY
                flight_execution_id,
                sequence_number
        """).bindparams(
            bindparam(
                "flight_execution_ids",
                expanding=True,
            )
        ),
        {"flight_execution_ids": flight_execution_ids},
    )

    route_map = {}
    for row in result.mappings().all():
        route_map.setdefault(
            row["flight_execution_id"],
            [],
        ).append(row["route_id"])

    return route_map


def _normalize_route_ids(route_ids):
    if route_ids is None:
        return []

    if not isinstance(route_ids, (list, tuple)):
        raise ValueError("route_ids must be an ordered list")

    normalized_route_ids = [str(route_id) for route_id in route_ids]

    if len(normalized_route_ids) != len(set(normalized_route_ids)):
        raise ValueError(
            "route_ids must not contain duplicate Routes"
        )

    return normalized_route_ids


def _validate_execution_status(execution_status):
    if execution_status not in EXECUTION_STATUSES:
        raise ValueError(
            "Invalid Flight Execution status: "
            f"{execution_status}"
        )


