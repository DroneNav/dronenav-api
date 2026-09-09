import hashlib

from sqlalchemy import text


def _intersection_lock_key(
    *,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
) -> int:
    value = (
        f"{route_node_id}:"
        f"{flight_band_id}:"
        f"{assigned_relative_altitude_ft}"
    )

    digest = hashlib.blake2b(
        value.encode("utf-8"),
        digest_size=8,
    ).digest()

    return int.from_bytes(
        digest,
        byteorder="big",
        signed=True,
    )


def lock_intersection_slot(
    connection,
    *,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
):
    lock_key = _intersection_lock_key(
        route_node_id=route_node_id,
        flight_band_id=flight_band_id,
        assigned_relative_altitude_ft=assigned_relative_altitude_ft,
    )

    connection.execute(
        text("""
            SELECT pg_advisory_xact_lock(:lock_key)
        """),
        {
            "lock_key": lock_key,
        },
    )


def select_intersection_state(
    connection,
    *,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
):
    result = connection.execute(
        text("""
            SELECT
                intersection_state_id,
                state,
                flight_execution_id,
                from_route_id,
                to_route_id,
                reserved_at,
                occupied_at,
                updated_at
            FROM intersection_states
            WHERE route_node_id = :route_node_id
              AND flight_band_id = :flight_band_id
              AND assigned_relative_altitude_ft =
                  :assigned_relative_altitude_ft
        """),
        {
            "route_node_id": route_node_id,
            "flight_band_id": flight_band_id,
            "assigned_relative_altitude_ft":
                assigned_relative_altitude_ft,
        },
    )

    return result.mappings().one_or_none()


def insert_intersection_state(
    connection,
    *,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
):
    result = connection.execute(
        text("""
            INSERT INTO intersection_states (
                route_node_id,
                flight_band_id,
                assigned_relative_altitude_ft,
                state
            )
            VALUES (
                :route_node_id,
                :flight_band_id,
                :assigned_relative_altitude_ft,
                'clear'
            )
            RETURNING
                intersection_state_id
        """),
        {
            "route_node_id": route_node_id,
            "flight_band_id": flight_band_id,
            "assigned_relative_altitude_ft":
                assigned_relative_altitude_ft,
        },
    )

    return result.scalar_one()


def reserve_intersection_state(
    connection,
    *,
    intersection_state_id,
    flight_execution_id,
    from_route_id,
    to_route_id,
):
    result = connection.execute(
        text("""
            UPDATE intersection_states
            SET
                state = 'reserved',
                flight_execution_id = :flight_execution_id,
                from_route_id = :from_route_id,
                to_route_id = :to_route_id,
                reserved_at = NOW(),
                occupied_at = NULL,
                updated_at = NOW()
            WHERE intersection_state_id = :intersection_state_id
              AND state = 'clear'
            RETURNING intersection_state_id
        """),
        {
            "intersection_state_id": intersection_state_id,
            "flight_execution_id": flight_execution_id,
            "from_route_id": from_route_id,
            "to_route_id": to_route_id,
        },
    )

    return result.scalar_one_or_none()


def occupy_intersection_state(
    connection,
    *,
    intersection_state_id,
    flight_execution_id,
):
    result = connection.execute(
        text("""
            UPDATE intersection_states
            SET
                state = 'occupied',
                occupied_at = NOW(),
                updated_at = NOW()
            WHERE intersection_state_id = :intersection_state_id
              AND flight_execution_id = :flight_execution_id
              AND state = 'reserved'
            RETURNING intersection_state_id
        """),
        {
            "intersection_state_id": intersection_state_id,
            "flight_execution_id": flight_execution_id,
        },
    )

    return result.scalar_one_or_none()


def clear_intersection_state(
    connection,
    *,
    intersection_state_id,
    flight_execution_id,
):
    result = connection.execute(
        text("""
            UPDATE intersection_states
            SET
                state = 'clear',
                flight_execution_id = NULL,
                from_route_id = NULL,
                to_route_id = NULL,
                reserved_at = NULL,
                occupied_at = NULL,
                updated_at = NOW()
            WHERE intersection_state_id = :intersection_state_id
              AND flight_execution_id = :flight_execution_id
              AND state = 'occupied'
            RETURNING intersection_state_id
        """),
        {
            "intersection_state_id": intersection_state_id,
            "flight_execution_id": flight_execution_id,
        },
    )

    return result.scalar_one_or_none()


