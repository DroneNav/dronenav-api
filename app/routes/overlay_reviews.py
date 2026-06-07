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
Flask route implementation source file for governance APIs on overlays.

Author:
DroneNav Project Contributors

Created:
2026-06-05

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""


from flask import Blueprint, jsonify, request

from app.services.overlay_review_service import (
    get_overlay_review_by_id,
    get_overlay_reviews,
    get_overlay_by_type_and_id,
    get_overlay_history,
    get_governance_metrics,
    approve_overlay,
    reject_overlay,
    request_overlay_review_changes,
    submit_overlay,
)


overlay_reviews_bp = Blueprint("overlay_reviews", __name__)


@overlay_reviews_bp.route("/api/governance/overlay-reviews", methods=["GET"])
def get_overlay_reviews_route():

    filters = {
        "overlay_type": request.args.get("type"),
        "review_status": request.args.get("status"),
    }

    reviews, error = get_overlay_reviews(filters)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify({
        "reviews": reviews
    })


@overlay_reviews_bp.route("/api/governance/overlay-reviews/<review_id>", methods=["GET"])
def get_overlay_review_route(review_id):
    review = get_overlay_review_by_id(review_id)

    if review is None:
        return jsonify({
            "status": "error",
            "message": "Overlay Review not found"
        }), 404

    return jsonify(review)


@overlay_reviews_bp.route("/api/governance/overlays/<overlay_type>/<overlay_id>", methods=["GET"])
def get_overlay_route(overlay_type, overlay_id):
    overlay = get_overlay_by_type_and_id(overlay_type, overlay_id)

    if overlay is None:
        return jsonify({
            "status": "error",
            "message": "Overlay not found"
        }), 404

    return jsonify(overlay)


@overlay_reviews_bp.route("/api/governance/overlays/<overlay_id>/history", methods=["GET"])
def get_overlay_history_route(overlay_id):
    history = get_overlay_history(overlay_id)

    if history is None:
        return jsonify({
            "status": "error",
            "message": "Overlay history not found"
        }), 404

    return jsonify(history)


@overlay_reviews_bp.route("/api/governance/dashboard", methods=["GET"])
def get_governance_dashboard_route():
    
    metrics = get_governance_metrics()

    if metrics is None:
        return jsonify({
            "status": "error",
            "message": "Governance metrics not available"
        }), 404

    return jsonify(metrics)


@overlay_reviews_bp.route("/api/governance/overlays/<overlay_type>/<overlay_id>/approve", methods=["POST"])
def approve_overlay_route(overlay_type, overlay_id):

    data = request.get_json()

    result, error = approve_overlay(overlay_type, overlay_id, data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 200


@overlay_reviews_bp.route("/api/governance/overlays/<overlay_type>/<overlay_id>/reject", methods=["POST"])
def reject_overlay_route(overlay_type, overlay_id):

    data = request.get_json()

    result, error = reject_overlay(overlay_type, overlay_id, data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 200


@overlay_reviews_bp.route("/api/governance/overlays/<overlay_type>/<overlay_id>/request-changes", methods=["POST"])
def request_changes_overlay_route(overlay_type, overlay_id):

    data = request.get_json()

    result, error = request_overlay_review_changes(overlay_type, overlay_id, data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 200


@overlay_reviews_bp.route("/api/governance/overlays/<overlay_type>/<overlay_id>/submit", methods=["POST"])
def submit_overlay_route(overlay_type, overlay_id):

    data = request.get_json()

    result, error = submit_overlay(overlay_type, overlay_id, data)

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    return jsonify(result), 200

