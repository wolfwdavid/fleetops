"""MBR (Monthly Business Review) report generator.

Produces a Markdown report and a self-contained HTML version (inline CSS,
no JS, no external assets) so it can be emailed or opened on any machine.
"""

from __future__ import annotations

import html
from datetime import date
from pathlib import Path

import fleet as fleet_mod
import metrics as metrics_mod
import telemetry as telemetry_mod
from models import FleetData

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def _fmt(value: float | None, suffix: str = "") -> str:
    return "n/a" if value is None else f"{value:.1f}{suffix}"


def build_markdown(data: FleetData, as_of: date, window_days: int = 30) -> str:
    kpis = metrics_mod.compute(data, as_of, window_days)
    findings = fleet_mod.verify(data, as_of)
    anomalies = telemetry_mod.detect(data)
    counts = fleet_mod.status_counts(data.robots)

    lines: list[str] = []
    add = lines.append

    add(f"# MBR — {data.meta.get('fleet_name', 'Robot Fleet')}")
    add("")
    add(f"**Site:** {data.meta.get('site', 'n/a')}  ")
    add(f"**Period:** {kpis.window_start} to {kpis.as_of} ({window_days} days)  ")
    add(f"**Fleet size:** {kpis.robot_count} robots")
    add("")

    add("## Executive summary")
    add("")
    add(f"| KPI | Value |")
    add(f"|---|---|")
    add(f"| Fleet availability | {_fmt(kpis.availability_pct, ' %')} |")
    add(f"| Failures in period | {kpis.failures} |")
    add(f"| Total downtime | {_fmt(kpis.total_downtime_hours, ' h')} |")
    add(f"| MTBF | {_fmt(kpis.mtbf_hours, ' h')} |")
    add(f"| MTTR | {_fmt(kpis.mttr_hours, ' h')} |")
    add(f"| PM compliance | {_fmt(kpis.pm_compliance_pct, ' %')} |")
    add("")
    status_line = ", ".join(f"{n} {s}" for s, n in sorted(counts.items()))
    add(f"Current fleet state: {status_line}.")
    add("")

    add("## Availability by robot")
    add("")
    add("| Robot | Failures | Downtime (h) | Availability |")
    add("|---|---|---|---|")
    for k in kpis.per_robot:
        add(f"| {k.robot_id} | {k.failures} | {k.downtime_hours:.1f} | {k.availability_pct:.1f} % |")
    add("")

    add("## Fault Pareto (period failures by category)")
    add("")
    if kpis.pareto:
        add("| Category | Failures | Downtime (h) |")
        add("|---|---|---|")
        for cat, n, dt in kpis.pareto:
            add(f"| {cat} | {n} | {dt:.1f} |")
    else:
        add("No failures recorded in the period.")
    add("")

    add("## Telemetry anomalies")
    add("")
    if anomalies:
        add("| Robot | Sensor | Timestamp | Value | Series median | Score |")
        add("|---|---|---|---|---|---|")
        for a in anomalies:
            add(
                f"| {a.robot_id} | {a.sensor} | {a.timestamp} "
                f"| {a.value} {a.unit} | {a.series_median} {a.unit} | {a.score} |"
            )
    else:
        add("No anomalies above threshold.")
    add("")

    add("## Configuration & data-integrity findings")
    add("")
    if findings:
        add("| Severity | Robot | Check | Detail |")
        add("|---|---|---|---|")
        for f in findings:
            add(f"| {f.severity} | {f.robot_id or '—'} | {f.check} | {f.message} |")
    else:
        add("No findings — fleet configuration is clean.")
    add("")

    add("## Recommended actions")
    add("")
    n = 0
    for f in findings:
        if f.severity == "error":
            n += 1
            add(f"{n}. **{f.robot_id or 'Fleet'}** — resolve {f.check}: {f.message}")
    for a in anomalies:
        n += 1
        add(
            f"{n}. **{a.robot_id}** — investigate {a.sensor} excursion "
            f"({a.value} {a.unit} vs median {a.series_median} {a.unit}); "
            f"run `python cli.py diagnose` to fault-isolate"
        )
    if n == 0:
        add("No open actions.")
    add("")
    return "\n".join(lines)


def _bar(pct: float, color: str = "#2e7d32") -> str:
    pct = max(0.0, min(100.0, pct))
    return (
        f'<div style="background:#eee;border-radius:3px;width:220px;display:inline-block">'
        f'<div style="background:{color};width:{pct:.1f}%;height:12px;border-radius:3px"></div></div>'
    )


