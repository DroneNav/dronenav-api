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
Flask route implementation source file for a site based overlay package.

Author:
DroneNav Project Contributors

Created:
2026-06-11

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.site_service import (
    get_site_by_id,
)
from app.services.zone_service import (
    get_zones_by_site_id,
)
from app.services.droneport_service import (
    get_droneports_by_site_id,
)
from app.services.route_service import (
    get_routes_by_site_id,
)


overlay_package_bp = Blueprint("overlay_package", __name__)

CORS(
    overlay_package_bp,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


@overlay_package_bp.route("/api/sites/<site_id>/package", methods=["GET", "OPTIONS"])
def get_overlay_package_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    site = get_site_by_id(site_id)

    if site is None:
        return jsonify({
            "status": "error",
            "message": "Site not found"
        }), 404

    zones = get_zones_by_site_id(site_id)
    droneports = get_droneports_by_site_id(site_id)
    routes = get_routes_by_site_id(site_id)

    return jsonify({
        "site": site,
        "zones": zones or [],
        "droneports": droneports or [],
        "routes": routes or [],
    })

