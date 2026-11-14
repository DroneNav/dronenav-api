
from app.models.intersection_state_model import (
    clear_intersection_state,
    insert_intersection_state,
    lock_intersection_slot,
    occupy_intersection_state,
    reserve_intersection_state,
    select_intersection_state,
)

from app.models.route_model import (
    select_route_maximum_aircraft_capacity,
)

from app.models.route_occupancy_state_model import (
    count_route_committed_occupancy,
    lock_route_flight_band_allocation,
    select_oldest_destination_route_hold,
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
    maximum_aircraft_capacity = (
        select_route_maximum_aircraft_capacity(
            connection,
            to_route_id,
        )
    )

    if maximum_aircraft_capacity is None:
        raise ValueError(
            f"Destination Route not found: {to_route_id}"
        )

    if maximum_aircraft_capacity > 0:
        lock_route_flight_band_allocation(
            connection,
            route_id=to_route_id,
            flight_band_id=flight_band_id,
        )

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

    if maximum_aircraft_capacity > 0:
        oldest_hold = select_oldest_destination_route_hold(
            connection,
            route_id=to_route_id,
            flight_band_id=flight_band_id,
        )

        if (
            oldest_hold is not None
            and str(oldest_hold["flight_execution_id"])
            != str(flight_execution_id)
        ):
            logger.info(
                "Destination Route FIFO admission deferred: "
                "route_id=%s flight_execution_id=%s "
                "oldest_waiting_flight_execution_id=%s",
                to_route_id,
                flight_execution_id,
                oldest_hold["flight_execution_id"],
            )

            if return_status:
                return None, False

            return None

    if maximum_aircraft_capacity > 0:
        committed_count = count_route_committed_occupancy(
            connection,
            route_id=to_route_id,
            flight_band_id=flight_band_id,
        )

        if committed_count >= maximum_aircraft_capacity:
            logger.info(
                "Destination Route at capacity: "
                "route_id=%s flight_band_id=%s "
                "committed=%s maximum=%s",
                to_route_id,
                flight_band_id,
                committed_count,
                maximum_aircraft_capacity,
            )

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


