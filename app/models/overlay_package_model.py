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

Created:
2026-06-12

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from sqlalchemy import text

from app.config.database import engine
from app.config.constants import SURVEY_STATUS_SURVEYED


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

            if site_result.rowcount != 1:
                raise Exception(f"Site not found: {site_id}")

            return {
                "status": "surveyed",
                "site_id": site_id,
                "surveyed_by": surveyed_by,
                "routes_surveyed": route_result.rowcount,
                "droneports_surveyed": droneport_result.rowcount,
                "zones_surveyed": zone_result.rowcount,
                "sites_surveyed": site_result.rowcount,
            }, None

    except Exception as e:
        return None, str(e)

