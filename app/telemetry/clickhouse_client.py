from __future__ import annotations

import os
from typing import Any

import clickhouse_connect


CLICKHOUSE_HOST = os.environ.get(
    "CLICKHOUSE_HOST",
    "clickhouse",
)

CLICKHOUSE_PORT = int(
    os.environ.get(
        "CLICKHOUSE_PORT",
        "8123",
    )
)

CLICKHOUSE_DATABASE = os.environ.get(
    "CLICKHOUSE_DATABASE",
    "dronenav",
)

CLICKHOUSE_USER = os.environ.get(
    "CLICKHOUSE_USER",
    "default",
)

CLICKHOUSE_PASSWORD = os.environ.get(
    "CLICKHOUSE_PASSWORD",
    "",
)


class ClickHouseTelemetryClient:
    """Low-level ClickHouse interface for raw telemetry storage."""

    def __init__(self) -> None:
        self.client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DATABASE,
        )

    def insert_raw_telemetry(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        """Insert one or more raw telemetry rows."""

        if not rows:
            return

        self.client.insert(
            "telemetry_raw",
            rows,
            column_names=[
                "flight_execution_id",
                "flight_id",
                "observed_at",
                "latitude",
                "longitude",
                "relative_altitude_ft",
                "absolute_altitude_ft",
                "armed",
                "heartbeat_active",
                "mission_sequence",
                "battery_percent",
                "energy_health",
                "navigation_health",
                "vehicle_health",
            ],
        )

