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
VERTICAL_CONFORMANCE_MARGIN_FT = 10
VERTICAL_LAYER_SEPARATION_FT = 10
VERTICAL_LAYER_SPACING_FT = ( 2 * VERTICAL_CONFORMANCE_MARGIN_FT
                              + VERTICAL_LAYER_SEPARATION_FT )
MINIMUM_LONGITUDINAL_SEPARATION_FT = 500

DEFAULT_MINIMUM_ALTITUDE_FT = 0
DEFAULT_MAXIMUM_ALTITUDE_FT = 400
DEFAULT_START_TIME = "00:00"
DEFAULT_END_TIME = "23:59"
DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_ALLDAYS = (0, 1, 2, 3, 4, 5, 6)

EPQS_URL = "https://epqs.nationalmap.gov/v1/json"
FAA_TFR_WFS_URL = "https://tfr.faa.gov/geoserver/TFR/ows"
FAA_TFR_AIXM_URL = "https://tfr.faa.gov/download"
FAA_TFR_WEBTEXT_URL = "https://tfr.faa.gov/tfrapi/getWebText"
FAA_TFR_CACHE_TTL_SECONDS = 300

DEFAULT_API_BASE_URL = "https://api.dronenav.org"
DEFAULT_API_TIMEOUT_SECONDS = 15

# ------------------------------------------------------------------
# SCHEDULER CONFIGURATION
# ------------------------------------------------------------------

LAUNCH_WINDOW_EXPIRES_MINUTES = 30
LAUNCH_WINDOW_PREFLIGHT_MINUTES = 15
PREFLIGHT_DURATION_SECONDS = 30

ROUTE_SLOT_RETRY_COUNT = 5
ROUTE_SLOT_RETRY_SECONDS = 10

# Scheduler begins pre-flight this many minutes before the
# scheduled departure time.
SCHEDULER_PREFLIGHT_WINDOW_MINUTES = 5
# Scheduled flights older than this are considered missed.
# They will not be dispatched by the scheduler.
SCHEDULER_EXPIRATION_GRACE_MINUTES = 45

# Heartbeat managment
HEARTBEAT_LOSS_TIMEOUT_SECONDS = 5.0
HEARTBEAT_RECOVERY_WINDOW_SECONDS = 30.0

# ------------------------------------------------------------------
# FLIGHT LOG STATUS
# ------------------------------------------------------------------

FLIGHT_LOG_STATUS_PRE_FLIGHT = "pre_flight"
FLIGHT_LOG_STATUS_IN_FLIGHT = "in_flight"
FLIGHT_LOG_STATUS_COMPLETED = "completed"
FLIGHT_LOG_STATUS_ABORTED = "aborted"
FLIGHT_LOG_STATUS_FAILED = "failed"

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

# ------------------------------------------------------------------
# Zone Types
# ------------------------------------------------------------------

ZONE_TYPE_RESTRICTED = "restricted"
ZONE_TYPE_OPEN = "open"
ZONE_TYPE_CAUTION = "hazardous"
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

# ------------------------------------------------------------------
# Survey Statuses
# ------------------------------------------------------------------

SURVEY_STATUS_NOT_SURVEYED = "not_surveyed"
SURVEY_STATUS_SURVEYED = "surveyed"
SURVEY_STATUS_SUBMITTED = "submitted"
SURVEY_STATUS_APPROVED = "approved"

DEFAULT_SURVEY_STATUS = SURVEY_STATUS_NOT_SURVEYED

VALID_SURVEY_STATUSES = {
    SURVEY_STATUS_SUBMITTED,
    SURVEY_STATUS_SURVEYED,
    SURVEY_STATUS_NOT_SURVEYED,
    SURVEY_STATUS_APPROVED
}

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
DEFAULT_DRONEPORT_DIAMETER_FT = 30
TRANSITION_DIAMETER_FT = DEFAULT_DRONEPORT_DIAMETER_FT

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
ROUTE_TYPE_RACEWAY = "raceway"

