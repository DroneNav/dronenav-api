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

from app.config.database import engine


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

