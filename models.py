"""Data models and file loaders for FleetOps.

Everything is stdlib-only so the toolkit runs on any machine with Python 3,
including locked-down site laptops with no package installs allowed.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

VALID_STATUSES = {"operational", "degraded", "down", "maintenance"}


@dataclass
class Robot:
    id: str
    model: str
    firmware: str
    commissioned: date
    status: str
    sensors: list[str]
    parts: dict[str, str]
    last_pm: date
    pm_interval_days: int

    @property
    def firmware_tuple(self) -> tuple[int, ...]:
        """Firmware as a comparable tuple, e.g. '2.4.1' -> (2, 4, 1)."""
        return tuple(int(p) for p in self.firmware.split("."))

    @property
    def pm_due_date(self) -> date:
        return self.last_pm + timedelta(days=self.pm_interval_days)

    def pm_overdue(self, as_of: date) -> bool:
        return self.pm_due_date < as_of


@dataclass
class MaintenanceEvent:
    date: date
    robot_id: str
    event_type: str  # failure | repair | pm
    category: str    # sensor | wiring | actuator | software | mechanical | preventive
    downtime_hours: float
    description: str


@dataclass
class TelemetryReading:
    timestamp: datetime
    robot_id: str
    sensor: str
    value: float
    unit: str


@dataclass
class FleetData:
    """Everything the CLI commands need, loaded once."""
    meta: dict
    robots: list[Robot]
    events: list[MaintenanceEvent]
    readings: list[TelemetryReading]

    def robot(self, robot_id: str) -> Robot | None:
        return next((r for r in self.robots if r.id == robot_id), None)


def load_fleet(path: Path = DATA_DIR / "fleet.json") -> tuple[dict, list[Robot]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    robots = [
        Robot(
            id=r["id"],
            model=r["model"],
            firmware=r["firmware"],
            commissioned=date.fromisoformat(r["commissioned"]),
            status=r["status"],
            sensors=list(r["sensors"]),
            parts=dict(r["parts"]),
            last_pm=date.fromisoformat(r["last_pm"]),
            pm_interval_days=int(r["pm_interval_days"]),
        )
        for r in raw["robots"]
    ]
    meta = {k: v for k, v in raw.items() if k != "robots"}
    return meta, robots


def load_maintenance_log(path: Path = DATA_DIR / "maintenance_log.csv") -> list[MaintenanceEvent]:
    with path.open(newline="", encoding="utf-8") as f:
        return [
            MaintenanceEvent(
                date=date.fromisoformat(row["date"]),
                robot_id=row["robot_id"],
                event_type=row["event_type"],
                category=row["category"],
                downtime_hours=float(row["downtime_hours"]),
                description=row["description"],
            )
            for row in csv.DictReader(f)
        ]


def load_telemetry(path: Path = DATA_DIR / "telemetry.csv") -> list[TelemetryReading]:
    with path.open(newline="", encoding="utf-8") as f:
        return [
            TelemetryReading(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                robot_id=row["robot_id"],
                sensor=row["sensor"],
                value=float(row["value"]),
                unit=row["unit"],
            )
            for row in csv.DictReader(f)
        ]


def load_all(data_dir: Path = DATA_DIR) -> FleetData:
    meta, robots = load_fleet(data_dir / "fleet.json")
    events = load_maintenance_log(data_dir / "maintenance_log.csv")
    readings = load_telemetry(data_dir / "telemetry.csv")
    return FleetData(meta=meta, robots=robots, events=events, readings=readings)
