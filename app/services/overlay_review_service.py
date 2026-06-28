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
Governance overlay review business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-06-05

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from app.models.site_model import (
    select_site,
    approve_site,
    reject_site,
    submit_site,
    request_site_changes,
)

from app.models.zone_model import (
    select_zone,
    approve_zone,
    reject_zone,
    submit_zone,
    request_zone_changes,
)

from app.models.droneport_model import (
    select_droneport,
    approve_droneport,
    reject_droneport,
    submit_droneport,
    request_droneport_changes,
)

from app.models.route_model import (
    select_route,
    approve_route,
    reject_route,
    submit_route,
    request_route_changes,
)

from app.models.overlay_review_model import (
    select_overlay_review,
    select_overlay_reviews,
    select_overlay_notes,
    get_overlay_review_id,
    approve_overlay_review,
    reject_overlay_review,
    request_overlay_review_changes,
    submit_overlay_review,
    select_pending_reviews_count,
    select_pending_surveys_count,
    select_approved_reviews_count,
    select_rejected_reviews_count,
    select_revision_requested_count,
    select_site_count,
    select_zone_count,
    select_droneport_count,
    select_route_count,
)

from app.services.site_service import get_site_by_id, format_site
from app.services.zone_service import get_zone_by_id, format_zone
from app.services.droneport_service import get_droneport_by_id, format_droneport
from app.services.route_service import get_route_by_id, format_route

from app.config.constants import (
    VALID_OVERLAY_TYPES,
    VALID_REVIEW_STATUSES,
    VALID_SURVEY_STATUSES,
    REVIEW_STATUS_REVISIONS_REQUESTED,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_SUBMITTED,
    SURVEY_STATUS_SURVEYED,
    SURVEY_STATUS_APPROVED
)

from app.config.constants import (
    OVERLAY_TYPE_SITE,
    OVERLAY_TYPE_ZONE,
    OVERLAY_TYPE_DRONEPORT,
    OVERLAY_TYPE_ROUTE
)


