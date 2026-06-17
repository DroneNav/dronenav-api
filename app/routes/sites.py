"""
DroneNav - Drone Navigation Network System
Copyright (C) 2026 DroneNav Project

This file is part of DroneNav.

DroneNav is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

DroneNav is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with DroneNav. If not, see https://www.gnu.org/licenses/.

Project:
DroneNav - Drone Navigation Network System

Repository:
https://github.com/DroneNav

License:
GNU Affero General Public License v3.0 (AGPL-3.0-or-later)

Purpose:
Flask route implementation source file for support of Site APIs.

Author:
DroneNav Project Contributors

Created:
2026-06-04

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.site_service import (
    create_site,
    get_site_by_id,
    get_all_sites,
    update_site,
    patch_site,
    delete_site,
)
from app.services.zone_service import get_zones_by_site_id
from app.services.droneport_service import get_droneports_by_site_id
from app.services.route_service import get_routes_by_site_id


sites_bp = Blueprint("sites", __name__)

CORS(
    sites_bp,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


@sites_bp.route("/api/sites", methods=["POST", "OPTIONS"])
def create_site_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_site(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@sites_bp.route("/api/sites", methods=["GET", "OPTIONS"])
def get_sites_route():

    if request.method == "OPTIONS":
        return "", 204

    survey_status = request.args.get("survey_status")

    sites = get_all_sites(survey_status)

    return jsonify({
        "sites": sites
    })


@sites_bp.route("/api/sites/<site_id>", methods=["GET", "OPTIONS"])
def get_site_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    site = get_site_by_id(site_id)

    if site is None:
        return jsonify({
            "status": "error",
            "message": "Site not found"
        }), 404

    return jsonify(site)


@sites_bp.route("/api/sites/<site_id>/zones", methods=["GET", "OPTIONS"])
def get_site_zones_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    zones = get_zones_by_site_id(site_id)

    return jsonify({
        "site_id": site_id,
        "zones": zones
    })


@sites_bp.route("/api/sites/<site_id>/droneports", methods=["GET", "OPTIONS"])
def get_site_droneports_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    droneports = get_droneports_by_site_id(site_id)

    return jsonify({
        "site_id": site_id,
        "droneports": droneports
    })


@sites_bp.route("/api/sites/<site_id>/routes", methods=["GET", "OPTIONS"])
def get_site_routes_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    routes = get_routes_by_site_id(site_id)

    return jsonify({
        "site_id": site_id,
        "routes": routes
    })


@sites_bp.route("/api/sites/<site_id>", methods=["PUT", "OPTIONS"])
def update_site_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = update_site(site_id, data)

    if error:
        status_code = 404 if error == "Site not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@sites_bp.route("/api/sites/<site_id>", methods=["PATCH", "OPTIONS"])
def patch_site_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_site(site_id, data)

    if error:
        status_code = 404 if error == "Site not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@sites_bp.route("/api/sites/<site_id>", methods=["DELETE", "OPTIONS"])
def delete_site_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_site(site_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Site not found"
        }), 404

    return jsonify(result)

