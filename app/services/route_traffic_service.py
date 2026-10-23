
from app.config.constants import (
    VERTICAL_CONFORMANCE_MARGIN_FT,
    VERTICAL_LAYER_SPACING_FT,
    MINIMUM_LONGITUDINAL_SEPARATION_FT,
)

from app.models.route_occupancy_state_model import (
    lock_route_flight_band_allocation,
    select_active_route_occupancy,
    assign_route_occupancy_altitude,
    count_active_route_occupancy,
    clear_route_occupancy,
)

from app.models.geospatial_model import (
    select_linestring_progress_feet,
)

from app.config.database import engine

from app.models.route_model import select_route

from app.models.flight_execution_model import (
    select_flight_execution_route_ranges,
)

from app.models.flight_band_model import (
    select_flight_band_record,
)

import logging


LOGGER = logging.getLogger(__name__)

LOGGER.setLevel(logging.INFO)

if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
    )
    LOGGER.addHandler(handler)

LOGGER.propagate = False


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
        if (
            row["assigned_relative_altitude_ft"] is not None
            and row["cleared"] is not True
        )
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


def build_layer_trailing_occupancy(
    *,
    route_geometry,
    active_occupancy,
    route_id,
    entry_node_id,
):
    trailing_by_layer = {}
    blocked_layers = set()

    for occupancy in active_occupancy:
        layer = occupancy["assigned_relative_altitude_ft"]

        if layer is None:
            continue

        if occupancy["cleared"] is True:
            continue

        occupancy_route_ranges = (
            select_flight_execution_route_ranges(
                occupancy["flight_execution_id"]
            )
        )

        occupancy_route_range = next(
            (
                route_range
                for route_range in occupancy_route_ranges
                if str(route_range["route_id"]) == str(route_id)
            ),
            None,
        )

        if (
            occupancy_route_range is None
            or str(occupancy_route_range["entry_node_id"])
            != str(entry_node_id)
        ):
            blocked_layers.add(layer)
            continue

        latitude = occupancy["last_latitude"]
        longitude = occupancy["last_longitude"]

        if latitude is None or longitude is None:
            blocked_layers.add(layer)
            continue

        progress = select_linestring_progress_feet(
            route_geometry,
            longitude=float(longitude),
            latitude=float(latitude),
        )

        if progress is None:
            blocked_layers.add(layer)
            continue

        distance_ft = progress.get("distance_ft")

        if distance_ft is None:
            blocked_layers.add(layer)
            continue

        candidate = {
            "occupancy": occupancy,
            "distance_ft": float(distance_ft),
        }

        current = trailing_by_layer.get(layer)

        if (
            current is None
            or candidate["distance_ft"] < current["distance_ft"]
        ):
            trailing_by_layer[layer] = candidate

    return {
        "trailing_by_layer": trailing_by_layer,
        "blocked_layers": blocked_layers,
    }


def select_reusable_vertical_layer(
    *,
    trailing_by_layer,
    blocked_layers,
):
    for layer in sorted(trailing_by_layer):
        if layer in blocked_layers:
            continue

        candidate = trailing_by_layer[layer]

        if (
            candidate["distance_ft"]
            >= MINIMUM_LONGITUDINAL_SEPARATION_FT
        ):
            return {
                "layer": layer,
                "occupancy": candidate["occupancy"],
                "distance_ft": candidate["distance_ft"],
            }

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
    flight_execution_id,
):
    lock_route_flight_band_allocation(
        connection,
        route_id=route["route_id"],
        flight_band_id=flight_band["flight_band_id"],
    )

    route_ranges = select_flight_execution_route_ranges(
        flight_execution_id
    )

    current_route_range = next(
        (
            route_range
            for route_range in route_ranges
            if str(route_range["route_id"]) == str(route["route_id"])
        ),
        None,
    )

    if current_route_range is None:
        return None

    entry_node_id = current_route_range["entry_node_id"]

    if str(entry_node_id) == str(route["origin_route_node_id"]):
        route_geometry = route["geometry"]

    elif str(entry_node_id) == str(route["destination_route_node_id"]):
        route_geometry = {
            **route["geometry"],
            "coordinates": list(
                reversed(route["geometry"]["coordinates"])
            ),
        }

    else:
        return None

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

    separation = build_layer_trailing_occupancy(
        route_geometry=route_geometry,
        active_occupancy=active_occupancy,
        route_id=route["route_id"],
        entry_node_id=entry_node_id,
    )

    reusable_layer = select_reusable_vertical_layer(
        trailing_by_layer=separation["trailing_by_layer"],
        blocked_layers=separation["blocked_layers"],
    )

    LOGGER.info(
        "Route altitude allocation: execution=%s route=%s "
        "active_layers=%s trailing_by_layer=%s "
        "blocked_layers=%s reusable_layer=%s",
        flight_execution_id,
        route["route_id"],
        sorted(active_assigned_layers),
        separation["trailing_by_layer"],
        sorted(separation["blocked_layers"]),
        reusable_layer,
    )

    for layer in vertical_layers:
        if layer not in active_assigned_layers:
            return layer

        if (
            reusable_layer is not None
            and reusable_layer["layer"] == layer
        ):
            return layer

    return None


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
            flight_execution_id=flight_execution_id,
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


