from app.config.database import engine

from app.models.intersection_state_model import (
    clear_intersection_state,
    insert_intersection_state,
    lock_intersection_slot,
    occupy_intersection_state,
    reserve_intersection_state,
    select_intersection_state,
)


def reserve_intersection_slot(
    *,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
    flight_execution_id,
    from_route_id,
    to_route_id,
):
    with engine.begin() as connection:
        lock_intersection_slot(
            connection,
            route_node_id=route_node_id,
            flight_band_id=flight_band_id,
            assigned_relative_altitude_ft=assigned_relative_altitude_ft,
        )

        state = select_intersection_state(
            connection,
            route_node_id=route_node_id,
            flight_band_id=flight_band_id,
            assigned_relative_altitude_ft=assigned_relative_altitude_ft,
        )

        if state is None:
            insert_intersection_state(
                connection,
                route_node_id=route_node_id,
                flight_band_id=flight_band_id,
                assigned_relative_altitude_ft=assigned_relative_altitude_ft,
            )

            state = select_intersection_state(
                connection,
                route_node_id=route_node_id,
                flight_band_id=flight_band_id,
                assigned_relative_altitude_ft=assigned_relative_altitude_ft,
            )

        if state["state"] != "clear":
            return None

        return reserve_intersection_state(
            connection,
            intersection_state_id=state["intersection_state_id"],
            flight_execution_id=flight_execution_id,
            from_route_id=from_route_id,
            to_route_id=to_route_id,
        )


def occupy_intersection_slot(
    connection,
    *,
    intersection_state_id,
    flight_execution_id,
):
    return occupy_intersection_state(
        connection,
        intersection_state_id=intersection_state_id,
        flight_execution_id=flight_execution_id,
    )


def clear_intersection_slot(
    connection,
    *,
    intersection_state_id,
    flight_execution_id,
):
    return clear_intersection_state(
        connection,
        intersection_state_id=intersection_state_id,
        flight_execution_id=flight_execution_id,
    )


