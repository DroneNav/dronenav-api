/******************************************************************************
 *
 * DroneNav Flight Log Table
 *
 * Purpose
 * -------
 * The flight_log table records one actual flight occurrence or launch attempt.
 * It represents operational history and is intentionally separated from both
 * the Flight Plan and the Flight Execution Record.
 *
 * Architectural Relationship
 * --------------------------
 *
 *     Flight Plan
 *          |
 *          v
 *     Flight Execution Record
 *          |
 *          v
 *     Flight Log
 *
 * Flight Plan
 * -----------
 * - Owned by Drupal.
 * - Represents aviator intent.
 * - Becomes immutable after successful submission and acceptance.
 * - Produces exactly one Flight Execution Record.
 *
 * Flight Execution Record
 * -----------------------
 * - Owned by the Flight Execution API.
 * - Represents the accepted operational contract.
 * - Contains the machine-readable definition used by NAVProxy.
 * - May represent either:
 *
 *     1. A scheduled execution:
 *        requested_departure_utc IS NOT NULL
 *
 *     2. A reusable on-demand execution:
 *        requested_departure_utc IS NULL
 *
 * - Does not store the runtime history of individual flight occurrences.
 *
 * Flight Log
 * ----------
 * - Records one actual flight occurrence or launch attempt.
 * - A scheduled Flight Execution normally produces one Flight Log.
 * - A reusable on-demand Flight Execution may produce many Flight Logs.
 * - Created by the scheduler for scheduled executions.
 * - Created by the aviator Launch action for on-demand executions.
 * - Updated by NAVProxy throughout the operational lifecycle.
 *
 * Scheduled Execution Workflow
 * ----------------------------
 * 1. The Flight Plan is submitted and accepted.
 * 2. A Flight Execution Record is created with a departure datetime.
 * 3. The scheduler identifies the execution as it enters pre-flight.
 * 4. The scheduler changes the Flight Execution status from active to
 *    dispatched.
 * 5. The scheduler creates one Flight Log in pre_flight status.
 * 6. NAVProxy performs pre-flight validation and runtime execution.
 * 7. The Flight Log records the outcome of the occurrence.
 *
 * The scheduler must only process Flight Execution Records where:
 *
 *     requested_departure_utc IS NOT NULL
 *
 * On-Demand Execution Workflow
 * ----------------------------
 * 1. The Flight Plan is submitted and accepted.
 * 2. A reusable Flight Execution Record is created with a NULL departure.
 * 3. The accepted, published Flight Plan displays a Launch operation.
 * 4. The aviator selects Launch.
 * 5. A new Flight Log is created in pre_flight status.
 * 6. NAVProxy immediately begins the pre-flight process.
 * 7. The Flight Execution Record remains active after the occurrence.
 *
 * The scheduler must never process Flight Execution Records where:
 *
 *     requested_departure_utc IS NULL
 *
 * Flight Log Status
 * -----------------
 * pre_flight
 *     The occurrence has been created and NAVProxy is performing operational
 *     preparation and runtime validation.
 *
 * in_flight
 *     The aircraft has departed and the flight is underway.
 *
 * completed
 *     The flight occurrence completed normally.
 *
 * aborted
 *     The occurrence was intentionally stopped before normal completion.
 *
 * failed
 *     The occurrence could not proceed or complete because of an operational
 *     or technical failure.
 *
 * Concurrency and Duplicate Prevention
 * ------------------------------------
 * Only one nonterminal Flight Log may exist for a Flight Execution Record at
 * one time. This prevents duplicate Launch requests, overlapping scheduler
 * runs, and multiple NAVProxy instances from operating against the same
 * execution concurrently.
 *
 * A scheduled Flight Execution may produce only one Flight Log. Reusable
 * on-demand executions are excluded from this restriction because their
 * scheduled_departure_utc value is NULL.
 *
 * Indexing Strategy
 * -----------------
 * The indexes defined below support:
 *
 * - Flight Log lookup by primary key.
 * - Flight history for a Flight Execution Record.
 * - Flight history for an Aviator.
 * - Flight history for an Aircraft.
 * - Operational queries by Flight Log status.
 * - Recent-flight and administrative activity queries.
 * - Prevention of concurrent occurrences for the same execution.
 * - Prevention of duplicate scheduled dispatch.
 *
 * Design Philosophy
 * -----------------
 *
 *     Flight Plan      = Aviator intent
 *     Flight Execution = Accepted operational contract
 *     Flight Log       = Actual operational occurrence and history
 *
 * Additional timestamps, failure details, telemetry references, controller
 * diagnostics, and mission statistics may be added later as NAVProxy and
 * operational requirements become concrete.
 *
 ******************************************************************************/

