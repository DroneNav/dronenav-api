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
Temporary Flight Restriction service implementation source file.

Author:
DroneNav Project Contributors

Created:
2026-09-02

Notes:
This software is intended to support drone navigation,
route planning, corridor management, and airspace safety
operations. All operational use remains the responsibility
of the aircraft operator and applicable regulatory authorities.
"""

import requests
import re

from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

from app.config.constants import (
    DEFAULT_API_TIMEOUT_SECONDS,
    FAA_TFR_WFS_URL,
    FAA_TFR_AIXM_URL,
    FAA_TFR_CACHE_TTL_SECONDS,
)

from app.models.geospatial_model import (
    select_geodesic_arc_points,
    select_geodesic_circle_polygon,
    select_geometry_difference,
    select_geometries_intersect,
)


AIXM_NAMESPACE = "http://www.aixm.aero/schema/5.0"
GML_NAMESPACE = "http://www.opengis.net/gml/3.2"
TFR_NAMESPACE = "http://www.faa.gov/AIM/SAA/TFR"

TFR_WEEKDAY_MAP = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
}

_TFR_CACHE = {
    "loaded_at": None,
    "features": None,
    "aixm": {},
}


def normalize_tfr_feature(feature):
    properties = feature.get("properties") or {}

    notam_key = properties.get("NOTAM_KEY")
    notam_id = notam_key.split("-", 1)[0] if notam_key else None

    return {
        "notam_id": notam_id,
        "notam_key": notam_key,
        "title": properties.get("TITLE"),
        "legal": properties.get("LEGAL"),
        "state": properties.get("STATE"),
        "last_modified_at": properties.get("LAST_MODIFICATION_DATETIME"),
        "geometry": feature.get("geometry"),
    }


def get_tfr_aixm(notam_id):
    cached_aixm = _TFR_CACHE["aixm"].get(
        notam_id
    )

    if cached_aixm is not None:
        return cached_aixm

    filename = (
        "detail_"
        + notam_id.replace("/", "_")
        + ".aixm50"
    )

    response = requests.get(
        f"{FAA_TFR_AIXM_URL}/{filename}",
        timeout=DEFAULT_API_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    aixm_data = response.content

    _TFR_CACHE["aixm"][notam_id] = aixm_data

    return aixm_data


def get_tfr_traditional_short_text(root):
    element = root.find(
        f".//{{{TFR_NAMESPACE}}}translationTraditionalShort"
    )

    if element is None:
        raise ValueError(
            "FAA AIXM does not contain translationTraditionalShort"
        )

    text = "".join(element.itertext()).strip()

    if not text:
        raise ValueError(
            "FAA AIXM translationTraditionalShort is empty"
        )

    return text


def parse_tfr_compact_validity_marker(
    traditional_short_text,
):
    pattern = re.compile(
        r"\b(\d{10})-(\d{10}|PERM)\b"
    )

    matches = list(
        pattern.finditer(
            traditional_short_text.upper()
        )
    )

    if not matches:
        raise ValueError(
            "FAA TFR traditional text contains no compact validity marker"
        )

    match = matches[-1]

    return {
        "begin": match.group(1),
        "end": (
            None
            if match.group(2) == "PERM"
            else match.group(2)
        ),
        "permanent": match.group(2) == "PERM",
    }


def parse_tfr_compact_datetime(value):
    if not isinstance(value, str):
        raise ValueError(
            "FAA TFR compact datetime must be a string"
        )

    try:
        return datetime.strptime(
            value,
            "%y%m%d%H%M",
        ).replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ValueError(
            f"Invalid FAA TFR compact datetime: {value}"
        ) from exc


def normalize_tfr_schedule(
    schedule,
    tfr_begins_at,
    tfr_ends_at,
):
    if schedule is None:
        return {
            "type": "TFR_VALIDITY",
            "begins_at": tfr_begins_at,
            "ends_at": tfr_ends_at,
            "day": None,
        }

    start_date = schedule.get("start_date")
    end_date = schedule.get("end_date")
    start_time = schedule.get("start_time")
    end_time = schedule.get("end_time")
    day = schedule.get("day")

    has_start = bool(
        start_date
        and start_time
    )

    has_end = bool(
        end_date
        and end_time
    )

    if has_start and has_end:
        return {
            "type": (
                "RECURRING"
                if day
                else "EXPLICIT_INTERVAL"
            ),
            "start_date": start_date,
            "end_date": end_date,
            "start_time": start_time,
            "end_time": end_time,
            "day": day,
        }

    if not has_start and has_end:
        if not tfr_begins_at:
            raise ValueError(
                "FAA TFR open-start schedule has no TFR begin"
            )

        return {
            "type": "OPEN_START",
            "begins_at": tfr_begins_at,
            "end_date": end_date,
            "end_time": end_time,
            "day": day,
        }

    if has_start and not has_end:
        return {
            "type": "OPEN_END",
            "start_date": start_date,
            "start_time": start_time,
            "ends_at": tfr_ends_at,
            "day": day,
        }

    raise ValueError(
        "Unsupported FAA TFR schedule structure"
    )


def parse_tfr_aixm_identity(aixm_data):
    root = ElementTree.fromstring(aixm_data)

    tfr_time_slice = root.find(
        f".//{{{TFR_NAMESPACE}}}TFRTimeSlice"
    )

    if tfr_time_slice is None:
        raise ValueError(
            "FAA AIXM response does not contain a TFRTimeSlice"
        )

    valid_time = tfr_time_slice.find(
        f".//{{{GML_NAMESPACE}}}validTime"
    )

    begin_position = None
    end_position = None

    if valid_time is not None:
        begin_element = valid_time.find(
            f".//{{{GML_NAMESPACE}}}beginPosition"
        )

        end_element = valid_time.find(
            f".//{{{GML_NAMESPACE}}}endPosition"
        )

        if (
            begin_element is not None
            and begin_element.text
        ):
            begin_position = datetime.strptime(
                begin_element.text.strip(),
                "%m/%d/%Y %I:%M:%S %p",
            ).replace(
                tzinfo=timezone.utc
            ).isoformat()

        if (
            end_element is not None
            and end_element.text
        ):
            end_position = datetime.strptime(
                end_element.text.strip(),
                "%m/%d/%Y %I:%M:%S %p",
            ).replace(
                tzinfo=timezone.utc
            ).isoformat()

    if begin_position is None:
        traditional_short_text = (
            get_tfr_traditional_short_text(root)
        )

        marker = parse_tfr_compact_validity_marker(
            traditional_short_text
        )

        begin_position = (
            parse_tfr_compact_datetime(
                marker["begin"]
            ).isoformat()
        )

        if marker["end"] is not None:
            end_position = (
                parse_tfr_compact_datetime(
                    marker["end"]
                ).isoformat()
            )

    def get_text(name):
        element = tfr_time_slice.find(
            f"{{{TFR_NAMESPACE}}}{name}"
        )

        return (
            element.text
            if element is not None
            else None
        )

    return {
        "notam_id": get_text("number"),
        "issued_at": get_text("issued"),
        "restriction_type": get_text("type"),
        "begins_at": begin_position,
        "ends_at": end_position,
        "begin_time_reference": get_text(
            "beginValidTimeReference"
        ),
        "end_time_reference": get_text(
            "endValidTimeReference"
        ),
    }


def parse_altitude_expressions(traditional_short_text):
    pattern = re.compile(
        r"\b("
        r"SFC|"
        r"\d+(?:\.\d+)?FT\s+(?:AGL|MSL)|"
        r"FL\d+"
        r")-("
        r"SFC|"
        r"\d+(?:\.\d+)?FT\s+(?:AGL|MSL)|"
        r"FL\d+"
        r")\b"
    )

    expressions = []

    for match in pattern.finditer(
        traditional_short_text.upper()
    ):
        expressions.append({
            "lower": match.group(1),
            "upper": match.group(2),
        })

    return expressions


def parse_altitude_expression_value(value):
    value = value.strip().upper()

    if value == "SFC":
        return {
            "value": 0,
            "unit": "FT",
            "reference": "SURFACE",
        }

    if value.startswith("FL"):
        return {
            "value": int(value[2:]) * 100,
            "unit": "FT",
            "reference": "FL",
        }

    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)FT\s*(AGL|MSL)",
        value,
    )

    if match is None:
        raise ValueError(
            f"Unsupported FAA altitude expression: {value}"
        )

    return {
        "value": float(match.group(1)),
        "unit": "FT",
        "reference": match.group(2),
    }


def resolve_layer_altitude_references(
    layer,
    altitude_expressions,
):
    lower_value = float(
        layer["lower_altitude"]["value"]
    )

    upper_value = float(
        layer["upper_altitude"]["value"]
    )

    matches = []

    for expression in altitude_expressions:
        lower = parse_altitude_expression_value(
            expression["lower"]
        )

        upper = parse_altitude_expression_value(
            expression["upper"]
        )

        if (
            lower["value"] == lower_value
            and
            upper["value"] == upper_value
        ):
            matches.append(
                (
                    lower["reference"],
                    upper["reference"],
                )
            )

    if not matches:
        raise ValueError(
            "FAA altitude references could not be resolved "
            f"for layer {lower_value}-{upper_value}"
        )

    unique_matches = set(matches)

    if len(unique_matches) != 1:
        raise ValueError(
            "FAA altitude references are ambiguous "
            f"for layer {lower_value}-{upper_value}"
        )

    lower_reference, upper_reference = (
        next(iter(unique_matches))
    )

    return {
        "lower_reference": lower_reference,
        "upper_reference": upper_reference,
    }


def parse_layer_and_time(
    layer_and_time,
    altitude_expressions,
    tfr_begins_at,
    tfr_ends_at,
):
    def get_text(name):
        element = layer_and_time.find(
            f"{{{AIXM_NAMESPACE}}}{name}"
        )
        return element.text if element is not None else None

    def get_altitude(name):
        element = layer_and_time.find(
            f"{{{AIXM_NAMESPACE}}}{name}"
        )

        if element is None:
            return None

        value = element.text

        if value is not None:
            value = value.strip()

        return {
            "value": value,
            "unit": element.get("uom"),
        }

    lower_altitude = get_altitude(
        "lowerLimit"
    )

    upper_altitude = get_altitude(
        "upperLimit"
    )

    lower_altitude_reference = get_text(
        "lowerLimitReference"
    )

    upper_altitude_reference = get_text(
        "upperLimitReference"
    )

    schedules = []

    for timesheet in layer_and_time.findall(
        f".//{{{AIXM_NAMESPACE}}}Timesheet"
    ):
        def get_timesheet_text(name):
            element = timesheet.find(
                f"{{{AIXM_NAMESPACE}}}{name}"
            )
            return element.text if element is not None else None

        schedules.append({
            "time_reference": get_timesheet_text("timeReference"),
            "start_date": get_timesheet_text("startDate"),
            "end_date": get_timesheet_text("endDate"),
            "day": get_timesheet_text("day"),
            "start_time": get_timesheet_text("startTime"),
            "end_time": get_timesheet_text("endTime"),
        })

    normalized_schedules = []

    if not schedules:
        normalized_schedules.append(
            normalize_tfr_schedule(
                None,
                tfr_begins_at,
                tfr_ends_at,
            )
        )
    else:
        for schedule in schedules:
            normalized_schedules.append(
                normalize_tfr_schedule(
                    schedule,
                    tfr_begins_at,
                    tfr_ends_at,
                )
            )

    references = resolve_layer_altitude_references(
        {
            "lower_altitude": lower_altitude,
            "upper_altitude": upper_altitude,
        },
        altitude_expressions,
    )

    return {
        "lower_altitude": {
            **lower_altitude,
            "raw_reference": lower_altitude_reference,
            "resolved_reference": references[
                "lower_reference"
            ],
        },
        "upper_altitude": {
            **upper_altitude,
            "raw_reference": upper_altitude_reference,
            "resolved_reference": references[
                "upper_reference"
            ],
        },
        "altitude_interpretation": get_text("altitudeInterpretation"),
        "schedules": schedules,
        "normalized_schedules": normalized_schedules,
    }


def get_restricted_airspace_reference(airspace_usage_time_slice):
    restricted_airspace = airspace_usage_time_slice.find(
        f"{{{AIXM_NAMESPACE}}}restrictedAirspace"
    )

    if restricted_airspace is None:
        return None

    href = restricted_airspace.get(
        "{http://www.w3.org/1999/xlink}href"
    )

    if not href:
        return None

    return href.removeprefix("#"
)


def get_airspace_by_id(root, airspace_id):
    gml_id_name = f"{{{GML_NAMESPACE}}}id"

    for element in root.iter():
        if not element.tag.endswith("}Airspace"):
            continue

        if element.get(gml_id_name) == airspace_id:
            return element

    return None


def parse_circle_geometry(airspace):
    circle = airspace.find(
        f".//{{{GML_NAMESPACE}}}CircleByCenterPoint"
    )

    if circle is None:
        return None

    position = circle.find(
        f".//{{{GML_NAMESPACE}}}pos"
    )
    radius = circle.find(
        f"{{{GML_NAMESPACE}}}radius"
    )

    if position is None or position.text is None:
        raise ValueError("FAA AIXM circle is missing center position")

    if radius is None or radius.text is None:
        raise ValueError("FAA AIXM circle is missing radius")

    coordinates = position.text.strip().split()

    if len(coordinates) != 2:
        raise ValueError("FAA AIXM circle center is invalid")

    latitude = float(coordinates[0])
    longitude = float(coordinates[1])

    return {
        "type": "circle",
        "center": [
            longitude,
            latitude,
        ],
        "radius": {
            "value": float(radius.text.strip()),
            "unit": radius.get("uom"),
        },
    }


def parse_line_string_segment(segment):
    points = []

    for position in segment.findall(
        f".//{{{GML_NAMESPACE}}}pos"
    ):
        if position.text is None:
            continue

        coordinates = position.text.strip().split()

        if len(coordinates) != 2:
            raise ValueError(
                "FAA AIXM LineStringSegment position is invalid"
            )

        latitude = float(coordinates[0])
        longitude = float(coordinates[1])

        points.append([
            longitude,
            latitude,
        ])

    return {
        "type": "line",
        "points": points,
    }


def parse_arc_by_center_point(segment):
    position = segment.find(
        f".//{{{GML_NAMESPACE}}}pos"
    )
    radius = segment.find(
        f"{{{GML_NAMESPACE}}}radius"
    )

    if position is None or position.text is None:
        raise ValueError(
            "FAA AIXM ArcByCenterPoint is missing center position"
        )

    if radius is None or radius.text is None:
        raise ValueError(
            "FAA AIXM ArcByCenterPoint is missing radius"
        )

    coordinates = position.text.strip().split()

    if len(coordinates) != 2:
        raise ValueError(
            "FAA AIXM ArcByCenterPoint center is invalid"
        )

    latitude = float(coordinates[0])
    longitude = float(coordinates[1])

    arc_direction = segment.find(
        f"{{{TFR_NAMESPACE}}}arcDirection"
    )

    return {
        "type": "arc",
        "center": [
            longitude,
            latitude,
        ],
        "radius": {
            "value": float(radius.text.strip()),
            "unit": radius.get("uom"),
        },
        "direction": (
            arc_direction.text
            if arc_direction is not None
            else None
        ),
    }


def parse_polygon_geometry(airspace):
    polygon = airspace.find(
        f".//{{{GML_NAMESPACE}}}PolygonPatch"
    )

    if polygon is None:
        return None

    segment_elements = polygon.findall(
        f".//{{{GML_NAMESPACE}}}segments/*"
    )

    if not segment_elements:
        raise ValueError(
            "FAA AIXM polygon does not contain curve segments"
        )

    segments = []

    for segment_element in segment_elements:
        if segment_element.tag == (
            f"{{{GML_NAMESPACE}}}LineStringSegment"
        ):
            segments.append(
                parse_line_string_segment(segment_element)
            )

        elif segment_element.tag == (
            f"{{{TFR_NAMESPACE}}}ArcByCenterPoint"
        ):
            segments.append(
                parse_arc_by_center_point(segment_element)
            )

        elif segment_element.tag == (
            f"{{{GML_NAMESPACE}}}CircleByCenterPoint"
        ):
            return None

        else:
            raise ValueError(
                "FAA AIXM polygon contains unsupported "
                f"curve segment: {segment_element.tag}"
            )

    for index, segment in enumerate(segments):
        if segment["type"] != "arc":
            continue

        if index == 0 or index == len(segments) - 1:
            raise ValueError(
                "FAA AIXM polygon arc is not bounded "
                "by line segments"
            )

        previous_segment = segments[index - 1]
        next_segment = segments[index + 1]

        if (
            previous_segment["type"] != "line"
            or next_segment["type"] != "line"
        ):
            raise ValueError(
                "FAA AIXM polygon arc is not bounded "
                "by line segments"
            )

        if not previous_segment["points"]:
            raise ValueError(
                "FAA AIXM polygon arc preceding line "
                "has no coordinates"
            )

        if not next_segment["points"]:
            raise ValueError(
                "FAA AIXM polygon arc following line "
                "has no coordinates"
            )

        segment["start"] = previous_segment["points"][-1]
        segment["end"] = next_segment["points"][0]

    return {
        "type": "polygon",
        "segments": segments,
    }


def parse_airspace_geometry_components(airspace):
    components = airspace.findall(
        f".//{{{AIXM_NAMESPACE}}}AirspaceGeometryComponent"
    )

    if not components:
        raise ValueError(
            "FAA AIXM airspace contains no geometry components"
        )

    parsed_components = []

    for component in components:
        operation_element = component.find(
            f"./{{{AIXM_NAMESPACE}}}operation"
        )

        if (
            operation_element is None
            or not operation_element.text
        ):
            raise ValueError(
                "FAA AIXM geometry component has no operation"
            )

        operation = operation_element.text.strip()

        if operation not in {
            "BASE",
            "SUBTR",
        }:
            raise ValueError(
                f"Unsupported FAA AIXM geometry operation: {operation}"
            )

        volume = component.find(
            f"./{{{AIXM_NAMESPACE}}}theAirspaceVolume/"
            f"{{{AIXM_NAMESPACE}}}AirspaceVolume"
        )

        if volume is None:
            raise ValueError(
                "FAA AIXM geometry component has no AirspaceVolume"
            )

        geometry = parse_circle_geometry(
            volume
        )

        if geometry is None:
            geometry = parse_polygon_geometry(
                volume
            )

        if geometry is None:
            raise ValueError(
                "FAA AIXM geometry component contains unsupported geometry"
            )

        parsed_components.append({
            "operation": operation,
            "geometry": geometry,
        })

    return parsed_components


def parse_airspace_usage(
    root,
    airspace_usage_time_slice,
    altitude_expressions,
    tfr_begins_at,
    tfr_ends_at,
):
    airspace_id = get_restricted_airspace_reference(
        airspace_usage_time_slice
    )

    if not airspace_id:
        raise ValueError(
            "FAA AIXM AirspaceUsage is missing restricted airspace reference"
        )

    airspace = get_airspace_by_id(
        root,
        airspace_id,
    )

    if airspace is None:
        raise ValueError(
            f"FAA AIXM referenced airspace was not found: {airspace_id}"
        )

    geometry_components = parse_airspace_geometry_components(
        airspace
    )

    layers = []

    for layer_and_time in airspace_usage_time_slice.findall(
        f".//{{{AIXM_NAMESPACE}}}LayerAndTime"
    ):
        layers.append(
            parse_layer_and_time(
                layer_and_time,
                altitude_expressions,
                tfr_begins_at,
                tfr_ends_at,
            )
        )

    return {
        "airspace_id": airspace_id,
        "geometry_components": geometry_components,
        "layers": layers,
    }


def parse_tfr_aixm(aixm_data):
    root = ElementTree.fromstring(aixm_data)

    traditional_short_text = (
        get_tfr_traditional_short_text(root)
    )

    altitude_expressions = (
        parse_altitude_expressions(
            traditional_short_text
        )
    )

    identity = parse_tfr_aixm_identity(aixm_data)

    usage_time_slices = root.findall(
        f".//{{{AIXM_NAMESPACE}}}AirspaceUsageTimeSlice"
    )

    if not usage_time_slices:
        raise ValueError(
            "FAA AIXM contains no AirspaceUsageTimeSlice"
        )

    airspace_usages = [
        parse_airspace_usage(
            root,
            usage_time_slice,
            altitude_expressions,
            identity["begins_at"],
            identity["ends_at"],
        )
        for usage_time_slice in usage_time_slices
    ]

    return {
        **identity,
        "airspace_usages": airspace_usages,
    }


def get_tfrs():
    now = datetime.now(
        timezone.utc
    )

    loaded_at = _TFR_CACHE["loaded_at"]
    features = _TFR_CACHE["features"]

    if (
        loaded_at is not None
        and features is not None
        and (
            now - loaded_at
        ).total_seconds()
        < FAA_TFR_CACHE_TTL_SECONDS
    ):
        return features

    response = requests.get(
        FAA_TFR_WFS_URL,
        params={
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typeName": "TFR:V_TFR_LOC",
            "maxFeatures": 300,
            "outputFormat": "application/json",
            "srsname": "EPSG:4326",
        },
        timeout=DEFAULT_API_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    data = response.json()

    features = [
        normalize_tfr_feature(feature)
        for feature in data["features"]
    ]

    _TFR_CACHE["loaded_at"] = now
    _TFR_CACHE["features"] = features
    _TFR_CACHE["aixm"] = {}

    return features


def resolve_tfr_schedule_date(
    value,
    not_before,
):
    if not isinstance(value, str):
        raise ValueError(
            "FAA TFR schedule date must be a string"
        )

    if not isinstance(not_before, datetime):
        raise ValueError(
            "FAA TFR schedule date requires datetime anchor"
        )

    try:
        day, month = map(
            int,
            value.split("-"),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid FAA TFR schedule date: {value}"
        ) from exc

    for year in (
        not_before.year,
        not_before.year + 1,
    ):
        try:
            candidate = datetime(
                year,
                month,
                day,
                tzinfo=timezone.utc,
            )
        except ValueError:
            continue

        if candidate.date() >= not_before.date():
            return candidate

    raise ValueError(
        f"Could not resolve FAA TFR schedule date: {value}"
    )


def build_tfr_schedule_interval(
    schedule,
    tfr_begins_at,
    tfr_ends_at,
):
    if not isinstance(schedule, dict):
        raise ValueError(
            "FAA TFR normalized schedule must be a dictionary"
        )

    schedule_type = schedule.get("type")

    tfr_begin = datetime.fromisoformat(
        tfr_begins_at
    )

    tfr_end = (
        datetime.fromisoformat(tfr_ends_at)
        if tfr_ends_at
        else None
    )

    if schedule_type == "TFR_VALIDITY":
        return {
            "begins_at": tfr_begin,
            "ends_at": tfr_end,
        }

    if schedule_type == "OPEN_START":
        end_date = resolve_tfr_schedule_date(
            schedule["end_date"],
            tfr_begin,
        )

        hour, minute = map(
            int,
            schedule["end_time"].split(":"),
        )

        end_datetime = end_date.replace(
            hour=hour,
            minute=minute,
        )

        return {
            "begins_at": tfr_begin,
            "ends_at": end_datetime,
        }

    if schedule_type == "OPEN_END":
        start_date = resolve_tfr_schedule_date(
            schedule["start_date"],
            tfr_begin,
        )

        hour, minute = map(
            int,
            schedule["start_time"].split(":"),
        )

        start_datetime = start_date.replace(
            hour=hour,
            minute=minute,
        )

        return {
            "begins_at": start_datetime,
            "ends_at": tfr_end,
        }

    if schedule_type == "EXPLICIT_INTERVAL":
        start_date = resolve_tfr_schedule_date(
            schedule["start_date"],
            tfr_begin,
        )

        start_hour, start_minute = map(
            int,
            schedule["start_time"].split(":"),
        )

        start_datetime = start_date.replace(
            hour=start_hour,
            minute=start_minute,
        )

        end_date = resolve_tfr_schedule_date(
            schedule["end_date"],
            start_datetime,
        )

        end_hour, end_minute = map(
            int,
            schedule["end_time"].split(":"),
        )

        end_datetime = end_date.replace(
            hour=end_hour,
            minute=end_minute,
        )

        if end_datetime < start_datetime:
            end_date = resolve_tfr_schedule_date(
                schedule["end_date"],
                start_datetime + timedelta(days=1),
            )

            end_datetime = end_date.replace(
                hour=end_hour,
                minute=end_minute,
            )

        return {
            "begins_at": start_datetime,
            "ends_at": end_datetime,
        }

    if schedule_type == "RECURRING":
        return None

    raise ValueError(
        f"Unsupported FAA TFR normalized schedule type: {schedule_type}"
    )


def is_tfr_recurring_schedule_active(
    schedule,
    current_datetime,
    tfr_begins_at,
    tfr_ends_at,
):
    if schedule.get("type") != "RECURRING":
        raise ValueError(
            "FAA TFR schedule is not recurring"
        )

    if current_datetime.tzinfo is None:
        raise ValueError(
            "FAA TFR applicability requires timezone-aware datetime"
        )

    current_datetime = current_datetime.astimezone(
        timezone.utc
    )

    tfr_begin = datetime.fromisoformat(
        tfr_begins_at
    )

    tfr_end = (
        datetime.fromisoformat(tfr_ends_at)
        if tfr_ends_at
        else None
    )

    if current_datetime < tfr_begin:
        return False

    if (
        tfr_end is not None
        and current_datetime > tfr_end
    ):
        return False

    start_date = resolve_tfr_schedule_date(
        schedule["start_date"],
        tfr_begin,
    )

    end_date = resolve_tfr_schedule_date(
        schedule["end_date"],
        start_date,
    )

    if current_datetime.date() < start_date.date():
        return False

    if current_datetime.date() > end_date.date():
        return False

    day = schedule["day"]

    if day != "ANY":
        weekday = TFR_WEEKDAY_MAP.get(
            day
        )

        if weekday is None:
            raise ValueError(
                f"Unsupported FAA TFR weekday: {day}"
            )

        if current_datetime.weekday() != weekday:
            return False

    start_hour, start_minute = map(
        int,
        schedule["start_time"].split(":"),
    )

    end_hour, end_minute = map(
        int,
        schedule["end_time"].split(":"),
    )

    start_minutes = (
        start_hour * 60
        + start_minute
    )

    end_minutes = (
        end_hour * 60
        + end_minute
    )

    current_minutes = (
        current_datetime.hour * 60
        + current_datetime.minute
    )

    if end_minutes >= start_minutes:
        return (
            start_minutes
            <= current_minutes
            <= end_minutes
        )

    return (
        current_minutes >= start_minutes
        or current_minutes <= end_minutes
    )


def is_tfr_layer_schedule_active(
    layer,
    current_datetime,
    tfr_begins_at,
    tfr_ends_at,
):
    if current_datetime.tzinfo is None:
        raise ValueError(
            "FAA TFR applicability requires timezone-aware datetime"
        )

    current_datetime = current_datetime.astimezone(
        timezone.utc
    )

    schedules = layer.get(
        "normalized_schedules"
    )

    if not schedules:
        raise ValueError(
            "FAA TFR layer contains no normalized schedules"
        )

    for schedule in schedules:
        schedule_type = schedule.get("type")

        if schedule_type == "RECURRING":
            if is_tfr_recurring_schedule_active(
                schedule,
                current_datetime,
                tfr_begins_at,
                tfr_ends_at,
            ):
                return True

            continue

        interval = build_tfr_schedule_interval(
            schedule,
            tfr_begins_at,
            tfr_ends_at,
        )

        begins_at = interval["begins_at"]
        ends_at = interval["ends_at"]

        if current_datetime < begins_at:
            continue

        if (
            ends_at is not None
            and current_datetime > ends_at
        ):
            continue

        return True

    return False


def build_tfr_circle_geojson(geometry):
    """Convert normalized FAA circle geometry to GeoJSON."""

    if geometry.get("type") != "circle":
        raise ValueError(
            "FAA TFR geometry is not a circle"
        )

    center = geometry.get("center")
    radius = geometry.get("radius") or {}

    if (
        not isinstance(center, list)
        or len(center) != 2
    ):
        raise ValueError(
            "FAA TFR circle center is invalid"
        )

    if radius.get("unit") != "NM":
        raise ValueError(
            "Unsupported FAA TFR circle radius unit: "
            f"{radius.get('unit')}"
        )

    radius_value = radius.get("value")

    if (
        not isinstance(radius_value, (int, float))
        or radius_value <= 0
    ):
        raise ValueError(
            "FAA TFR circle radius is invalid"
        )

    geometry = select_geodesic_circle_polygon(
        longitude=center[0],
        latitude=center[1],
        radius_nm=radius_value,
    )

    if geometry is None:
        raise ValueError(
            "FAA TFR circle produced no geometry"
        )

    return geometry


def build_tfr_polygon_geojson(geometry):
    """Convert normalized FAA polygon geometry to GeoJSON."""

    if geometry.get("type") != "polygon":
        raise ValueError(
            "FAA TFR geometry is not a polygon"
        )

    segments = geometry.get("segments")

    if not segments:
        raise ValueError(
            "FAA TFR polygon contains no segments"
        )

    ring = []

    for segment in segments:
        segment_type = segment.get("type")

        if segment_type == "line":
            points = segment.get("points")

            if not points:
                raise ValueError(
                    "FAA TFR polygon line contains no points"
                )

        elif segment_type == "arc":
            radius = segment.get("radius") or {}

            if radius.get("unit") != "NM":
                raise ValueError(
                    "Unsupported FAA TFR arc radius unit: "
                    f"{radius.get('unit')}"
                )

            points = select_geodesic_arc_points(
                start=segment["start"],
                end=segment["end"],
                center=segment["center"],
                radius_nm=radius["value"],
                direction=segment["direction"],
            )

            if not points:
                raise ValueError(
                    "FAA TFR polygon arc produced no points"
                )

        else:
            raise ValueError(
                "Unsupported FAA TFR polygon segment type: "
                f"{segment_type}"
            )

        for point in points:
            normalized_point = [
                float(point[0]),
                float(point[1]),
            ]

            if (
                ring
                and ring[-1] == normalized_point
            ):
                continue

            ring.append(normalized_point)

    if len(ring) < 3:
        raise ValueError(
            "FAA TFR polygon contains insufficient coordinates"
        )

    if ring[0] != ring[-1]:
        ring.append(list(ring[0]))

    return {
        "type": "Polygon",
        "coordinates": [
            ring,
        ],
    }


def build_tfr_geometry_component_geojson(component):
    """Convert a normalized FAA geometry component to GeoJSON."""

    geometry = component.get("geometry")

    if not geometry:
        raise ValueError(
            "FAA TFR geometry component has no geometry"
        )

    geometry_type = geometry.get("type")

    if geometry_type == "circle":
        return build_tfr_circle_geojson(
            geometry
        )

    if geometry_type == "polygon":
        return build_tfr_polygon_geojson(
            geometry
        )

    raise ValueError(
        "Unsupported FAA TFR geometry type: "
        f"{geometry_type}"
    )


def build_tfr_airspace_usage_geojson(airspace_usage):
    """Build effective GeoJSON for one FAA AirspaceUsage."""

    components = airspace_usage.get(
        "geometry_components"
    )

    if not components:
        raise ValueError(
            "FAA TFR airspace usage has no geometry components"
        )

    base_geometries = []
    subtract_geometries = []

    for component in components:
        operation = component.get("operation")

        geometry = build_tfr_geometry_component_geojson(
            component
        )

        if operation == "BASE":
            base_geometries.append(
                geometry
            )

        elif operation == "SUBTR":
            subtract_geometries.append(
                geometry
            )

        else:
            raise ValueError(
                "Unsupported FAA TFR geometry operation: "
                f"{operation}"
            )

    if len(base_geometries) != 1:
        raise ValueError(
            "FAA TFR airspace usage must contain "
            "exactly one BASE geometry"
        )

    geometry = select_geometry_difference(
        base_geometries[0],
        subtract_geometries,
    )

    if geometry is None:
        raise ValueError(
            "FAA TFR airspace usage produced no geometry"
        )

    return geometry


def does_tfr_airspace_usage_intersect_geometry(
    airspace_usage,
    geometry,
):
    """Return whether an FAA AirspaceUsage intersects GeoJSON geometry."""

    tfr_geometry = build_tfr_airspace_usage_geojson(
        airspace_usage
    )

    intersects = select_geometries_intersect(
        tfr_geometry,
        geometry,
    )

    if intersects is None:
        raise ValueError(
            "FAA TFR geometry intersection produced no result"
        )

    return intersects


def does_tfr_intersect_geometry(
    tfr,
    geometry,
):
    """Return whether any AirspaceUsage in a TFR intersects geometry."""

    airspace_usages = tfr.get(
        "airspace_usages"
    )

    if not airspace_usages:
        raise ValueError(
            "FAA TFR contains no airspace usages"
        )

    for airspace_usage in airspace_usages:
        if does_tfr_airspace_usage_intersect_geometry(
            airspace_usage,
            geometry,
        ):
            return True

    return False


def is_tfr_airspace_usage_active(
    airspace_usage,
    current_datetime,
    tfr_begins_at,
    tfr_ends_at,
):
    """Return whether any layer in an AirspaceUsage is active."""

    layers = airspace_usage.get("layers")

    if not layers:
        raise ValueError(
            "FAA TFR airspace usage contains no layers"
        )

    for layer in layers:
        if is_tfr_layer_schedule_active(
            layer,
            current_datetime,
            tfr_begins_at,
            tfr_ends_at,
        ):
            return True

    return False


def is_tfr_applicable_to_geometry(
    tfr,
    geometry,
    current_datetime,
):
    """Return whether an active TFR intersects GeoJSON geometry."""

    airspace_usages = tfr.get(
        "airspace_usages"
    )

    if not airspace_usages:
        raise ValueError(
            "FAA TFR contains no airspace usages"
        )

    for airspace_usage in airspace_usages:
        if not is_tfr_airspace_usage_active(
            airspace_usage,
            current_datetime,
            tfr["begins_at"],
            tfr["ends_at"],
        ):
            continue

        if does_tfr_airspace_usage_intersect_geometry(
            airspace_usage,
            geometry,
        ):
            return True

    return False


def get_tfrs_for_geometry(
    geometry,
    current_datetime=None,
):
    """Return current FAA TFRs applicable to GeoJSON geometry."""

    if current_datetime is None:
        current_datetime = datetime.now(
            timezone.utc
        )

    if current_datetime.tzinfo is None:
        raise ValueError(
            "TFR applicability requires timezone-aware datetime"
        )

    candidate_notam_ids = set()

    for tfr_feature in get_tfrs():
        feature_geometry = tfr_feature.get(
            "geometry"
        )

        if not feature_geometry:
            continue

        intersects = select_geometries_intersect(
            feature_geometry,
            geometry,
        )

        if intersects:
            candidate_notam_ids.add(
                tfr_feature["notam_id"]
            )

    applicable_tfrs = []

    for notam_id in sorted(
        candidate_notam_ids
    ):
        tfr = parse_tfr_aixm(
            get_tfr_aixm(
                notam_id
            )
        )

        if is_tfr_applicable_to_geometry(
            tfr,
            geometry,
            current_datetime,
        ):
            applicable_tfrs.append(
                tfr
            )

    return applicable_tfrs


