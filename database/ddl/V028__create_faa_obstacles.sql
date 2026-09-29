CREATE TABLE faa_obstacles (
    faa_obstacle_id UUID PRIMARY KEY DEFAULT uuidv7(),
    oas_number VARCHAR(20) NOT NULL,
    verification_status VARCHAR(1) NOT NULL,
    dronenav_verified BOOLEAN NOT NULL DEFAULT FALSE,
    obstacle_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    maximum_height_agl_ft INTEGER NOT NULL,
    elevation_amsl_ft INTEGER NOT NULL,
    diameter_ft INTEGER NULL,
    geometry geometry(Point,4326) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'faa'
);

ALTER TABLE faa_obstacles
ADD CONSTRAINT uq_faa_obstacles_oas_number
UNIQUE (oas_number);

ALTER TABLE faa_obstacles
ADD CONSTRAINT chk_faa_obstacles_verification_status
CHECK (verification_status IN ('O', 'U'));

ALTER TABLE faa_obstacles
ADD CONSTRAINT chk_faa_obstacles_quantity
CHECK (quantity > 0);

ALTER TABLE faa_obstacles
ADD CONSTRAINT chk_faa_obstacles_dronenav_verification
CHECK (
    dronenav_verified = FALSE
    OR diameter_ft IS NOT NULL
);

ALTER TABLE faa_obstacles
ADD CONSTRAINT chk_faa_obstacles_diameter
CHECK (
    diameter_ft IS NULL
    OR diameter_ft > 0
);

CREATE INDEX idx_faa_obstacles_geometry
ON faa_obstacles
USING GIST (geometry);

ALTER TABLE faa_obstacles
ADD CONSTRAINT chk_faa_obstacles_maximum_height
CHECK (maximum_height_agl_ft >= 0);

ALTER TABLE faa_obstacles
ADD CONSTRAINT chk_faa_obstacles_elevation_amsl
CHECK (elevation_amsl_ft >= 0);


