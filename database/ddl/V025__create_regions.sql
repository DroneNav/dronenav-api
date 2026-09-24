CREATE TABLE regions (
    region_id VARCHAR(2) PRIMARY KEY,
    region_code VARCHAR(2) NOT NULL UNIQUE,
    region_name VARCHAR(100) NOT NULL,

    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL
);

CREATE INDEX idx_regions_geometry
ON regions
USING GIST (geometry);

