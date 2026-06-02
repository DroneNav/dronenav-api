import json
import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from app.config.database import engine
from app.config.constants import (
    DEFAULT_MINIMUM_ALTITUDE_FT,
    DEFAULT_MAXIMUM_ALTITUDE_FT,
    DEFAULT_OPERATIONAL_STATUS,
    DEFAULT_SURVEY_STATUS,
    DEFAULT_SRID,
)

sites_bp = Blueprint("sites", __name__)


@sites_bp.route("/api/sites", methods=["POST"])
def create_site():
    data = request.get_json()

    required_fields = [
        "authority_id",
        "site_name",
        "site_type",
        "created_by",
        "geometry",
    ]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return jsonify({
                "status": "error",
                "message": f"Missing required field: {field}"
            }), 400

    geometry = data["geometry"]

    if geometry.get("type") != "Polygon":
        return jsonify({
            "status": "error",
            "message": "Site geometry must be a Polygon"
        }), 400

    minimum_altitude_ft = data.get(
        "minimum_altitude_ft",
        DEFAULT_MINIMUM_ALTITUDE_FT
    )

    maximum_altitude_ft = data.get(
        "maximum_altitude_ft",
        DEFAULT_MAXIMUM_ALTITUDE_FT
    )

    params = {
        "authority_id": data["authority_id"],
        "site_name": data["site_name"],
        "site_type": data["site_type"],
        "created_by": data["created_by"],
        "operational_status": DEFAULT_OPERATIONAL_STATUS,
        "survey_status": DEFAULT_SURVEY_STATUS,
        "minimum_altitude_ft": minimum_altitude_ft,
        "maximum_altitude_ft": maximum_altitude_ft,
        "geometry": json.dumps(geometry),
        "srid": DEFAULT_SRID,
    }

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
            params
        )

        site_id = str(result.scalar())

    return jsonify({
        "status": "created",
        "site_id": site_id,
        "site_name": data["site_name"]
    }), 201

@sites_bp.route("/api/sites/<site_id>", methods=["GET"])
def get_site(site_id):
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
            """),
            {
                "site_id": site_id
            }
        )

        row = result.mappings().first()

    if row is None:
        return jsonify({
            "status": "error",
            "message": "Site not found"
        }), 404

    return jsonify({
        "site_id": str(row["site_id"]),
        "authority_id": str(row["authority_id"]),
        "site_name": row["site_name"],
        "site_type": row["site_type"],
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "operational_status": row["operational_status"],
        "survey_status": row["survey_status"],
        "last_surveyed_at": row["last_surveyed_at"].isoformat() if row["last_surveyed_at"] else None,
        "surveyed_by": row["surveyed_by"],
        "approved_by": row["approved_by"],
        "minimum_altitude_ft": row["minimum_altitude_ft"],
        "maximum_altitude_ft": row["maximum_altitude_ft"],
        "geometry": row["geometry"]
    })

