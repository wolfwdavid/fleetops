"""Fleet configuration integrity verification.

Catches the config-drift problems that bite robot fleets in practice:
firmware behind baseline, mixed part revisions, overdue PM, and log/telemetry
records pointing at robots that don't exist.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from models import VALID_STATUSES, FleetData, Robot

SEVERITIES = ("error", "warning", "info")


@dataclass
class Finding:
    severity: str   # error | warning | info
    robot_id: str   # "" for fleet-wide findings
    check: str
    message: str


def _baseline_firmware(robots: list[Robot]) -> dict[str, str]:
    """Highest firmware version seen per model = the fleet baseline."""
    baseline: dict[str, str] = {}
    for r in robots:
        if r.model not in baseline or r.firmware_tuple > tuple(
            int(p) for p in baseline[r.model].split(".")
        ):
            baseline[r.model] = r.firmware
    return baseline


def _majority_parts(robots: list[Robot]) -> dict[str, dict[str, str]]:
    """Most common revision per part slot per model."""
    majority: dict[str, dict[str, str]] = {}
    for model in {r.model for r in robots}:
        slots: dict[str, Counter] = {}
        for r in robots:
            if r.model != model:
                continue
            for slot, part in r.parts.items():
                slots.setdefault(slot, Counter())[part] += 1
        majority[model] = {slot: c.most_common(1)[0][0] for slot, c in slots.items()}
    return majority


def verify(data: FleetData, as_of: date) -> list[Finding]:
    findings: list[Finding] = []
    robots = data.robots

    # Unique IDs
    dupes = [rid for rid, n in Counter(r.id for r in robots).items() if n > 1]
    for rid in dupes:
        findings.append(Finding("error", rid, "unique-id", f"Duplicate robot id {rid}"))

    # Valid status values
    for r in robots:
        if r.status not in VALID_STATUSES:
            findings.append(Finding(
                "error", r.id, "status",
                f"Invalid status '{r.status}' (expected one of {sorted(VALID_STATUSES)})",
            ))

    # Firmware vs model baseline
    baseline = _baseline_firmware(robots)
    for r in robots:
        if r.firmware != baseline[r.model]:
            findings.append(Finding(
                "warning", r.id, "firmware",
                f"Firmware {r.firmware} behind {r.model} baseline {baseline[r.model]}",
            ))

    # Part revision drift vs model majority
    majority = _majority_parts(robots)
    for r in robots:
        for slot, part in r.parts.items():
            expected = majority[r.model].get(slot)
            if expected and part != expected:
                findings.append(Finding(
                    "warning", r.id, "part-revision",
                    f"{slot} is {part}; fleet majority for {r.model} is {expected}",
                ))

    # PM overdue
    for r in robots:
        if r.pm_overdue(as_of):
            days = (as_of - r.pm_due_date).days
            findings.append(Finding(
                "error" if days > 14 else "warning", r.id, "pm-overdue",
                f"PM overdue by {days} days (last {r.last_pm}, due {r.pm_due_date})",
            ))

    # Cross-reference: every logged/telemetered robot must exist in the fleet
    known = {r.id for r in robots}
    for source, ids in (
        ("maintenance log", {e.robot_id for e in data.events}),
        ("telemetry", {t.robot_id for t in data.readings}),
    ):
        for rid in sorted(ids - known):
            findings.append(Finding(
                "error", rid, "orphan-record",
                f"{source} references unknown robot {rid}",
            ))

    # Down robots should have a recent failure on record explaining why
    failed_ids = {e.robot_id for e in data.events if e.event_type == "failure"}
    for r in robots:
        if r.status == "down" and r.id not in failed_ids:
            findings.append(Finding(
                "warning", r.id, "down-unexplained",
                "Status is 'down' but no failure event exists in the log",
            ))

    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: (order[f.severity], f.robot_id))
    return findings


def status_counts(robots: list[Robot]) -> Counter:
    return Counter(r.status for r in robots)
