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
    state=None,
):
    connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET
                actual_entry_time = COALESCE(
                    actual_entry_time,
                    :actual_entry_time
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
                state = COALESCE(
                    :state,
                    state
                )
            WHERE route_id = :route_id
              AND flight_execution_id = :flight_execution_id
        """),
        {
            "route_id": route_id,
            "flight_execution_id": flight_execution_id,
            "actual_entry_time": actual_entry_time,
            "actual_exit_time": actual_exit_time,
            "last_latitude": last_latitude,
            "last_longitude": last_longitude,
            "last_altitude_ft": last_altitude_ft,
            "state": state,
        },
    )

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


