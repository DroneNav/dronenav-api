CREATE TABLE overlay_reviews (

    review_id UUID PRIMARY KEY DEFAULT uuidv7(),

    overlay_type VARCHAR(50) NOT NULL,
    overlay_id UUID NOT NULL,

    review_status VARCHAR(50) NOT NULL DEFAULT 'pending_review',

    submitted_by VARCHAR(100) NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    reviewed_by VARCHAR(100) NULL,
    reviewed_at TIMESTAMPTZ NULL,

    review_comments TEXT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NULL,

    CONSTRAINT chk_overlay_reviews_status
	CHECK (review_status IN (
	    'pending_review',
	    'approved',
	    'rejected',
	    'revisions_requested'
	)),

    CONSTRAINT chk_overlay_reviews_type
	CHECK (overlay_type IN (
	    'site',
	    'zone',
	    'droneport',
	    'route'
	))
);

CREATE INDEX idx_overlay_reviews_overlay
ON overlay_reviews (overlay_type, overlay_id);

CREATE INDEX idx_overlay_reviews_status
ON overlay_reviews (review_status);

