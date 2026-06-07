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
System-wide constant definition file.

Author:
DroneNav Project Contributors

Created:
2026-06-04

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


""" DroneNav System Constants """

# ------------------------------------------------------------------
# Site Defaults
# ------------------------------------------------------------------

DEFAULT_MINIMUM_ALTITUDE_FT = 0
DEFAULT_MAXIMUM_ALTITUDE_FT = 400

# ------------------------------------------------------------------
# SRID
# ------------------------------------------------------------------

DEFAULT_SRID = 4326

# ------------------------------------------------------------------
# Site Types
# ------------------------------------------------------------------

SITE_TYPE_SCHOOL = "school"
SITE_TYPE_PARK = "park"
SITE_TYPE_COMMERCIAL = "commercial"
SITE_TYPE_GOVERNMENT = "government"
SITE_TYPE_PRIVATE = "private"
SITE_TYPE_RESIDENTIAL = "residential"

# -----------------------------------------------------------------
# Authority Types
# -----------------------------------------------------------------

AUTHORITY_TYPE_LOCAL_GOVERNMENT = "local_government"
AUTHORITY_TYPE_STATE_GOVERNMENT = "state_government"
AUTHORITY_TYPE_FEDERAL_GOVERNMENT = "federal_government"
AUTHORITY_TYPE_PRIVATE = "private"
AUTHORITY_TYPE_EDUCATIONAL = "educational"

DEFAULT_AUTHORITY_STATUS = "active"

# ------------------------------------------------------------------
# Site Statuses
# ------------------------------------------------------------------

SITE_STATUS_ACTIVE = "active"
SITE_STATUS_INACTIVE = "inactive"
SITE_STATUS_DELETED = "deleted"

DEFAULT_OPERATIONAL_STATUS = SITE_STATUS_INACTIVE

SITE_OVERLAY_LINE_TYPE = "site-overlay-line-type"
SITE_OVERLAY_LINE_COLOR = "site-overlay-line-color"
SITE_OVERLAY_FILL_PATTERN = "site-overlay-fill-pattern"
SITE_OVERLAY_FILL_COLOR = "site-overlay-fill-color"

# ------------------------------------------------------------------
# Zone Types
# ------------------------------------------------------------------

ZONE_TYPE_RESTRICTED = "restricted"
ZONE_TYPE_OPEN = "open"
ZONE_TYPE_CAUTION = "caution"
ZONE_TYPE_EMERGENCY = "emergency"
ZONE_TYPE_PRIVATE = "private"
ZONE_TYPE_INCLUSION = "inclusion"

# ------------------------------------------------------------------
# Zone Statuses
# ------------------------------------------------------------------

ZONE_STATUS_ACTIVE = "active"
ZONE_STATUS_INACTIVE = "inactive"
ZONE_STATUS_DELETED = "deleted"

DEFAULT_ZONE_STATUS = ZONE_STATUS_INACTIVE

ZONE_OVERLAY_LINE_TYPE = "zone-overlay-line-type"
ZONE_OVERLAY_LINE_COLOR = "zone-overlay-line-color"
ZONE_OVERLAY_FILL_PATTERN = "zone-overlay-fill-pattern"
ZONE_OVERLAY_FILL_COLOR = "zone-overlay-fill-color"

# ------------------------------------------------------------------
# Survey Statuses
# ------------------------------------------------------------------

SURVEY_STATUS_NOT_SURVEYED = "not_surveyed"
SURVEY_STATUS_SURVEYED = "surveyed"

DEFAULT_SURVEY_STATUS = SURVEY_STATUS_NOT_SURVEYED

# -----------------------------------------------------------------
# Authority Statuses
# -----------------------------------------------------------------

AUTHORITY_STATUS_ACTIVE = "active"
AUTHORITY_STATUS_INACTIVE = "inactive"
AUTHORITY_STATUS_DELETED = "deleted"

DEFAULT_AUTHORITY_STATUS = AUTHORITY_STATUS_ACTIVE

# ------------------------------------------------------------------
# DronePort Types
# ------------------------------------------------------------------

