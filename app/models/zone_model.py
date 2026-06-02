import json

from sqlalchemy import text

from app.config.constants import DEFAULT_SRID, ZONE_STATUS_DELETED
from app.config.database import engine


def insert_zone(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO zones (
                    site_id,
                    zone_name,
                    zone_type,
                    created_by,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    geometry
                )
                VALUES (
                    :site_id,
                    :zone_name,
                    :zone_type,
                    :created_by,
                    :operational_status,
                    :survey_status,
                    :minimum_altitude_ft,
                    :maximum_altitude_ft,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                )
                RETURNING zone_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return str(result.scalar())


def select_zone(zone_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    zone_id,
                    site_id,
                    zone_name,
                    zone_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    last_surveyed_at,
                    surveyed_by,
                    approved_by,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM zones 
                WHERE zone_id = :zone_id
                  AND operational_status <> :deleted_status
            """),
            {
                "zone_id": zone_id,
                "deleted_status": ZONE_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_zones():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    zone_id,
                    site_id,
                    zone_name,
                    zone_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM zones
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": ZONE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_zone_record(zone_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE zones
                SET
                    site_id = :site_id,
                    zone_name = :zone_name,
                    zone_type = :zone_type,
                    created_by = :created_by,
                    minimum_altitude_ft = :minimum_altitude_ft,
                    maximum_altitude_ft = :maximum_altitude_ft,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                WHERE zone_id = :zone_id
                RETURNING zone_id, zone_name
            """),
            {
                **data,
                "zone_id": zone_id,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def soft_delete_zone(zone_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE zones
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE zone_id = :zone_id
                RETURNING zone_id
            """),
            {
                "zone_id": zone_id,
                "status": ZONE_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()

