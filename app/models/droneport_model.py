import json

from sqlalchemy import text

from app.config.constants import DEFAULT_SRID, DRONEPORT_STATUS_DELETED
from app.config.database import engine


def insert_droneport(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO droneports (
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    operational_status,
                    survey_status,
                    droneport_diameter_ft,
                    geometry 
                )
                VALUES (
                    :site_id,
                    :droneport_name,
                    :droneport_type,
                    :created_by,
                    :operational_status,
                    :survey_status,
                    :droneport_diameter_ft,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                )
                RETURNING droneport_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return str(result.scalar())


def select_droneport(droneport_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    droneport_id,
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    last_surveyed_at,
                    surveyed_by,
                    approved_by,
                    droneport_diameter_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneports 
                WHERE droneport_id = :droneport_id
                  AND operational_status <> :deleted_status
            """),
            {
                "droneport_id": droneport_id,
                "deleted_status": DRONEPORT_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_droneports():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    droneport_id,
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    droneport_diameter_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneports
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": DRONEPORT_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def select_droneports_by_site_id(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    droneport_id,
                    site_id,
                    droneport_name,
                    droneport_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    droneport_diameter_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM droneports
                WHERE operational_status <> :deleted_status
                  AND site_id = :site_id
                ORDER BY created_at DESC
            """),
            {
                "site_id": site_id,
                "deleted_status": DRONEPORT_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_droneport_record(droneport_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE droneports
                SET
                    site_id = :site_id,
                    droneport_name = :droneport_name,
                    droneport_type = :droneport_type,
                    created_by = :created_by,
                    droneport_diameter_ft = :droneport_diameter_ft,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                WHERE droneport_id = :droneport_id
                RETURNING droneport_id, droneport_name
            """),
            {
                **data,
                "droneport_id": droneport_id,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def soft_delete_droneport(droneport_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE droneports
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE droneport_id = :droneport_id
                RETURNING droneport_id
            """),
            {
                "droneport_id": droneport_id,
                "status": DRONEPORT_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()

