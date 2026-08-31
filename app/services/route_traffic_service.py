
from app.config.constants import (
    VERTICAL_CONFORMANCE_MARGIN_FT,
    VERTICAL_LAYER_SPACING_FT,
)

from app.models.route_occupancy_state_model import (
    lock_route_flight_band_allocation,
    select_active_route_occupancy,
    assign_route_occupancy_altitude,
    count_active_route_occupancy,
)

from app.config.database import engine

from app.models.route_model import select_route

from app.models.flight_band_model import (
    select_flight_band_record,
)


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


def route_has_available_capacity(
    connection,
    *,
    route,
    flight_band_id,
):
    active_occupancy_count = count_active_route_occupancy(
        connection,
        route_id=route["route_id"],
        flight_band_id=flight_band_id,
    )

    return has_route_capacity(
        maximum_aircraft_capacity=route[
            "maximum_aircraft_capacity"
        ],
        active_occupancy_count=active_occupancy_count,
    )


def build_vertical_layers(
    *,
    min_agl_ft,
    max_agl_ft,
):
    lowest_altitude_ft = (
        min_agl_ft
        + VERTICAL_CONFORMANCE_MARGIN_FT
    )

    highest_altitude_ft = (
        max_agl_ft
        - VERTICAL_CONFORMANCE_MARGIN_FT
    )

    if lowest_altitude_ft > highest_altitude_ft:
        return []

    layers = []
    altitude_ft = lowest_altitude_ft

    while altitude_ft <= highest_altitude_ft:
        layers.append(altitude_ft)
        altitude_ft += VERTICAL_LAYER_SPACING_FT

    return layers


def get_active_assigned_layers(
    active_occupancy,
):
    return {
        row["assigned_relative_altitude_ft"]
        for row in active_occupancy
        if row["assigned_relative_altitude_ft"] is not None
    }


def select_available_vertical_layer(
    *,
    vertical_layers,
    active_assigned_layers,
):
    for layer in vertical_layers:
        if layer not in active_assigned_layers:
            return layer

    return None


def select_route_vertical_layer(
    connection,
    *,
    route,
    flight_band,
):
    if not route_has_available_capacity(
        connection,
        route=route,
        flight_band_id=flight_band["flight_band_id"],
    ):
        return None

    vertical_layers = build_vertical_layers(
        min_agl_ft=flight_band["min_agl_ft"],
        max_agl_ft=flight_band["max_agl_ft"],
    )

    if not vertical_layers:
        return None

    active_occupancy = select_active_route_occupancy(
        connection,
        route_id=route["route_id"],
        flight_band_id=flight_band["flight_band_id"],
    )

    active_assigned_layers = get_active_assigned_layers(
        active_occupancy
    )

    return select_available_vertical_layer(
        vertical_layers=vertical_layers,
        active_assigned_layers=active_assigned_layers,
    )


def allocate_route_vertical_layer(
    connection,
    *,
    route,
    flight_band,
):
    lock_route_flight_band_allocation(
        connection,
        route_id=route["route_id"],
        flight_band_id=flight_band["flight_band_id"],
    )

    if not route_has_available_capacity(
        connection,
        route=route,
        flight_band_id=flight_band["flight_band_id"],
    ):
        return None

    vertical_layers = build_vertical_layers(
        min_agl_ft=flight_band["min_agl_ft"],
        max_agl_ft=flight_band["max_agl_ft"],
    )

    if not vertical_layers:
        return None

    active_occupancy = select_active_route_occupancy(
        connection,
        route_id=route["route_id"],
        flight_band_id=flight_band["flight_band_id"],
    )

    active_assigned_layers = get_active_assigned_layers(
        active_occupancy
    )

    return select_available_vertical_layer(
        vertical_layers=vertical_layers,
        active_assigned_layers=active_assigned_layers,
    )


def allocate_and_assign_route_vertical_layer(
    *,
    route,
    flight_band,
    flight_execution_id,
):
    with engine.begin() as connection:
        assigned_layer = allocate_route_vertical_layer(
            connection,
            route=route,
            flight_band=flight_band,
        )

        if assigned_layer is None:
            return None

        occupancy_ids = assign_route_occupancy_altitude(
            connection,
            flight_execution_id=flight_execution_id,
            assigned_relative_altitude_ft=assigned_layer,
        )

        if not occupancy_ids:
            return None

        return assigned_layer


def request_route_vertical_layer(
    *,
    route_id,
    flight_band_id,
    flight_execution_id,
):
    route = select_route(route_id)

    if route is None:
        return {
            "error": "Route not found."
        }, 404

    flight_band = select_flight_band_record(
        flight_band_id
    )

    if flight_band is None:
        return {
            "error": "Flight Band not found."
        }, 404

    assigned_layer = (
        allocate_and_assign_route_vertical_layer(
            route=route,
            flight_band=flight_band,
            flight_execution_id=flight_execution_id,
        )
    )

    return {
        "assigned_relative_altitude_ft": assigned_layer
    }, 200


