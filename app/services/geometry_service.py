from __future__ import annotations

import math



def offset_segment(
    start_coordinate: list[float],
    end_coordinate: list[float],
    offset_ft: float,
) -> tuple[list[float], list[float]]:
    """Return a segment shifted laterally by offset_ft."""

    start_longitude, start_latitude = start_coordinate
    end_longitude, end_latitude = end_coordinate

    mean_latitude_radians = math.radians(
        (start_latitude + end_latitude) / 2
    )

    feet_per_degree_latitude = 364000.0
    feet_per_degree_longitude = (
        feet_per_degree_latitude * math.cos(mean_latitude_radians)
    )

    delta_x_ft = (
        end_longitude - start_longitude
    ) * feet_per_degree_longitude

    delta_y_ft = (
        end_latitude - start_latitude
    ) * feet_per_degree_latitude

    segment_length_ft = math.hypot(delta_x_ft, delta_y_ft)

    if segment_length_ft == 0:
        raise ValueError("Cannot offset a zero-length segment.")

    right_x_ft = delta_y_ft / segment_length_ft
    right_y_ft = -delta_x_ft / segment_length_ft

    offset_longitude = (
        right_x_ft * offset_ft / feet_per_degree_longitude
    )
    offset_latitude = (
        right_y_ft * offset_ft / feet_per_degree_latitude
    )

    return (
        [
            start_longitude + offset_longitude,
            start_latitude + offset_latitude,
        ],
        [
            end_longitude + offset_longitude,
            end_latitude + offset_latitude,
        ],
    )


def intersect_lines(
    first_start: list[float],
    first_end: list[float],
    second_start: list[float],
    second_end: list[float],
) -> list[float] | None:
    """Return the intersection of two infinite lines, or None if parallel."""

    x1, y1 = first_start
    x2, y2 = first_end
    x3, y3 = second_start
    x4, y4 = second_end

    denominator = (
        (x1 - x2) * (y3 - y4)
        - (y1 - y2) * (x3 - x4)
    )

    if abs(denominator) < 1e-15:
        return None

    first_cross = x1 * y2 - y1 * x2
    second_cross = x3 * y4 - y3 * x4

    intersection_x = (
        first_cross * (x3 - x4)
        - (x1 - x2) * second_cross
    ) / denominator

    intersection_y = (
        first_cross * (y3 - y4)
        - (y1 - y2) * second_cross
    ) / denominator

    return [intersection_x, intersection_y]


def build_offset_polyline(
    coordinates: list[list[float]],
    segment_widths_ft: list[float],
    side: str,
) -> list[list[float]]:
    """Return a Route polyline offset to the requested side."""

    if len(coordinates) < 2:
        raise ValueError("Polyline must contain at least two coordinates.")

    if len(segment_widths_ft) != len(coordinates) - 1:
        raise ValueError(
            "Segment widths must match the number of Route segments."
        )

    if side not in {"left", "right"}:
        raise ValueError("Offset side must be 'left' or 'right'.")

    side_multiplier = 1.0 if side == "right" else -1.0

    offset_segments: list[
        tuple[list[float], list[float]]
    ] = []

    for segment_index in range(len(coordinates) - 1):
        offset_ft = (
            segment_widths_ft[segment_index] / 4.0
        ) * side_multiplier

        offset_segments.append(
            offset_segment(
                coordinates[segment_index],
                coordinates[segment_index + 1],
                offset_ft,
            )
        )

    offset_coordinates: list[list[float]] = [
        offset_segments[0][0]
    ]

    for segment_index in range(len(offset_segments) - 1):
        current_segment = offset_segments[segment_index]
        next_segment = offset_segments[segment_index + 1]

        intersection = intersect_lines(
            current_segment[0],
            current_segment[1],
            next_segment[0],
            next_segment[1],
        )

        if intersection is None:
            intersection = current_segment[1]

        offset_coordinates.append(intersection)

    offset_coordinates.append(
        offset_segments[-1][1]
    )

    return offset_coordinates


