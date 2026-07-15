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
Overlay Package API object model implentation source file.

Author:
DroneNav Project Contributors

Created: 2026-06-12 

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from sqlalchemy import bindparam, text

from app.config.database import engine
from app.config.constants import (
    SURVEY_STATUS_SUBMITTED,
    SURVEY_STATUS_SURVEYED,
    SURVEY_STATUS_NOT_SURVEYED,
    SURVEY_STATUS_APPROVED,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_SUBMITTED,
    OVERLAY_TYPE_SITE,
    OVERLAY_TYPE_ZONE,
    OVERLAY_TYPE_DRONEPORT,
    OVERLAY_TYPE_ROUTE,
    ROUTE_STATUS_DELETED,
    DRONEPORT_STATUS_DELETED,
    ZONE_STATUS_DELETED,
    SITE_STATUS_DELETED,
)


def get_context_package_record(site_id):

    try:
        with engine.connect() as connection:

            route_result = connection.execute(
                text("""
                    SELECT
                        route_id,
                        origin_site_id,
                        destination_site_id,
                        route_name,
                        route_type,
                        direction,
                        ST_AsGeoJSON(geometry)::json AS geometry
                    FROM routes
                    WHERE (origin_site_id = :site_id OR destination_site_id = :site_id)
                      AND operational_status <> :deleted_status
                """),
                {
                    "site_id": site_id,
                    "deleted_status": ROUTE_STATUS_DELETED,
                }
            )

            droneport_result = connection.execute(
                text("""
                    SELECT
                        droneport_id,
                        site_id,
                        droneport_name,
                        droneport_type,
                        droneport_diameter_ft,
                        ST_AsGeoJSON(geometry)::json AS geometry
                    FROM droneports
                    WHERE site_id = :site_id
                      AND operational_status <> :deleted_status
                """),
                {
                    "site_id": site_id,
                    "deleted_status": DRONEPORT_STATUS_DELETED,
                }
            )

            zone_result = connection.execute(
                text("""
                    SELECT
                        zone_id,
                        site_id,
                        zone_name,
                        zone_type,
                        ST_AsGeoJSON(geometry)::json AS geometry
                    FROM zones
                    WHERE operational_status <> :deleted_status
                      AND site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "deleted_status": ZONE_STATUS_DELETED,
                }
            )

            site_result = connection.execute(
                text("""
                    SELECT
                        site_id,
                        site_name,
                        site_type,
                        ST_AsGeoJSON(geometry)::json AS geometry
                    FROM sites
                    WHERE site_id = :site_id
                      AND operational_status <> :deleted_status
                """),
                {
                    "site_id": site_id,
                    "deleted_status": SITE_STATUS_DELETED,
                }
            )

            site = site_result.mappings().first()

            if site is None:
                return None, f"Site not found: {site_id}"

            return {
                "site": site,
                "zones": zone_result.mappings().all(),
                "droneports": droneport_result.mappings().all(),
                "routes": route_result.mappings().all(),
            }, None

    except Exception as e:
        return None, str(e)


def select_unsubmitted_site_package_surveys(site_id):

    try:
        with engine.connect() as connection:

            # --------------------------------------------------------
            # Site
            # --------------------------------------------------------

            site_result = connection.execute(
                text("""
                    SELECT
                        site_id AS overlay_id,
                        site_name AS overlay_name,
                        survey_status
                    FROM sites
                    WHERE site_id = :site_id
                      AND survey_status <> :submitted_status
                """),
                {
                    "site_id": site_id,
                    "submitted_status": SURVEY_STATUS_SURVEYED,
                }
            )

            # --------------------------------------------------------
            # Exclusive Zones
            # --------------------------------------------------------

            zone_result = connection.execute(
                text("""
                    SELECT
                        zone_id AS overlay_id,
                        zone_name AS overlay_name,
                        survey_status
                    FROM zones
                    WHERE site_id = :site_id
                      AND survey_status <> :submitted_status
                """),
                {
                    "site_id": site_id,
                    "submitted_status": SURVEY_STATUS_SURVEYED,
                }
            )

            # --------------------------------------------------------
            # Exclusive DronePorts
            # --------------------------------------------------------

            droneport_result = connection.execute(
                text("""
                    SELECT
                        droneport_id AS overlay_id,
                        droneport_name AS overlay_name,
                        survey_status
                    FROM droneports
                    WHERE site_id = :site_id
                      AND survey_status <> :submitted_status
                """),
                {
                    "site_id": site_id,
                    "submitted_status": SURVEY_STATUS_SURVEYED,
                }
            )

            # --------------------------------------------------------
            # Shared Routes
            #
            # Load all Routes connected to this Site. Do not decide
            # eligibility in SQL. Classification occurs below.
            # --------------------------------------------------------

            route_result = connection.execute(
                text("""
                    SELECT
                        r.route_id AS overlay_id,
                        r.route_name AS overlay_name,
                        r.origin_site_id,
                        r.destination_site_id,
                        r.survey_status,
                        r.operational_status,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status IN (
                                  :review_pending,
                                  :review_submitted
                              )
                        ) AS has_active_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_approved
                        ) AS has_approved_review

                    FROM routes r
                    WHERE r.origin_site_id = :site_id
                       OR r.destination_site_id = :site_id
                    ORDER BY
                        r.route_name,
                        r.route_id
                """),
                {
                    "site_id": site_id,
                    "route_overlay_type": OVERLAY_TYPE_ROUTE,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "review_approved": REVIEW_STATUS_APPROVED,
                }
            )

            route_rows = [
                dict(row)
                for row in route_result.mappings().all()
            ]

            missing_routes = []

            for route in route_rows:
                route_state = classify_site_package_route(route)

                route["package_route_state"] = route_state

                if route_state == "survey_required":
                    missing_routes.append(route)

            return {
                "site": [
                    dict(row)
                    for row in site_result.mappings().all()
                ],
                "zones": [
                    dict(row)
                    for row in zone_result.mappings().all()
                ],
                "droneports": [
                    dict(row)
                    for row in droneport_result.mappings().all()
                ],

                # Only Routes that genuinely require survey work block
                # Site package submission.
                "routes": missing_routes,

                # Temporary diagnostic output. This lets us inspect how
                # every connected Route was classified during V2 testing.
                "route_states": route_rows,
            }, None

    except Exception as e:
        return None, str(e)


def classify_site_package_route(route):
    """
    Classify a Route connected to a Site survey package.

    This function performs no database writes.

    Possible results:

        survey_required
        review_required
        review_in_progress
        governance_complete
    """

    survey_status = route.get("survey_status")
    has_active_review = bool(route.get("has_active_review"))
    has_approved_review = bool(route.get("has_approved_review"))

    # The Route has already completed review. It must not be surveyed
    # or reviewed again for another connected Site package.
    if has_approved_review:
        return "governance_complete"

    # The Route is already participating in an active review process.
    # The new Site package reuses that existing survey and review.
    if has_active_review:
        return "review_in_progress"

    # Survey work is complete, but no active or approved review exists.
    # This Route is eligible to enter review through this package.
    if survey_status in (
        SURVEY_STATUS_SURVEYED,
        SURVEY_STATUS_SUBMITTED,
        SURVEY_STATUS_APPROVED,
    ):
        return "review_required"

    # The Route still requires survey work.
    return "survey_required"


def survey_overlay_package_record(site_id, surveyed_by):

    try:

        with engine.begin() as connection:

            # --------------------------------------------------------
            # Inspect and classify Routes connected to this Site
            # --------------------------------------------------------

            route_state_result = connection.execute(
                text("""
                    SELECT
                        r.route_id AS overlay_id,
                        r.route_name AS overlay_name,
                        r.origin_site_id,
                        r.destination_site_id,
                        r.survey_status,
                        r.operational_status,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status IN (
                                  :review_pending,
                                  :review_submitted
                              )
                        ) AS has_active_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_approved
                        ) AS has_approved_review

                    FROM routes r
                    WHERE r.origin_site_id = :site_id
                       OR r.destination_site_id = :site_id
                    ORDER BY
                        r.route_name,
                        r.route_id
                """),
                {
                    "site_id": site_id,
                    "route_overlay_type": OVERLAY_TYPE_ROUTE,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "review_approved": REVIEW_STATUS_APPROVED,
                }
            )

            route_rows = [
                dict(row)
                for row in route_state_result.mappings().all()
            ]

            review_required_route_ids = []
            review_in_progress_route_ids = []
            governance_complete_route_ids = []
            survey_required_route_ids = []

            for route in route_rows:

                route_state = classify_site_package_route(route)
                route_id = route["overlay_id"]

                if route_state == "review_required":
                    review_required_route_ids.append(route_id)

                elif route_state == "review_in_progress":
                    review_in_progress_route_ids.append(route_id)

                elif route_state == "governance_complete":
                    governance_complete_route_ids.append(route_id)

                elif route_state == "survey_required":
                    survey_required_route_ids.append(route_id)

            # Eligibility should already have been validated by the
            # service. Keep this defensive check so the persistence
            # function cannot submit incomplete Route survey work.
            if survey_required_route_ids:
                raise Exception(
                    "Site package contains one or more Routes "
                    "that still require survey work"
                )

            # --------------------------------------------------------
            # Routes requiring this package to complete survey
            # submission and move toward review
            # --------------------------------------------------------

            if review_required_route_ids:

                route_result = connection.execute(
                    text("""
                        UPDATE routes
                        SET
                            survey_status = :survey_status,
                            surveyed_by = :surveyed_by,
                            last_surveyed_at = NOW()
                        WHERE route_id IN :route_ids
                    """).bindparams(
                        bindparam(
                            "route_ids",
                            expanding=True,
                        )
                    ),
                    {
                        "route_ids": review_required_route_ids,
                        "survey_status": SURVEY_STATUS_SURVEYED,
                        "surveyed_by": surveyed_by,
                    }
                )

                route_review_result = connection.execute(
                    text("""
                        UPDATE overlay_reviews
                        SET
                            survey_status = :survey_status,
                            surveyed_by = :surveyed_by,
                            surveyed_at = NOW()
                        WHERE overlay_type = :overlay_type
                          AND overlay_id IN :route_ids
                    """).bindparams(
                        bindparam(
                            "route_ids",
                            expanding=True,
                        )
                    ),
                    {
                        "route_ids": review_required_route_ids,
                        "survey_status": SURVEY_STATUS_SURVEYED,
                        "surveyed_by": surveyed_by,
                        "overlay_type": OVERLAY_TYPE_ROUTE,
                    }
                )

                routes_surveyed = route_result.rowcount
                route_reviews_updated = route_review_result.rowcount

            else:

                routes_surveyed = 0
                route_reviews_updated = 0

            # Routes classified as review_in_progress or
            # governance_complete are intentionally not modified.

            # --------------------------------------------------------
            # DronePorts exclusive to this Site
            # --------------------------------------------------------

            droneport_result = connection.execute(
                text("""
                    UPDATE droneports
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        last_surveyed_at = NOW()
                    WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                }
            )

            droneport_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        surveyed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id IN (
                          SELECT droneport_id
                          FROM droneports
                          WHERE site_id = :site_id
                      )
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                    "overlay_type": OVERLAY_TYPE_DRONEPORT,
                }
            )

            # --------------------------------------------------------
            # Zones exclusive to this Site
            # --------------------------------------------------------

            zone_result = connection.execute(
                text("""
                    UPDATE zones
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        last_surveyed_at = NOW()
                    WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                }
            )

            zone_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        surveyed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id IN (
                          SELECT zone_id
                          FROM zones
                          WHERE site_id = :site_id
                      )
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                    "overlay_type": OVERLAY_TYPE_ZONE,
                }
            )

            # --------------------------------------------------------
            # Site itself
            # --------------------------------------------------------

            site_result = connection.execute(
                text("""
                    UPDATE sites
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        last_surveyed_at = NOW()
                    WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                }
            )

            site_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        surveyed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                    "overlay_type": OVERLAY_TYPE_SITE,
                }
            )

            if site_result.rowcount != 1:
                raise Exception(f"Site not found: {site_id}")

            return {
                "status": "surveyed",
                "site_id": site_id,
                "surveyed_by": surveyed_by,
                "routes_surveyed": routes_surveyed,
                "route_reviews_updated": route_reviews_updated,
                "routes_review_in_progress": len(
                    review_in_progress_route_ids
                ),
                "routes_governance_complete": len(
                    governance_complete_route_ids
                ),
                "droneports_surveyed": droneport_result.rowcount,
                "droneport_reviews_updated":
                    droneport_review_result.rowcount,
                "zones_surveyed": zone_result.rowcount,
                "zone_reviews_updated": zone_review_result.rowcount,
                "sites_surveyed": site_result.rowcount,
                "site_reviews_updated": site_review_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)



