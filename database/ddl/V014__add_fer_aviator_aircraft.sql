-- Remove the test Flight Execution Records.
DELETE FROM flight_execution_routes;

DELETE FROM flight_log;

DELETE FROM flight;

DELETE FROM flight_executions;

-- Add the new required columns.
ALTER TABLE flight_executions
ADD COLUMN aviator_id UUID NOT NULL;

ALTER TABLE flight_executions
ADD COLUMN aircraft_id UUID NOT NULL;
