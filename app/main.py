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
 Main driver/entry point for the DroneNav API application server.

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


from flask import Flask, jsonify, request
from flask_cors import CORS

from app.config.constants import load_reference_data
from app.config.database import check_database
from app.routes.authorities import authorities_bp
from app.routes.sites import sites_bp
from app.routes.zones import zones_bp
from app.routes.droneports import droneports_bp
from app.routes.routes import routes_bp
from app.routes.overlay_reviews import overlay_reviews_bp
from app.routes.overlay_package import overlay_package_bp
from app.routes.operational_readiness import operational_readiness_bp


app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "https://dronenav.org",
                "https://www.dronenav.org",
                "https://app.dronenav.org"
            ],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)


app.register_blueprint(authorities_bp)
app.register_blueprint(sites_bp)
app.register_blueprint(zones_bp)
app.register_blueprint(droneports_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(overlay_reviews_bp)
app.register_blueprint(overlay_package_bp)
app.register_blueprint(operational_readiness_bp)


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    allowed_origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://dronenav.org",
        "https://www.dronenav.org",
        "https://app.dronenav.org"
    }

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"

    return response


@app.route("/api/cors-test", methods=["GET", "OPTIONS"])
def cors_test():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify({"message": "cors test ok"})


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify({"status": "ok"})


@app.route("/api/system/database", methods=["GET", "OPTIONS"])
def database_status():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify(check_database())


@app.route("/api/reference-data", methods=["GET", "OPTIONS"])
def reference_data():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify(load_reference_data())
