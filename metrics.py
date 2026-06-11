"""Fleet KPIs: availability, MTBF, MTTR, PM compliance, fault Pareto.

These are the numbers an MBR (Monthly Business Review) deck is built from.
All metrics are computed over a trailing window ending at `as_of`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from models import FleetData, MaintenanceEvent


@dataclass
class RobotKpis:
    robot_id: str
    failures: int
    downtime_hours: float
    availability_pct: float


@dataclass
class FleetKpis:
    window_days: int
    window_start: date
    as_of: date
    robot_count: int
    failures: int
    total_downtime_hours: float
    availability_pct: float
    mtbf_hours: float | None   # None when no failures in window
    mttr_hours: float | None
    pm_compliance_pct: float
    pareto: list[tuple[str, int, float]]  # (category, failure count, downtime h)
    per_robot: list[RobotKpis]


def _window_events(events: list[MaintenanceEvent], start: date, end: date) -> list[MaintenanceEvent]:
    return [e for e in events if start <= e.date <= end]


def compute(data: FleetData, as_of: date, window_days: int = 30) -> FleetKpis:
    start = as_of - timedelta(days=window_days)
    window = _window_events(data.events, start, as_of)
    failures = [e for e in window if e.event_type == "failure"]

    window_hours = window_days * 24
    per_robot: list[RobotKpis] = []
    for r in data.robots:
        own = [e for e in failures if e.robot_id == r.id]
        downtime = sum(e.downtime_hours for e in own)
        per_robot.append(RobotKpis(
            robot_id=r.id,
            failures=len(own),
            downtime_hours=downtime,
            availability_pct=100.0 * (1 - downtime / window_hours),
        ))

    total_downtime = sum(k.downtime_hours for k in per_robot)
    fleet_hours = window_hours * len(data.robots)
    uptime_hours = fleet_hours - total_downtime

    pareto_counts: Counter = Counter()
    pareto_downtime: dict[str, float] = {}
    for e in failures:
        pareto_counts[e.category] += 1
        pareto_downtime[e.category] = pareto_downtime.get(e.category, 0.0) + e.downtime_hours
    pareto = sorted(
        ((cat, n, pareto_downtime[cat]) for cat, n in pareto_counts.items()),
        key=lambda t: (-t[1], -t[2]),
    )

    compliant = sum(1 for r in data.robots if not r.pm_overdue(as_of))

    return FleetKpis(
        window_days=window_days,
        window_start=start,
        as_of=as_of,
        robot_count=len(data.robots),
        failures=len(failures),
        total_downtime_hours=total_downtime,
        availability_pct=100.0 * uptime_hours / fleet_hours if fleet_hours else 100.0,
        mtbf_hours=uptime_hours / len(failures) if failures else None,
        mttr_hours=total_downtime / len(failures) if failures else None,
        pm_compliance_pct=100.0 * compliant / len(data.robots) if data.robots else 100.0,
        pareto=pareto,
        per_robot=sorted(per_robot, key=lambda k: k.availability_pct),
    )