CREATE TABLE flight_log (
    /*
     * Unique identifier for one actual flight occurrence or launch attempt.
     *
     * DroneNav uses UUID identifiers for persistent operational entities.
     * The application should generate this value using the project's selected
     * UUIDv7 implementation before inserting the row.
     */
    flight_log_id UUID PRIMARY KEY DEFAULT uuidv7(),

    /*
     * References the accepted Flight Execution Record used for this occurrence.
     *
     * A scheduled Flight Execution normally has one Flight Log.
     * A reusable on-demand Flight Execution may have many Flight Logs over time.
     */
    flight_execution_id UUID NOT NULL,

    /*
     * Identifies the Aviator responsible for this flight occurrence.
     *
     * This value is copied from the accepted execution context so that flight
     * history can be queried directly by Aviator without reconstructing the
     * complete governance relationship.
     */
    aviator_id UUID NOT NULL,

    /*
     * Identifies the Aircraft used for this flight occurrence.
     *
     * This value is copied from the accepted execution context so that aircraft
     * operational history can be queried directly.
     */
    aircraft_id UUID NOT NULL,

    /*
     * Accepted scheduled departure time for this occurrence, expressed as an
     * absolute UTC-aware timestamp.
     *
     * Non-NULL:
     *     The occurrence was created from a scheduled Flight Execution.
     *
     * NULL:
     *     The occurrence was launched from a reusable on-demand Flight
     *     Execution.
     */
    scheduled_departure_utc TIMESTAMPTZ NULL,

    /*
     * Current runtime state of this individual flight occurrence.
     *
     * This status belongs to the Flight Log and is managed operationally by
     * NAVProxy. It must not be confused with execution_status on the reusable
     * or scheduled Flight Execution Record.
     */
    flight_log_status VARCHAR(32) NOT NULL
        DEFAULT 'pre_flight',

    /*
     * Time at which this particular occurrence was requested.
     *
     * For scheduled flights, this is when the scheduler dispatched the
     * execution into pre-flight.
     *
     * For on-demand flights, this is when the Aviator selected Launch.
     *
     * This value is distinct from scheduled_departure_utc.
     */
    launch_requested_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    /*
     * Standard audit timestamp recording when the Flight Log row was created.
     */
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    /*
     * Standard audit timestamp recording the most recent modification.
     *
     * Application code is responsible for updating this value whenever the
     * Flight Log status or other mutable operational data changes.
     */
    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    /*
     * A Flight Log cannot exist without its associated Flight Execution Record.
     *
     * RESTRICT prevents an accepted operational contract from being removed
     * while operational history still references it.
     */
    CONSTRAINT fk_flight_log_execution
        FOREIGN KEY (flight_execution_id)
        REFERENCES flight_executions (flight_execution_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    /*
     * Restricts the initial Phase 2 Flight Log lifecycle to the explicitly
     * supported operational states.
     *
     * Additional states should be added only when implementation demonstrates
     * a concrete operational requirement.
     */
    CONSTRAINT chk_flight_log_status
        CHECK (
            flight_log_status IN (
                'pre_flight',
                'in_flight',
                'completed',
                'aborted',
                'failed'
            )
        )
);

/*
 * Supports Flight Execution history queries such as:
 *
 *     SELECT *
 *     FROM flight_log
 *     WHERE flight_execution_id = :flight_execution_id
 *     ORDER BY created_at DESC;
 *
 * This index also supports locating the most recent occurrence associated with
 * a reusable or scheduled Flight Execution Record.
 */
CREATE INDEX idx_flight_log_execution_created
    ON flight_log (
        flight_execution_id,
        created_at DESC
    );

/*
 * Supports Aviator flight-history queries ordered from newest to oldest.
 */
CREATE INDEX idx_flight_log_aviator
    ON flight_log (
        aviator_id,
        created_at DESC
    );

/*
 * Supports Aircraft operational-history and maintenance-analysis queries
 * ordered from newest to oldest.
 */
CREATE INDEX idx_flight_log_aircraft
    ON flight_log (
        aircraft_id,
        created_at DESC
    );

/*
 * Supports operational queries that locate Flight Logs by their current
 * lifecycle state, including pre-flight and in-flight monitoring.
 */
CREATE INDEX idx_flight_log_status
    ON flight_log (
        flight_log_status
    );

/*
 * Supports recent-flight dashboards, administrative review, troubleshooting,
 * and operational activity reports.
 */
CREATE INDEX idx_flight_log_created
    ON flight_log (
        created_at DESC
