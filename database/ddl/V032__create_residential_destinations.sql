CREATE TABLE residential_destinations (
    destination_id UUID PRIMARY KEY DEFAULT uuidv7(),

    site_id UUID NOT NULL
        REFERENCES sites(site_id),

    street_address TEXT NOT NULL,

    latitude NUMERIC NOT NULL,
    longitude NUMERIC NOT NULL,

    CONSTRAINT residential_destinations_site_address_unique
        UNIQUE (site_id, street_address),

    CONSTRAINT residential_destinations_latitude_check
        CHECK (latitude BETWEEN -90 AND 90),

    CONSTRAINT residential_destinations_longitude_check
        CHECK (longitude BETWEEN -180 AND 180)
);

