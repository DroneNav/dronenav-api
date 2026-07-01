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
Operational Readiness Package API object model implentation source file.

Author:
DroneNav Project Contributors

Created: 2026-06-14 

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from sqlalchemy import text

from app.config.database import engine
from app.config.constants import (
    OVERLAY_TYPE_SITE,
    OVERLAY_TYPE_ZONE,
    OVERLAY_TYPE_DRONEPORT,
    OVERLAY_TYPE_ROUTE,
    SITE_STATUS_INACTIVE,
    ZONE_STATUS_INACTIVE,
    DRONEPORT_STATUS_INACTIVE,
    ROUTE_STATUS_INACTIVE,
    SURVEY_STATUS_APPROVED,
    REVIEW_STATUS_APPROVED,
    SITE_STATUS_ACTIVE,
    ZONE_STATUS_ACTIVE,
    DRONEPORT_STATUS_ACTIVE,
    ROUTE_STATUS_ACTIVE,
)
    

def activate_overlay_record(overlay_type, overlay_id, activated_by):

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
        return None, "Invalid overlay type for single overlay"

    config = table_config[overlay_type]

    try:
        with engine.begin() as connection:

            overlay_result = connection.execute(

                text(f"""
                    UPDATE {config["table"]}
                    SET
                        operational_status = :operational_status
                    WHERE {config["id_column"]} = :overlay_id
                      AND survey_status = :survey_status
                      AND EXISTS (
                             SELECT 1
                               FROM overlay_reviews
                              WHERE overlay_type = :overlay_type
                                AND overlay_id = :overlay_id
                                AND review_status = :review_status
                          )
                     """),
                {
                    "overlay_id": overlay_id,
                    "overlay_type": overlay_type,
                    "operational_status": "active",
                    "survey_status": SURVEY_STATUS_APPROVED,
                    "review_status": REVIEW_STATUS_APPROVED,
                }
            )

            if overlay_result.rowcount != 1:
                raise Exception("Overlay not found or not approved")

            return {
                "status": "active",
                "overlay_type": overlay_type,
                "overlay_id": overlay_id,
                "overlay_records_activated": overlay_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


def activate_overlay_package_record(site_id, activated_by):

    try:
        with engine.begin() as connection:

            # --------------------------------------------------------
            # Validate site is approved and has approved package review.
            # --------------------------------------------------------
            site_check = connection.execute(
                text("""
                    SELECT COUNT(*) AS approved
                    FROM sites
                    WHERE site_id = :site_id
                      AND survey_status = :survey_status
                      AND EXISTS (
                          SELECT 1
                          FROM overlay_reviews
                          WHERE site_id = :site_id
                            AND review_status = :review_status
                      )
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_APPROVED,
                    "review_status": REVIEW_STATUS_APPROVED,
                }
            ).scalar()

            if site_check != 1:
                raise Exception("Site package cannot be activated: site package is not approved.")

            # --------------------------------------------------------
            # Validate all zones are approved.
            # --------------------------------------------------------
            zone_counts = connection.execute(
                text("""
                    SELECT
                      COUNT(*) AS total,
                      COUNT(*) FILTER (
                        WHERE survey_status = :survey_status
                          AND EXISTS (
                            SELECT 1
                            FROM overlay_reviews
                            WHERE overlay_type = 'zone'
                              AND overlay_id = zones.zone_id
                              AND review_status = :review_status
                          )
                      ) AS approved
                    FROM zones
                    WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_APPROVED,
                    "review_status": REVIEW_STATUS_APPROVED,
                }
            ).mappings().first()

            if zone_counts["total"] != zone_counts["approved"]:
                raise Exception(
                    f"Site package cannot be activated: "
                    f"{zone_counts['total'] - zone_counts['approved']} zone(s) are not approved."
                )

            # --------------------------------------------------------
            # Validate all droneports are approved.
            # --------------------------------------------------------
            droneport_counts = connection.execute(
                text("""
                    SELECT
                      COUNT(*) AS total,
                      COUNT(*) FILTER (
                        WHERE survey_status = :survey_status
                          AND EXISTS (
                            SELECT 1
                            FROM overlay_reviews
                            WHERE overlay_type = 'droneport'
                              AND overlay_id = droneports.droneport_id
                              AND review_status = :review_status
                          )
                      ) AS approved
                    FROM droneports
                    WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_APPROVED,
                    "review_status": REVIEW_STATUS_APPROVED,
                }
            ).mappings().first()

            if droneport_counts["total"] != droneport_counts["approved"]:
                raise Exception(
                    f"Site package cannot be activated: "
                    f"{droneport_counts['total'] - droneport_counts['approved']} droneport(s) are not approved."
                )

            # --------------------------------------------------------
            # Validate all connected routes are approved.
            # --------------------------------------------------------
            route_counts = connection.execute(
                text("""
                    SELECT
                      COUNT(*) AS total,
                      COUNT(*) FILTER (
                        WHERE survey_status = :survey_status
                          AND EXISTS (
                            SELECT 1
                            FROM overlay_reviews
                            WHERE overlay_type = 'route'
                              AND overlay_id = routes.route_id
                              AND review_status = :review_status
                          )
                      ) AS approved
                    FROM routes
                    WHERE origin_site_id = :site_id
                       OR destination_site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_APPROVED,
                    "review_status": REVIEW_STATUS_APPROVED,
                }
            ).mappings().first()

            if route_counts["total"] != route_counts["approved"]:
                raise Exception(
                    f"Site package cannot be activated: "
                    f"{route_counts['total'] - route_counts['approved']} route(s) are not approved."
                )

            # --------------------------------------------------------
            # Activate site.
            # --------------------------------------------------------
            site_result = connection.execute(
                text("""
                    UPDATE sites
                    SET operational_status = :operational_status
                    WHERE site_id = :site_id
                      AND survey_status = :survey_status
                """),
                {
                    "site_id": site_id,
                    "operational_status": SITE_STATUS_ACTIVE,
                    "survey_status": SURVEY_STATUS_APPROVED,
                }
            )

            if site_result.rowcount != 1:
                raise Exception(f"Site not found or not approved: {site_id}")

            # --------------------------------------------------------
            # Activate zones.
            # --------------------------------------------------------
            zone_result = connection.execute(
                text("""
                    UPDATE zones
                    SET operational_status = :operational_status
                    WHERE site_id = :site_id
                      AND survey_status = :survey_status
                """),
                {
                    "site_id": site_id,
                    "operational_status": ZONE_STATUS_ACTIVE,
                    "survey_status": SURVEY_STATUS_APPROVED,
                }
            )

            # --------------------------------------------------------
            # Activate droneports.
            # --------------------------------------------------------
            droneport_result = connection.execute(
                text("""
                    UPDATE droneports
                    SET operational_status = :operational_status
                    WHERE site_id = :site_id
                      AND survey_status = :survey_status
                """),
                {
                    "site_id": site_id,
                    "operational_status": DRONEPORT_STATUS_ACTIVE,
                    "survey_status": SURVEY_STATUS_APPROVED,
                }
            )

            # --------------------------------------------------------
            # Activate connected routes.
            # --------------------------------------------------------
            route_result = connection.execute(
                text("""
                    UPDATE routes
                    SET operational_status = :operational_status
                    WHERE (origin_site_id = :site_id OR destination_site_id = :site_id)
                      AND survey_status = :survey_status
                """),
                {
                    "site_id": site_id,
                    "operational_status": ROUTE_STATUS_ACTIVE,
                    "survey_status": SURVEY_STATUS_APPROVED,
                }
            )

            return {
                "status": SITE_STATUS_ACTIVE,
                "site_id": site_id,
                "activated_by": activated_by,
                "site_activated": site_result.rowcount,
                "zones_activated": zone_result.rowcount,
                "droneports_activated": droneport_result.rowcount,
                "routes_activated": route_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


def deactivate_overlay_package_record(site_id):

    try:
        with engine.begin() as connection:

            # --------------------------------------------------------
            # Routes where this site is either origin or destination
            # --------------------------------------------------------
            route_result = connection.execute(

                text("""
                UPDATE routes
                SET
                    operational_status = :operational_status
                WHERE origin_site_id = :site_id
                   OR destination_site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "operational_status": ROUTE_STATUS_INACTIVE,
                }
            )

            # --------------------------------------------------------
            # DronePorts for this site
            # --------------------------------------------------------
            droneport_result = connection.execute(

                text("""
                UPDATE droneports
                SET
                    operational_status = :operational_status
                WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "operational_status": DRONEPORT_STATUS_INACTIVE,
                }
            )

            # --------------------------------------------------------
            # Zones for this site
            # --------------------------------------------------------
            zone_result = connection.execute(

                text("""
                UPDATE zones
                SET
                    operational_status = :operational_status
                WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "operational_status": ZONE_STATUS_INACTIVE,
                }
            )

            # --------------------------------------------------------
            # Site itself
            # --------------------------------------------------------
            site_result = connection.execute(

                text("""
                UPDATE sites
                SET
                    operational_status = :operational_status
                WHERE site_id = :site_id
                """),
                {
                    "site_id": site_id,
                    "operational_status": SITE_STATUS_INACTIVE,
                }
            )

            if site_result.rowcount != 1:
                raise Exception(f"Site not found: {site_id}")

            return {
                "status": SITE_STATUS_INACTIVE,
                "site_id": site_id,
                "routes_deactivated": route_result.rowcount,
                "droneports_deactivated": droneport_result.rowcount,
                "zones_deactivated": zone_result.rowcount,
                "sites_deactivated": site_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


def deactivate_overlay_record(overlay_type, overlay_id):

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
        return None, "Invalid overlay type for single overlay"

    config = table_config[overlay_type]

    try:
        with engine.begin() as connection:

            overlay_result = connection.execute(

                text(f"""
                    UPDATE {config["table"]}
                    SET
                        operational_status = :operational_status
                    WHERE {config["id_column"]} = :overlay_id
                     """),
                {
                    "overlay_id": overlay_id,
                    "operational_status": "inactive",
                }
            )

            if overlay_result.rowcount != 1:
                raise Exception("Overlay not found")

            return {
                "status": "inactive",
                "overlay_type": overlay_type,
                "overlay_id": overlay_id,
                "overlay_records_deactivated": overlay_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)


