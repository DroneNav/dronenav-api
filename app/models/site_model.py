import json

from sqlalchemy import text

from app.config.constants import DEFAULT_SRID, SITE_STATUS_DELETED
from app.config.database import engine


def insert_site(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO sites (
                    authority_id,
                    site_name,
                    site_type,
                    created_by,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    geometry
                )
                VALUES (
                    :authority_id,
                    :site_name,
                    :site_type,
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
                RETURNING site_id
            """),
            {
                **data,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return str(result.scalar())


def select_site(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    site_id,
                    authority_id,
                    site_name,
                    site_type,
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
                FROM sites
                WHERE site_id = :site_id
                  AND operational_status <> :deleted_status
            """),
            {
                "site_id": site_id,
                "deleted_status": SITE_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_sites():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    site_id,
                    authority_id,
                    site_name,
                    site_type,
                    created_by,
                    created_at,
                    operational_status,
                    survey_status,
                    minimum_altitude_ft,
                    maximum_altitude_ft,
                    ST_AsGeoJSON(geometry)::json AS geometry
                FROM sites
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": SITE_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_site_record(site_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET
                    authority_id = :authority_id,
                    site_name = :site_name,
                    site_type = :site_type,
                    created_by = :created_by,
                    minimum_altitude_ft = :minimum_altitude_ft,
                    maximum_altitude_ft = :maximum_altitude_ft,
                    geometry = ST_SetSRID(
                        ST_GeomFromGeoJSON(:geometry),
                        :srid
                    )
                WHERE site_id = :site_id
                RETURNING site_id, site_name
            """),
            {
                **data,
                "site_id": site_id,
                "geometry": json.dumps(data["geometry"]),
                "srid": DEFAULT_SRID,
            }
        )

        return result.mappings().first()


def soft_delete_site(site_id, deleted_by):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE sites
                SET
                    operational_status = :status,
                    deleted_at = now(),
                    deleted_by = :deleted_by
                WHERE site_id = :site_id
                RETURNING site_id
            """),
            {
                "site_id": site_id,
                "status": SITE_STATUS_DELETED,
                "deleted_by": deleted_by,
            }
        )

        return result.mappings().first()
