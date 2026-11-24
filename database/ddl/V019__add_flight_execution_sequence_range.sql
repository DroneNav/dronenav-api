ALTER TABLE flight_execution_routes
    ADD COLUMN start_mission_sequence INTEGER,
    ADD COLUMN end_mission_sequence INTEGER,
    ADD COLUMN segment_mission_sequences INTEGER[];

ALTER TABLE flight_execution_routes
    DROP CONSTRAINT uq_flight_execution_route,
    ADD CONSTRAINT uq_flight_execution_route
    UNIQUE (flight_execution_id, route_id, sequence_number);
