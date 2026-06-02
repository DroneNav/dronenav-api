from sqlalchemy import text

from app.config.database import engine
from app.config.constants import AUTHORITY_STATUS_DELETED


def insert_authority(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO authorities (
                    authority_name,
                    authority_code,
                    authority_type,
                    operational_status,
                    contact_name,
                    contact_email,
                    contact_phone,
                    created_by
                )
                VALUES (
                    :authority_name,
                    :authority_code,
                    :authority_type,
                    :operational_status,
                    :contact_name,
                    :contact_email,
                    :contact_phone,
                    :created_by
                )
                RETURNING authority_id
            """),
            data
        )

        return str(result.scalar())


def select_authority(authority_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    authority_id,
                    authority_name,
                    authority_code,
                    authority_type,
                    operational_status,
                    contact_name,
                    contact_email,
                    contact_phone,
                    created_by,
                    created_at,
                    approved_by,
                    approved_at
                FROM authorities
                WHERE authority_id = :authority_id
                  AND operational_status <> :deleted_status
            """),
            {
                "authority_id": authority_id,
                "deleted_status": AUTHORITY_STATUS_DELETED,
            }
        )

        return result.mappings().first()


def select_authorities():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    authority_id,
                    authority_name,
                    authority_code,
                    authority_type,
                    operational_status,
                    contact_name,
                    contact_email,
                    contact_phone,
                    created_by,
                    created_at,
                    approved_by,
                    approved_at
                FROM authorities
                WHERE operational_status <> :deleted_status
                ORDER BY created_at DESC
            """),
            {
                "deleted_status": AUTHORITY_STATUS_DELETED,
            }
        )

        return result.mappings().all()


def update_authority_record(authority_id, data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE authorities
                SET
                    authority_name = :authority_name,
                    authority_code = :authority_code,
                    authority_type = :authority_type,
                    contact_name = :contact_name,
                    contact_email = :contact_email,
                    contact_phone = :contact_phone
                WHERE authority_id = :authority_id
                RETURNING authority_id, authority_name
            """),
            {
                **data,
                "authority_id": authority_id,
            }
        )

        return result.mappings().first()


def soft_delete_authority(authority_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE authorities
                SET
                    operational_status = :deleted_status
                WHERE authority_id = :authority_id
                RETURNING authority_id
            """),
            {
                "authority_id": authority_id,
                "deleted_status": AUTHORITY_STATUS_DELETED,
            }
        )

        return result.mappings().first()
