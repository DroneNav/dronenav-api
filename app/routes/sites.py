from flask import Blueprint, jsonify, request

from app.services.site_service import (
    create_site,
    get_site_by_id,
    get_all_sites,
    update_site,
    delete_site,
)
from app.services.zone_service import get_zones_by_site_id


sites_bp = Blueprint("sites", __name__)


@sites_bp.route("/api/sites", methods=["POST"])
def create_site_route():
    data = request.get_json()

    result, error = create_site(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@sites_bp.route("/api/sites", methods=["GET"])
def get_sites_route():
    sites = get_all_sites()

    return jsonify({
        "sites": sites
    })


@sites_bp.route("/api/sites/<site_id>", methods=["GET"])
def get_site_route(site_id):
    site = get_site_by_id(site_id)

    if site is None:
        return jsonify({
            "status": "error",
            "message": "Site not found"
        }), 404

    return jsonify(site)


@sites_bp.route("/api/sites/<site_id>/zones", methods=["GET"])
def get_site_zones_route(site_id):
    zones = get_zones_by_site_id(site_id)

    return jsonify({
        "site_id": site_id,
        "zones": zones
    })


@sites_bp.route("/api/sites/<site_id>", methods=["PUT"])
def update_site_route(site_id):
    data = request.get_json()

    result, error = update_site(site_id, data)

    if error:
        status_code = 404 if error == "Site not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@sites_bp.route("/api/sites/<site_id>", methods=["DELETE"])
def delete_site_route(site_id):
    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_site(site_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Site not found"
        }), 404

    return jsonify(result)

