CREATE TABLE authorities (
    authority_id UUID PRIMARY KEY,

    authority_name VARCHAR(200) NOT NULL,
    authority_code VARCHAR(50) NOT NULL UNIQUE,

    authority_type VARCHAR(50) NOT NULL,

    operational_status VARCHAR(50) NOT NULL DEFAULT 'active',

    contact_name VARCHAR(100),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(50),

    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ
);

ALTER TABLE sites
ADD CONSTRAINT fk_sites_authority
FOREIGN KEY (authority_id)
REFERENCES authorities(authority_id);

ALTER TABLE authorities
ALTER COLUMN authority_id
SET DEFAULT uuidv7();

