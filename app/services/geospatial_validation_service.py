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
Geospatial validation layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-11

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.

---

Geospatial validation service for Flight Execution processing.

This service validates:

- Site existence
- Site operational status
- Site authority ownership
- DronePort existence
- DronePort operational status
- DronePort-to-Site relationships
- Route existence
- Route operational status
- Route endpoint Site validation
- Ordered Flight Path continuity
"""

from app.models.site_model import select_site
from app.models.droneport_model import select_droneport
from app.models.route_model import select_route


ACTIVE_STATUS = "active"


def validate_operational_geospatial_data(data):
    errors = []

    authority_id = str(data["authority_id"])
    origin_site_id = str(data["origin_site_id"])
    destination_site_id = str(data["destination_site_id"])

    origin_site = select_site(origin_site_id)
    destination_site = select_site(destination_site_id)

    errors.extend(
        _validate_site(
            site=origin_site,
            field_name="origin_site_id",
            site_label="origin Site",
            expected_authority_id=authority_id,
        )
    )

    errors.extend(
        _validate_site(
            site=destination_site,
            field_name="destination_site_id",
            site_label="destination Site",
            expected_authority_id=authority_id,
        )
    )

    # DronePort and Route relationship validation depends on valid Site
    # records. Return the Site errors before attempting those checks.
    if origin_site is None or destination_site is None:
        return errors

    departure_droneport_id = data.get("departure_droneport_id")

    if departure_droneport_id is not None:
        departure_droneport = select_droneport(
            str(departure_droneport_id)
        )

        errors.extend(
            _validate_droneport(
                droneport=departure_droneport,
                field_name="departure_droneport_id",
                droneport_label="departure DronePort",
                expected_site_id=origin_site_id,
            )
        )

    arrival_droneport_id = data.get("arrival_droneport_id")

    if arrival_droneport_id is not None:
        arrival_droneport = select_droneport(
            str(arrival_droneport_id)
        )

        errors.extend(
            _validate_droneport(
                droneport=arrival_droneport,
                field_name="arrival_droneport_id",
                droneport_label="arrival DronePort",
                expected_site_id=destination_site_id,
            )
        )


    is_cross_site = origin_site_id != destination_site_id

    if is_cross_site and departure_droneport_id is None:
        errors.append({
            "field": "departure_droneport_id",
            "code": "departure_droneport_required",
            "message": (
                "A departure DronePort is required for a "
                "cross-site Flight Plan."
            ),
        })

    if is_cross_site and arrival_droneport_id is None:
        errors.append({
            "field": "arrival_droneport_id",
            "code": "arrival_droneport_required",
            "message": (
                "An arrival DronePort is required for a "
                "cross-site Flight Plan."
            ),
        })


    flight_path_ids = data.get("flight_path_ids", [])

    # An empty Flight Path is valid.
    if not flight_path_ids:
        return errors

    route_errors, routes = _load_and_validate_routes(
        flight_path_ids=flight_path_ids,
        expected_authority_id=authority_id,
    )

    errors.extend(route_errors)

    # Continuity validation requires every Route and endpoint Site to
    # have loaded and passed the operational checks.
    if route_errors:
        return errors

    errors.extend(
        _validate_ordered_route_sequence(
            routes=routes,
            origin_site_id=origin_site_id,
            destination_site_id=destination_site_id,
        )
    )

    if errors:
        return errors

    errors.extend(
        _validate_terminal_droneports(
            routes=routes,
            departure_droneport_id=departure_droneport_id,
            arrival_droneport_id=arrival_droneport_id,
        )
    )

    return errors


def _validate_terminal_droneports(
    routes,
    departure_droneport_id,
    arrival_droneport_id,
):
    errors = []

    first_route = routes[0]
    last_route = routes[-1]

    if departure_droneport_id is None:
        errors.append({
            "field": "departure_droneport_id",
            "code": "departure_droneport_required",
            "message": (
                "A departure DronePort is required when a Flight Path "
                "is specified."
            ),
        })
    elif str(first_route["origin_droneport_id"]) != str(
        departure_droneport_id
    ):
        errors.append({
            "field": "departure_droneport_id",
            "code": "departure_droneport_route_mismatch",
            "message": (
                "The selected departure DronePort must be the origin "
                "DronePort of the first Route in the Flight Path."
            ),
        })

    if arrival_droneport_id is None:
        errors.append({
            "field": "arrival_droneport_id",
            "code": "arrival_droneport_required",
            "message": (
                "An arrival DronePort is required when a Flight Path "
                "is specified."
            ),
        })
    elif str(last_route["destination_droneport_id"]) != str(
        arrival_droneport_id
    ):
        errors.append({
            "field": "arrival_droneport_id",
            "code": "arrival_droneport_route_mismatch",
            "message": (
                "The selected arrival DronePort must be the destination "
                "DronePort of the final Route in the Flight Path."
            ),
        })

    return errors


def _validate_site(
    site,
    field_name,
    site_label,
    expected_authority_id,
):
    errors = []

    if site is None:
        errors.append({
            "field": field_name,
            "code": "site_not_found",
            "message": f"The {site_label} was not found.",
        })

        return errors

    if site["operational_status"] != ACTIVE_STATUS:
        errors.append({
            "field": field_name,
            "code": "site_not_operational",
            "message": f"The {site_label} is not operational.",
        })

    if str(site["authority_id"]) != str(expected_authority_id):
        errors.append({
            "field": field_name,
            "code": "authority_mismatch",
            "message": (
                f"The {site_label} does not belong to the "
                "Flight Plan authority."
            ),
        })

    return errors


def _validate_droneport(
    droneport,
    field_name,
    droneport_label,
    expected_site_id,
):
    errors = []

    if droneport is None:
        errors.append({
            "field": field_name,
            "code": "droneport_not_found",
            "message": f"The {droneport_label} was not found.",
        })

        return errors

    if droneport["operational_status"] != ACTIVE_STATUS:
        errors.append({
            "field": field_name,
            "code": "droneport_not_operational",
            "message": f"The {droneport_label} is not operational.",
        })

    if str(droneport["site_id"]) != str(expected_site_id):
        errors.append({
            "field": field_name,
            "code": "droneport_site_mismatch",
            "message": (
                f"The {droneport_label} does not belong to the "
                "corresponding Flight Plan Site."
            ),
        })

    return errors


def _load_and_validate_routes(
    flight_path_ids,
    expected_authority_id,
):
    errors = []
    routes = []

    normalized_route_ids = [
        str(route_id)
        for route_id in flight_path_ids
    ]

    if len(normalized_route_ids) != len(set(normalized_route_ids)):
        errors.append({
            "field": "flight_path_ids",
            "code": "duplicate_route",
            "message": "The Flight Path must not contain duplicate Routes.",
        })

        return errors, routes

    endpoint_site_ids = set()

    for route_id in normalized_route_ids:
        route = select_route(route_id)

        if route is None:
            errors.append({
                "field": "flight_path_ids",
                "code": "route_not_found",
                "message": f"Route {route_id} was not found.",
            })

            continue

        routes.append(route)

        if route["operational_status"] != ACTIVE_STATUS:
            errors.append({
                "field": "flight_path_ids",
                "code": "route_not_operational",
                "message": f"Route {route_id} is not operational.",
            })

        endpoint_site_ids.add(str(route["origin_site_id"]))
        endpoint_site_ids.add(str(route["destination_site_id"]))

    endpoint_sites = {
        site_id: select_site(site_id)
        for site_id in endpoint_site_ids
    }

    for site_id, site in endpoint_sites.items():
        if site is None:
            errors.append({
                "field": "flight_path_ids",
                "code": "route_site_not_found",
                "message": (
                    "A Site referenced by the Flight Path was not found: "
                    f"{site_id}."
                ),
            })

            continue

        if site["operational_status"] != ACTIVE_STATUS:
            errors.append({
                "field": "flight_path_ids",
                "code": "route_site_not_operational",
                "message": (
                    "A Site referenced by the Flight Path is not "
                    f"operational: {site_id}."
                ),
            })

        if str(site["authority_id"]) != str(expected_authority_id):
            errors.append({
                "field": "flight_path_ids",
                "code": "route_site_authority_mismatch",
                "message": (
                    "A Site referenced by the Flight Path does not belong "
                    "to the Flight Plan authority."
                ),
            })

    return errors, routes


def _validate_ordered_route_sequence(
    routes,
    origin_site_id,
    destination_site_id,
):
    errors = []

    if not routes:
        return errors

    current_site_id = str(origin_site_id)

    for index, route in enumerate(routes):
        route_origin_site_id = str(route["origin_site_id"])
        route_destination_site_id = str(route["destination_site_id"])

        if current_site_id == route_origin_site_id:
            current_site_id = route_destination_site_id
        elif current_site_id == route_destination_site_id:
            current_site_id = route_origin_site_id
        else:
            errors.append({
                "field": "flight_path_ids",
                "code": "disconnected_route_sequence",
                "message": (
                    f"Route at Flight Path position {index + 1} does not "
                    "connect to the preceding Route or the Flight Plan "
                    "origin Site."
                ),
            })

            return errors

    if current_site_id != str(destination_site_id):
        errors.append({
            "field": "flight_path_ids",
            "code": "route_destination_mismatch",
            "message": (
                "The ordered Flight Path does not terminate at the "
                "Flight Plan destination Site."
            ),
        })

    return errors


