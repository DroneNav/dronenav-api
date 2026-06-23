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


from sqlalchemy import text

from app.config.database import engine
from app.config.constants import (
    SURVEY_STATUS_SUBMITTED,
    SURVEY_STATUS_SURVEYED,
    SURVEY_STATUS_NOT_SURVEYED,
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

            route_result = connection.execute(
                text("""
                    SELECT
                        route_id AS overlay_id,
                        route_name AS overlay_name,
                        survey_status
                    FROM routes
                    WHERE (
                        origin_site_id = :site_id
                        OR destination_site_id = :site_id
                    )
                      AND survey_status <> :submitted_status
                """),
                {
                    "site_id": site_id,
                    "submitted_status": SURVEY_STATUS_SURVEYED,
                }
            )

            return {
                "site": [dict(row) for row in site_result.mappings().all()],
                "zones": [dict(row) for row in zone_result.mappings().all()],
                "droneports": [dict(row) for row in droneport_result.mappings().all()],
                "routes": [dict(row) for row in route_result.mappings().all()],
            }, None

    except Exception as e:
        return None, str(e)


def survey_overlay_package_record(site_id, surveyed_by):

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
                    surveyed_by = :surveyed_by,
                    last_surveyed_at = NOW()
                WHERE origin_site_id = :site_id
                   OR destination_site_id = :site_id
                """),
                {
                    "site_id": site_id,
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
                     AND overlay_id IN (
                    SELECT route_id
                     FROM routes
                    WHERE origin_site_id = :site_id
                       OR destination_site_id = :site_id
                     )
                """),
                {
                    "site_id": site_id,
                    "survey_status": SURVEY_STATUS_SURVEYED,
                    "surveyed_by": surveyed_by,
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
            # Zones for this site
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
                "routes_surveyed": route_result.rowcount,
                "route_reviews_updated": route_review_result.rowcount,
                "droneports_surveyed": droneport_result.rowcount,
                "droneport_reviews_updated": droneport_review_result.rowcount,
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


