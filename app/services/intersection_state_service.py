
from app.models.intersection_state_model import (
    clear_intersection_state,
    insert_intersection_state,
    lock_intersection_slot,
    occupy_intersection_state,
    reserve_intersection_state,
    select_intersection_state,
)

import logging


logger = logging.getLogger(__name__)

def reserve_intersection_slot(
    connection,
    *,
    route_node_id,
    flight_band_id,
    assigned_relative_altitude_ft,
    flight_execution_id,
    from_route_id,
    to_route_id,
    return_status=False,
):
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

    if state["state"] == "reserved":
        if (
            str(state["flight_execution_id"])
            == str(flight_execution_id)
            and str(state["from_route_id"])
            == str(from_route_id)
            and str(state["to_route_id"])
            == str(to_route_id)
        ):
            if return_status:
                return state["intersection_state_id"], False

            return state["intersection_state_id"]

        if return_status:
            return None, False

        return None

    if state["state"] != "clear":
        if return_status:
            return None, False

        return None

    result = reserve_intersection_state(
        connection,
        intersection_state_id=state["intersection_state_id"],
        flight_execution_id=flight_execution_id,
        from_route_id=from_route_id,
        to_route_id=to_route_id,
    )

    if result is not None:
        logger.info(
            "Intersection reserved: route_node_id=%s "
            "flight_execution_id=%s altitude_ft=%s",
            route_node_id,
            flight_execution_id,
            assigned_relative_altitude_ft,
        )

    if return_status:
        return result, result is not None

    return result


def occupy_intersection_slot(
    connection,
    *,
    intersection_state_id,
    flight_execution_id,
):
    result = occupy_intersection_state(
        connection,
        intersection_state_id=intersection_state_id,
        flight_execution_id=flight_execution_id,
    )

    if result is not None:
        logger.info(
            "Intersection occupied: intersection_state_id=%s "
            "flight_execution_id=%s",
            intersection_state_id,
            flight_execution_id,
        )

    return result


def clear_intersection_slot(
    connection,
    *,
    intersection_state_id,
    flight_execution_id,
):
    result = clear_intersection_state(
        connection,
        intersection_state_id=intersection_state_id,
        flight_execution_id=flight_execution_id,
    )

    if result is not None:
        logger.info(
            "Intersection cleared: intersection_state_id=%s "
            "flight_execution_id=%s",
            intersection_state_id,
            flight_execution_id,
        )

    return result


