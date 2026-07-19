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
Flight Context API business rules layer implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-07-18

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

from typing import Any
from app.models.site_model import select_site
from app.models.zone_model import select_zone
from app.models.zone_model import select_zones_by_site_id
from app.models.droneport_model import select_droneport
from app.models.droneport_model import select_droneports_by_site_id
from app.models.route_model import select_route


def get_flight_context(
    payload: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        service = FlightContextService()
        context = service.get_flight_context(payload)

        return context, None

    except ValueError as error:
        return None, str(error)

    except Exception:
        return None, "Unable to build flight context."


class FlightContextService:
    OVERLAY_TYPES = (
        "sites",
        "zones",
        "droneports",
        "routes",
    )

    OVERLAY_ID_FIELDS = {
        "sites": "site_id",
        "zones": "zone_id",
        "droneports": "droneport_id",
        "routes": "route_id",
    }

    def get_flight_context(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        request_data = self._normalize_request(payload)

        selection = self._build_selection(request_data)
        context = self._build_context(selection)

        context = self._remove_selected_from_context(
            selection,
            context,
        )

        bounds = self._calculate_bounds(
            selection,
            context,
        )

        return {
            "selection": selection,
            "context": context,
            "bounds": bounds,
        }

    def _normalize_request(
        self,
        payload: dict[str, Any],
    ) -> dict[str, list[str]]:
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")

        normalized: dict[str, list[str]] = {}

        for overlay_type in self.OVERLAY_TYPES:
            values = payload.get(overlay_type, [])

            if values is None:
                values = []

            if not isinstance(values, list):
                raise ValueError(
                    f"'{overlay_type}' must be an array."
                )

            normalized[overlay_type] = self._deduplicate_ids(
                values,
                overlay_type,
            )

        return normalized

    def _deduplicate_ids(
        self,
        values: list[Any],
        overlay_type: str,
    ) -> list[str]:
        unique_ids: list[str] = []
        seen: set[str] = set()

        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"'{overlay_type}' must contain UUID strings."
                )

            overlay_id = value.strip()

            if overlay_id not in seen:
                seen.add(overlay_id)
                unique_ids.append(overlay_id)

        return unique_ids

    def _build_selection(
        self,
        request_data: dict[str, list[str]],
    ) -> dict[str, list[dict[str, Any]]]:
        return {
            "sites": self._load_sites(
                request_data["sites"]
            ),
            "zones": self._load_zones(
                request_data["zones"]
            ),
            "droneports": self._load_droneports(
                request_data["droneports"]
            ),
            "routes": self._load_routes(
                request_data["routes"]
            ),
        }

    def _build_context(
        self,
        selection: dict[str, list[dict[str, Any]]],
    ) -> dict[str, list[dict[str, Any]]]:
        context = self._empty_overlay_collection()

        self._merge_context(
            context,
            self._context_from_sites(selection["sites"]),
        )

        self._merge_context(
            context,
            self._context_from_zones(selection["zones"]),
        )

        self._merge_context(
            context,
            self._context_from_droneports(
                selection["droneports"]
            ),
        )

        self._merge_context(
            context,
            self._context_from_routes(selection["routes"]),
        )

        return context

    def _empty_overlay_collection(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        return {
            overlay_type: []
            for overlay_type in self.OVERLAY_TYPES
        }

    def _merge_context(
        self,
        target: dict[str, list[dict[str, Any]]],
        source: dict[str, list[dict[str, Any]]],
    ) -> None:
        for overlay_type in self.OVERLAY_TYPES:
            target[overlay_type].extend(
                source.get(overlay_type, [])
            )

        self._deduplicate_overlay_collection(target)

    def _deduplicate_overlay_collection(
        self,
        overlays: dict[str, list[dict[str, Any]]],
    ) -> None:
        for overlay_type in self.OVERLAY_TYPES:
            id_field = self.OVERLAY_ID_FIELDS[overlay_type]
            unique: dict[str, dict[str, Any]] = {}

            for overlay in overlays[overlay_type]:
                overlay_id = str(overlay[id_field])
                unique[overlay_id] = overlay

            overlays[overlay_type] = list(unique.values())

    def _remove_selected_from_context(
        self,
        selection: dict[str, list[dict[str, Any]]],
        context: dict[str, list[dict[str, Any]]],
    ) -> dict[str, list[dict[str, Any]]]:
        cleaned_context = self._empty_overlay_collection()

        for overlay_type in self.OVERLAY_TYPES:
            id_field = self.OVERLAY_ID_FIELDS[overlay_type]

            selected_ids = {
                str(overlay[id_field])
                for overlay in selection[overlay_type]
            }

            cleaned_context[overlay_type] = [
                overlay
                for overlay in context[overlay_type]
                if str(overlay[id_field]) not in selected_ids
            ]

        return cleaned_context

    def _context_from_sites(
        self,
        sites: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        site_ids = [
            site["site_id"]
            for site in sites
        ]

        return {
            "sites": [],
            "zones": self._load_zones_for_sites(site_ids),
            "droneports": self._load_droneports_for_sites(
                site_ids
            ),
            "routes": [],
        }

    def _context_from_zones(
        self,
        zones: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        site_ids = []
        seen = set()

        for zone in zones:
            site_id = zone["site_id"]

            if site_id not in seen:
                seen.add(site_id)
                site_ids.append(site_id)

        return {
            "sites": self._load_sites(site_ids),
            "zones": [],
            "droneports": self._load_droneports_for_sites(
                site_ids
            ),
            "routes": [],
        }

    def _context_from_droneports(
        self,
        droneports: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        site_ids = []
        seen = set()

        for droneport in droneports:
            site_id = droneport["site_id"]

            if site_id not in seen:
                seen.add(site_id)
                site_ids.append(site_id)

        return {
            "sites": self._load_sites(site_ids),
            "zones": self._load_zones_for_sites(site_ids),
            "droneports": [],
            "routes": [],
        }

    def _context_from_routes(
        self,
        routes: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        site_ids = self._find_endpoint_site_ids(routes)
        droneport_ids = self._find_endpoint_droneport_ids(
            routes
        )

        return {
            "sites": self._load_sites(site_ids),
            "zones": self._load_zones_for_sites(site_ids),
            "droneports": self._load_droneports(
                droneport_ids
            ),
            "routes": [],
        }

    def _load_sites(
        self,
        site_ids: list[str],
    ) -> list[dict[str, Any]]:
        sites: list[dict[str, Any]] = []

        for site_id in site_ids:
            site = select_site(site_id)

            if site is not None:
                sites.append(dict(site))

        return sites

    def _load_zones(
        self,
        zone_ids: list[str],
    ) -> list[dict[str, Any]]:
        zones: list[dict[str, Any]] = []

        for zone_id in zone_ids:
            zone = select_zone(zone_id)

            if zone is not None:
                zones.append(dict(zone))

        return zones

    def _load_droneports(
        self,
        droneport_ids: list[str],
    ) -> list[dict[str, Any]]:
        droneports: list[dict[str, Any]] = []

        for droneport_id in droneport_ids:
            droneport = select_droneport(droneport_id)

            if droneport is not None:
                droneports.append(dict(droneport))

        return droneports

    def _load_routes(
        self,
        route_ids: list[str],
    ) -> list[dict[str, Any]]:
        routes: list[dict[str, Any]] = []

        for route_id in route_ids:
            route = select_route(route_id)

            if route is not None:
                routes.append(dict(route))

        return routes

    def _load_zones_for_sites(
        self,
        site_ids: list[str],
    ) -> list[dict[str, Any]]:
        zones: list[dict[str, Any]] = []

        for site_id in site_ids:
            site_zones = select_zones_by_site_id(site_id)

            zones.extend(
                dict(zone)
                for zone in site_zones
            )

        return zones

    def _load_droneports_for_sites(
        self,
        site_ids: list[str],
    ) -> list[dict[str, Any]]:
        droneports: list[dict[str, Any]] = []

        for site_id in site_ids:
            site_droneports = select_droneports_by_site_id(site_id)

            droneports.extend(
                dict(droneport)
                for droneport in site_droneports
            )

        return droneports

    def _find_endpoint_site_ids(
        self,
        routes: list[dict[str, Any]],
    ) -> list[str]:
        site_ids: list[str] = []
        seen: set[str] = set()

        for route in routes:
            for field_name in (
                "origin_site_id",
                "destination_site_id",
            ):
                site_id = route.get(field_name)

                if site_id is not None:
                    site_id = str(site_id)

                    if site_id not in seen:
                        seen.add(site_id)
                        site_ids.append(site_id)

        return site_ids

    def _find_endpoint_droneport_ids(
        self,
        routes: list[dict[str, Any]],
    ) -> list[str]:
        droneport_ids: list[str] = []
        seen: set[str] = set()

        for route in routes:
            for field_name in (
                "origin_droneport_id",
                "destination_droneport_id",
            ):
                droneport_id = route.get(field_name)

                if droneport_id is not None:
                    droneport_id = str(droneport_id)

                    if droneport_id not in seen:
                        seen.add(droneport_id)
                        droneport_ids.append(droneport_id)

        return droneport_ids

    def _calculate_bounds(
        self,
        selection: dict[str, list[dict[str, Any]]],
        context: dict[str, list[dict[str, Any]]],
    ) -> dict[str, list[float]] | None:
        coordinates: list[tuple[float, float]] = []

        for overlay_collection in (
            selection,
            context,
        ):
            for overlay_type in self.OVERLAY_TYPES:
                for overlay in overlay_collection[overlay_type]:
                    geometry = overlay.get("geometry")

                    if geometry is not None:
                        coordinates.extend(
                            self._collect_geometry_coordinates(
                                geometry
                            )
                        )

        if not coordinates:
            return None

        longitudes = [
            longitude
            for longitude, _ in coordinates
        ]

        latitudes = [
            latitude
            for _, latitude in coordinates
        ]

        return {
            "southWest": [
                min(latitudes),
                min(longitudes),
            ],
            "northEast": [
                max(latitudes),
                max(longitudes),
            ],
        }

    def _collect_geometry_coordinates(
        self,
        geometry: dict[str, Any],
    ) -> list[tuple[float, float]]:
        coordinates: list[tuple[float, float]] = []

        self._walk_coordinates(
            geometry.get("coordinates"),
            coordinates,
        )

        return coordinates

    def _walk_coordinates(
        self,
        value: Any,
        coordinates: list[tuple[float, float]],
    ) -> None:
        if not isinstance(value, list):
            return

        if (
            len(value) >= 2
            and isinstance(value[0], (int, float))
            and isinstance(value[1], (int, float))
        ):
            coordinates.append(
                (
                    float(value[0]),
                    float(value[1]),
                )
            )
            return

        for child in value:
            self._walk_coordinates(
                child,
                coordinates,
            )


