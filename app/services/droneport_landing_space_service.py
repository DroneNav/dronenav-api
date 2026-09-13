from __future__ import annotations

from app.config.constants import (
    DRONEPORT_LANDING_SPACE_OPERATIONAL_STATUSES,
    DRONEPORT_LANDING_SPACE_STATUS_ACTIVE,
    MAX_DRONEPORT_LANDING_SPACES,
)
from app.models.droneport_landing_space_model import (
    insert_droneport_landing_space,
    patch_droneport_landing_space,
    select_droneport_landing_space,
    select_droneport_landing_spaces,
    select_duplicate_droneport_landing_space,
    select_droneport_landing_space_counts,
)
from app.models.droneport_model import (
    select_droneport,
    select_droneport_point_containment,
)


def _validate_heading_degrees(value):
    try:
        heading = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            "heading_degrees must be numeric."
        )

    if heading < 0 or heading >= 360:
        raise ValueError(
            "heading_degrees must be greater than or equal "
            "to 0 and less than 360."
        )

    return heading


def _validate_charging_capable(value):
    if not isinstance(value, bool):
        raise ValueError(
            "charging_capable must be a boolean."
        )

    return value


def _validate_operational_status(value):
    if value not in DRONEPORT_LANDING_SPACE_OPERATIONAL_STATUSES:
        raise ValueError(
            "operational_status must be active or inactive."
        )

    return value


def _validate_geometry(geometry):
    if not isinstance(geometry, dict):
        raise ValueError(
            "geometry must be a GeoJSON Point."
        )

    if geometry.get("type") != "Point":
        raise ValueError(
            "geometry must be a GeoJSON Point."
        )

    coordinates = geometry.get("coordinates")

    if (
        not isinstance(coordinates, list)
        or len(coordinates) != 2
    ):
        raise ValueError(
            "geometry coordinates must contain "
            "[longitude, latitude]."
        )

    longitude, latitude = coordinates

    if not isinstance(longitude, (int, float)):
        raise ValueError(
            "geometry longitude must be numeric."
        )

    if not isinstance(latitude, (int, float)):
        raise ValueError(
            "geometry latitude must be numeric."
        )

    if longitude < -180 or longitude > 180:
        raise ValueError(
            "geometry longitude must be between -180 and 180."
        )

    if latitude < -90 or latitude > 90:
        raise ValueError(
            "geometry latitude must be between -90 and 90."
        )

    return geometry


def _validate_point_inside_droneport(
    *,
    droneport_id,
    geometry,
):
    longitude, latitude = geometry["coordinates"]

    containment = select_droneport_point_containment(
        droneport_id,
        {
            "longitude": longitude,
            "latitude": latitude,
        },
    )

    if containment is None:
        raise ValueError(
            "DronePort was not found."
        )

    if not containment["inside"]:
        raise ValueError(
            "Landing-space point must be within the DronePort."
        )


def _validate_unique_landing_space_point(
    *,
    droneport_id,
    geometry,
    exclude_landing_space_id=None,
):
    duplicate = select_duplicate_droneport_landing_space(
        droneport_id,
        geometry,
        exclude_landing_space_id=exclude_landing_space_id,
    )

    if duplicate is not None:
        raise ValueError(
            "A landing space already exists at this point."
        )


def create_droneport_landing_space(data):
    required_fields = {
        "droneport_id",
        "geometry",
        "created_by",
    }

    missing_fields = [
        field
        for field in required_fields
        if data.get(field) is None
    ]

    if missing_fields:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(sorted(missing_fields))
        )

    droneport = select_droneport(
        data["droneport_id"]
    )

    if droneport is None:
        raise ValueError(
            "DronePort was not found."
        )

    counts = select_droneport_landing_space_counts(
        data["droneport_id"]
    )

    if counts["total_count"] >= MAX_DRONEPORT_LANDING_SPACES:
        raise ValueError(
            "DronePort cannot have more than 16 landing spaces."
        )

    geometry = _validate_geometry(
        data["geometry"]
    )

    _validate_point_inside_droneport(
        droneport_id=data["droneport_id"],
        geometry=geometry,
    )

    _validate_unique_landing_space_point(
        droneport_id=data["droneport_id"],
        geometry=geometry,
    )

    heading_degrees = _validate_heading_degrees(
        data.get("heading_degrees", 0)
    )

    charging_capable = _validate_charging_capable(
        data.get("charging_capable", False)
    )

    operational_status = _validate_operational_status(
        data.get(
            "operational_status",
            DRONEPORT_LANDING_SPACE_STATUS_ACTIVE,
        )
    )

    landing_space_id = insert_droneport_landing_space(
        {
            "droneport_id": data["droneport_id"],
            "geometry": geometry,
            "heading_degrees": heading_degrees,
            "charging_capable": charging_capable,
            "operational_status": operational_status,
            "created_by": data["created_by"],
        }
    )

    return select_droneport_landing_space(
        landing_space_id
    )


def get_droneport_landing_space(
    landing_space_id,
):
    return select_droneport_landing_space(
        landing_space_id
    )


def get_droneport_landing_spaces(
    *,
    droneport_id=None,
    operational_status=None,
):
    if operational_status is not None:
        _validate_operational_status(
            operational_status
        )

    return select_droneport_landing_spaces(
        droneport_id=droneport_id,
        operational_status=operational_status,
    )


def update_droneport_landing_space(
    landing_space_id,
    data,
):
    existing = select_droneport_landing_space(
        landing_space_id
    )

    if existing is None:
        return None

    allowed_fields = {
        "geometry",
        "heading_degrees",
        "charging_capable",
        "operational_status",
    }

    unknown_fields = (
        set(data.keys()) - allowed_fields
    )

    if unknown_fields:
        raise ValueError(
            "Unsupported PATCH fields: "
            + ", ".join(sorted(unknown_fields))
        )

    patch = {}

    if "geometry" in data:
        geometry = _validate_geometry(
            data["geometry"]
        )

        _validate_point_inside_droneport(
            droneport_id=existing["droneport_id"],
            geometry=geometry,
        )

        _validate_unique_landing_space_point(
            droneport_id=existing["droneport_id"],
            geometry=geometry,
            exclude_landing_space_id=landing_space_id,
        )

        patch["geometry"] = geometry

    if "heading_degrees" in data:
        patch["heading_degrees"] = (
            _validate_heading_degrees(
                data["heading_degrees"]
            )
        )

    if "charging_capable" in data:
        patch["charging_capable"] = (
            _validate_charging_capable(
                data["charging_capable"]
            )
        )

    if "operational_status" in data:
        operational_status = _validate_operational_status(
            data["operational_status"]
        )

        if (
            existing["operational_status"] == "active"
            and operational_status == "inactive"
        ):
            counts = select_droneport_landing_space_counts(
                existing["droneport_id"]
            )

            if counts["active_count"] <= 1:
                raise ValueError(
                    "DronePort must have at least one active landing space."
                )

        patch["operational_status"] = operational_status

    return patch_droneport_landing_space(
        landing_space_id,
        patch,
    )

