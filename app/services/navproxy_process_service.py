"""
Simulated NAVProxy flight process for DroneNav Phase 2 testing.

This service operates on an existing Flight Log created by the launch or
scheduler workflow. It simulates a two-minute flight:

    30 seconds  pre-flight
    90 seconds  in-flight

Scheduled Flight Executions are completed after landing. Reusable on-demand
Flight Executions remain active so that they may be launched again.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import requests

import argparse
import logging
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from app.config.database import engine
from app.config.constants import (
    EXECUTION_STATUS_COMPLETED,
    EXECUTION_STATUS_DISPATCHED,
    FLIGHT_LOG_STATUS_COMPLETED,
    FLIGHT_LOG_STATUS_IN_FLIGHT,
    FLIGHT_LOG_STATUS_PRE_FLIGHT,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_PREFLIGHT_SECONDS = 30
DEFAULT_FLIGHT_SECONDS = 90

DRUPAL_STATUS_CALLBACK_URL = os.getenv(
    "DRUPAL_STATUS_CALLBACK_URL",
    "https://dronenav.org/api/flight-plans/status-callback",
)

DRUPAL_STATUS_CALLBACK_TOKEN = os.getenv(
    "DRUPAL_STATUS_CALLBACK_TOKEN"
)

DRUPAL_STATUS_CALLBACK_TIMEOUT_SECONDS = int(
    os.getenv(
        "DRUPAL_STATUS_CALLBACK_TIMEOUT_SECONDS",
        "10",
    )
)

FLIGHT_PLAN_STATUS_ACTIVE = "active"
FLIGHT_PLAN_STATUS_COMPLETED = "completed"
FLIGHT_PLAN_STATUS_SUBMITTED = "submitted"


@dataclass(frozen=True)
class FlightProcessContext:
    flight_execution_id: str
    flight_log_id: str
    is_scheduled: bool


def run_navproxy_process(
    flight_execution_id: str,
    flight_log_id: str,
    preflight_seconds: int = DEFAULT_PREFLIGHT_SECONDS,
    flight_seconds: int = DEFAULT_FLIGHT_SECONDS,
) -> None:
    """Simulate one NAVProxy-controlled aircraft flight."""

    preflight_seconds = _validate_wait_seconds(
        "preflight_seconds",
        preflight_seconds,
    )
    flight_seconds = _validate_wait_seconds(
        "flight_seconds",
        flight_seconds,
    )

    context = _load_and_validate_context(
        flight_execution_id=flight_execution_id,
        flight_log_id=flight_log_id,
    )

    LOGGER.info(
        "NAVProxy simulation started: execution=%s log=%s scheduled=%s",
        context.flight_execution_id,
        context.flight_log_id,
        context.is_scheduled,
    )

    LOGGER.info(
        "Pre-flight checks in progress for %s second(s).",
        preflight_seconds,
    )
    time.sleep(preflight_seconds)

    _start_flight(context)

    LOGGER.info(
        "Aircraft is in flight for %s second(s).",
        flight_seconds,
    )
    time.sleep(flight_seconds)

    _complete_flight(context)

    LOGGER.info(
        "NAVProxy simulation completed: execution=%s log=%s",
        context.flight_execution_id,
        context.flight_log_id,
    )


def _load_and_validate_context(
    flight_execution_id: str,
    flight_log_id: str,
) -> FlightProcessContext:
    """Validate the supplied Flight Execution and Flight Log pair."""

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    fe.flight_execution_id,
                    fe.requested_departure_datetime,
                    fe.execution_status,
                    fl.flight_log_id,
                    fl.flight_log_status
                FROM flight_executions AS fe
                JOIN flight_log AS fl
                  ON fl.flight_execution_id = fe.flight_execution_id
                WHERE fe.flight_execution_id = :flight_execution_id
                  AND fl.flight_log_id = :flight_log_id
            """),
            {
                "flight_execution_id": flight_execution_id,
                "flight_log_id": flight_log_id,
            },
        )
        row = result.mappings().first()

    if row is None:
        raise ValueError(
            "The Flight Execution and Flight Log combination was not found."
        )

    if row["flight_log_status"] != FLIGHT_LOG_STATUS_PRE_FLIGHT:
        raise ValueError(
            "The Flight Log must be in pre_flight status before launch."
        )

    is_scheduled = row["requested_departure_datetime"] is not None

    if is_scheduled and row["execution_status"] != EXECUTION_STATUS_DISPATCHED:
        raise ValueError(
            "A scheduled Flight Execution must be dispatched before launch."
        )

    return FlightProcessContext(
        flight_execution_id=str(row["flight_execution_id"]),
        flight_log_id=str(row["flight_log_id"]),
        is_scheduled=is_scheduled,
    )


