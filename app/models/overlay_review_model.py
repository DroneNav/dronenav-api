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
Overlay Review API object model implentation source file.

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


from sqlalchemy import text
from datetime import datetime

from app.config.database import engine

from app.config.constants import (
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_SUBMITTED,
    REVIEW_STATUS_REVISIONS_REQUESTED
)


def get_overlay_review_id(overlay_type, overlay_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT review_id
                FROM overlay_reviews
                WHERE overlay_type = :overlay_type
                  AND overlay_id = :overlay_id
            """),
            {
                "overlay_type": overlay_type,
                "overlay_id": overlay_id
            }
        )

        return str(result.scalar_one())


def select_overlay_review(review_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    review_id,
                    overlay_type,
                    overlay_id,
                    review_status,
                    submitted_by,
                    submitted_at,
                    reviewed_by,
                    reviewed_at,
                    review_comments,
                    created_at,
                    updated_at
                FROM overlay_reviews
                WHERE review_id = :review_id
            """),
            {
                "review_id": review_id,
            }
        )

        return result.mappings().first()


def select_overlay_reviews(overlay_type=None, review_status=None):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    review_id,
                    overlay_type,
                    overlay_id,
                    review_status,
                    submitted_by,
                    submitted_at,
                    reviewed_by,
                    reviewed_at,
                    review_comments,
                    created_at,
                    updated_at
                FROM overlay_reviews
                WHERE (:overlay_type IS NULL OR overlay_type = :overlay_type)
                  AND (:review_status IS NULL OR review_status = :review_status)
                ORDER BY created_at DESC
            """),
            {
                "overlay_type": overlay_type,
                "review_status": review_status,
            }
        )

        return result.mappings().all()


def select_overlay_notes(overlay_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT review_comments
                FROM overlay_reviews
                WHERE overlay_id = :overlay_id
            """),
            {
                "overlay_id": overlay_id
            }
        )

        return result.scalar_one()


def get_overlay_review_prior_comments(review_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT review_comments
                FROM overlay_reviews
                WHERE review_id = :review_id
            """),
            {
                "review_id": review_id
            }
        )

        return str(result.scalar_one())


def approve_overlay_review(review_id, reviewed_by, new_comment):

    prior_comments = get_overlay_review_prior_comments(review_id) or ""
    updated_comments = datetime.now().isoformat() + "  " + reviewed_by + "  " + new_comment + "\n\n" + prior_comments

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE overlay_reviews 
                SET
                    review_status = :status,
                    reviewed_by = :reviewed_by,
                    reviewed_at = now(),
                    review_comments = :updated_comments
                WHERE review_id = :review_id
                RETURNING review_id, reviewed_by
            """),
            {
                "review_id": review_id,
                "reviewed_by": reviewed_by,
                "status": REVIEW_STATUS_APPROVED,
                "updated_comments": updated_comments
            }
        )

        return result.mappings().first()


def reject_overlay_review(review_id, reviewed_by, new_comment):

    prior_comments = get_overlay_review_prior_comments(review_id) or ""
    updated_comments = datetime.now().isoformat() + "  " + reviewed_by + "  " + new_comment + "\n\n" + prior_comments

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE overlay_reviews
                SET
                    review_status = :status,
                    reviewed_by = :reviewed_by,
                    reviewed_at = now(),
                    review_comments = :updated_comments
                WHERE review_id = :review_id
                RETURNING review_id, reviewed_by
            """),
            {
                "review_id": review_id,
                "reviewed_by": reviewed_by,
                "status": REVIEW_STATUS_REJECTED,
                "updated_comments": updated_comments
            }
        )

        return result.mappings().first()


def request_overlay_review_changes(review_id, reviewed_by, new_comment):

    prior_comments = get_overlay_review_prior_comments(review_id) or ""
    updated_comments = datetime.now().isoformat() + "  " + reviewed_by + "  " + new_comment + "\n\n" + prior_comments

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE overlay_reviews
                SET
                    review_status = :status,
                    reviewed_by = :reviewed_by,
                    reviewed_at = now(),
                    review_comments = :updated_comments
                WHERE review_id = :review_id
                RETURNING review_id, reviewed_by
            """),
            {
                "review_id": review_id,
                "reviewed_by": reviewed_by,
                "status": REVIEW_STATUS_REVISIONS_REQUESTED,
                "updated_comments": updated_comments
            }
        )

        return result.mappings().first()


def submit_overlay_review(review_id, submitted_by, new_comment):

    prior_comments = get_overlay_review_prior_comments(review_id) or ""
    updated_comments = datetime.now().isoformat() + "  " + submitted_by + "  " + new_comment + "\n\n" + prior_comments

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE overlay_reviews
                SET
                    review_status = :status,
                    submitted_by = :submitted_by,
                    submitted_at = now(),
                    reviewed_by = NULL,
                    reviewed_at = NULL,
                    updated_at = now(),
                    review_comments = :updated_comments
                WHERE review_id = :review_id
                RETURNING review_id, submitted_by
            """),
            {
                "review_id": review_id,
                "submitted_by": submitted_by,
                "status": REVIEW_STATUS_SUBMITTED,
                "updated_comments": updated_comments
            }
        )

        return result.mappings().first()


def select_pending_reviews_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM overlay_reviews
                WHERE review_status = :pending_status
                  OR review_status = :submitted_status
            """),
            {
                "pending_status": "pending_review",
                "submitted_status": "submitted"
            }
        )

        return result.scalar_one()


def select_approved_reviews_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM overlay_reviews
                WHERE review_status = :approved_status
            """),
            {
                "approved_status": "approved"
            }
        )

        return result.scalar_one()


def select_rejected_reviews_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM overlay_reviews
                WHERE review_status = :rejected_status
            """),
            {
                "rejected_status": "rejected"
            }
        )

        return result.scalar_one()


def select_revision_requested_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM overlay_reviews
                WHERE review_status = :requested_status
            """),
            {
                "requested_status": "revisions_requested"
            }
        )

        return result.scalar_one()


def select_site_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM sites
                WHERE operational_status <> :deleted_status
            """),
            {
                "deleted_status": "deleted"
            }
        )

        return result.scalar_one()


def select_zone_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM zones
                WHERE operational_status <> :deleted_status
            """),
            {
                "deleted_status": "deleted"
            }
        )

        return result.scalar_one()


def select_droneport_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM droneports
                WHERE operational_status <> :deleted_status
            """),
            {
                "deleted_status": "deleted"
            }
        )

        return result.scalar_one()


def select_route_count():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT count(*)
                FROM routes
                WHERE operational_status <> :deleted_status
            """),
            {
                "deleted_status": "deleted"
            }
        )

        return result.scalar_one()

