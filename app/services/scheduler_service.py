"""
DroneNav - Drone Navigation Network System
Copyright (C) 2026 DroneNav Project

This file is part of DroneNav.

DroneNav is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

DroneNav is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with DroneNav. If not, see https://www.gnu.org/licenses/.

Project:
DroneNav - Drone Navigation Network System

Repository:
https://github.com/DroneNav

License:
GNU Affero General Public License v3.0 (AGPL-3.0-or-later)

Purpose:
Execution Scheduler business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-22

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.


DroneNav Flight Execution Scheduler

Invoked by cron once per minute.

Responsibilities:
    1. Expire scheduled Flight Executions.
    2. Find Flight Executions ready for dispatch.
    3. Atomically claim each Flight Execution by creating a Flight Log.
    4. Launch a NAVProxy instance for each successfully claimed flight.
"""

import logging

from app.config.constants import (
    PREFLIGHT_WINDOW_MINUTES,
    EXPIRATION_GRACE_MINUTES,
)

from app.models.flight_execution_model import (
    expire_scheduled_flight_executions,
    select_flight_executions_ready_for_dispatch,
)

from app.services.flight_execution_service import (
    launch_scheduled_flight_execution,
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Scheduler
# ----------------------------------------------------------------------

def run_scheduler():
    """
    Executes one scheduler pass.
    """

    logger.info("Scheduler pass started.")

    #
    # Expire scheduled Flight Executions.
    #
    expire_scheduled_flight_executions(
        EXPIRATION_GRACE_MINUTES
    )

    #
    # Find Flight Executions ready for dispatch.
    #
    executions = select_flight_executions_ready_for_dispatch(
        PREFLIGHT_WINDOW_MINUTES,
        EXPIRATION_GRACE_MINUTES,
    )

    if not executions:

        logger.info("No Flight Executions ready for dispatch.")

        return

    logger.info(
        "Found %d Flight Execution(s) ready for dispatch.",
        len(executions),
    )

    for execution in executions:

        try:

            flight_log = launch_scheduled_flight_execution(
                execution["flight_execution_id"]
            )

            if flight_log is None:

                logger.info(
                    "Flight Execution %s already claimed.",
                    execution["flight_execution_id"],
                )

                continue

            logger.info(
                "Flight Execution %s dispatched.",
                execution["flight_execution_id"],
            )

        except Exception:

            logger.exception(
                "Failed dispatch of Flight Execution %s",
                execution["flight_execution_id"],
            )


# ----------------------------------------------------------------------
# Main Entry Point
# ----------------------------------------------------------------------

def main():
    run_scheduler()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    main()

