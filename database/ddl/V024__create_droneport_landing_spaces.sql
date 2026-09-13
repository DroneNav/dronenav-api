CREATE TABLE droneport_landing_spaces (
    landing_space_id UUID PRIMARY KEY DEFAULT uuidv7(),

    droneport_id UUID NOT NULL,

    geometry GEOMETRY(POINT, 4326) NOT NULL,

    heading_degrees NUMERIC(5,2) NOT NULL DEFAULT 0,

    charging_capable BOOLEAN NOT NULL DEFAULT FALSE,

    operational_status VARCHAR(50) NOT NULL DEFAULT 'active',

    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_droneport_landing_spaces_droneport
        FOREIGN KEY (droneport_id)
        REFERENCES droneports(droneport_id)
        ON DELETE CASCADE,

    CONSTRAINT ck_droneport_landing_spaces_heading
        CHECK (
            heading_degrees >= 0
            AND heading_degrees < 360
        )
);

CREATE INDEX idx_droneport_landing_spaces_droneport
    ON droneport_landing_spaces(droneport_id);

