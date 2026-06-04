import json

from sqlalchemy import text

from app.config.constants import DEFAULT_SRID, ROUTE_STATUS_DELETED
from app.config.database import engine


def insert_route(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO routes (
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    operational_status,
                    survey_status,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    buffered,
                    geometry,
                    segment_attributes
                )
                VALUES (
                    :origin_site_id,
                    :destination_site_id,
                    :origin_droneport_id,
                    :destination_droneport_id,
                    :route_name,
                    :route_type,
                    :created_by,
                    :operational_status,
                    :survey_status,
                    :minimum_aircraft_weight_lbs,
                    :maximum_aircraft_weight_lbs,
                    :direction,
                    :buffered,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    ),
                    CAST(:segment_attributes AS jsonb)
                )
                RETURNING route_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
                "segment_attributes": json.dumps(data["segment_attributes"]),
                "srid": DEFAULT_SRID,
            }
        )

        return str(result.scalar())


def select_route(route_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    route_id,
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    last_surveyed_at,
                    surveyed_by,
                    approved_by,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    buffered,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    segment_attributes
                FROM routes 
                WHERE route_id = :route_id
                  AND operational_status <> :deleted_status
            """),
            {
                "route_id": route_id,
                "deleted_status": ROUTE_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_routes():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    route_id,
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    buffered,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    segment_attributes
                FROM routes
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": ROUTE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def select_routes_by_site_id(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    route_id,
                    origin_site_id,
                    destination_site_id,
                    origin_droneport_id,
                    destination_droneport_id,
                    route_name,
                    route_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs,
                    direction,
                    buffered,
                    ST_AsGeoJSON(geometry)::json AS geometry,
                    segment_attributes
                FROM routes
                WHERE operational_status <> :deleted_status
                  AND (origin_site_id = :site_id OR destination_site_id = :site_id)
                ORDER BY created_at DESC
            """),
            {
                "site_id": site_id,
                "deleted_status": ROUTE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_route_record(route_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    origin_site_id = :origin_site_id,
                    destination_site_id = :destination_site_id,
                    origin_droneport_id = :origin_droneport_id,
                    destination_droneport_id = :destination_droneport_id,
                    route_name = :route_name,
                    route_type = :route_type,
                    created_by = :created_by,
                    minimum_aircraft_weight_lbs = :minimum_aircraft_weight_lbs,
                    maximum_aircraft_weight_lbs = :maximum_aircraft_weight_lbs,
                    direction = :direction,
                    buffered = :buffered,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    ),
                    segment_attributes = CAST(:segment_attributes AS jsonb)
                WHERE route_id = :route_id
                RETURNING route_id, route_name
            """),
            {
                **data,
                "route_id": route_id,
                "geometry": json.dumps(data["geometry"]),
                "segment_attributes": json.dumps(data["segment_attributes"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def soft_delete_route(route_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE routes
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE route_id = :route_id
                RETURNING route_id
            """),
            {
                "route_id": route_id,
                "status": ROUTE_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()

