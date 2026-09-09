CREATE TABLE intersection_states (
    intersection_state_id UUID PRIMARY KEY DEFAULT uuidv7(),

    route_node_id UUID NOT NULL,
    flight_band_id UUID NOT NULL,
    assigned_relative_altitude_ft INTEGER NOT NULL,

    state TEXT NOT NULL DEFAULT 'clear',

    flight_execution_id UUID,
    from_route_id UUID,
    to_route_id UUID,

    reserved_at TIMESTAMPTZ,
    occupied_at TIMESTAMPTZ,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT intersection_states_state_ck
        CHECK (state IN ('clear', 'reserved', 'occupied')),

    CONSTRAINT intersection_states_slot_uq
        UNIQUE (
            route_node_id,
            flight_band_id,
            assigned_relative_altitude_ft
        ),

    CONSTRAINT intersection_states_route_node_fk
        FOREIGN KEY (route_node_id)
        REFERENCES route_nodes(route_node_id),

    CONSTRAINT intersection_states_flight_band_fk
        FOREIGN KEY (flight_band_id)
        REFERENCES flight_bands(flight_band_id),

    CONSTRAINT intersection_states_flight_execution_fk
        FOREIGN KEY (flight_execution_id)
        REFERENCES flight_executions(flight_execution_id),

    CONSTRAINT intersection_states_from_route_fk
        FOREIGN KEY (from_route_id)
        REFERENCES routes(route_id),

    CONSTRAINT intersection_states_to_route_fk
        FOREIGN KEY (to_route_id)
        REFERENCES routes(route_id)
);

