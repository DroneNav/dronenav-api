CREATE TABLE route_nodes (
    route_node_id UUID PRIMARY KEY DEFAULT uuidv7(),

    site_id UUID NOT NULL,

    geometry GEOMETRY(POINT, 4326) NOT NULL,

    CONSTRAINT fk_route_nodes_site
        FOREIGN KEY (site_id)
        REFERENCES sites(site_id)
);

ALTER TABLE droneports
ADD COLUMN route_node_id UUID NOT NULL;

ALTER TABLE droneports
ADD CONSTRAINT fk_droneports_route_node
    FOREIGN KEY (route_node_id)
    REFERENCES route_nodes(route_node_id);

ALTER TABLE droneports
ADD CONSTRAINT uq_droneports_route_node
    UNIQUE (route_node_id);

ALTER TABLE routes
ADD COLUMN origin_route_node_id UUID NOT NULL;

ALTER TABLE routes
ADD COLUMN destination_route_node_id UUID NOT NULL;

ALTER TABLE routes
ADD CONSTRAINT fk_routes_origin_route_node
    FOREIGN KEY (origin_route_node_id)
    REFERENCES route_nodes(route_node_id);

ALTER TABLE routes
ADD CONSTRAINT fk_routes_destination_route_node
    FOREIGN KEY (destination_route_node_id)
    REFERENCES route_nodes(route_node_id);



