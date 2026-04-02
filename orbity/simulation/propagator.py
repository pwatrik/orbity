from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

import numpy as np

from orbity.config.models import BodyConfig

SECONDS_PER_DAY = 86400.0


@dataclass(slots=True)
class StateVector:
    position_m: np.ndarray
    velocity_mps: np.ndarray


def _rotation_matrix(inc: float, lan: float, argp: float) -> np.ndarray:
    ci = math.cos(inc)
    si = math.sin(inc)
    co = math.cos(lan)
    so = math.sin(lan)
    cw = math.cos(argp)
    sw = math.sin(argp)

    return np.array(
        [
            [co * cw - so * sw * ci, -co * sw - so * cw * ci, so * si],
            [so * cw + co * sw * ci, -so * sw + co * cw * ci, -co * si],
            [sw * si, cw * si, ci],
        ],
        dtype=np.float64,
    )


def _solve_eccentric_anomaly(mean_anomaly_rad: float, eccentricity: float) -> float:
    if eccentricity < 1e-12:
        return mean_anomaly_rad

    ecc_anomaly = mean_anomaly_rad
    for _ in range(6):
        f = ecc_anomaly - eccentricity * math.sin(ecc_anomaly) - mean_anomaly_rad
        fp = 1.0 - eccentricity * math.cos(ecc_anomaly)
        ecc_anomaly -= f / fp
    return ecc_anomaly


def _datetime_to_seconds(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds()


def propagate_body(
    body: BodyConfig,
    now: datetime,
    au_m: float,
) -> StateVector:
    # Root-frame stationary body.
    if body.orbital_elements is None:
        return StateVector(position_m=np.zeros(3), velocity_mps=np.zeros(3))

    oe = body.orbital_elements
    epoch = datetime.fromisoformat(oe.epoch.replace("Z", "+00:00"))

    delta_t = _datetime_to_seconds(epoch, now)

    n = (2.0 * math.pi) / (oe.orbital_period_days * SECONDS_PER_DAY)
    mean_anomaly = math.radians(oe.mean_anomaly_deg) + n * delta_t
    mean_anomaly = (mean_anomaly + 2.0 * math.pi) % (2.0 * math.pi)

    e = oe.eccentricity
    ecc_anomaly = _solve_eccentric_anomaly(mean_anomaly, e)

    a = oe.semi_major_axis_au * au_m
    x_orb = a * (math.cos(ecc_anomaly) - e)
    y_orb = a * math.sqrt(1.0 - e * e) * math.sin(ecc_anomaly)

    denom = max(1e-12, 1.0 - e * math.cos(ecc_anomaly))
    vx_orb = -a * n * math.sin(ecc_anomaly) / denom
    vy_orb = a * n * math.sqrt(1.0 - e * e) * math.cos(ecc_anomaly) / denom

    rot = _rotation_matrix(
        math.radians(oe.inclination_deg),
        math.radians(oe.longitude_ascending_node_deg),
        math.radians(oe.argument_periapsis_deg),
    )

    pos = rot @ np.array([x_orb, y_orb, 0.0], dtype=np.float64)
    vel = rot @ np.array([vx_orb, vy_orb, 0.0], dtype=np.float64)

    return StateVector(position_m=pos, velocity_mps=vel)
