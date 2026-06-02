from app.config.constants import DEFAULT_AUTHORITY_STATUS

from app.models.authority_model import (
    insert_authority,
    select_authority,
    select_authorities,
    update_authority_record,
    soft_delete_authority,
)


def validate_authority_payload(data):
    required_fields = [
        "authority_name",
        "authority_code",
        "authority_type",
        "created_by",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return f"Missing required field: {field}"

    return None


def normalize_authority_payload(data):
    return {
        "authority_name": data["authority_name"],
        "authority_code": data["authority_code"],
        "authority_type": data["authority_type"],
        "operational_status": data.get(
            "operational_status",
            DEFAULT_AUTHORITY_STATUS
        ),
        "contact_name": data.get("contact_name"),
        "contact_email": data.get("contact_email"),
        "contact_phone": data.get("contact_phone"),
        "created_by": data["created_by"],
    }


def format_authority(row):
    if row is None:
        return None

    return {
        "authority_id": str(row["authority_id"]),
        "authority_name": row["authority_name"],
        "authority_code": row["authority_code"],
        "authority_type": row["authority_type"],
        "operational_status": row["operational_status"],
        "contact_name": row["contact_name"],
        "contact_email": row["contact_email"],
        "contact_phone": row["contact_phone"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "approved_by": row["approved_by"],
        "approved_at": row["approved_at"].isoformat() if row["approved_at"] else None,
    }


def create_authority(data):
    error = validate_authority_payload(data)

    if error:
        return None, error

    normalized_data = normalize_authority_payload(data)
    authority_id = insert_authority(normalized_data)

    return {
        "status": "created",
        "authority_id": authority_id,
        "authority_name": normalized_data["authority_name"],
    }, None


def get_authority_by_id(authority_id):
    row = select_authority(authority_id)
    return format_authority(row)


def get_all_authorities():
    rows = select_authorities()
    return [format_authority(row) for row in rows]


def update_authority(authority_id, data):
    error = validate_authority_payload(data)

    if error:
        return None, error

    normalized_data = normalize_authority_payload(data)
    row = update_authority_record(authority_id, normalized_data)

    if row is None:
        return None, "Authority not found"

    return {
        "status": "updated",
        "authority_id": str(row["authority_id"]),
        "authority_name": row["authority_name"],
    }, None


def delete_authority(authority_id):
    row = soft_delete_authority(authority_id)

    if row is None:
        return None

    return {
        "status": "deleted",
        "authority_id": str(row["authority_id"]),
    }

