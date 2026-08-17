
ALTER TABLE sites
ADD COLUMN site_attributes JSONB;

ALTER TABLE zones
ADD COLUMN zone_attributes JSONB;

