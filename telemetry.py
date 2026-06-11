"""Sensor telemetry anomaly detection (stdlib only).

Uses the modified z-score (Iglewicz & Hoaglin): 0.6745 * (x - median) / MAD.
Median/MAD are robust to the outlier itself, so a single 55 C spike in a
40 C series still scores high — a plain z-score gets dragged down because
the spike inflates the mean and stdev it is measured against.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from models import FleetData, TelemetryReading

DEFAULT_THRESHOLD = 3.5  # Iglewicz & Hoaglin's recommended cutoff
MIN_POINTS = 4           # below this, "anomaly" is meaningless


@dataclass
class Anomaly:
    robot_id: str
    sensor: str
    timestamp: str
    value: float
    unit: str
    score: float
    series_median: float


def _modified_z(values: list[float]) -> list[float]:
    med = median(values)
    abs_dev = [abs(v - med) for v in values]
    mad = median(abs_dev)
    if mad == 0:
        # Fall back to mean absolute deviation (constant-ish series)
        mean_ad = sum(abs_dev) / len(abs_dev)
        if mean_ad == 0:
            return [0.0] * len(values)  # truly constant: no anomalies
        return [(v - med) / (1.253314 * mean_ad) for v in values]
    return [0.6745 * (v - med) / mad for v in values]


def detect(data: FleetData, threshold: float = DEFAULT_THRESHOLD) -> list[Anomaly]:
    series: dict[tuple[str, str], list[TelemetryReading]] = {}
    for t in data.readings:
        series.setdefault((t.robot_id, t.sensor), []).append(t)

    anomalies: list[Anomaly] = []
    for (robot_id, sensor), readings in sorted(series.items()):
        if len(readings) < MIN_POINTS:
            continue
        readings.sort(key=lambda t: t.timestamp)
        values = [t.value for t in readings]
        scores = _modified_z(values)
        med = median(values)
        for reading, score in zip(readings, scores):
            if abs(score) >= threshold:
                anomalies.append(Anomaly(
                    robot_id=robot_id,
                    sensor=sensor,
                    timestamp=reading.timestamp.isoformat(),
                    value=reading.value,
                    unit=reading.unit,
                    score=round(score, 2),
                    series_median=med,
                ))
    anomalies.sort(key=lambda a: -abs(a.score))
    return anomalies
