ALTER TABLE route_nodes
    ALTER COLUMN site_id DROP NOT NULL;

ALTER TABLE droneports
    ALTER COLUMN site_id DROP NOT NULL;

ALTER TABLE routes
    ALTER COLUMN origin_site_id DROP NOT NULL,
    ALTER COLUMN destination_site_id DROP NOT NULL;

ALTER TABLE routes
    DROP CONSTRAINT fk_routes_origin_droneport,
    DROP CONSTRAINT fk_routes_destination_droneport;

ALTER TABLE routes
    DROP COLUMN origin_droneport_id,
    DROP COLUMN destination_droneport_id;