def build_html(data: FleetData, as_of: date, window_days: int = 30) -> str:
    kpis = metrics_mod.compute(data, as_of, window_days)
    findings = fleet_mod.verify(data, as_of)
    anomalies = telemetry_mod.detect(data)
    e = html.escape

    css = (
        "body{font-family:Segoe UI,Arial,sans-serif;max-width:880px;margin:2em auto;"
        "color:#222;line-height:1.45}h1{border-bottom:3px solid #1a73e8;padding-bottom:.3em}"
        "h2{color:#1a73e8;margin-top:1.6em}table{border-collapse:collapse;width:100%;"
        "margin:.6em 0}th,td{border:1px solid #ddd;padding:6px 10px;text-align:left;"
        "font-size:14px}th{background:#f5f7fa}.kpi{display:inline-block;background:#f5f7fa;"
        "border:1px solid #ddd;border-radius:8px;padding:10px 18px;margin:4px;text-align:center}"
        ".kpi b{display:block;font-size:22px;color:#1a73e8}.sev-error{color:#c62828;font-weight:600}"
        ".sev-warning{color:#ef6c00;font-weight:600}.sev-info{color:#555}"
    )

    parts: list[str] = []
    add = parts.append
    add("<!DOCTYPE html><html><head><meta charset='utf-8'>")
    add(f"<title>MBR {e(str(as_of))}</title><style>{css}</style></head><body>")
    add(f"<h1>MBR — {e(data.meta.get('fleet_name', 'Robot Fleet'))}</h1>")
    add(f"<p><b>Site:</b> {e(data.meta.get('site', 'n/a'))}<br>"
        f"<b>Period:</b> {kpis.window_start} to {kpis.as_of} ({window_days} days)<br>"
        f"<b>Fleet size:</b> {kpis.robot_count} robots</p>")

    add("<h2>Executive summary</h2><div>")
    for label, value in (
        ("Availability", _fmt(kpis.availability_pct, " %")),
        ("Failures", str(kpis.failures)),
        ("Downtime", _fmt(kpis.total_downtime_hours, " h")),
        ("MTBF", _fmt(kpis.mtbf_hours, " h")),
        ("MTTR", _fmt(kpis.mttr_hours, " h")),
        ("PM compliance", _fmt(kpis.pm_compliance_pct, " %")),
    ):
        add(f"<span class='kpi'><b>{e(value)}</b>{e(label)}</span>")
    add("</div>")

    add("<h2>Availability by robot</h2><table>")
    add("<tr><th>Robot</th><th>Failures</th><th>Downtime (h)</th><th>Availability</th><th></th></tr>")
    for k in kpis.per_robot:
        color = "#2e7d32" if k.availability_pct >= 99 else "#ef6c00" if k.availability_pct >= 98 else "#c62828"
        add(f"<tr><td>{e(k.robot_id)}</td><td>{k.failures}</td><td>{k.downtime_hours:.1f}</td>"
            f"<td>{k.availability_pct:.1f} %</td><td>{_bar(k.availability_pct, color)}</td></tr>")
    add("</table>")

    add("<h2>Fault Pareto</h2>")
    if kpis.pareto:
        max_n = kpis.pareto[0][1]
        add("<table><tr><th>Category</th><th>Failures</th><th>Downtime (h)</th><th></th></tr>")
        for cat, n, dt in kpis.pareto:
            add(f"<tr><td>{e(cat)}</td><td>{n}</td><td>{dt:.1f}</td>"
                f"<td>{_bar(100.0 * n / max_n, '#1a73e8')}</td></tr>")
        add("</table>")
    else:
        add("<p>No failures recorded in the period.</p>")

    add("<h2>Telemetry anomalies</h2>")
    if anomalies:
        add("<table><tr><th>Robot</th><th>Sensor</th><th>Timestamp</th><th>Value</th>"
            "<th>Median</th><th>Score</th></tr>")
        for a in anomalies:
            add(f"<tr><td>{e(a.robot_id)}</td><td>{e(a.sensor)}</td><td>{e(a.timestamp)}</td>"
                f"<td>{a.value} {e(a.unit)}</td><td>{a.series_median} {e(a.unit)}</td>"
                f"<td class='sev-error'>{a.score}</td></tr>")
        add("</table>")
    else:
        add("<p>No anomalies above threshold.</p>")

    add("<h2>Configuration &amp; data-integrity findings</h2>")
    if findings:
        add("<table><tr><th>Severity</th><th>Robot</th><th>Check</th><th>Detail</th></tr>")
        for f in findings:
            add(f"<tr><td class='sev-{f.severity}'>{e(f.severity)}</td><td>{e(f.robot_id) or '—'}</td>"
                f"<td>{e(f.check)}</td><td>{e(f.message)}</td></tr>")
        add("</table>")
    else:
        add("<p>No findings — fleet configuration is clean.</p>")

    add("</body></html>")
    return "".join(parts)


def write_reports(data: FleetData, as_of: date, window_days: int = 30,
                  out_dir: Path = REPORTS_DIR) -> tuple[Path, Path]:
    out_dir.mkdir(exist_ok=True)
    stem = f"MBR-{as_of.isoformat()}"
    md_path = out_dir / f"{stem}.md"
    html_path = out_dir / f"{stem}.html"
    md_path.write_text(build_markdown(data, as_of, window_days), encoding="utf-8")
    html_path.write_text(build_html(data, as_of, window_days), encoding="utf-8")
    return md_path, html_path
