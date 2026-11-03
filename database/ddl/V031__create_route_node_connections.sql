
CREATE TABLE route_node_connections (
    route_id uuid NOT NULL,
    route_node_id uuid NOT NULL,
    waypoint_index integer NOT NULL,

    CONSTRAINT route_node_connections_pkey
        PRIMARY KEY (route_id, route_node_id),

    CONSTRAINT route_node_connections_waypoint_unique
        UNIQUE (route_id, waypoint_index),

    CONSTRAINT route_node_connections_waypoint_check
        CHECK (waypoint_index >= 0),

    CONSTRAINT route_node_connections_route_fk
        FOREIGN KEY (route_id)
        REFERENCES routes(route_id),

    CONSTRAINT route_node_connections_node_fk
        FOREIGN KEY (route_node_id)
        REFERENCES route_nodes(route_node_id)
);

