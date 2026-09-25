CREATE TABLE obstacles (
    obstacle_id UUID PRIMARY KEY DEFAULT uuidv7(),
    site_id UUID NULL,
    obstacle_name VARCHAR(200) NOT NULL,
    obstacle_type VARCHAR(50) NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    operational_status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    survey_status VARCHAR(50) NOT NULL DEFAULT 'not_surveyed',
    last_surveyed_at TIMESTAMPTZ NULL,
    surveyed_by VARCHAR(100) NULL,
    approved_by VARCHAR(100) NULL,
    maximum_height_agl_ft INTEGER NULL,
    description TEXT NULL,
    deleted_at TIMESTAMPTZ NULL,
    deleted_by VARCHAR(100) NULL,
    geometry geometry(Geometry,4326) NOT NULL,

    CONSTRAINT fk_obstacles_site
        FOREIGN KEY (site_id)
        REFERENCES sites(site_id)
);

ALTER TABLE obstacles
ADD CONSTRAINT chk_obstacles_geometry_type
CHECK (GeometryType(geometry) IN ('POINT', 'LINESTRING', 'POLYGON'));

ALTER TABLE obstacles
ADD CONSTRAINT chk_obstacles_maximum_height
CHECK (
    maximum_height_agl_ft IS NULL
    OR maximum_height_agl_ft >= 0
);

CREATE INDEX idx_obstacles_name
ON obstacles (obstacle_name);

CREATE INDEX idx_obstacles_geometry
ON obstacles USING GIST (geometry);

CREATE TABLE obstacle_collections (
    obstacle_collection_id UUID PRIMARY KEY DEFAULT uuidv7(),
    collection_name VARCHAR(200) NOT NULL,
    description TEXT NULL
);

CREATE TABLE obstacle_membership (
    obstacle_collection_id UUID NOT NULL,
    obstacle_id UUID NOT NULL,

    PRIMARY KEY (obstacle_collection_id, obstacle_id),

    CONSTRAINT fk_obstacle_membership_collection
        FOREIGN KEY (obstacle_collection_id)
        REFERENCES obstacle_collections(obstacle_collection_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_obstacle_membership_obstacle
        FOREIGN KEY (obstacle_id)
        REFERENCES obstacles(obstacle_id)
);

CREATE INDEX idx_obstacle_membership_obstacle
ON obstacle_membership (obstacle_id);


