"""FleetOps CLI — robot fleet operations toolkit.

Usage:
  python cli.py status                       # fleet status table
  python cli.py verify                       # config/data integrity checks
  python cli.py diagnose                     # interactive fault isolation
  python cli.py diagnose --answers n,y,y     # scripted fault isolation
  python cli.py telemetry [--threshold 3.5]  # sensor anomaly detection
  python cli.py report [--window 30]         # generate MBR (md + html)

All commands accept --as-of YYYY-MM-DD (defaults to today).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

import diagnostics
import fleet as fleet_mod
import metrics as metrics_mod
import report as report_mod
import telemetry as telemetry_mod
from models import load_all


def _table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
              for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    out = [fmt.format(*headers), fmt.format(*("-" * w for w in widths))]
    out += [fmt.format(*row) for row in rows]
    return "\n".join(out)


def cmd_status(data, as_of: date, _args) -> int:
    kpis = metrics_mod.compute(data, as_of)
    rows = []
    for r in sorted(data.robots, key=lambda r: r.id):
        pm = f"OVERDUE ({(as_of - r.pm_due_date).days}d)" if r.pm_overdue(as_of) else str(r.pm_due_date)
        rows.append([r.id, r.model, r.firmware, r.status, str(r.last_pm), pm])
    print(f"{data.meta.get('fleet_name')} — {data.meta.get('site')}  (as of {as_of})\n")
    print(_table(["ID", "Model", "FW", "Status", "Last PM", "PM due"], rows))
    counts = fleet_mod.status_counts(data.robots)
    print(f"\n{len(data.robots)} robots: " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())))
    print(f"30-day availability: {kpis.availability_pct:.1f} %   "
          f"PM compliance: {kpis.pm_compliance_pct:.1f} %")
    return 0


def cmd_verify(data, as_of: date, _args) -> int:
    findings = fleet_mod.verify(data, as_of)
    if not findings:
        print("OK — no integrity findings.")
        return 0
    rows = [[f.severity.upper(), f.robot_id or "—", f.check, f.message] for f in findings]
    print(_table(["Severity", "Robot", "Check", "Detail"], rows))
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    print(f"\n{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def cmd_diagnose(data, _as_of: date, args) -> int:
    tree = diagnostics.load_tree()
    if args.answers:
        try:
            result = diagnostics.run_auto(tree, diagnostics.parse_answers(args.answers))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        print(f"{tree['name']} v{tree['version']} — answer y/n\n")
        result = diagnostics.run_interactive(tree)
    print("\nPath taken:")
    for q, a in result.path:
        print(f"  [{a:>3}] {q}")
    print(f"\nDiagnosis: {result.diagnosis}  (category: {result.category})")
    print("Actions:")
    for i, action in enumerate(result.actions, 1):
        print(f"  {i}. {action}")
    return 0


def cmd_telemetry(data, _as_of: date, args) -> int:
    anomalies = telemetry_mod.detect(data, threshold=args.threshold)
    if not anomalies:
        print(f"No anomalies at threshold {args.threshold}.")
        return 0
    rows = [[a.robot_id, a.sensor, a.timestamp, f"{a.value} {a.unit}",
             f"{a.series_median} {a.unit}", str(a.score)] for a in anomalies]
    print(_table(["Robot", "Sensor", "Timestamp", "Value", "Median", "Score"], rows))
    print(f"\n{len(anomalies)} anomaly(ies) at modified-z threshold {args.threshold}")
    return 0


def cmd_report(data, as_of: date, args) -> int:
    md_path, html_path = report_mod.write_reports(data, as_of, window_days=args.window)
    print(f"Wrote {md_path}")
    print(f"Wrote {html_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fleetops", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                        help="reference date for PM/metrics (YYYY-MM-DD, default: today)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="fleet status table")
    sub.add_parser("verify", help="config & data integrity checks")

    p_diag = sub.add_parser("diagnose", help="decision-tree fault isolation")
    p_diag.add_argument("--answers", help="scripted y/n answers, e.g. 'n,y,y'")

    p_tel = sub.add_parser("telemetry", help="sensor anomaly detection")
    p_tel.add_argument("--threshold", type=float, default=telemetry_mod.DEFAULT_THRESHOLD,
                       help=f"modified z-score cutoff (default {telemetry_mod.DEFAULT_THRESHOLD})")

    p_rep = sub.add_parser("report", help="generate MBR report (md + html)")
    p_rep.add_argument("--window", type=int, default=30, help="trailing window in days (default 30)")

    args = parser.parse_args(argv)
    data = load_all()
    handler = {
        "status": cmd_status,
        "verify": cmd_verify,
        "diagnose": cmd_diagnose,
        "telemetry": cmd_telemetry,
        "report": cmd_report,
    }[args.command]
    return handler(data, args.as_of, args)


if __name__ == "__main__":
    sys.exit(main())
