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
# Survey Statuses
# ------------------------------------------------------------------

SURVEY_STATUS_NOT_SURVEYED = "not_surveyed"
SURVEY_STATUS_SURVEYED = "surveyed"

DEFAULT_SURVEY_STATUS = SURVEY_STATUS_NOT_SURVEYED


