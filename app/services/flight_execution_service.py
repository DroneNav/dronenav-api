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
Flight Execution API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-08

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from app.models.flight_band_model import select_active_flight_band_records_by_class

from app.services.geospatial_validation_service import (
    validate_operational_geospatial_data,
)
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.exc import IntegrityError

from app.config.constants import (
    EXECUTION_STATUS_ACTIVE,
    VALID_FLIGHT_CLASSES,
)

from app.models.droneport_model import select_droneport
from app.models.flight_execution_model import (
    insert_flight_execution_record,
    select_flight_execution_by_flight_plan,
    claim_scheduled_flight_execution,
    release_scheduled_flight_execution,
    cancel_flight_execution,
    claim_reusable_flight_execution,
    select_flight_executions,
    select_flight_execution,
)
from app.models.site_model import select_site

from app.services.timezone_service import (
    resolve_droneport_timezone,
    resolve_site_timezone,
)

import subprocess
import sys
import os

import logging


logger = logging.getLogger(__name__)


def create_flight_execution(data):
    if not isinstance(data, dict):
        return rejected_response([
            {
                "field": None,
                "code": "invalid_payload",
                "message": (
                    "Flight Execution submission must be a JSON object."
                ),
            }
        ])

    flight_plan_id = data.get("flight_plan_id")

    # A Flight Plan may be translated into only one
    # Flight Execution Record.
    if flight_plan_id not in (None, ""):
        existing_record = (
            select_flight_execution_by_flight_plan(
                str(flight_plan_id)
            )
        )

        if existing_record is not None:
            return accepted_response(
                existing_record,
                status_code=200,
            )

    if data.get("force_reject") is True:
        return rejected_response([
            {
                "field": "flight_class",
                "code": "flight_band_unavailable",
                "message": (
                    "No active Flight Band is available for this "
                    "flight class at the requested execution time."
                ),
            }
        ])

    operational_timezone = resolve_operational_timezone(data)

    if operational_timezone is None:
        return rejected_response([
            {
                "field": "origin_site_id",
                "code": "operational_timezone_unavailable",
                "message": (
                    "The operational timezone could not be resolved "
                    "from the departure DronePort or origin Site."
                ),
            }
        ])

    errors = validate_flight_execution_submission(data, operational_timezone)

    if errors:
        return rejected_response(errors)

    requested_departure_datetime = None

    if data["requested_departure_datetime"] is not None:
        requested_departure_datetime = (
            _parse_requested_departure_datetime(
                data["requested_departure_datetime"]
            )
        )

    flight_execution_data = {
        "flight_plan_id": str(data["flight_plan_id"]),
        "authority_id": str(data["authority_id"]),
        "aviator_id": str(data["aviator_id"]),
        "aircraft_id": str(data["aircraft_id"]),
        "flight_class": data["flight_class"],
        "origin_site_id": str(data["origin_site_id"]),
        "destination_site_id": str(
            data["destination_site_id"]
        ),
        "departure_droneport_id": (
            str(data["departure_droneport_id"])
            if data["departure_droneport_id"] is not None
            else None
        ),
        "arrival_droneport_id": (
            str(data["arrival_droneport_id"])
            if data["arrival_droneport_id"] is not None
            else None
        ),
        "requested_departure_datetime":
            requested_departure_datetime,
        "flight_termination_datetime": None,
        "operational_timezone": operational_timezone,
        "execution_status": EXECUTION_STATUS_ACTIVE,
        "route_ids": [
            str(route_id)
            for route_id in data["flight_path_ids"]
        ],
    }

    try:
        flight_execution = insert_flight_execution_record(
            flight_execution_data
        )

    except IntegrityError:
        # Protect against two concurrent submissions of the
        # same immutable Flight Plan.
        existing_record = (
            select_flight_execution_by_flight_plan(
                str(data["flight_plan_id"])
            )
        )

        if existing_record is not None:
            return accepted_response(
                existing_record,
                status_code=200,
            )

        raise

    return accepted_response(
        flight_execution,
        status_code=201,
    )