DEFAULT_MINIMUM_AIRCRAFT_WEIGHT_LBS = 1
DEFAULT_MAXIMUM_AIRCRAFT_WEIGHT_LBS = 50
DEFAULT_ROUTE_WIDTH_FT = 30
DEFAULT_ROUTE_DIRECTION = 0
DEFAULT_ROUTE_BUFFERED = 0
DEFAULT_ROUTE_SPEED_LIMIT_MPH = 15
DEFAULT_MINIMUM_SEGMENT_COUNT = 3
DEFAULT_MINIMUM_SEGMENT_ALTITUDE_FT = DEFAULT_MINIMUM_ALTITUDE_FT
DEFAULT_MAXIMUM_SEGMENT_ALTITUDE_FT = DEFAULT_MAXIMUM_ALTITUDE_FT

# --------------------------------------------------------------
# Flight Execution Status
# --------------------------------------------------------------
EXECUTION_STATUS_ACTIVE = "active"
EXECUTION_STATUS_COMPLETED = "completed"
EXECUTION_STATUS_DISPATCHED = "dispatched"
EXECUTION_STATUS_EXPIRED = "expired"
EXECUTION_STATUS_SUSPENDED = "suspended"
EXECUTION_STATUS_REVOKED = "revoked"
EXECUTION_STATUS_CANCELLED = "cancelled"

# -----------------------------------------------------------------
# Flight Classes
# -----------------------------------------------------------------
FLIGHT_CLASS_AGRICULTURE = "Agriculture"
FLIGHT_CLASS_COMMERCIAL = "Commercial"
FLIGHT_CLASS_DELIVERY = "Delivery"
FLIGHT_CLASS_EMERGENCY = "Emergency"
FLIGHT_CLASS_INSPECTION = "Inspection"
FLIGHT_CLASS_PHOTOGRAPHY = "Photography"
FLIGHT_CLASS_PUBLICSAFETY = "Public Safety"
FLIGHT_CLASS_RECREATIONAL = "Recreational"
FLIGHT_CLASS_EDUCATIONAL = "Educational"
FLIGHT_CLASS_RESEARCH = "Research"
FLIGHT_CLASS_SURVEY = "Survey"
FLIGHT_CLASS_TRAINING = "Training"
FLIGHT_CLASS_RACING = "Racing"

VALID_FLIGHT_CLASSES = {
    FLIGHT_CLASS_AGRICULTURE,
    FLIGHT_CLASS_COMMERCIAL,
    FLIGHT_CLASS_DELIVERY,
    FLIGHT_CLASS_EMERGENCY,
    FLIGHT_CLASS_INSPECTION,
    FLIGHT_CLASS_PHOTOGRAPHY,
    FLIGHT_CLASS_PUBLICSAFETY,
    FLIGHT_CLASS_RECREATIONAL,
    FLIGHT_CLASS_EDUCATIONAL,
    FLIGHT_CLASS_RESEARCH,
    FLIGHT_CLASS_SURVEY,
    FLIGHT_CLASS_TRAINING,
    FLIGHT_CLASS_RACING
}

DEFAULT_FLIGHT_CLASS = FLIGHT_CLASS_RECREATIONAL

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
    OVERLAY_TYPE_ROUTE
}


OVERLAY_TYPES = {
  OVERLAY_TYPE_SITE: "Site",
  OVERLAY_TYPE_ZONE: "Zone",
  OVERLAY_TYPE_DRONEPORT: "Droneport",
  OVERLAY_TYPE_ROUTE: "Route"
},

SITE_OPERATIONAL_STATUSES = {
    SITE_STATUS_ACTIVE: "Active",
    SITE_STATUS_INACTIVE: "Inactive",
    SITE_STATUS_DELETED: "Deleted"
}
 
ZONE_OPERATIONAL_STATUSES = {
    ZONE_STATUS_ACTIVE: "Active",
    ZONE_STATUS_INACTIVE: "Inactive",
    ZONE_STATUS_DELETED: "Deleted"
}

DRONEPORT_OPERATIONAL_STATUSES = {
    DRONEPORT_STATUS_ACTIVE: "Active",
    DRONEPORT_STATUS_INACTIVE: "Inactive",
    DRONEPORT_STATUS_DELETED: "Deleted"
}

ROUTE_OPERATIONAL_STATUSES = {
    ROUTE_STATUS_ACTIVE: "Active",
    ROUTE_STATUS_INACTIVE: "Inactive",
    ROUTE_STATUS_DELETED: "Deleted"
}

