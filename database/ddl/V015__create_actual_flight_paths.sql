CREATE TABLE flight_execution_actual_paths (
    flight_execution_id UUID PRIMARY KEY,

    flight_id UUID NOT NULL,

    geometry geometry(LineString, 4326) NOT NULL,

    point_count INTEGER NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'recording',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_actual_path_flight_execution
        FOREIGN KEY (flight_execution_id)
        REFERENCES flight_executions(flight_execution_id),

    CONSTRAINT fk_actual_path_flight
        FOREIGN KEY (flight_id)
        REFERENCES flight(flight_id),

    CONSTRAINT chk_actual_path_status
        CHECK (
            status IN (
                'recording',
                'complete'
            )
        ),

    CONSTRAINT chk_actual_path_point_count
        CHECK (
            point_count >= 2
        )
);