def validate_flight_execution_submission(data, operational_timezone):
    errors = []

    required_fields = [
        "flight_plan_id",
        "authority_id",
        "aviator_id",
        "aircraft_id",
        "flight_class",
        "origin_site_id",
        "destination_site_id",
        "requested_departure_datetime",
        "departure_droneport_id",
        "arrival_droneport_id",
        "flight_path_ids",
        "submitted_by",
    ]

    for field in required_fields:
        if field not in data:
            errors.append({
                "field": field,
                "code": "missing_required_field",
                "message": f"Missing required field: {field}.",
            })

    # Later validation accesses required dictionary keys directly.
    if errors:
        return errors

    if data["flight_class"] not in VALID_FLIGHT_CLASSES:
        errors.append({
            "field": "flight_class",
            "code": "invalid_flight_class",
            "message": "flight_class is not valid.",
        })

    active_flight_bands = (
        select_active_flight_band_records_by_class(
            data["flight_class"]
        )
    )

    if not active_flight_bands:
        errors.append({
            "field": "flight_class",
            "code": "flight_band_unavailable",
            "message": (
                "No active Flight Band is available for this "
                "flight class."
            ),
        })
    else:
        departure_error = (
            validate_requested_departure_datetime(
                data["requested_departure_datetime"],
                operational_timezone,
                active_flight_bands,
            )
        )

        if departure_error:
            errors.append(departure_error)

    nullable_fields = [
        "requested_departure_datetime",
        "departure_droneport_id",
        "arrival_droneport_id",
    ]

    for field in nullable_fields:
        if data[field] == "":
            errors.append({
                "field": field,
                "code": "invalid_null_value",
                "message": (
                    f"{field} must be null or a valid value, "
                    "not an empty string."
                ),
            })

    if not isinstance(data["flight_path_ids"], list):
        errors.append({
            "field": "flight_path_ids",
            "code": "invalid_list",
            "message": "flight_path_ids must be an array.",
        })
    else:
        for route_id in data["flight_path_ids"]:
            if route_id in ("", None):
                errors.append({
                    "field": "flight_path_ids",
                    "code": "invalid_route_id",
                    "message": (
                        "flight_path_ids must contain only "
                        "non-empty Route IDs."
                    ),
                })

    # Do not evaluate flight structure until the basic payload
    # values and flight_path_ids type have been validated.
    if errors:
        return errors

    requested_departure_datetime = data[
        "requested_departure_datetime"
    ]
    departure_droneport_id = data[
        "departure_droneport_id"
    ]
    arrival_droneport_id = data[
        "arrival_droneport_id"
    ]
    flight_path_ids = data["flight_path_ids"]

    # A reusable execution cannot prescribe droneports or a route.
    if requested_departure_datetime is None:
        if departure_droneport_id is not None:
            errors.append({
                "field": "departure_droneport_id",
                "code": "invalid_reusable_flight_structure",
                "message": (
                    "departure_droneport_id must be null when "
                    "requested_departure_datetime is null."
                ),
            })

        if arrival_droneport_id is not None:
            errors.append({
                "field": "arrival_droneport_id",
                "code": "invalid_reusable_flight_structure",
                "message": (
                    "arrival_droneport_id must be null when "
                    "requested_departure_datetime is null."
                ),
            })

        if flight_path_ids:
            errors.append({
                "field": "flight_path_ids",
                "code": "invalid_reusable_flight_structure",
                "message": (
                    "flight_path_ids must be an empty array when "
                    "requested_departure_datetime is null."
                ),
            })

    # A scheduled execution must prescribe both droneports
    # and at least one Route.
    else:
        if departure_droneport_id is None:
            errors.append({
                "field": "departure_droneport_id",
                "code": "missing_scheduled_flight_field",
                "message": (
                    "departure_droneport_id is required when "
                    "requested_departure_datetime is provided."
                ),
            })

        if arrival_droneport_id is None:
            errors.append({
                "field": "arrival_droneport_id",
                "code": "missing_scheduled_flight_field",
                "message": (
                    "arrival_droneport_id is required when "
                    "requested_departure_datetime is provided."
                ),
            })

        if not flight_path_ids:
            errors.append({
                "field": "flight_path_ids",
                "code": "missing_scheduled_flight_field",
                "message": (
                    "flight_path_ids must contain at least one "
                    "Route when requested_departure_datetime "
                    "is provided."
                ),
            })

    # Do not perform database relationship validation when the
    # Flight Execution structure is invalid.
    if errors:
        return errors

    geospatial_errors = (
        validate_operational_geospatial_data(data)
    )
    errors.extend(geospatial_errors)

    return errors


def accepted_response(
    flight_execution,
    status_code=201,
):
    return {
        "status": "accepted",
        "message": "Flight plan accepted.",
        "flight_execution_record_id": str(
            flight_execution["flight_execution_id"]
        ),
        "flight_plan_status": "submitted",
    }, status_code


