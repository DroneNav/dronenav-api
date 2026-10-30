CREATE TABLE aircraft_calibration_profiles (
    profile_id UUID PRIMARY KEY DEFAULT uuidv7(),

    aircraft_id UUID NOT NULL,
    cruise_speed_ft_s NUMERIC(8,2) NOT NULL,
    planned_deceleration_ft_s2 NUMERIC(8,2),
    deceleration_verified BOOLEAN NOT NULL DEFAULT FALSE,
    calibrated_at TIMESTAMPTZ,
    calibration_flight_execution_id UUID,
    sample_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(100) NOT NULL,

    CONSTRAINT fk_aircraft_calibration_aircraft
        FOREIGN KEY (aircraft_id)
        REFERENCES aircraft(aircraft_id),

    CONSTRAINT fk_aircraft_calibration_execution
        FOREIGN KEY (calibration_flight_execution_id)
        REFERENCES flight_executions(flight_execution_id),

    CONSTRAINT uq_aircraft_calibration_speed
        UNIQUE (aircraft_id, cruise_speed_ft_s),

    CONSTRAINT chk_aircraft_calibration_speed
        CHECK (cruise_speed_ft_s > 0),

    CONSTRAINT chk_aircraft_calibration_deceleration
        CHECK (
            planned_deceleration_ft_s2 IS NULL
            OR planned_deceleration_ft_s2 > 0
        ),

    CONSTRAINT chk_aircraft_calibration_samples
        CHECK (sample_count >= 0),

    CONSTRAINT chk_aircraft_calibration_verified
        CHECK (
            deceleration_verified = FALSE
            OR (
                planned_deceleration_ft_s2 IS NOT NULL
                AND calibrated_at IS NOT NULL
            )
        )
);

CREATE INDEX idx_aircraft_calibration_profiles_aircraft
    ON aircraft_calibration_profiles (aircraft_id);

