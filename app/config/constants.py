"""
DroneNav System Constants
"""

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
ZONE_TYPE_CAUTION = "caution"
ZONE_TYPE_EMERGENCY = "emergency"
ZONE_TYPE_CLOSED = "closed"

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
DEFAULT_MAXIMUM_AIRCRAFT_WEIGHT_LBS = 10
DEFAULT_ROUTE_WIDTH_FT = 10
DEFAULT_ROUTE_SPEED_LIMIT_MPH = 15
DEFAULT_MINIMUM_SEGMENT_ALTITUDE_FT = DEFAULT_MINIMUM_ALTITUDE_FT
DEFAULT_MAXIMUM_SEGMENT_ALTITUDE_FT = DEFAULT_MAXIMUM_ALTITUDE_FT