def rejected_response(errors):

    return {
        "status": "rejected",
        "message": "Flight plan rejected.",
        "flight_plan_status": "draft",
        "errors": errors,
    }, 422


def validate_requested_departure_datetime(
    requested_departure_datetime,
    operational_timezone,
    active_flight_bands,
):
    """
    Validate an optional requested departure against active Flight Bands.

    A null value means no specific departure time was requested. The Flight
    Execution may be scheduled whenever an active Flight Band permits it.
    """

    if requested_departure_datetime is None:
        return None

    requested_datetime = _parse_requested_departure_datetime(
        requested_departure_datetime
    )

    if requested_datetime is None:
        return {
            "field": "requested_departure_datetime",
            "code": "invalid_departure_datetime",
            "message": (
                "requested_departure_datetime must be a valid "
                "ISO 8601 datetime with a timezone offset."
            ),
        }

    for flight_band in active_flight_bands:
        if _requested_departure_matches_band(
            requested_datetime,
            operational_timezone,
            flight_band,
        ):
            return None

    return {
        "field": "requested_departure_datetime",
        "code": "outside_flight_band_window",
        "message": (
            "The requested departure datetime is outside every active "
            "Flight Band window for this flight class."
        ),
    }


def resolve_operational_timezone(data):
    departure_droneport_id = data.get("departure_droneport_id")

    if departure_droneport_id is not None:
        droneport = select_droneport(departure_droneport_id)

        if droneport is None:
            return None

        return resolve_droneport_timezone(droneport)

    origin_site_id = data.get("origin_site_id")

    if not origin_site_id:
        return None

    site = select_site(origin_site_id)

    if site is None:
        return None

    return resolve_site_timezone(site)


def _parse_requested_departure_datetime(value):
    if not isinstance(value, str):
        return None

    normalized_value = value.strip()

    if not normalized_value:
        return None

    # Python 3.11 accepts ISO 8601 offsets through fromisoformat().
    # Normalize a trailing Z to the equivalent UTC offset.
    if normalized_value.endswith("Z"):
        normalized_value = normalized_value[:-1] + "+00:00"

    try:
        parsed_datetime = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None

    # Require an aware datetime so its meaning is unambiguous when converted
    # into the operational timezone of the Flight Execution.
    if (
        parsed_datetime.tzinfo is None
        or parsed_datetime.utcoffset() is None
    ):
        return None

    return parsed_datetime


def _requested_departure_matches_band(
    requested_datetime,
    operational_timezone,
    flight_band,
):
    try:
        operational_timezone_info = ZoneInfo(
            operational_timezone
        )
    except ZoneInfoNotFoundError:
        return False

    local_datetime = requested_datetime.astimezone(
        operational_timezone_info 
    )

    day_of_week = _to_flight_band_day_of_week(local_datetime)

    allowed_days = {
        int(day)
        for day in flight_band["days"]
    }

    if day_of_week not in allowed_days:
        return False

    requested_time = local_datetime.time().replace(
        second=0,
        microsecond=0,
        tzinfo=None,
    )

    start_time = flight_band["start_time"]
    end_time = flight_band["end_time"]

    return start_time <= requested_time <= end_time


def _to_flight_band_day_of_week(value):
    """
    Convert Python weekday numbering to DroneNav numbering.

    Python:
        Monday = 0
        Sunday = 6

    DroneNav:
        Sunday = 0
        Monday = 1
        Saturday = 6
    """

    return (value.weekday() + 1) % 7

# ----------------------------------------------------------------------
# NAVProxy Launcher
# ----------------------------------------------------------------------

def launch_navproxy(
    flight_execution_id,
    flight_id,
    execution_mode="scheduled",
):
    """
    Launch the Phase 2 NAVProxy simulator as a separate process.
    """

    logger.info(
        "Launching NAVProxy simulator: execution=%s flight=%s",
        flight_execution_id,
        flight_id,
    )

    navproxy_project_dir = os.environ["NAVPROXY_PROJECT_DIR"]

    navproxy_log_path = os.environ.get(
        "NAVPROXY_LOG_PATH",
        os.path.expanduser("~/logs/navproxy.log"),
    )

    with open(navproxy_log_path, "a", encoding="utf-8") as log_file:
        subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-m",
                "app.navproxy",
                "--flight-execution-id",
                str(flight_execution_id),
                "--flight-id",
                str(flight_id),
                "--execution-mode",
                execution_mode,
            ],
            cwd=navproxy_project_dir,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


