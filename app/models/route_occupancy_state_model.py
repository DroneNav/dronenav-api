from sqlalchemy import text


def insert_route_occupancy_state(
    connection,
    *,
    route_id,
    flight_band_id,
    flight_execution_id,
    aircraft_id,
    planned_entry_time,
    planned_exit_time,
):
    result = connection.execute(
        text("""
            INSERT INTO route_occupancy_state (
                route_id,
                flight_band_id,
                flight_execution_id,
                aircraft_id,
                state,
                planned_entry_time,
                planned_exit_time
            )
            VALUES (
                :route_id,
                :flight_band_id,
                :flight_execution_id,
                :aircraft_id,
                'planned',
                :planned_entry_time,
                :planned_exit_time
            )
            RETURNING
                route_occupancy_state_id
        """),
        {
            "route_id": route_id,
            "flight_band_id": flight_band_id,
            "flight_execution_id": flight_execution_id,
            "aircraft_id": aircraft_id,
            "planned_entry_time": planned_entry_time,
            "planned_exit_time": planned_exit_time,
        },
    )

    return result.scalar_one()


def clear_route_occupancy(
    connection,
    *,
    route_occupancy_state_id,
):
    connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET cleared = TRUE
            WHERE route_occupancy_state_id =
                :route_occupancy_state_id
        """),
        {
            "route_occupancy_state_id":
                route_occupancy_state_id,
        },
    )


def update_active_route_position(
    connection,
    *,
    route_id,
    flight_execution_id,
    latitude,
    longitude,
    altitude_ft,
):
    connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET
                last_latitude = :latitude,
                last_longitude = :longitude,
                last_altitude_ft = :altitude_ft
            WHERE route_id = :route_id
              AND flight_execution_id = :flight_execution_id
              AND state = 'active'
        """),
        {
            "route_id": route_id,
            "flight_execution_id": flight_execution_id,
            "latitude": latitude,
            "longitude": longitude,
            "altitude_ft": altitude_ft,
        },
    )


def update_route_occupancy_state(
    connection,
    *,
    route_id,
    flight_execution_id,
    actual_entry_time=None,
    actual_exit_time=None,
    last_latitude=None,
    last_longitude=None,
    last_altitude_ft=None,
    last_state_change_at=None,
    state=None,
):
    connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET
                actual_entry_time = COALESCE(
                    actual_entry_time,
                    :actual_entry_time,
                    CASE
                        WHEN :state = 'exited'
                        THEN CAST(:actual_exit_time AS timestamptz)
                        ELSE NULL
                    END
                ),
                actual_exit_time = COALESCE(
                    actual_exit_time,
                    :actual_exit_time
                ),
                last_latitude = COALESCE(
                    :last_latitude,
                    last_latitude
                ),
                last_longitude = COALESCE(
                    :last_longitude,
                    last_longitude
                ),
                last_altitude_ft = COALESCE(
                    :last_altitude_ft,
                    last_altitude_ft
                ),
                last_state_change_at = CASE
                    WHEN :state IS NOT NULL
                         AND :state <> state
                    THEN :last_state_change_at
                    ELSE last_state_change_at
                END,
                state = COALESCE(
                    :state,
                    state
                )
            WHERE route_id = :route_id
              AND flight_execution_id = :flight_execution_id
              AND (
                  :state IS NULL
                  OR (
                      state = 'planned'
                      AND :state IN ('active', 'exited')
                  )
                  OR (
                      state = 'active'
                      AND :state IN ('active', 'exited')
                  )
              )
        """),
        {
            "route_id": route_id,
            "flight_execution_id": flight_execution_id,
            "actual_entry_time": actual_entry_time,
            "actual_exit_time": actual_exit_time,
            "last_latitude": last_latitude,
            "last_longitude": last_longitude,
            "last_altitude_ft": last_altitude_ft,
            "last_state_change_at": last_state_change_at,
            "state": state,
        },
    )

def set_route_intersection_hold(
    connection,
    *,
    route_id,
    flight_execution_id,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
):
    hold_position = connection.execute(
        text("""
            SELECT COALESCE(
                MAX(intersection_hold_position),
                0
            ) + 1
            FROM route_occupancy_state
            WHERE route_id = :route_id
              AND flight_band_id = :flight_band_id
              AND assigned_relative_altitude_ft =
                  :assigned_relative_altitude_ft
              AND state = 'active'
        """),
        {
            "route_id": route_id,
            "flight_band_id": flight_band_id,
            "assigned_relative_altitude_ft": (
                assigned_relative_altitude_ft
            ),
        },
    ).scalar_one()

    result = connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET
                intersection_hold_route_node_id = :route_node_id,
                intersection_hold_at = COALESCE(
                    intersection_hold_at,
                    NOW()
                ),
                intersection_hold_position = COALESCE(
                    intersection_hold_position,
                    :hold_position
                )
            WHERE route_id = :route_id
              AND flight_execution_id = :flight_execution_id
              AND state = 'active'
              AND flight_band_id = :flight_band_id
              AND assigned_relative_altitude_ft =
                  :assigned_relative_altitude_ft
              AND (
                  intersection_hold_route_node_id IS NULL
                  OR intersection_hold_route_node_id = :route_node_id
              )
            RETURNING route_occupancy_state_id
        """),
        {
            "hold_position": hold_position,
            "route_id": route_id,
            "flight_execution_id": flight_execution_id,
            "route_node_id": route_node_id,
            "flight_band_id": flight_band_id,
            "assigned_relative_altitude_ft": (
                assigned_relative_altitude_ft
            ),
        },
    )

    return result.scalar_one_or_none()


