-- Route State Engine Phase 3A
-- Route / Flight Band occupancy state.
--
-- This table represents operational state, not telemetry history.
--
-- aircraft_id intentionally has no foreign key.
-- The aircraft domain currently exists outside the backend schema.
-- Referential integrity will be added when aircraft ownership
-- is introduced into the backend.

CREATE TABLE route_occupancy_state (
    route_occupancy_state_id uuid PRIMARY KEY DEFAULT uuidv7(),

    route_id uuid NOT NULL,
    flight_band_id uuid NOT NULL,

    flight_execution_id uuid NOT NULL,
    aircraft_id uuid NOT NULL,

    state text NOT NULL,

    planned_entry_time timestamptz NOT NULL,
    planned_exit_time timestamptz NOT NULL,

    actual_entry_time timestamptz,
    actual_exit_time timestamptz,

    last_latitude numeric,
    last_longitude numeric,
    last_altitude_ft numeric,

    assigned_relative_altitude_ft integer,

    CONSTRAINT route_occupancy_state_state_ck
        CHECK (
            state IN (
                'planned',
                'active',
                'exited'
            )
        ),

    CONSTRAINT route_occupancy_state_lifecycle_ck
        CHECK (
            (
                state = 'planned'
                AND actual_entry_time IS NULL
                AND actual_exit_time IS NULL
            )
            OR
            (
                state = 'active'
                AND actual_entry_time IS NOT NULL
                AND actual_exit_time IS NULL
            )
            OR
            (
                state = 'exited'
                AND actual_entry_time IS NOT NULL
                AND actual_exit_time IS NOT NULL
            )
        )
);


ALTER TABLE route_occupancy_state
    ADD CONSTRAINT route_occupancy_state_route_fk
    FOREIGN KEY (route_id)
    REFERENCES routes(route_id);


ALTER TABLE route_occupancy_state
    ADD CONSTRAINT route_occupancy_state_flight_band_fk
    FOREIGN KEY (flight_band_id)
    REFERENCES flight_bands(flight_band_id);


ALTER TABLE route_occupancy_state
    ADD CONSTRAINT route_occupancy_state_flight_execution_fk
    FOREIGN KEY (flight_execution_id)
    REFERENCES flight_executions(flight_execution_id);


CREATE UNIQUE INDEX route_occupancy_state_execution_route_uq
    ON route_occupancy_state (
        flight_execution_id,
        route_id
    );

CREATE INDEX route_occupancy_state_route_state_idx
    ON route_occupancy_state (
        route_id,
        state
    );

CREATE INDEX route_occupancy_state_aircraft_state_idx
    ON route_occupancy_state (
        aircraft_id,
        state
    );

