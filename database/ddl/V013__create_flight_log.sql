
CREATE TABLE flight (
    flight_id UUID PRIMARY KEY DEFAULT uuidv7(),

    flight_execution_id UUID NOT NULL,

    aviator_id UUID NOT NULL,

    aircraft_id UUID NOT NULL,

    scheduled_departure_utc TIMESTAMPTZ NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_flight_execution
        FOREIGN KEY (flight_execution_id)
        REFERENCES flight_executions (flight_execution_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

CREATE TABLE flight_log (
    flight_log_id UUID PRIMARY KEY DEFAULT uuidv7(),

    flight_id UUID NOT NULL,

    flight_execution_id UUID NOT NULL,

    lifecycle_phase VARCHAR(32) NOT NULL,

    event_type VARCHAR(64) NOT NULL,

    event_status VARCHAR(32) NULL,

    message TEXT NOT NULL,

    details JSONB NULL,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_flight_log_flight
        FOREIGN KEY (flight_id)
        REFERENCES flight (flight_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_flight_log_execution
        FOREIGN KEY (flight_execution_id)
        REFERENCES flight_executions (flight_execution_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_flight_log_phase
        CHECK (
            lifecycle_phase IN (
                'pre_flight',
                'in_flight',
                'post_flight'
            )
        )
);

CREATE INDEX idx_flight_execution_created
    ON flight (
        flight_execution_id,
        created_at DESC
    );

CREATE INDEX idx_flight_log_flight_time
    ON flight_log (
        flight_id,
        occurred_at,
        flight_log_id
    );

CREATE INDEX idx_flight_log_execution_time
    ON flight_log (
        flight_execution_id,
        occurred_at DESC
    );