DRONEPORT_TYPE_RECREATION = "recreation"
DRONEPORT_TYPE_EMERGENCY = "emergency"
DRONEPORT_TYPE_COMMERCIAL = "commercial"
DRONEPORT_TYPE_EDUCATION = "education"
DRONEPORT_TYPE_MILITARY = "military"
DRONEPORT_TYPE_GOVERNMENT = "government"
DRONEPORT_TYPE_CIVIL = "civil"

# ------------------------------------------------------------------
# DronePort Statuses
# ------------------------------------------------------------------

DRONEPORT_STATUS_ACTIVE = "active"
DRONEPORT_STATUS_INACTIVE = "inactive"
DRONEPORT_STATUS_DELETED = "deleted"

DEFAULT_DRONEPORT_STATUS = DRONEPORT_STATUS_INACTIVE
DEFAULT_DRONEPORT_DIAMETER_FT = 25

DRONEPORT_OVERLAY_LINE_TYPE = "droneport-overlay-line-type"
DRONEPORT_OVERLAY_LINE_COLOR = "droneport-overlay-line-color"
DRONEPORT_OVERLAY_FILL_PATTERN = "droneport-overlay-fill-pattern"
DRONEPORT_OVERLAY_FILL_COLOR = "droneport-overlay-fill-color"


# ------------------------------------------------------------------
# Route Statuses
# ------------------------------------------------------------------

ROUTE_STATUS_ACTIVE = "active"
ROUTE_STATUS_INACTIVE = "inactive"
ROUTE_STATUS_DELETED = "deleted"

DEFAULT_ROUTE_STATUS = ROUTE_STATUS_INACTIVE

# ------------------------------------------------------------------
# Route Types 
# ------------------------------------------------------------------

ROUTE_TYPE_COMMERCIAL = "commercial"
ROUTE_TYPE_OPEN = "open"
ROUTE_TYPE_EMERGENCY = "emergency"

DEFAULT_MINIMUM_AIRCRAFT_WEIGHT_LBS = 1
DEFAULT_MAXIMUM_AIRCRAFT_WEIGHT_LBS = 50
DEFAULT_ROUTE_WIDTH_FT = 10
DEFAULT_ROUTE_DIRECTION = 0
DEFAULT_ROUTE_BUFFERED = 0
DEFAULT_ROUTE_SPEED_LIMIT_MPH = 15
DEFAULT_MINIMUM_SEGMENT_COUNT = 3
DEFAULT_MINIMUM_SEGMENT_ALTITUDE_FT = DEFAULT_MINIMUM_ALTITUDE_FT
DEFAULT_MAXIMUM_SEGMENT_ALTITUDE_FT = DEFAULT_MAXIMUM_ALTITUDE_FT

ROUTE_OVERLAY_LINE_TYPE = "route-overlay-line-type"
ROUTE_OVERLAY_LINE_COLOR = "route-overlay-line-color"


# -----------------------------------------------------------------
# Overlay Review Status
# -----------------------------------------------------------------
REVIEW_STATUS_PENDING = "pending_review"
REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_REJECTED = "rejected"
REVIEW_STATUS_SUBMITTED = "submitted"
REVIEW_STATUS_REVISIONS_REQUESTED = "revisions_requested"

VALID_REVIEW_STATUSES = {
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_SUBMITTED,
    REVIEW_STATUS_REVISIONS_REQUESTED
}

DEFAULT_REVIEW_STATUS = REVIEW_STATUS_PENDING

# -----------------------------------------------------------------
# Valid Overlay Types
# -----------------------------------------------------------------
OVERLAY_TYPE_SITE = "site"
OVERLAY_TYPE_ZONE = "zone"
OVERLAY_TYPE_DRONEPORT = "droneport"
OVERLAY_TYPE_ROUTE = "route"

VALID_OVERLAY_TYPES = {
    OVERLAY_TYPE_SITE,
    OVERLAY_TYPE_ZONE,
    OVERLAY_TYPE_DRONEPORT,
    OVERLAY_TYPE_ROUTE,
}