def validate_overlay_review_payload(data):
    required_fields = [
        "overlay_id",
        "overlay_type",
        "review_status",
        "submitted_by",
        "reviewed_by",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    return None


def normalize_overlay_review_payload(data):
    return {
        "overlay_id": data["overlay_id"],
        "overlay_type": data["overlay_type"],
        "review_status": data["review_status"],
        "submitted_by": data["submitted_by"],
        "reviewed_by": data["reviewed_by"],
        "review_comments": data["review_comments"],
        "survey_status": data["survey_status"],
        "surveyed_by": data["surveyed_by"],
    }


def format_overlay_review(row):
    if row is None:
        return None

    return {
        "review_id": str(row["review_id"]),
        "overlay_id": str(row["overlay_id"]),
        "overlay_type": row["overlay_type"],
        "review_status": row["review_status"],
        "survey_status": row["survey_status"],
        "surveyed_by": row["surveyed_by"],
        "surveyed_at": row["surveyed_at"].isoformat()
            if row["surveyed_at"] else None,
        "submitted_by": row["submitted_by"],
        "submitted_at": row["submitted_at"].isoformat()
            if row["submitted_at"] else None,
        "reviewed_by": row["reviewed_by"],
        "reviewed_at": row["reviewed_at"].isoformat()
            if row["reviewed_at"] else None,
        "review_comments": row["review_comments"],
        "created_at": row.get("created_at").isoformat()
            if row.get("created_at") else None,
        "updated_at": row.get("updated_at").isoformat()
            if row.get("updated_at") else None,
    }


def format_overlay_review_summary(row):
    return {
        "review_id": str(row["review_id"]),
        "overlay_id": str(row["overlay_id"]),
        "overlay_type": row["overlay_type"],
        "review_status": row["review_status"],
        "survey_status": row["survey_status"],
        "surveyed_by": row["surveyed_by"],
        "surveyed_at": row["surveyed_at"].isoformat()
            if row["surveyed_at"] else None,
        "submitted_by": row["submitted_by"],
        "submitted_at": row["submitted_at"].isoformat()
            if row["submitted_at"] else None,
        "reviewed_by": row["reviewed_by"],
        "reviewed_at": row["reviewed_at"].isoformat()
            if row["reviewed_at"] else None,
        "review_comments": row["review_comments"],
        "created_at": row.get("created_at").isoformat()
            if row.get("created_at") else None,
        "updated_at": row.get("updated_at").isoformat()
            if row.get("updated_at") else None,
    }


def get_governance_metrics():
    pending = select_pending_reviews_count()
    approved = select_approved_reviews_count()
    rejected = select_rejected_reviews_count()
    requested = select_revision_requested_count()
    not_surveyed = select_pending_surveys_count()

    sites = select_site_count()
    zones = select_zone_count()
    droneports = select_droneport_count()
    routes = select_route_count()

    return {
        "review_counts": {
            "pending_review": pending,
            "not_surveyed": not_surveyed,
            "approved": approved,
            "rejected": rejected,
            "revisions_requested": requested,
        },
        "overlay_counts": {
            "site": sites,
            "zone": zones,
            "droneport": droneports,
            "route": routes,
        }
    }


def get_overlay_review_by_id(review_id):
    row = select_overlay_review(review_id)
    return format_overlay_review(row)


def get_overlay_reviews(filters):

    overlay_type = filters.get("overlay_type")
    review_status = filters.get("review_status")
    survey_status = filters.get("survey_status")

    if overlay_type and overlay_type not in VALID_OVERLAY_TYPES:
        return None, "Invalid overlay type"

    if review_status and review_status not in VALID_REVIEW_STATUSES:
        return None, "Invalid review status"

    if survey_status and survey_status not in VALID_SURVEY_STATUSES:
        return None, "Invalid survey status"

    rows = select_overlay_reviews(overlay_type, review_status, survey_status)

    return [format_overlay_review_summary(row) for row in rows], None


def get_overlay_history(overlay_id):

    return {
               "history": select_overlay_notes(overlay_id),
               "overlay_id": overlay_id
    }


def get_overlay_by_type_and_id(overlay_type, overlay_id):

    if overlay_type == OVERLAY_TYPE_SITE:
        row = select_site(overlay_id)
        return format_site(row)
    elif overlay_type == OVERLAY_TYPE_ZONE:
        row = select_zone(overlay_id)
        return format_zone(row)
    elif overlay_type == OVERLAY_TYPE_DRONEPORT:
        row = select_droneport(overlay_id)
        return format_droneport(row)
    elif overlay_type == OVERLAY_TYPE_ROUTE:
        row = select_route(overlay_id)
        return format_route(row)
    else:
        return None


def approve_overlay(overlay_type, overlay_id, data):

    if overlay_type not in VALID_OVERLAY_TYPES:
        return None, "Invalid overlay type"

    if data is None:
        data = {}

    approved_by = data.get("approved_by")

    if approved_by in ("", None):
        return None, "Missing required field: approved_by"

    overlay = get_overlay_by_type_and_id(overlay_type, overlay_id)

    if overlay is None:
        return None, "Overlay not found"

    if overlay.get("survey_status") != SURVEY_STATUS_SURVEYED:
        return None, "Overlay not surveyed"

    review_comments = data.get("review_comments", "Approved review")

    review_id = get_overlay_review_id(overlay_type, overlay_id)

    if review_id is None:
        return None, "Overlay review not found"

    if overlay_type == OVERLAY_TYPE_SITE:
        result = approve_site(overlay_id, approved_by)
    elif overlay_type == OVERLAY_TYPE_ZONE:
        result = approve_zone(overlay_id, approved_by)
    elif overlay_type == OVERLAY_TYPE_DRONEPORT:
        result = approve_droneport(overlay_id, approved_by)
    elif overlay_type == OVERLAY_TYPE_ROUTE:
        result = approve_route(overlay_id, approved_by)
    else:
        return None, "Invalid overlay type"

    if result is None:
        return None, "Overlay not found"

    approve_overlay_review(
        review_id,
        approved_by,
        review_comments
    )

    return {
        "status": REVIEW_STATUS_APPROVED,
        "overlay_type": overlay_type,
        "overlay_id": overlay_id,
        "review_id": review_id,
        "approved_by": approved_by,
    }, None


def reject_overlay(overlay_type, overlay_id, data):

    if overlay_type not in VALID_OVERLAY_TYPES:
        return None, "Invalid overlay type"

    if data is None:
        data = {}

    reviewed_by = data.get("reviewed_by")

    if reviewed_by in ("", None):
        return None, "Missing required field: reviewed_by"

    review_comments = data.get("review_comments", "Rejected review")

    review_id = get_overlay_review_id(overlay_type, overlay_id)

    if review_id is None:
        return None, "Overlay review not found"

    if overlay_type == OVERLAY_TYPE_SITE:
        result = reject_site(overlay_id)
    elif overlay_type == OVERLAY_TYPE_ZONE:
        result = reject_zone(overlay_id)
    elif overlay_type == OVERLAY_TYPE_DRONEPORT:
        result = reject_droneport(overlay_id)
    elif overlay_type == OVERLAY_TYPE_ROUTE:
        result = reject_route(overlay_id)
    else:
        return None, "Invalid overlay type"

    if result is None:
        return None, "Overlay not found"

    reject_overlay_review(
        review_id,
        reviewed_by,
        review_comments
    )

    return {
        "status": REVIEW_STATUS_REJECTED,
        "overlay_type": overlay_type,
        "overlay_id": overlay_id,
        "review_id": review_id,
        "reviewed_by": reviewed_by,
    }, None


def request_changes_overlay(overlay_type, overlay_id, data):

    if overlay_type not in VALID_OVERLAY_TYPES:
        return None, "Invalid overlay type"

    if data is None:
        data = {}

    reviewed_by = data.get("reviewed_by")

    if reviewed_by in ("", None):
        return None, "Missing required field: reviewed_by"

    review_comments = data.get("review_comments", "Additional revisions requested")

    review_id = get_overlay_review_id(overlay_type, overlay_id)

    if review_id is None:
        return None, "Overlay review not found"

    if overlay_type == OVERLAY_TYPE_SITE:
        result = request_site_changes(overlay_id)
    elif overlay_type == OVERLAY_TYPE_ZONE:
        result = request_zone_changes(overlay_id)
    elif overlay_type == OVERLAY_TYPE_DRONEPORT:
        result = request_droneport_changes(overlay_id)
    elif overlay_type == OVERLAY_TYPE_ROUTE:
        result = request_route_changes(overlay_id)
    else:
        return None, "Invalid overlay type"

    if result is None:
        return None, "Overlay not found"

    request_overlay_review_changes(
        review_id,
        reviewed_by,
        review_comments
    )

    return {
        "status": REVIEW_STATUS_REVISIONS_REQUESTED,
        "overlay_type": overlay_type,
        "overlay_id": overlay_id,
        "review_id": review_id,
        "reviewed_by": reviewed_by,
    }, None


def submit_overlay(overlay_type, overlay_id, data):

    if overlay_type not in VALID_OVERLAY_TYPES:
        return None, "Invalid overlay type"

    if data is None:
        data = {}

    reviewed_by = data.get("reviewed_by")

    if reviewed_by in ("", None):
        return None, "Missing required field: reviewed_by"

    survey_status = data.get("survey_status")

    if (survey_status != SURVEY_STATUS_SURVEYED):
        return None, "Overlay not surveyed"

    review_comments = data.get("review_comments", "Submitted review")

    review_id = get_overlay_review_id(overlay_type, overlay_id)

    if review_id is None:
        return None, "Overlay review not found"

    if overlay_type == OVERLAY_TYPE_SITE:
        result = submit_site(overlay_id)
    elif overlay_type == OVERLAY_TYPE_ZONE:
        result = submit_zone(overlay_id)
    elif overlay_type == OVERLAY_TYPE_DRONEPORT:
        result = submit_droneport(overlay_id)
    elif overlay_type == OVERLAY_TYPE_ROUTE:
        result = submit_route(overlay_id)
    else:
        return None, "Invalid overlay type"

    if result is None:
        return None, "Overlay not found"

    submit_overlay_review(
        review_id,
        reviewed_by,
        review_comments
    )

    return {
        "status": REVIEW_STATUS_SUBMITTED,
        "overlay_type": overlay_type,
        "overlay_id": overlay_id,
        "review_id": review_id,
        "reviewed_by": reviewed_by,
    }, None

