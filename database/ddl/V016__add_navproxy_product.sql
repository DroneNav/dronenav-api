ALTER TABLE flight_executions
    ADD COLUMN navproxy_product VARCHAR(2) NOT NULL DEFAULT 'st';

ALTER TABLE flight_executions
    ADD CONSTRAINT chk_flight_executions_navproxy_product
        CHECK (
            navproxy_product IN ('st', 'fr')
        );


ALTER TABLE flight
    ADD COLUMN navproxy_product VARCHAR(2) NOT NULL DEFAULT 'st';

ALTER TABLE flight
    ADD CONSTRAINT chk_flight_navproxy_product
        CHECK (
            navproxy_product IN ('st', 'fr')
        );


ALTER TABLE flight_log
    ADD COLUMN navproxy_product VARCHAR(2) NOT NULL DEFAULT 'st';

ALTER TABLE flight_log
    ADD CONSTRAINT chk_flight_log_navproxy_product
        CHECK (
            navproxy_product IN ('st', 'fr')
        );

