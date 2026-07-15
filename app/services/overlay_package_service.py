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
Governance overlay package business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-06-12

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from app.models.overlay_package_model import (
    survey_overlay_package_record,
    select_unsubmitted_site_package_surveys,
    survey_overlay_record,
    expire_survey_overlay_package_record,
    expire_survey_overlay_record,
    approve_site_review_package_record,
    reject_site_review_package_record,
    select_unapproved_site_package_reviews,
)

from app.models.droneport_model import (
    select_droneports_by_site,
)

from app.models.site_model import (
    select_site,
    update_site_timezone_record,
)

from app.services.timezone_service import (
    resolve_authoritative_site_timezone,
)


def survey_overlay_package(site_id, data):

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return None, "Survey payload must be an object"

    surveyed_by = data.get("surveyed_by")

    if surveyed_by in ("", None):
        return None, "Missing required field: surveyed_by"

    missing, error = select_unsubmitted_site_package_surveys(
        site_id=site_id
    )

    if error:
        return None, error

    if has_unsubmitted_site_package_surveys(missing):
        return None, build_unsubmitted_site_package_error(missing)

    site = select_site(site_id)

    if site is None:
        return None, "Site not found"

    droneports = select_droneports_by_site(site_id)

    timezone, timezone_condition = resolve_authoritative_site_timezone(
        site=site,
        droneports=droneports,
    )

    if timezone is None:
        return None, "Unable to determine the Site operational timezone"

    timezone_result, error = update_site_timezone_record(
        site_id=site_id,
        timezone=timezone,
    )

    if error:
        return None, error

    result, error = survey_overlay_package_record(
        site_id=site_id,
        surveyed_by=surveyed_by,
    )

    if error:
        return None, error

    return result, None

def has_unsubmitted_site_package_surveys(missing):

    return (
        bool(missing.get("site"))
        or bool(missing.get("zones"))
        or bool(missing.get("droneports"))
        or bool(missing.get("routes"))
    )

def build_unsubmitted_site_package_error(missing):

    return {
        "message": "Site package cannot be submitted. One or more required surveys have not been submitted.",
        "missing": missing,
    }


def survey_overlay(overlay_type, overlay_id, data):

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return None, "Survey payload must be an object"

    surveyed_by = data.get("surveyed_by")

    if surveyed_by in ("", None):
        return None, "Missing required field: surveyed_by"

    normalized_overlay_type = normalize_overlay_type(overlay_type)

    if not normalized_overlay_type:
        return None, "Invalid overlay type"

    result, error = survey_overlay_record(
        overlay_type=normalized_overlay_type,
        overlay_id=overlay_id,
        surveyed_by=surveyed_by,
    )

    if error:
        return None, error

    return result, None


def expire_survey_overlay_package(site_id):

    result, error = expire_survey_overlay_package_record(
        site_id=site_id,
    )

    if error:
        return None, error

    return result, None


def expire_survey_overlay(overlay_type, overlay_id):

    normalized_overlay_type = normalize_overlay_type(overlay_type)

    if not normalized_overlay_type:
        return None, "Invalid overlay type"

    result, error = expire_survey_overlay_record(
        overlay_type=normalized_overlay_type,
        overlay_id=overlay_id,
    )

    if error:
        return None, error

    return result, None


def normalize_overlay_type(overlay_type):

    if overlay_type is None:
        return None

    overlay_type_map = {
        "site": "site",
        "zone": "zone",
        "zones": "zone",
        "droneport": "droneport",
        "droneports": "droneport",
        "route": "route",
        "routes": "route",
    }

    return overlay_type_map.get(
        overlay_type.lower()
    )


def approve_site_review_package(site_id, data):

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return None, "Review payload must be an object"

    reviewed_by = data.get("reviewed_by")

    if reviewed_by in ("", None):
        return None, "Missing required field: reviewed_by"

    unapproved, error = select_unapproved_site_package_reviews(
        site_id=site_id
    )

    if error:
        return None, error

    if has_unapproved_site_package_reviews(unapproved):
        return None, build_unapproved_site_package_error(unapproved)

    result, error = approve_site_review_package_record(
        site_id=site_id,
        reviewed_by=reviewed_by,
    )

    if error:
        return None, error

    return result, None

def has_unapproved_site_package_reviews(unapproved):

    return (
        bool(unapproved.get("site"))
        or bool(unapproved.get("zones"))
        or bool(unapproved.get("droneports"))
        or bool(unapproved.get("routes"))
    )


def build_unapproved_site_package_error(unapproved):

    return {
        "message": "Site package is not eligible for operational review. One or more required overlay reviews have not been approved.",
        "unapproved": unapproved,
    }

def reject_site_review_package(site_id, data):

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return None, "Review payload must be an object"

    reviewed_by = data.get("reviewed_by")

    if reviewed_by in ("", None):
        return None, "Missing required field: reviewed_by"

    review_comments = data.get("review_comments", "Rejected review")

    unapproved, error = select_unapproved_site_package_reviews(
        site_id=site_id
    )

    if error:
        return None, error

    if has_unapproved_site_package_reviews(unapproved):
        return None, build_unapproved_site_package_error(unapproved)

    result, error = reject_site_review_package_record(
        site_id=site_id,
        reviewed_by=reviewed_by,
        review_comments=review_comments,
    )

    if error:
        return None, error

    return result, None

