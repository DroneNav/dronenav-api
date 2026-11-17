CREATE TABLE residential_destinations (
    destination_id UUID PRIMARY KEY DEFAULT uuidv7(),

    site_id UUID NOT NULL
        REFERENCES sites(site_id),

    street_address TEXT NOT NULL,
    normalized_address TEXT NOT NULL,

    latitude NUMERIC NOT NULL,
    longitude NUMERIC NOT NULL,

    geocoded_latitude NUMERIC,
    geocoded_longitude NUMERIC,

    geocode_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by TEXT,
    verified_at TIMESTAMPTZ,

    CONSTRAINT residential_destinations_site_address_unique
        UNIQUE (site_id, normalized_address),

    CONSTRAINT residential_destinations_latitude_check
        CHECK (latitude BETWEEN -90 AND 90),

    CONSTRAINT residential_destinations_longitude_check
        CHECK (longitude BETWEEN -180 AND 180)
);

