from __future__ import annotations

from app.models.geospatial_model import (
    select_geodesic_buffer_geometry,
    select_geodesic_circle_polygon,
)
from app.services.tfr_service import (
    get_tfrs_for_geometry,
)
from app.models.site_model import select_site
from app.models.route_model import select_route
from app.models.droneport_model import select_droneport


FEET_PER_NAUTICAL_MILE = 6076.12


def get_droneport_operational_geometry(droneport):
    """Return DronePort operational footprint as GeoJSON."""

    radius_ft = (
        float(droneport["droneport_diameter_ft"])
        / 2.0
    )

    radius_nm = (
        radius_ft
        / FEET_PER_NAUTICAL_MILE
    )

    return select_geodesic_circle_polygon(
        longitude=float(droneport["longitude"]),
        latitude=float(droneport["latitude"]),
        radius_nm=radius_nm,
    )


def get_tfrs_for_droneport(
    droneport,
    evaluation_datetime,
):
    """Return applicable FAA TFRs for a DronePort."""

    geometry = get_droneport_operational_geometry(
        droneport
    )

    return get_tfrs_for_operational_geometry(
        geometry,
        evaluation_datetime,
    )


def get_route_operational_geometries(route):
    """Return Route segment operational corridors as GeoJSON."""

    coordinates = route["geometry"]["coordinates"]
    segment_attributes = route["segment_attributes"]

    if len(coordinates) - 1 != len(segment_attributes):
        raise ValueError(
            "Route segment attributes do not match Route geometry"
        )

    geometries = []

    for segment_index, attributes in enumerate(
        segment_attributes
    ):
        segment_geometry = {
            "type": "LineString",
            "coordinates": [
                coordinates[segment_index],
                coordinates[segment_index + 1],
            ],
        }

        half_width_ft = (
            float(attributes["route_width_ft"])
            / 2.0
        )

        geometry = select_geodesic_buffer_geometry(
            segment_geometry,
            half_width_ft,
        )

        if geometry is None:
            raise ValueError(
                "Route segment operational geometry "
                "could not be created"
            )

        geometries.append(geometry)

    return geometries


def get_tfrs_for_route(
    route,
    evaluation_datetime,
):
    """Return applicable FAA TFRs for a Route."""

    applicable_tfrs = {}

    for geometry in get_route_operational_geometries(
        route
    ):
        for tfr in get_tfrs_for_operational_geometry(
            geometry,
            evaluation_datetime,
        ):
            applicable_tfrs[
                tfr["notam_id"]
            ] = tfr

    return list(
        applicable_tfrs.values()
    )


def get_tfrs_for_operational_geometry(
    geometry,
    evaluation_datetime,
):
    """Return applicable FAA TFRs for DroneNav operational geometry."""

    return get_tfrs_for_geometry(
        geometry,
        current_datetime=evaluation_datetime,
    )


def get_tfrs_for_site(
    site,
    evaluation_datetime,
):
    """Return applicable FAA TFRs for a Site."""

    return get_tfrs_for_operational_geometry(
        site["geometry"],
        evaluation_datetime,
    )


def get_tfrs_for_zone(
    zone,
    evaluation_datetime,
):
    """Return applicable FAA TFRs for a Zone."""

    return get_tfrs_for_operational_geometry(
        zone["geometry"],
        evaluation_datetime,
    )


def load_scheduled_flight_overlays(data):
    """Load overlays referenced by a scheduled Flight Plan."""

    origin_site = select_site(
        str(data["origin_site_id"])
    )
    destination_site = select_site(
        str(data["destination_site_id"])
    )

    departure_droneport = select_droneport(
        str(data["departure_droneport_id"])
    )
    arrival_droneport = select_droneport(
        str(data["arrival_droneport_id"])
    )

    routes = [
        select_route(str(route_id))
        for route_id in data["flight_path_ids"]
    ]

    return {
        "sites": [
            origin_site,
            destination_site,
        ],
        "droneports": [
            departure_droneport,
            arrival_droneport,
        ],
        "routes": routes,
    }


def get_scheduled_flight_tfr_conflicts(
    data,
    evaluation_datetime,
):
    """Return TFR conflicts for a scheduled Flight Plan."""

    overlays = load_scheduled_flight_overlays(
        data
    )

    conflicts = []

    sites = {
        str(site["site_id"]): site
        for site in overlays["sites"]
    }

    for site_id, site in sites.items():
        tfrs = get_tfrs_for_site(
            site,
            evaluation_datetime,
        )

        if tfrs:
            conflicts.append(
                {
                    "overlay_type": "site",
                    "overlay_id": site_id,
                    "tfrs": tfrs,
                }
            )

    droneports = {
        str(droneport["droneport_id"]): droneport
        for droneport in overlays["droneports"]
    }

    for droneport_id, droneport in droneports.items():
        tfrs = get_tfrs_for_droneport(
            droneport,
            evaluation_datetime,
        )

        if tfrs:
            conflicts.append(
                {
                    "overlay_type": "droneport",
                    "overlay_id": droneport_id,
                    "tfrs": tfrs,
                }
            )

    for route in overlays["routes"]:
        tfrs = get_tfrs_for_route(
            route,
            evaluation_datetime,
        )

        if tfrs:
            conflicts.append(
                {
                    "overlay_type": "route",
                    "overlay_id": str(
                        route["route_id"]
                    ),
                    "tfrs": tfrs,
                }
            )

    return conflicts


