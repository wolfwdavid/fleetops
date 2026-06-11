# FleetOps Maintenance Runbook

Standard operating procedures for the DC-West robotic fleet. Written so a
newly onboarded technician can execute every procedure without tribal
knowledge.

---

## 1. Daily fleet health check (start of shift)

1. Run `python cli.py status`.
2. Confirm every robot reports `operational`. For any `degraded` or `down`
   unit, check the maintenance log for an open investigation; if none exists,
   open one before doing anything else.
3. Run `python cli.py telemetry`. Any anomaly above threshold gets a ticket
   the same shift — sensor excursions are leading indicators (a current spike
   today is a seized bearing next week).
4. Run `python cli.py verify`. Errors (PM overdue > 14 days, orphan records)
   must be cleared or escalated before end of shift; warnings go on the
   weekly worklist.

## 2. Preventive maintenance (PM) procedure

**Cadence:** every robot, every `pm_interval_days` (currently 30).
**Compliance target:** 100 % — `verify` flags anything overdue.

1. Tag the robot out of service; set status to `maintenance` in
   `data/fleet.json`.
2. Perform the model checklist: lubrication, connector inspection and
   reseat, harness abrasion check, optics cleaning (InspectBot), drive belt
   and load-cell check (HaulBot), firmware version vs fleet baseline.
3. Replace wear items proactively if > 70 % worn — a planned 1.5 h PM beats
   a 12 h unplanned failure (see RBT-006 caster seizure, 2026-05-24).
4. Update `last_pm` in `data/fleet.json` and append a `pm` row to
   `data/maintenance_log.csv`.
5. Return status to `operational` only after a self-test pass.

## 3. Fault isolation procedure

When a robot faults, **do not start swapping parts.** Run the decision tree:

```
python cli.py diagnose          # interactive, walks you through it
```

The tree (`data/decision_tree.json`) encodes the fleet's actual failure
history — every leaf cites the precedent repair. Top-level flow:

```
Unresponsive? ──yes──> Normal idle current? ──yes──> CONTROLLER
     │                        └──no──> POWER / BATTERY
     no
     ▼
Sensor faults? ──yes──> Optical? ──yes──> LIDAR / OPTICS
     │                     └──no──> Bus errors? ──yes──> WIRING
     no                                  └──no──> SENSOR CALIBRATION
     ▼
Overcurrent / motion fault? ──yes──> Moves freely de-energized?
     │                                  ├──yes──> ACTUATOR / MOTOR
     no                                 └──no───> MECHANICAL SEIZURE
     ▼
Started after fw/config change? ──yes──> SOFTWARE ROLLBACK
     └──no──> ESCALATE with evidence package
```

**Rules:**
- Capture logs **before** any reset. Evidence first, recovery second.
- Every failure and repair gets a row in `data/maintenance_log.csv` with
  honest `downtime_hours` — the MBR numbers are only as good as the log.
- Two recurrences of the same fault on the same unit = stop repairing,
  start root-cause investigation (see RBT-003 lidar, 2026-06-08).

## 4. Configuration management

The fleet config (`data/fleet.json`) is the single source of truth for
firmware, part revisions, and PM state.

- **Any** physical change to a robot (part swap, firmware update) is
  reflected in `fleet.json` in the same work session. No exceptions.
- `python cli.py verify` runs the drift checks: firmware behind model
  baseline, part revision differing from fleet majority, PM overdue,
  log/telemetry rows referencing unknown robots.
- Run `verify` after every config edit; it exits non-zero on errors so it
  can gate an automated pipeline.

## 5. Monthly Business Review (MBR)

1. On the first business day of the month, run:
   `python cli.py report --window 30`
2. Outputs land in `reports/` as Markdown (for the wiki) and self-contained
   HTML (for email — no external assets, renders anywhere).
3. Review the Recommended Actions section; every item gets an owner and a
   date before the report is sent.
4. Talking order for the meeting: availability trend → Pareto (what's
   actually costing us hours) → PM compliance → open actions from last MBR.

## 6. Escalation

| Condition | Action |
|---|---|
| Safety risk (thermal event, unexpected motion) | E-stop, tag out, escalate immediately |
| Same fault twice on one unit | Root-cause investigation, not a third repair |
| Diagnosis reaches the ESCALATE leaf | Evidence package to site engineering |
| Fleet availability < 98 % in any week | Flag to operations lead, don't wait for MBR |
