from app.config.constants import (
    MINIMUM_TURN_ANGLE_DEG,
    MAXIMUM_TURN_ANGLE_DEG,
    ROUTE_DIRECTION_BIDIRECTIONAL,
)

from app.models.route_model import (
    count_incident_segments_for_route_node,
    select_routes_for_route_node,
)

from app.models.droneport_model import (
    select_droneport_by_route_node_id,
)

from app.services.geometry_service import calculate_turn_angle
from app.services.route_service import get_route_by_id


def is_managed_turn(route_node_id):
    if count_incident_segments_for_route_node(route_node_id) != 2:
        return False

    if select_droneport_by_route_node_id(route_node_id) is not None:
        return False

    connections = select_routes_for_route_node(route_node_id)

    if len(connections) != 1:
        return False

    connection = connections[0]
    route = get_route_by_id(connection["route_id"])

    if route is None:
        return False

    if route["direction"] != ROUTE_DIRECTION_BIDIRECTIONAL:
        return False

    if route["maximum_aircraft_capacity"] == 1:
        return False

    coordinates = route["geometry"]["coordinates"]
    waypoint_index = connection["waypoint_index"]

    if not 0 < waypoint_index < len(coordinates) - 1:
        return False

    angle = calculate_turn_angle(
        coordinates[waypoint_index - 1],
        coordinates[waypoint_index],
        coordinates[waypoint_index + 1],
    )

    return (
        MINIMUM_TURN_ANGLE_DEG
        <= angle
        <= MAXIMUM_TURN_ANGLE_DEG
    )


