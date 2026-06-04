CREATE TABLE routes (
    route_id UUID PRIMARY KEY DEFAULT uuidv7(),

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
    buffered INTEGER NOT NULL DEFAULT 0,

    minimum_altitude_ft INTEGER NOT NULL DEFAULT 20,
    maximum_altitude_ft INTEGER NOT NULL DEFAULT 400,

    minimum_aircraft_weight_lbs INTEGER NOT NULL DEFAULT 5,
    maximum_aircraft_weight_lbs INTEGER NOT NULL DEFAULT 50,

    deleted_at TIMESTAMPTZ NULL,
    deleted_by VARCHAR(100) NULL,

    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,

    CONSTRAINT fk_routes_origin_droneport
        FOREIGN KEY (origin_droneport_id)
        REFERENCES droneports(droneport_id),

    CONSTRAINT fk_routes_destination_droneport
        FOREIGN KEY (destination_droneport_id)
        REFERENCES droneports(droneport_id)

);

