ALTER TABLE route_occupancy_state
ADD COLUMN cleared boolean NULL;

ALTER TABLE route_occupancy_state
ADD COLUMN sequence_number integer;

ALTER TABLE route_occupancy_state
    ALTER COLUMN sequence_number SET NOT NULL,
    ADD CONSTRAINT route_occupancy_state_sequence_ck
        CHECK (sequence_number >= 1);

DROP INDEX route_occupancy_state_execution_route_uq;

CREATE UNIQUE INDEX route_occupancy_state_execution_route_uq
    ON route_occupancy_state (
        flight_execution_id,
        route_id,
        sequence_number
    );
