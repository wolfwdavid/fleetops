# FleetOps — Robot Fleet Operations Toolkit

A self-contained Python toolkit for managing the operational health of a
robotic fleet: configuration integrity, fault diagnosis, sensor anomaly
detection, KPI metrics, and stakeholder (MBR) reporting.

Built as a working demonstration of the software/process half of a robot
maintenance & technical operations role. **Stdlib only** — runs on any
machine with Python 3.10+, no installs, no internet (data-center-floor
friendly).

## What it does

| Capability | Command | Demonstrates |
|---|---|---|
| Fleet status & PM tracking | `python cli.py status` | Operational awareness, PM scheduling |
| Config & data integrity checks | `python cli.py verify` | Configuration management, data integrity |
| Decision-tree fault isolation | `python cli.py diagnose` | Structured diagnostic workflows |
| Sensor anomaly detection | `python cli.py telemetry` | Sensor data analysis (robust statistics) |
| MBR report (Markdown + HTML) | `python cli.py report` | Presenting operational data to stakeholders |

All commands accept `--as-of YYYY-MM-DD` for reproducible runs against the
sample data.

## Quick start

```
python cli.py status
python cli.py verify                 # exits non-zero on errors -> CI-gateable
python cli.py diagnose               # interactive fault isolation
python cli.py diagnose --answers n,y,y   # scripted: lidar fault path
python cli.py telemetry              # flags RBT-003 current spike + thermal excursion
python cli.py report                 # writes reports/MBR-<date>.{md,html}
```

## How it works

```
data/
  fleet.json           single source of truth: robots, firmware, parts, PM state
  maintenance_log.csv  failures / repairs / PM events with downtime hours
  telemetry.csv        time-series sensor readings
  decision_tree.json   fault-isolation tree (editable by techs, no code changes)

models.py       dataclasses + loaders
fleet.py        integrity verifier: firmware vs baseline, part-revision drift,
                PM overdue, orphan records, unexplained 'down' status
metrics.py      availability, MTBF, MTTR, PM compliance, fault Pareto
diagnostics.py  decision-tree engine (interactive + scripted replay)
telemetry.py    modified z-score (median/MAD) anomaly detection
report.py       MBR generator: Markdown + self-contained HTML
cli.py          argparse entrypoint

docs/RUNBOOK.md  maintenance SOP: daily checks, PM, fault isolation, escalation
```

### Design choices worth noting

- **Robust statistics, not naive z-scores.** A single 55.8 °C spike in a
  ~41 °C series only scores z ≈ 1.8 with mean/stdev (the outlier inflates its
  own baseline). The modified z-score (median/MAD) scores it ~25 and the
  9.8 A current spike ~89 — both flagged, zero false positives on healthy
  series.
- **The decision tree is data, not code.** Technicians extend
  `decision_tree.json` without touching Python; the loader validates every
  branch terminates at a leaf and fails loudly on a broken tree.
- **`verify` exits non-zero on errors** so it can gate a pipeline or a
  pre-shift check, same as a failing test.
- **Reports are self-contained.** The HTML MBR has inline CSS, no JS, no
  external assets — it can be emailed and renders identically everywhere.

## JD → feature mapping

| Job requirement | Where it's demonstrated |
|---|---|
| "Structured problem-solving and diagnostic workflows" | `diagnostics.py` + `data/decision_tree.json`, every leaf citing a precedent repair |
| "Meticulous attention to data integrity and configuration management" | `fleet.py` verifier: firmware baseline, part-revision drift, orphan records |
| "Clear, instructional technical documentation" | `docs/RUNBOOK.md` — executable by a new hire without tribal knowledge |
| "Presenting operational data to stakeholders (MBRs)" | `report.py` — availability, MTBF/MTTR, Pareto, recommended actions |
| "Sensor, wire and (Python or Linux)" | `telemetry.py` sensor analytics; wiring/sensor fault paths in the decision tree |

## Sample data

The fleet is a simulated 8-robot data-center fleet (inspection + haul
models) with realistic seeded faults: an overdue-PM unit with a lidar
recurrence (RBT-003), a down unit with a seized caster (RBT-006), firmware
and part-revision drift, and telemetry excursions that the anomaly detector
catches.
