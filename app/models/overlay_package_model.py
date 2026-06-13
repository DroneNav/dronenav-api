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
    SURVEY_STATUS_SURVEYED,
    OVERLAY_TYPE_SITE,
    OVERLAY_TYPE_ZONE,
    OVERLAY_TYPE_DRONEPORT,
    OVERLAY_TYPE_ROUTE,
)
    

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
"""
	    if site_review_result.rowcount != 1:
		raise Exception(f"Site overlay review not found: {site_id}")

	    if route_review_result.rowcount != route_result.rowcount:
		raise Exception("Route overlay review count mismatch")

	    if droneport_review_result.rowcount != droneport_result.rowcount:
		raise Exception("DronePort overlay review count mismatch")

	    if zone_review_result.rowcount != zone_result.rowcount:
		raise Exception("Zone overlay review count mismatch")
"""
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

