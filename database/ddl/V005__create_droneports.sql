CREATE TABLE droneports (
    droneport_id UUID PRIMARY KEY DEFAULT uuidv7(),

    site_id UUID NOT NULL,

    droneport_name VARCHAR(200) NOT NULL,
    droneport_type VARCHAR(50),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    operational_status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    survey_status VARCHAR(50) NOT NULL DEFAULT 'not_surveyed',
    last_surveyed_at TIMESTAMPTZ NULL,
    surveyed_by VARCHAR(100) NULL,
    approved_by VARCHAR(100) NULL,

    deleted_at TIMESTAMPTZ NULL,
    deleted_by VARCHAR(100) NULL,

    droneport_diameter_ft INTEGER NOT NULL DEFAULT 30,

    geometry GEOMETRY(POINT, 4326) NOT NULL,

    CONSTRAINT fk_droneports_site
        FOREIGN KEY (site_id)
        REFERENCES sites(site_id)
);

