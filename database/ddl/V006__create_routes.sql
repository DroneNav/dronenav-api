CREATE TABLE routes (
    route_id UUID PRIMARY KEY DEFAULT uuidv7(),

    origin_site_id UUID NOT NULL,
    destination_site_id UUID NOT NULL,

    origin_droneport_id UUID NOT NULL,
    destination_droneport_id UUID NOT NULL,

    route_name VARCHAR(200) NOT NULL,
    route_type VARCHAR(50),

    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    operational_status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    survey_status VARCHAR(50) NOT NULL DEFAULT 'not_surveyed',
    last_surveyed_at TIMESTAMPTZ NULL,
    surveyed_by VARCHAR(100) NULL,
    approved_by VARCHAR(100) NULL,

    direction INTEGER NOT NULL DEFAULT 0,
    maximum_aircraft_capacity INTEGER NOT NULL DEFAULT 0,

    minimum_aircraft_weight_lbs NUMERIC(6,2) NOT NULL DEFAULT 5.00,
    maximum_aircraft_weight_lbs NUMERIC(6,2) NOT NULL DEFAULT 50.00,

    deleted_at TIMESTAMPTZ NULL,
    deleted_by VARCHAR(100) NULL,

    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,

    segment_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,

    CONSTRAINT chk_routes_direction
        CHECK (direction IN (0, 1, 2)),

    CONSTRAINT chk_routes_aircraft_weight
        CHECK (minimum_aircraft_weight_lbs <= maximum_aircraft_weight_lbs),

    CONSTRAINT chk_routes_segment_attributes_array
        CHECK (jsonb_typeof(segment_attributes) = 'array'),

    CONSTRAINT chk_routes_maximum_aircraft_capacity
        CHECK (maximum_aircraft_capacity >= 0),

    CONSTRAINT fk_routes_origin_site
        FOREIGN KEY (origin_site_id)
        REFERENCES sites(site_id),

    CONSTRAINT fk_routes_destination_site
        FOREIGN KEY (destination_site_id)
        REFERENCES sites(site_id),

    CONSTRAINT fk_routes_origin_droneport
        FOREIGN KEY (origin_droneport_id)
        REFERENCES droneports(droneport_id),

    CONSTRAINT fk_routes_destination_droneport
        FOREIGN KEY (destination_droneport_id)
        REFERENCES droneports(droneport_id)
);