SITE_TYPES = {
    SITE_TYPE_SCHOOL: "School",
    SITE_TYPE_PARK: "Park",
    SITE_TYPE_COMMERCIAL: "Commercial",
    SITE_TYPE_GOVERNMENT: "Government",
    SITE_TYPE_PRIVATE: "Private",
    SITE_TYPE_RESIDENTIAL: "Residential"
}

ZONE_TYPES = {
  ZONE_TYPE_RESTRICTED: "Restricted",
  ZONE_TYPE_OPEN: "Open",
  ZONE_TYPE_CAUTION: "Hazardous",
  ZONE_TYPE_EMERGENCY: "Emergency",
  ZONE_TYPE_PRIVATE: "Private",
  ZONE_TYPE_INCLUSION: "Inclusion"
}

SURVEY_STATUSES = {
  SURVEY_STATUS_SUBMITTED: "Submitted",
  SURVEY_STATUS_SURVEYED: "Surveyed",
  SURVEY_STATUS_NOT_SURVEYED: "Not surveyed",
  SURVEY_STATUS_APPROVED: "Approved"
}

OVERLAY_REVIEW_STATUSES = {
  REVIEW_STATUS_PENDING: "Pending review",
  REVIEW_STATUS_APPROVED: "Approved",
  REVIEW_STATUS_REJECTED: "Rejected",
  REVIEW_STATUS_SUBMITTED: "Submitted",
  REVIEW_STATUS_REVISIONS_REQUESTED: "Revisions requested"
}

DRONEPORT_TYPES = {
  DRONEPORT_TYPE_CIVIL: "Civil",
  DRONEPORT_TYPE_EDUCATION: "Educational",
  DRONEPORT_TYPE_RECREATION: "Recreation",
  DRONEPORT_TYPE_EMERGENCY: "Emergency",
  DRONEPORT_TYPE_COMMERCIAL: "Commercial",
  DRONEPORT_TYPE_MILITARY: "Military",
  DRONEPORT_TYPE_GOVERNMENT: "Government"
}

ROUTE_TYPES = {
  ROUTE_TYPE_OPEN: "Open",
  ROUTE_TYPE_COMMERCIAL: "Commercial",
  ROUTE_TYPE_EMERGENCY: "Emergency",
  ROUTE_TYPE_RACEWAY: "Raceway"
}

FLIGHT_CLASSES = {
    FLIGHT_CLASS_AGRICULTURE: "Agriculture",
    FLIGHT_CLASS_COMMERCIAL: "Commercial",
    FLIGHT_CLASS_DELIVERY: "Delivery",
    FLIGHT_CLASS_EMERGENCY: "Emergency",
    FLIGHT_CLASS_INSPECTION: "Inspection",
    FLIGHT_CLASS_PHOTOGRAPHY: "Photography",
    FLIGHT_CLASS_PUBLICSAFETY: "Public Safety",
    FLIGHT_CLASS_RECREATIONAL: "Recreational",
    FLIGHT_CLASS_EDUCATIONAL: "Educational",
    FLIGHT_CLASS_RESEARCH: "Research",
    FLIGHT_CLASS_SURVEY: "Survey",
    FLIGHT_CLASS_TRAINING: "Training",
    FLIGHT_CLASS_RACING: "Racing"
}


def load_reference_data():

    return {
        "overlay_type": OVERLAY_TYPES,
        "site_type": SITE_TYPES,
        "zone_type": ZONE_TYPES,
        "droneport_type": DRONEPORT_TYPES,
        "route_type":  ROUTE_TYPES,
        "site_operational_status": SITE_OPERATIONAL_STATUSES,
        "zone_operational_status": ZONE_OPERATIONAL_STATUSES,
        "droneport_operational_status": DRONEPORT_OPERATIONAL_STATUSES,
        "route_operational_status": ROUTE_OPERATIONAL_STATUSES,
        "survey_status": SURVEY_STATUSES,
        "overlay_review_status": OVERLAY_REVIEW_STATUSES,
        "flight_class": FLIGHT_CLASSES,
    } # end...return

