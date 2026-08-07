-----------------------------------------------------------------
-- Flight Execution Records are immutable operational contracts.
--
-- They are intentionally concise and machine-readable.
--
-- The record contains only the information required by NAVProxy
-- to locate and retrieve authoritative operational data prior
-- to aircraft arming.
--
-- Flight Execution Records are not telemetry records,
-- not audit records,
-- not mission history,
-- and not copies of Flight Plans.
-----------------------------------------------------------------

CREATE TABLE flight_executions (

    flight_execution_id UUID PRIMARY KEY DEFAULT uuidv7(),

    -- Immutable Flight Plan reference (Drupal)
    flight_plan_id UUID NOT NULL,

    -- Operational partition
    authority_id UUID NOT NULL,

    -- Flight characteristics
    flight_class VARCHAR(50) NOT NULL,

    -- Operational references
    origin_site_id UUID NOT NULL,
    destination_site_id UUID NOT NULL,

    departure_droneport_id UUID NULL,
    arrival_droneport_id UUID NULL,

    -- NULL = reusable execution
    requested_departure_datetime TIMESTAMPTZ NULL,

    -- Populated by NAVProxy after successful landing/disarm
    flight_termination_datetime TIMESTAMPTZ NULL,

    -- Operational timezone resolved during translation
    operational_timezone VARCHAR(64) NOT NULL,

    -- Lifecycle
    execution_status VARCHAR(20) NOT NULL DEFAULT 'active',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    --------------------------------------------------------------------
    -- Constraints
    --------------------------------------------------------------------

    CONSTRAINT uq_flight_execution_plan
        UNIQUE (flight_plan_id),

    CONSTRAINT chk_flight_execution_status
        CHECK (
            execution_status IN (
                'active',
                'completed',
                'dispatched',
                'expired',
                'suspended',
                'revoked',
                'cancelled'
            )
        ),

    CONSTRAINT fk_flight_execution_origin_site
        FOREIGN KEY (origin_site_id)
        REFERENCES sites(site_id),

    CONSTRAINT fk_flight_execution_destination_site
        FOREIGN KEY (destination_site_id)
        REFERENCES sites(site_id),

    CONSTRAINT fk_flight_execution_departure_droneport
        FOREIGN KEY (departure_droneport_id)
        REFERENCES droneports(droneport_id),

    CONSTRAINT fk_flight_execution_arrival_droneport
        FOREIGN KEY (arrival_droneport_id)
        REFERENCES droneports(droneport_id)

);

CREATE TABLE flight_execution_routes (

    flight_execution_id UUID NOT NULL,

    sequence_number INTEGER NOT NULL,

    route_id UUID NOT NULL,

    --------------------------------------------------------------------
    -- Constraints
    --------------------------------------------------------------------

    CONSTRAINT pk_flight_execution_routes
        PRIMARY KEY (
            flight_execution_id,
            sequence_number
        ),

    CONSTRAINT uq_flight_execution_route
        UNIQUE (
            flight_execution_id,
            route_id
        ),

    CONSTRAINT chk_flight_execution_route_sequence
        CHECK (sequence_number >= 1),

    CONSTRAINT fk_flight_execution_routes_execution
        FOREIGN KEY (flight_execution_id)
        REFERENCES flight_executions(flight_execution_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_flight_execution_routes_route
        FOREIGN KEY (route_id)
        REFERENCES routes(route_id)

);

CREATE INDEX idx_flight_execution_authority
    ON flight_executions(authority_id);

CREATE INDEX idx_flight_execution_origin_site
    ON flight_executions(origin_site_id);

CREATE INDEX idx_flight_execution_destination_site
    ON flight_executions(destination_site_id);

CREATE INDEX idx_flight_execution_departure_datetime
    ON flight_executions(requested_departure_datetime)
    WHERE requested_departure_datetime IS NOT NULL;

CREATE INDEX idx_flight_execution_status
    ON flight_executions(execution_status);

CREATE INDEX idx_flight_execution_route
    ON flight_execution_routes(route_id);