def clear_route_intersection_hold(
    connection,
    *,
    route_id,
    flight_execution_id,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
):
    result = connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET
                intersection_hold_route_node_id = NULL,
                intersection_hold_at = NULL
            WHERE route_id = :route_id
              AND flight_execution_id = :flight_execution_id
              AND state = 'active'
              AND flight_band_id = :flight_band_id
              AND assigned_relative_altitude_ft = :assigned_relative_altitude_ft
              AND intersection_hold_route_node_id = :route_node_id
            RETURNING route_occupancy_state_id
        """),
        {
            "route_id": route_id,
            "flight_execution_id": flight_execution_id,
            "route_node_id": route_node_id,
            "flight_band_id": flight_band_id,
            "assigned_relative_altitude_ft": (
                assigned_relative_altitude_ft
            ),
        },
    )

    cleared_state_id = result.scalar_one_or_none()

    if cleared_state_id is None:
        return None

    connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET intersection_hold_position = NULL
            WHERE route_id = :route_id
              AND flight_band_id = :flight_band_id
              AND assigned_relative_altitude_ft =
                  :assigned_relative_altitude_ft
              AND intersection_hold_position IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM route_occupancy_state AS waiting
                  WHERE waiting.route_id = :route_id
                    AND waiting.flight_band_id = :flight_band_id
                    AND waiting.assigned_relative_altitude_ft =
                        :assigned_relative_altitude_ft
                    AND waiting.state = 'active'
                    AND waiting.intersection_hold_route_node_id =
                        :route_node_id
              )
        """),
        {
            "route_id": route_id,
            "route_node_id": route_node_id,
            "flight_band_id": flight_band_id,
            "assigned_relative_altitude_ft": (
                assigned_relative_altitude_ft
            ),
        },
    )

    return cleared_state_id


def select_next_intersection_hold(
    connection,
    *,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
):
    result = connection.execute(
        text("""
            SELECT
                route_occupancy_state_id,
                route_id,
                flight_execution_id,
                flight_band_id,
                assigned_relative_altitude_ft,
                intersection_hold_at
            FROM route_occupancy_state
            WHERE state = 'active'
              AND intersection_hold_route_node_id = :route_node_id
              AND flight_band_id = :flight_band_id
              AND assigned_relative_altitude_ft =
                  :assigned_relative_altitude_ft
            ORDER BY
                intersection_hold_at ASC,
                route_occupancy_state_id ASC
            LIMIT 1
            FOR UPDATE
        """),
        {
            "route_node_id": route_node_id,
            "flight_band_id": flight_band_id,
            "assigned_relative_altitude_ft": (
                assigned_relative_altitude_ft
            ),
        },
    )

    return result.mappings().one_or_none()


def select_route_occupancy_state(
    connection,
    *,
    route_id,
    flight_execution_id,
):
    result = connection.execute(
        text("""
            SELECT
                route_occupancy_state_id,
                route_id,
                flight_band_id,
                flight_execution_id,
                aircraft_id,
                state,
                assigned_relative_altitude_ft,
                intersection_hold_route_node_id,
                intersection_hold_position
            FROM route_occupancy_state
            WHERE route_id = :route_id
              AND flight_execution_id = :flight_execution_id
        """),
        {
            "route_id": route_id,
            "flight_execution_id": flight_execution_id,
        },
    )

    return result.mappings().one_or_none()


def count_active_route_occupancy(
    connection,
    *,
    route_id,
    flight_band_id,
):
    result = connection.execute(
        text("""
            SELECT COUNT(*)
            FROM route_occupancy_state
            WHERE route_id = :route_id
              AND flight_band_id = :flight_band_id
              AND state = 'active'
        """),
        {
            "route_id": route_id,
            "flight_band_id": flight_band_id,
        },
    )

    return result.scalar_one()


def has_route_capacity(
    *,
    maximum_aircraft_capacity,
    active_occupancy_count,
):
    if maximum_aircraft_capacity == 0:
        return True

    return (
        active_occupancy_count
        < maximum_aircraft_capacity
    )


def select_active_route_occupancy(
    connection,
    *,
    route_id,
    flight_band_id,
):
    result = connection.execute(
        text("""
            SELECT
                route_occupancy_state_id,
                flight_execution_id,
                aircraft_id,
                assigned_relative_altitude_ft,
                cleared,
                actual_entry_time,
                last_latitude,
                last_longitude,
                last_altitude_ft
            FROM route_occupancy_state
            WHERE route_id = :route_id
              AND flight_band_id = :flight_band_id
              AND state = 'active'
            ORDER BY actual_entry_time
        """),
        {
            "route_id": route_id,
            "flight_band_id": flight_band_id,
        },
    )

    return result.mappings().all()


def lock_route_flight_band_allocation(
    connection,
    *,
    route_id,
    flight_band_id,
):
    connection.execute(
        text("""
            SELECT pg_advisory_xact_lock(
                hashtext(:route_id),
                hashtext(:flight_band_id)
            )
        """),
        {
            "route_id": str(route_id),
            "flight_band_id": str(flight_band_id),
        },
    )


def assign_route_occupancy_altitude(
    connection,
    *,
    flight_execution_id,
    assigned_relative_altitude_ft,
):
    result = connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET assigned_relative_altitude_ft =
                :assigned_relative_altitude_ft
            WHERE flight_execution_id = :flight_execution_id
              AND state = 'planned'
              AND assigned_relative_altitude_ft IS NULL
            RETURNING route_occupancy_state_id
        """),
        {
            "flight_execution_id": flight_execution_id,
            "assigned_relative_altitude_ft":
                assigned_relative_altitude_ft,
        },
    )

    return result.scalars().all()


