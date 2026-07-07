CREATE TABLE flight_bands (

    flight_band_id UUID PRIMARY KEY,

    flight_class VARCHAR(50) NOT NULL,

    band_name VARCHAR(50) NOT NULL,

    min_agl_ft INTEGER NOT NULL DEFAULT 0,
    max_agl_ft INTEGER NOT NULL DEFAULT 500,

    start_time TIME NOT NULL DEFAULT '00:00:00',
    end_time   TIME NOT NULL DEFAULT '23:59:59',

    timezone VARCHAR(64) NOT NULL DEFAULT 'America/New_York',

    operational_status VARCHAR(20) NOT NULL DEFAULT 'active',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by VARCHAR(100),

    updated_at TIMESTAMPTZ,
    updated_by VARCHAR(100),

    CHECK (min_agl_ft >= 0),
    CHECK (max_agl_ft > min_agl_ft),
    CHECK (start_time < end_time),
    CHECK (operational_status IN ('active', 'inactive'))

);

ALTER TABLE flight_bands
ALTER COLUMN flight_band_id
SET DEFAULT uuidv7();

CREATE TABLE flight_band_days (

    flight_band_id UUID NOT NULL
        REFERENCES flight_bands(flight_band_id)
        ON DELETE CASCADE,

    day_of_week SMALLINT NOT NULL,

    PRIMARY KEY (flight_band_id, day_of_week),

    CHECK (day_of_week BETWEEN 0 AND 6)

);

CREATE UNIQUE INDEX uq_flight_bands_class_band
    ON flight_bands (flight_class, band_name);

CREATE INDEX idx_flight_bands_flight_class
    ON flight_bands (flight_class);

CREATE INDEX idx_flight_bands_status
    ON flight_bands (operational_status);

CREATE INDEX idx_flight_band_days_day
    ON flight_band_days (day_of_week);

