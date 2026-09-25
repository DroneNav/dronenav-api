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
Obstacles API route layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-09-25

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from app.services.obstacle_service import (
    create_obstacle,
    get_obstacle_by_id,
    get_obstacles,
    get_obstacles_by_site_id,
    patch_obstacle,
    delete_obstacle,
    create_obstacle_collection,
    get_obstacle_collection_by_id,
    get_obstacle_collections,
    patch_obstacle_collection_record,
    delete_obstacle_collection_record,
    add_obstacle_to_collection,
    remove_obstacle_from_collection,
    get_obstacles_by_collection_id,
)


obstacles_bp = Blueprint("obstacles", __name__)

CORS(
    obstacles_bp,
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


@obstacles_bp.route("/api/obstacles", methods=["POST", "OPTIONS"])
def create_obstacle_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_obstacle(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@obstacles_bp.route("/api/obstacles", methods=["GET", "OPTIONS"])
def get_obstacles_route():

    if request.method == "OPTIONS":
        return "", 204

    survey_status = request.args.get("survey_status")

    obstacles = get_obstacles(survey_status)

    return jsonify({
        "obstacles": obstacles
    })


@obstacles_bp.route("/api/obstacles/<obstacle_id>", methods=["GET", "OPTIONS"])
def get_obstacle_route(obstacle_id):

    if request.method == "OPTIONS":
        return "", 204

    obstacle = get_obstacle_by_id(obstacle_id)

    if obstacle is None:
        return jsonify({
            "status": "error",
            "message": "Obstacle not found"
        }), 404

    return jsonify(obstacle)


@obstacles_bp.route("/api/obstacles/<obstacle_id>", methods=["PATCH", "OPTIONS"])
def patch_obstacle_route(obstacle_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_obstacle(obstacle_id, data)

    if error:
        status_code = 404 if error == "Obstacle not found" else 400

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@obstacles_bp.route("/api/obstacles/<obstacle_id>", methods=["DELETE", "OPTIONS"])
def delete_obstacle_route(obstacle_id):

    if request.method == "OPTIONS":
        return "", 204

    deleted_by = request.args.get("deleted_by", "dronenav")

    result = delete_obstacle(obstacle_id, deleted_by)

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Obstacle not found"
        }), 404

    return jsonify(result)


@obstacles_bp.route("/api/obstacles/site/<site_id>", methods=["GET", "OPTIONS"])
def get_obstacles_by_site_route(site_id):

    if request.method == "OPTIONS":
        return "", 204

    obstacles = get_obstacles_by_site_id(site_id)

    return jsonify({
        "obstacles": obstacles
    })


@obstacles_bp.route("/api/obstacle-collections", methods=["POST", "OPTIONS"])
def create_obstacle_collection_route():

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = create_obstacle_collection(data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 201


@obstacles_bp.route("/api/obstacle-collections", methods=["GET", "OPTIONS"])
def get_obstacle_collections_route():

    if request.method == "OPTIONS":
        return "", 204

    collections = get_obstacle_collections()

    return jsonify({
        "obstacle_collections": collections
    })


@obstacles_bp.route("/api/obstacle-collections/<obstacle_collection_id>", methods=["GET", "OPTIONS"])
def get_obstacle_collection_route(obstacle_collection_id):

    if request.method == "OPTIONS":
        return "", 204

    collection = get_obstacle_collection_by_id(
        obstacle_collection_id
    )

    if collection is None:
        return jsonify({
            "status": "error",
            "message": "Obstacle collection not found"
        }), 404

    return jsonify(collection)


@obstacles_bp.route("/api/obstacle-collections/<obstacle_collection_id>", methods=["PATCH", "OPTIONS"])
def patch_obstacle_collection_route(obstacle_collection_id):

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()

    result, error = patch_obstacle_collection_record(
        obstacle_collection_id,
        data,
    )

    if error:
        status_code = (
            404
            if error == "Obstacle collection not found"
            else 400
        )

        return jsonify({
            "status": "error",
            "message": error
        }), status_code

    return jsonify(result)


@obstacles_bp.route("/api/obstacle-collections/<obstacle_collection_id>", methods=["DELETE", "OPTIONS"])
def delete_obstacle_collection_route(obstacle_collection_id):

    if request.method == "OPTIONS":
        return "", 204

    result = delete_obstacle_collection_record(
        obstacle_collection_id
    )

    if result is None:
        return jsonify({
            "status": "error",
            "message": "Obstacle collection not found"
        }), 404

    return jsonify(result)


@obstacles_bp.route("/api/obstacle-collections/<obstacle_collection_id>/obstacles", methods=["GET", "OPTIONS"])
def get_obstacle_collection_members_route(obstacle_collection_id):

    if request.method == "OPTIONS":
        return "", 204

    obstacles = get_obstacles_by_collection_id(
        obstacle_collection_id
    )

    return jsonify({
        "obstacles": obstacles
    })


@obstacles_bp.route("/api/obstacle-collections/<obstacle_collection_id>/obstacles/<obstacle_id>", methods=["POST", "OPTIONS"])
def add_obstacle_to_collection_route(
    obstacle_collection_id,
    obstacle_id,
):

    if request.method == "OPTIONS":
        return "", 204

    result = add_obstacle_to_collection(
        obstacle_collection_id,
        obstacle_id,
    )

    return jsonify(result), 201


@obstacles_bp.route("/api/obstacle-collections/<obstacle_collection_id>/obstacles/<obstacle_id>", methods=["DELETE", "OPTIONS"])
def remove_obstacle_from_collection_route(
    obstacle_collection_id,
    obstacle_id,
):

    if request.method == "OPTIONS":
        return "", 204

    result = remove_obstacle_from_collection(
        obstacle_collection_id,
        obstacle_id,
    )

    return jsonify(result)



