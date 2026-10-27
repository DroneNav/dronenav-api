CREATE TABLE aircraft (
    aircraft_id UUID PRIMARY KEY DEFAULT uuidv7(),

    aviator_id UUID NOT NULL,

    aircraft_name VARCHAR(150) NOT NULL,
    manufacturer VARCHAR(150),
    model VARCHAR(150) NOT NULL,
    aircraft_type VARCHAR(50) NOT NULL,

    length_cm NUMERIC(8,2) NOT NULL,
    width_cm NUMERIC(8,2) NOT NULL,
    height_cm NUMERIC(8,2) NOT NULL,

    maximum_takeoff_weight_kg NUMERIC(10,2) NOT NULL,
    maximum_speed_ft_s NUMERIC(8,2) NOT NULL,

    planned_deceleration_ft_s2 NUMERIC(8,2),
    deceleration_verified BOOLEAN NOT NULL DEFAULT FALSE,

    operational_status VARCHAR(20) NOT NULL DEFAULT 'active',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by VARCHAR(100) NOT NULL,
    updated_at TIMESTAMPTZ,
    updated_by VARCHAR(100),

    CONSTRAINT uq_aircraft_aviator_model
        UNIQUE (aviator_id, model),

    CONSTRAINT chk_aircraft_dimensions
        CHECK (
            length_cm > 0
            AND width_cm > 0
            AND height_cm > 0
        ),

    CONSTRAINT chk_aircraft_maximum_takeoff_weight
        CHECK (
            maximum_takeoff_weight_kg > 0
        ),

    CONSTRAINT chk_aircraft_maximum_speed
        CHECK (
            maximum_speed_ft_s > 0
        ),

    CONSTRAINT chk_aircraft_operational_status
        CHECK (
            operational_status IN ('active', 'inactive')
        ),

    CONSTRAINT chk_aircraft_planned_deceleration
        CHECK (
            planned_deceleration_ft_s2 IS NULL
            OR planned_deceleration_ft_s2 > 0
        )
);

CREATE INDEX idx_aircraft_aviator_id
    ON aircraft (aviator_id);

