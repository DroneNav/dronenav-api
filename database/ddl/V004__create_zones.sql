CREATE TABLE zones (
    zone_id UUID PRIMARY KEY DEFAULT uuidv7(),

    site_id UUID NOT NULL,

    zone_name VARCHAR(200) NOT NULL,
    zone_type VARCHAR(50),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    operational_status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    survey_status VARCHAR(50) NOT NULL DEFAULT 'not_surveyed',
    last_surveyed_at TIMESTAMPTZ NULL,
    surveyed_by VARCHAR(100) NULL,
    approved_by VARCHAR(100) NULL,

    minimum_altitude_ft INTEGER NOT NULL DEFAULT 0,
    maximum_altitude_ft INTEGER NOT NULL DEFAULT 400,

    deleted_at TIMESTAMPTZ NULL,
    deleted_by VARCHAR(100) NULL,

    geometry GEOMETRY(POLYGON, 4326) NOT NULL,

    CONSTRAINT fk_zones_site
        FOREIGN KEY (site_id)
        REFERENCES sites(site_id)
);

