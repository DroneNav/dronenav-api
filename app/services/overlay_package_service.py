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
    survey_overlay_package_record
)


def survey_overlay_package(site_id, data):

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return None, "Survey payload must be an object"

    surveyed_by = data.get("surveyed_by")

    if surveyed_by in ("", None):
        return None, "Missing required field: surveyed_by"

    result, error = survey_overlay_package_record(
        site_id=site_id,
        surveyed_by=surveyed_by,
    )

    if error:
        return None, error

    return result, None