def _start_flight(context: FlightProcessContext) -> None:
    """Simulate takeoff by changing the Flight Log to in_flight."""

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE flight_log
                SET
                    flight_log_status = :in_flight_status,
                    updated_at = NOW()
                WHERE flight_log_id = :flight_log_id
                  AND flight_execution_id = :flight_execution_id
                  AND flight_log_status = :pre_flight_status
                RETURNING flight_log_id
            """),
            {
                "flight_log_id": context.flight_log_id,
                "flight_execution_id": context.flight_execution_id,
                "pre_flight_status": FLIGHT_LOG_STATUS_PRE_FLIGHT,
                "in_flight_status": FLIGHT_LOG_STATUS_IN_FLIGHT,
            },
        )

        if result.scalar_one_or_none() is None:
            raise RuntimeError(
                "Flight Log could not transition from pre_flight to in_flight."
            )

    LOGGER.info(
        "Takeoff recorded: Flight Log %s is now in_flight.",
        context.flight_log_id,
    )

    _notify_drupal_flight_plan_status(
        flight_execution_id=context.flight_execution_id,
        status=FLIGHT_PLAN_STATUS_ACTIVE,
    )


def _complete_flight(context: FlightProcessContext) -> None:
    """Simulate landing and complete the appropriate records."""

    with engine.begin() as connection:
        log_result = connection.execute(
            text("""
                UPDATE flight_log
                SET
                    flight_log_status = :completed_status,
                    updated_at = NOW()
                WHERE flight_log_id = :flight_log_id
                  AND flight_execution_id = :flight_execution_id
                  AND flight_log_status = :in_flight_status
                RETURNING flight_log_id
            """),
            {
                "flight_log_id": context.flight_log_id,
                "flight_execution_id": context.flight_execution_id,
                "in_flight_status": FLIGHT_LOG_STATUS_IN_FLIGHT,
                "completed_status": FLIGHT_LOG_STATUS_COMPLETED,
            },
        )

        if log_result.scalar_one_or_none() is None:
            raise RuntimeError(
                "Flight Log could not transition from in_flight to completed."
            )

        if context.is_scheduled:
            execution_result = connection.execute(
                text("""
                    UPDATE flight_executions
                    SET
                        execution_status = :completed_status,
                        flight_termination_datetime = NOW(),
                        updated_at = NOW()
                    WHERE flight_execution_id = :flight_execution_id
                      AND execution_status = :dispatched_status
                    RETURNING flight_execution_id
                """),
                {
                    "flight_execution_id": context.flight_execution_id,
                    "dispatched_status": EXECUTION_STATUS_DISPATCHED,
                    "completed_status": EXECUTION_STATUS_COMPLETED,
                },
            )

            if execution_result.scalar_one_or_none() is None:
                raise RuntimeError(
                    "Scheduled Flight Execution could not transition from "
                    "dispatched to completed."
                )

    LOGGER.info(
        "Landing recorded: Flight Log %s is now completed.",
        context.flight_log_id,
    )

    if context.is_scheduled:
        LOGGER.info(
            "Scheduled Flight Execution %s is now completed.",
            context.flight_execution_id,
        )
    #
    # Notify Drupal of the Flight Plan lifecycle transition.
    #
    if context.is_scheduled:
        callback_status = FLIGHT_PLAN_STATUS_COMPLETED
    else:
        callback_status = FLIGHT_PLAN_STATUS_SUBMITTED

    _notify_drupal_flight_plan_status(
        flight_execution_id=context.flight_execution_id,
        status=callback_status,
    )


def _validate_wait_seconds(name: str, value: Any) -> int:
    try:
        normalized_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer.") from exc

    if normalized_value < 0:
        raise ValueError(f"{name} must not be negative.")

    return normalized_value


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate a DroneNav NAVProxy flight process.",
    )
    parser.add_argument(
        "--flight-execution-id",
        required=True,
        help="Flight Execution UUID.",
    )
    parser.add_argument(
        "--flight-log-id",
        required=True,
        help="Flight Log UUID created during claim.",
    )
    parser.add_argument(
        "--preflight-seconds",
        type=int,
        default=DEFAULT_PREFLIGHT_SECONDS,
        help="Pre-flight wait in seconds. Default: 30.",
    )
    parser.add_argument(
        "--flight-seconds",
        type=int,
        default=DEFAULT_FLIGHT_SECONDS,
        help="In-flight wait in seconds. Default: 90.",
    )
    return parser.parse_args()


def _notify_drupal_flight_plan_status(
    flight_execution_id: str,
    status: str,
) -> None:
    """Notify Drupal of a Flight Plan lifecycle status transition."""

    if not DRUPAL_STATUS_CALLBACK_TOKEN:
        raise RuntimeError(
            "DRUPAL_STATUS_CALLBACK_TOKEN is not configured."
        )

    occurred_at = datetime.now(timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )

    response = requests.post(
        DRUPAL_STATUS_CALLBACK_URL,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-DroneNav-Callback-Token": (
                DRUPAL_STATUS_CALLBACK_TOKEN
            ),
        },
        json={
            "flight_execution_id": flight_execution_id,
            "status": status,
            "occurred_at": occurred_at,
        },
        timeout=DRUPAL_STATUS_CALLBACK_TIMEOUT_SECONDS,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError:
        LOGGER.error(
            "Drupal Flight Plan status callback failed: "
            "execution=%s status=%s http_status=%s response=%s",
            flight_execution_id,
            status,
            response.status_code,
            response.text,
        )
        raise

    LOGGER.info(
        "Drupal Flight Plan status callback succeeded: "
        "execution=%s status=%s",
        flight_execution_id,
        status,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    arguments = _parse_arguments()

    run_navproxy_process(
        flight_execution_id=arguments.flight_execution_id,
        flight_log_id=arguments.flight_log_id,
        preflight_seconds=arguments.preflight_seconds,
        flight_seconds=arguments.flight_seconds,
    )


if __name__ == "__main__":
    main()