def survey_overlay_record(overlay_type, overlay_id, surveyed_by):

    table_config = {
        OVERLAY_TYPE_SITE: {
            "table": "sites",
            "id_column": "site_id",
        },
        OVERLAY_TYPE_ZONE: {
            "table": "zones",
            "id_column": "zone_id",
        },
        OVERLAY_TYPE_DRONEPORT: {
            "table": "droneports",
            "id_column": "droneport_id",
        },
        OVERLAY_TYPE_ROUTE: {
            "table": "routes",
            "id_column": "route_id",
        },
    }

    if overlay_type not in table_config:
        return None, "Invalid overlay type for single overlay survey"

    config = table_config[overlay_type]

    try:
        with engine.begin() as connection:

            overlay_result = connection.execute(

                text(f"""
                    UPDATE {config["table"]}
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        last_surveyed_at = NOW()
                    WHERE {config["id_column"]} = :overlay_id
                """),
                {
                    "overlay_id": overlay_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                }
            )

            if overlay_result.rowcount != 1:
                raise Exception("Overlay not found")

            review_result = connection.execute(

                text("""
                    UPDATE overlay_reviews
                    SET
                        survey_status = :survey_status,
                        surveyed_by = :surveyed_by,
                        surveyed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id = :overlay_id
                """),
                {
                    "overlay_type": overlay_type,
                    "overlay_id": overlay_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
                }
            )

            return {
                "status": "surveyed",
                "overlay_type": overlay_type,
                "overlay_id": overlay_id,
                "surveyed_by": surveyed_by,
                "overlay_records_updated": overlay_result.rowcount,
                "review_records_updated": review_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


def expire_survey_overlay_package_record(site_id):

    try:
        with engine.begin() as connection:

            # --------------------------------------------------------
            # Routes where this site is either origin or destination
            # --------------------------------------------------------
            route_result = connection.execute(

                text("""
                UPDATE routes
                SET
                    survey_status = :survey_status,
                    surveyed_by = NULL
                WHERE origin_site_id = :site_id
                   OR destination_site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                }
            )

            route_review_result = connection.execute(

                text("""
                   UPDATE overlay_reviews
                   SET
                       survey_status = :survey_status,
                       surveyed_by = NULL
                   WHERE overlay_type = :overlay_type
                     AND overlay_id IN (
                     SELECT route_id
                     FROM routes
                     WHERE origin_site_id = :site_id
                       OR destination_site_id = :site_id
                     )
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                    "overlay_type": OVERLAY_TYPE_ROUTE,
                }
            )

            # --------------------------------------------------------
            # DronePorts for this site
            # --------------------------------------------------------
            droneport_result = connection.execute(

                text("""
                UPDATE droneports
                SET
                    survey_status = :survey_status,
                    surveyed_by = NULL
                WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                }
            )

            droneport_review_result = connection.execute(

                text("""
                   UPDATE overlay_reviews
                   SET
                       survey_status = :survey_status,
                       surveyed_by = NULL
                   WHERE overlay_type = :overlay_type
                     AND overlay_id IN (
                     SELECT droneport_id
                     FROM droneports
                     WHERE site_id = :site_id
                     )
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                    "overlay_type": OVERLAY_TYPE_DRONEPORT,
                }
            )

            # --------------------------------------------------------
            # Zones for this site
            # --------------------------------------------------------
            zone_result = connection.execute(

                text("""
                UPDATE zones
                SET
                    survey_status = :survey_status,
                    surveyed_by = NULL
                WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                }
            )

            zone_review_result = connection.execute(

                text("""
                   UPDATE overlay_reviews
                   SET
                       survey_status = :survey_status,
                       surveyed_by = NULL
                   WHERE overlay_type = :overlay_type
                     AND overlay_id IN (
                     SELECT zone_id
                     FROM zones
                     WHERE site_id = :site_id
                     )
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                    "overlay_type": OVERLAY_TYPE_ZONE,
                }
            )

            # --------------------------------------------------------
            # Site itself
            # --------------------------------------------------------
            site_result = connection.execute(

                text("""
                UPDATE sites
                SET
                    survey_status = :survey_status,
                    surveyed_by = NULL
                WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                }
            )

            site_review_result = connection.execute(

                text("""
                   UPDATE overlay_reviews
                   SET
                       survey_status = :survey_status,
                       surveyed_by = NULL
                   WHERE overlay_type = :overlay_type
                     AND overlay_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                    "overlay_type": OVERLAY_TYPE_SITE,
                }
            )

            if site_result.rowcount != 1:
                raise Exception(f"Site not found: {site_id}")

            return {
                "status": "not_surveyed",
                "site_id": site_id,
                "routes_expired": route_result.rowcount,
                "route_reviews_updated": route_review_result.rowcount,
                "droneports_expired": droneport_result.rowcount,
                "droneport_reviews_updated": droneport_review_result.rowcount,
                "zones_expired": zone_result.rowcount,
                "zone_reviews_updated": zone_review_result.rowcount,
                "sites_expired": site_result.rowcount,
                "site_reviews_updated": site_review_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


def expire_survey_overlay_record(overlay_type, overlay_id):

    table_config = {
        OVERLAY_TYPE_SITE: {
            "table": "sites",
            "id_column": "site_id",
        },
        OVERLAY_TYPE_ZONE: {
            "table": "zones",
            "id_column": "zone_id",
        },
        OVERLAY_TYPE_DRONEPORT: {
            "table": "droneports",
            "id_column": "droneport_id",
        },
        OVERLAY_TYPE_ROUTE: {
            "table": "routes",
            "id_column": "route_id",
        },
    }

    if overlay_type not in table_config:
        return None, "Invalid overlay type for single overlay survey"

    config = table_config[overlay_type]

    try:

        with engine.begin() as connection:

            overlay_result = connection.execute( 

                text(f"""
                    UPDATE {config["table"]}
                    SET
                        survey_status = :survey_status,
                        surveyed_by = NULL
                    WHERE {config["id_column"]} = :overlay_id
                    """),
                    {
                        "overlay_id": overlay_id,
                        "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                    }
            )

            if overlay_result.rowcount != 1:
                raise Exception("Overlay not found")

            review_result = connection.execute(

                text("""
                UPDATE overlay_reviews
                SET
                    survey_status = :survey_status,
                    surveyed_by = NULL
                WHERE overlay_type = :overlay_type
                  AND overlay_id = :overlay_id
                """),
                {
                    "overlay_type": overlay_type,
                    "overlay_id": overlay_id,
                    "survey_status": SURVEY_STATUS_NOT_SURVEYED,
                }
            )

            return {
                "status": "not_surveyed",
                "overlay_type": overlay_type,
                "overlay_id": overlay_id,
                "overlay_records_expired": overlay_result.rowcount,
                "review_records_updated": review_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


def select_unapproved_site_package_reviews(site_id):

    try:
        with engine.connect() as connection:

            # --------------------------------------------------------
            # Site
            # --------------------------------------------------------

            site_result = connection.execute(
                text("""
                    SELECT
                        site_id AS overlay_id,
                        site_name AS overlay_name,
                        survey_status
                    FROM sites
                    WHERE site_id = :site_id
                      AND survey_status <> :approved_status
                """),
                {
                    "site_id": site_id,
                    "approved_status": SURVEY_STATUS_APPROVED,
                }
            )

            # --------------------------------------------------------
            # Exclusive Zones
            # --------------------------------------------------------

            zone_result = connection.execute(
                text("""
                    SELECT
                        zone_id AS overlay_id,
                        zone_name AS overlay_name,
                        survey_status
                    FROM zones
                    WHERE site_id = :site_id
                      AND survey_status <> :approved_status
                """),
                {
                    "site_id": site_id,
                    "approved_status": SURVEY_STATUS_APPROVED,
                }
            )

            # --------------------------------------------------------
            # Exclusive DronePorts
            # --------------------------------------------------------

            droneport_result = connection.execute(
                text("""
                    SELECT
                        droneport_id AS overlay_id,
                        droneport_name AS overlay_name,
                        survey_status
                    FROM droneports
                    WHERE site_id = :site_id
                      AND survey_status <> :approved_status
                """),
                {
                    "site_id": site_id,
                    "approved_status": SURVEY_STATUS_APPROVED,
                }
            )

            # --------------------------------------------------------
            # Connected Routes
            #
            # Load every connected Route and its current review state.
            # Route eligibility is classified below rather than decided
            # solely from routes.survey_status.
            # --------------------------------------------------------

            route_result = connection.execute(
                text("""
                    SELECT
                        r.route_id AS overlay_id,
                        r.route_name AS overlay_name,
                        r.origin_site_id,
                        r.destination_site_id,
                        r.survey_status,
                        r.operational_status,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status IN (
                                  :review_pending,
                                  :review_submitted
                              )
                        ) AS has_active_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_approved
                        ) AS has_approved_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_rejected
                        ) AS has_rejected_review

                    FROM routes r
                    WHERE r.origin_site_id = :site_id
                       OR r.destination_site_id = :site_id
                    ORDER BY
                        r.route_name,
                        r.route_id
                """),
                {
                    "site_id": site_id,
                    "route_overlay_type": OVERLAY_TYPE_ROUTE,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "review_approved": REVIEW_STATUS_APPROVED,
                    "review_rejected": REVIEW_STATUS_REJECTED,
                }
            )

            route_rows = [
                dict(row)
                for row in route_result.mappings().all()
            ]

            unapproved_routes = []

            for route in route_rows:
                route_state = classify_site_package_review_route(route)

                route["package_review_state"] = route_state

                # Only a governance-complete shared Route satisfies the
                # package's final review dependency.
                if route_state != "governance_complete":
                    unapproved_routes.append(route)

            return {
                "site": [
                    dict(row)
                    for row in site_result.mappings().all()
                ],
                "zones": [
                    dict(row)
                    for row in zone_result.mappings().all()
                ],
                "droneports": [
                    dict(row)
                    for row in droneport_result.mappings().all()
                ],

                # Any Route that has not completed governance blocks the
                # Site package's final approval.
                "routes": unapproved_routes,

                # Temporary diagnostic output for direct V2 testing.
                "route_review_states": route_rows,
            }, None

    except Exception as e:
        return None, str(e)


def classify_site_package_review_route(route):
    """
    Classify the review state of a Route connected to a Site package.

    This function performs no database writes.

    Possible results:

        review_required
        review_in_progress
        governance_complete
        review_rejected
    """

    has_active_review = bool(route.get("has_active_review"))
    has_approved_review = bool(route.get("has_approved_review"))
    has_rejected_review = bool(route.get("has_rejected_review"))

    if has_approved_review:
        return "governance_complete"

    if has_rejected_review:
        return "review_rejected"

    if has_active_review:
        return "review_in_progress"

    return "review_required"


def approve_site_review_package_record(site_id, reviewed_by):

    try:

        with engine.begin() as connection:

            # --------------------------------------------------------
            # Inspect connected Route review states
            # --------------------------------------------------------

            route_state_result = connection.execute(
                text("""
                    SELECT
                        r.route_id AS overlay_id,
                        r.route_name AS overlay_name,
                        r.origin_site_id,
                        r.destination_site_id,
                        r.survey_status,
                        r.operational_status,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status IN (
                                  :review_pending,
                                  :review_submitted
                              )
                        ) AS has_active_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_approved
                        ) AS has_approved_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_rejected
                        ) AS has_rejected_review

                    FROM routes r
                    WHERE r.origin_site_id = :site_id
                       OR r.destination_site_id = :site_id
                    ORDER BY
                        r.route_name,
                        r.route_id
                """),
                {
                    "site_id": site_id,
                    "route_overlay_type": OVERLAY_TYPE_ROUTE,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "review_approved": REVIEW_STATUS_APPROVED,
                    "review_rejected": REVIEW_STATUS_REJECTED,
                }
            )

            route_rows = [
                dict(row)
                for row in route_state_result.mappings().all()
            ]

            review_required_route_ids = []
            review_in_progress_route_ids = []
            governance_complete_route_ids = []
            review_rejected_route_ids = []

            for route in route_rows:

                route_state = classify_site_package_review_route(route)
                route_id = route["overlay_id"]

                origin_site_id = str(route["origin_site_id"])
                destination_site_id = str(route["destination_site_id"])

                is_shared_route = (
                    origin_site_id != destination_site_id
                )

                if route_state == "governance_complete":
                    governance_complete_route_ids.append(route_id)

                elif route_state == "review_rejected":
                    review_rejected_route_ids.append(route_id)

                elif route_state == "review_in_progress":

                    # A shared Route is already being reviewed through
                    # another connected Site package. Leave it untouched.
                    if is_shared_route:
                        review_in_progress_route_ids.append(route_id)

                    # A non-shared Route belongs entirely to this Site
                    # package and its pending review is approved here.
                    else:
                        review_required_route_ids.append(route_id)

                elif route_state == "review_required":
                    review_required_route_ids.append(route_id)

            if review_rejected_route_ids:
                raise Exception(
                    "Site package contains one or more Routes "
                    "with rejected reviews"
                )

            if review_in_progress_route_ids:
                raise Exception(
                    "Site package contains one or more shared Routes "
                    "whose reviews are still in progress"
                )

            # --------------------------------------------------------
            # Approve only Route reviews belonging to this package
            # --------------------------------------------------------

            if review_required_route_ids:

                route_review_result = connection.execute(
                    text("""
                        UPDATE overlay_reviews
                        SET
                            review_status = :review_status,
                            reviewed_by = :reviewed_by,
                            reviewed_at = NOW()
                        WHERE overlay_type = :overlay_type
                          AND overlay_id IN :route_ids
                          AND review_status IN (
                              :review_pending,
                              :review_submitted
                          )
                    """).bindparams(
                        bindparam(
                            "route_ids",
                            expanding=True,
                        )
                    ),
                    {
                        "route_ids": review_required_route_ids,
                        "review_status": REVIEW_STATUS_APPROVED,
                        "review_pending": REVIEW_STATUS_PENDING,
                        "review_submitted": REVIEW_STATUS_SUBMITTED,
                        "overlay_type": OVERLAY_TYPE_ROUTE,
                        "reviewed_by": reviewed_by,
                    }
                )

                route_reviews_updated = route_review_result.rowcount

            else:

                route_reviews_updated = 0

            # --------------------------------------------------------
            # DronePorts exclusive to this Site
            # --------------------------------------------------------

            droneport_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        review_status = :review_status,
                        reviewed_by = :reviewed_by,
                        reviewed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id IN (
                          SELECT droneport_id
                          FROM droneports
                          WHERE site_id = :site_id
                      )
                      AND review_status IN (
                          :review_pending,
                          :review_submitted
                      )
                """),
                {
                    "site_id": site_id,
                    "review_status": REVIEW_STATUS_APPROVED,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "overlay_type": OVERLAY_TYPE_DRONEPORT,
                    "reviewed_by": reviewed_by,
                }
            )

            # --------------------------------------------------------
            # Zones exclusive to this Site
            # --------------------------------------------------------

            zone_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        review_status = :review_status,
                        reviewed_by = :reviewed_by,
                        reviewed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id IN (
                          SELECT zone_id
                          FROM zones
                          WHERE site_id = :site_id
                      )
                      AND review_status IN (
                          :review_pending,
                          :review_submitted
                      )
                """),
                {
                    "site_id": site_id,
                    "review_status": REVIEW_STATUS_APPROVED,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "overlay_type": OVERLAY_TYPE_ZONE,
                    "reviewed_by": reviewed_by,
                }
            )

            # --------------------------------------------------------
            # Site itself
            # --------------------------------------------------------

            site_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        review_status = :review_status,
                        reviewed_by = :reviewed_by,
                        reviewed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id = :site_id
                      AND review_status IN (
                          :review_pending,
                          :review_submitted
                      )
                """),
                {
                    "site_id": site_id,
                    "review_status": REVIEW_STATUS_APPROVED,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "overlay_type": OVERLAY_TYPE_SITE,
                    "reviewed_by": reviewed_by,
                }
            )

            return {
                "status": "approved",
                "site_id": site_id,
                "reviewed_by": reviewed_by,
                "route_reviews_updated": route_reviews_updated,
                "routes_review_in_progress": len(
                    review_in_progress_route_ids
                ),
                "routes_governance_complete": len(
                    governance_complete_route_ids
                ),
                "droneport_reviews_updated":
                    droneport_review_result.rowcount,
                "zone_reviews_updated":
                    zone_review_result.rowcount,
                "site_reviews_updated":
                    site_review_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


def reject_site_review_package_record(
    site_id,
    reviewed_by,
    review_comments,
):

    try:

        with engine.begin() as connection:

            # --------------------------------------------------------
            # Inspect connected Route review states
            # --------------------------------------------------------

            route_state_result = connection.execute(
                text("""
                    SELECT
                        r.route_id AS overlay_id,
                        r.route_name AS overlay_name,
                        r.origin_site_id,
                        r.destination_site_id,
                        r.survey_status,
                        r.operational_status,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status IN (
                                  :review_pending,
                                  :review_submitted
                              )
                        ) AS has_active_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_approved
                        ) AS has_approved_review,

                        EXISTS (
                            SELECT 1
                            FROM overlay_reviews review
                            WHERE review.overlay_type = :route_overlay_type
                              AND review.overlay_id = r.route_id
                              AND review.review_status = :review_rejected
                        ) AS has_rejected_review

                    FROM routes r
                    WHERE r.origin_site_id = :site_id
                       OR r.destination_site_id = :site_id
                    ORDER BY
                        r.route_name,
                        r.route_id
                """),
                {
                    "site_id": site_id,
                    "route_overlay_type": OVERLAY_TYPE_ROUTE,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "review_approved": REVIEW_STATUS_APPROVED,
                    "review_rejected": REVIEW_STATUS_REJECTED,
                }
            )

            route_rows = [
                dict(row)
                for row in route_state_result.mappings().all()
            ]

            reject_route_ids = []
            shared_review_in_progress_route_ids = []
            governance_complete_route_ids = []
            previously_rejected_route_ids = []

            for route in route_rows:

                route_state = classify_site_package_review_route(route)
                route_id = route["overlay_id"]

                origin_site_id = str(route["origin_site_id"])
                destination_site_id = str(route["destination_site_id"])

                is_shared_route = (
                    origin_site_id != destination_site_id
                )

                if route_state == "governance_complete":
                    governance_complete_route_ids.append(route_id)

                elif route_state == "review_rejected":
                    previously_rejected_route_ids.append(route_id)

                elif route_state == "review_in_progress":

                    # A shared Route may be participating in another
                    # Site package's review. Rejecting this package must
                    # not reject or alter that shared Route review.
                    if is_shared_route:
                        shared_review_in_progress_route_ids.append(
                            route_id
                        )

                    # A Site-to-itself Route belongs to this package.
                    # Its pending review is rejected with the package.
                    else:
                        reject_route_ids.append(route_id)

                elif route_state == "review_required":

                    # There should normally be a pending/submitted review
                    # before package rejection. Including the Route here
                    # is harmless because the UPDATE below is restricted
                    # to pending/submitted review records.
                    reject_route_ids.append(route_id)

            # --------------------------------------------------------
            # Reject only Route reviews belonging to this package
            # --------------------------------------------------------

            if reject_route_ids:

                route_review_result = connection.execute(
                    text("""
                        UPDATE overlay_reviews
                        SET
                            review_status = :review_status,
                            reviewed_by = :reviewed_by,
                            reviewed_at = NOW()
                        WHERE overlay_type = :overlay_type
                          AND overlay_id IN :route_ids
                          AND review_status IN (
                              :review_pending,
                              :review_submitted
                          )
                    """).bindparams(
                        bindparam(
                            "route_ids",
                            expanding=True,
                        )
                    ),
                    {
                        "route_ids": reject_route_ids,
                        "review_status": REVIEW_STATUS_REJECTED,
                        "review_pending": REVIEW_STATUS_PENDING,
                        "review_submitted": REVIEW_STATUS_SUBMITTED,
                        "overlay_type": OVERLAY_TYPE_ROUTE,
                        "reviewed_by": reviewed_by,
                    }
                )

                route_reviews_updated = route_review_result.rowcount

            else:

                route_reviews_updated = 0

            # --------------------------------------------------------
            # DronePorts exclusive to this Site
            # --------------------------------------------------------

            droneport_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        review_status = :review_status,
                        reviewed_by = :reviewed_by,
                        reviewed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id IN (
                          SELECT droneport_id
                          FROM droneports
                          WHERE site_id = :site_id
                      )
                      AND review_status IN (
                          :review_pending,
                          :review_submitted
                      )
                """),
                {
                    "site_id": site_id,
                    "review_status": REVIEW_STATUS_REJECTED,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "overlay_type": OVERLAY_TYPE_DRONEPORT,
                    "reviewed_by": reviewed_by,
                }
            )

            # --------------------------------------------------------
            # Zones exclusive to this Site
            # --------------------------------------------------------

            zone_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        review_status = :review_status,
                        reviewed_by = :reviewed_by,
                        reviewed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id IN (
                          SELECT zone_id
                          FROM zones
                          WHERE site_id = :site_id
                      )
                      AND review_status IN (
                          :review_pending,
                          :review_submitted
                      )
                """),
                {
                    "site_id": site_id,
                    "review_status": REVIEW_STATUS_REJECTED,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "overlay_type": OVERLAY_TYPE_ZONE,
                    "reviewed_by": reviewed_by,
                }
            )

            # --------------------------------------------------------
            # Site itself
            # --------------------------------------------------------

            site_review_result = connection.execute(
                text("""
                    UPDATE overlay_reviews
                    SET
                        review_comments = :review_comments,
                        review_status = :review_status,
                        reviewed_by = :reviewed_by,
                        reviewed_at = NOW()
                    WHERE overlay_type = :overlay_type
                      AND overlay_id = :site_id
                      AND review_status IN (
                          :review_pending,
                          :review_submitted
                      )
                """),
                {
                    "site_id": site_id,
                    "review_status": REVIEW_STATUS_REJECTED,
                    "review_pending": REVIEW_STATUS_PENDING,
                    "review_submitted": REVIEW_STATUS_SUBMITTED,
                    "overlay_type": OVERLAY_TYPE_SITE,
                    "review_comments": review_comments,
                    "reviewed_by": reviewed_by,
                }
            )

            return {
                "status": "rejected",
                "site_id": site_id,
                "reviewed_by": reviewed_by,
                "route_reviews_updated": route_reviews_updated,
                "shared_route_reviews_untouched": len(
                    shared_review_in_progress_route_ids
                ),
                "routes_governance_complete": len(
                    governance_complete_route_ids
                ),
                "routes_previously_rejected": len(
                    previously_rejected_route_ids
                ),
                "droneport_reviews_updated":
                    droneport_review_result.rowcount,
                "zone_reviews_updated":
                    zone_review_result.rowcount,
                "site_reviews_updated":
                    site_review_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)