# ----------------------------------------------------------------------
# Flight Launch
# ----------------------------------------------------------------------
def launch_scheduled_flight_execution(
    flight_execution_id,
    aviator_id,
    aircraft_id,
):
    flight = claim_scheduled_flight_execution(
        flight_execution_id,
        aviator_id,
        aircraft_id,
    )

    if flight is None:
        return {
            "status": "rejected",
            "message": (
                "Flight Execution could not be launched. "
                "It may already be active or unavailable."
            ),
        }, 409

    launch_navproxy(
        flight_execution_id,
        flight["flight_id"],
    )

    return {
        "status": "accepted",
        "message": "Flight launched.",
        "flight_execution_id": str(flight_execution_id),
        "flight_id": str(flight["flight_id"]),
    }, 200


def release_scheduled_flight_execution_service(
    flight_execution_id,
):
    """
    Return a preflight-failed scheduled Flight Execution to active status.
    """

    released_execution = release_scheduled_flight_execution(
        flight_execution_id
    )

    if released_execution is None:
        return {
            "status": "error",
            "message": (
                "Flight Execution could not be released because it is "
                "not a dispatched, unterminated scheduled execution."
            ),
        }, 409

    return {
        "status": "success",
        "flight_execution": released_execution,
    }, 200


def cancel_flight_execution_service(
    flight_execution_id,
):
    """
    Cancels a Flight Execution Record.
    """

    cancelled_execution = cancel_flight_execution(
        flight_execution_id
    )

    if cancelled_execution is None:
        return {
            "status": "error",
            "message": (
                "Flight Execution could not be cancelled because it is "
                "not an active execution."
            ),
        }, 409

    return {
        "status": "success",
        "flight_execution": cancelled_execution,
    }, 200


def launch_reusable_flight_execution(
    flight_execution_id,
    aviator_id,
    aircraft_id,
):
    flight = claim_reusable_flight_execution(
        flight_execution_id,
        aviator_id,
        aircraft_id,
    )

    if flight is None:
        return {
            "status": "rejected",
            "message": (
                "Flight Execution could not be launched. "
                "It may already be active or unavailable."
            ),
        }, 409

    launch_navproxy(
        flight_execution_id,
        flight["flight_id"],
        execution_mode="reusable",
    )

    return {
        "status": "accepted",
        "message": "Flight launched.",
        "flight_execution_id": str(flight_execution_id),
        "flight_id": str(flight["flight_id"]),
    }, 200


def get_flight_execution(flight_execution_id):

    flight_execution = select_flight_execution(
        flight_execution_id
    )

    if flight_execution is None:
        return {
            "error": "Flight Execution Record not found."
        }, 404

    return format_flight_execution(
        flight_execution
    ), 200


def list_flight_executions(
    requested_departure_datetime,
):
    if requested_departure_datetime not in (
        None,
        "null",
        "not_null",
    ):
        return {
            "error": (
                "requested_departure_datetime must be "
                "'null', 'not_null', or omitted."
            )
        }, 400

    flight_executions = select_flight_executions(
        requested_departure_datetime=requested_departure_datetime
    )

    flight_executions = normalize_flight_executions(
        flight_executions
    )

    return flight_executions, 200


def normalize_flight_executions(rows):
    return [
        format_flight_execution(row)
        for row in rows
    ]


def format_flight_execution(row):
    return {
        "flight_execution_id": str(
            row["flight_execution_id"]
        ),
        "authority_id": str(
            row["authority_id"]
        ),
        "aviator_id": str(
            row["aviator_id"]
        ),
        "aircraft_id": str(
            row["aircraft_id"]
        ),
        "flight_class": row["flight_class"],
        "origin_site_id": str(
            row["origin_site_id"]
        ),
        "destination_site_id": str(
            row["destination_site_id"]
        ),
        "departure_droneport_id": (
            str(row["departure_droneport_id"])
            if row["departure_droneport_id"]
            else None
        ),
        "arrival_droneport_id": (
            str(row["arrival_droneport_id"])
            if row["arrival_droneport_id"]
            else None
        ),
        "route_ids": [
          str(route_id)
          for route_id in row["route_ids"]
        ],
        "requested_departure_datetime": (
            row["requested_departure_datetime"].isoformat()
            if row["requested_departure_datetime"]
            else None
        ),
        "operational_timezone": row[
            "operational_timezone"
        ],
    }


