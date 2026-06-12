ALTER TABLE overlay_reviews
ADD COLUMN surveyed_at TIMESTAMPTZ;

ALTER TABLE overlay_reviews
ADD COLUMN surveyed_by VARCHAR(100);

ALTER TABLE overlay_reviews
ADD COLUMN survey_status VARCHAR(50);

