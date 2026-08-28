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
    state=None,
):
    connection.execute(
        text("""
            UPDATE route_occupancy_state
            SET
                actual_entry_time = COALESCE(
                    :actual_entry_time,
                    actual_entry_time
                ),
                actual_exit_time = COALESCE(
                    :actual_exit_time,
                    actual_exit_time
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
            "state": state,
        },
    )

