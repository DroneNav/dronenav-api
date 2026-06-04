from app.config.constants import (
    DEFAULT_MINIMUM_SEGMENT_ALTITUDE_FT,
    DEFAULT_MAXIMUM_SEGMENT_ALTITUDE_FT,
    DEFAULT_MINIMUM_AIRCRAFT_WEIGHT_LBS,
    DEFAULT_MAXIMUM_AIRCRAFT_WEIGHT_LBS,
    DEFAULT_ROUTE_SPEED_LIMIT_MPH,
    DEFAULT_ROUTE_WIDTH_FT,
    DEFAULT_ROUTE_STATUS,
    DEFAULT_SURVEY_STATUS,
)

from app.models.route_model import (
    insert_route,
    select_route,
    select_routes,
    select_routes_by_site_id,
    select_routes_by_droneport_id,
    update_route_record,
    soft_delete_route,
)


def validate_route_payload(data):
    required_fields = [
        "origin_droneport_id",
        "destination_droneport_id",
        "route_name",
        "route_type",
        "created_by",
        "geometry",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    geometry = data["geometry"]

    if geometry.get("type") != "LineString":
        return "Route geometry must be a LineString"

    return None


def normalize_route_payload(data):
    return {
        "origin_droneport_id": data["origin_droneport_id"],
        "destination_droneport_id": data["destination_droneport_id"],
        "route_name": data["route_name"],
        "route_type": data["route_type"],
        "created_by": data["created_by"],
        "operational_status": DEFAULT_ROUTE_STATUS,
        "survey_status": DEFAULT_SURVEY_STATUS,
        "minimum_aircraft_weight_lbs": data["minimum_aircraft_weight_lbs"],
        "maximum_aircraft_weight_lbs": data["maximum_aircraft_weight_lbs"],
        "direction": data["direction"],
        "buffered": data["buffered"],
        "geometry": data["geometry"],
    }


def format_route(row):
    if row is None:
        return None

    return {
        "route_id": str(row["route_id"]),
        "origin_droneport_id": str(row["origin_droneport_id"]),
        "destination_droneport_id": str(row["destination_droneport_id"]),
        "route_name": row["route_name"],
        "route_type": row["route_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "last_surveyed_at": row.get("last_surveyed_at").isoformat()
            if row.get("last_surveyed_at") else None,
        "surveyed_by": row.get("surveyed_by"),
        "approved_by": row.get("approved_by"),
        "minimum_aircraft_weight_lbs": row["minimum_aircraft_weight_lbs"],
        "maximum_aircraft_weight_lbs": row["maximum_aircraft_weight_lbs"],
        "direction": row["direction"],
        "buffered": row["buffered"],
        "geometry": row["geometry"],
    }


def format_route_summary(row):
    return {
        "route_id": str(row["route_id"]),
        "origin_droneport_id": str(row["origin_droneport_id"]),
        "destination_droneport_id": str(row["destination_droneport_id"]),
        "route_name": row["route_name"],
        "route_type": row["route_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "minimum_aircraft_weight_lbs": row["minimum_aircraft_weight_lbs"],
        "maximum_aircraft_weight_lbs": row["maximum_aircraft_weight_lbs"],
        "direction": row["direction"],
        "buffered": row["buffered"],
        "geometry": row["geometry"],
    }


def create_route(data):
    error = validate_route_payload(data)

    if error:
        return None, error

    normalized_data = normalize_route_payload(data)
    route_id = insert_route(normalized_data)

    return {
        "status": "created",
        "route_id": route_id,
        "route_name": normalized_data["route_name"],
    }, None


def get_route_by_id(route_id):
    row = select_route(route_id)
    return format_route(row)


def get_routes_by_site_id(site_id):
    rows = select_routes_by_site_id(site_id)
    return [format_route_summary(row) for row in rows]


def get_routes_by_droneport_id(droneport_id):
    rows = select_routes_by_droneport_id(droneport_id)
    return [format_route_summary(row) for row in rows]


def get_all_routes():
    rows = select_routes()
    return [format_route_summary(row) for row in rows]


def update_route(route_id, data):
    error = validate_route_payload(data)

    if error:
        return None, error

    normalized_data = normalize_route_payload(data)
    row = update_route_record(route_id, normalized_data)

    if row is None:
        return None, "Route not found"

    return {
        "status": "updated",
        "route_id": str(row["route_id"]),
        "route_name": row["route_name"],
    }, None


def delete_route(route_id, deleted_by):
    row = soft_delete_route(route_id, deleted_by)

    if row is None:
        return None

    return {
        "status": "deleted",
        "route_id": str(row["route_id"]),
    }

