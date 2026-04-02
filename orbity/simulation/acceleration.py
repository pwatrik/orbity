from __future__ import annotations

import math

import numpy as np

try:
    from numba import njit

    NUMBA_AVAILABLE = True
except Exception:  # pragma: no cover
    njit = None
    NUMBA_AVAILABLE = False


def _distances_numpy(
    positions: np.ndarray,
    idx_a: np.ndarray,
    idx_b: np.ndarray,
) -> np.ndarray:
    deltas = positions[idx_a] - positions[idx_b]
    return np.linalg.norm(deltas, axis=1)


def _relative_speeds_numpy(
    velocities: np.ndarray,
    idx_a: np.ndarray,
    idx_b: np.ndarray,
) -> np.ndarray:
    deltas = velocities[idx_a] - velocities[idx_b]
    return np.linalg.norm(deltas, axis=1)


if NUMBA_AVAILABLE:

    @njit(cache=True)
    def _distances_numba(
        positions: np.ndarray,
        idx_a: np.ndarray,
        idx_b: np.ndarray,
    ) -> np.ndarray:
        out = np.empty(idx_a.shape[0], dtype=np.float64)
        for i in range(idx_a.shape[0]):
            a = idx_a[i]
            b = idx_b[i]
            dx = positions[a, 0] - positions[b, 0]
            dy = positions[a, 1] - positions[b, 1]
            dz = positions[a, 2] - positions[b, 2]
            out[i] = math.sqrt(dx * dx + dy * dy + dz * dz)
        return out

    @njit(cache=True)
    def _relative_speeds_numba(
        velocities: np.ndarray,
        idx_a: np.ndarray,
        idx_b: np.ndarray,
    ) -> np.ndarray:
        out = np.empty(idx_a.shape[0], dtype=np.float64)
        for i in range(idx_a.shape[0]):
            a = idx_a[i]
            b = idx_b[i]
            dx = velocities[a, 0] - velocities[b, 0]
            dy = velocities[a, 1] - velocities[b, 1]
            dz = velocities[a, 2] - velocities[b, 2]
            out[i] = math.sqrt(dx * dx + dy * dy + dz * dz)
        return out


def bulk_distances_m(
    positions: np.ndarray,
    idx_a: np.ndarray,
    idx_b: np.ndarray,
    use_numba: bool,
) -> np.ndarray:
    if use_numba and NUMBA_AVAILABLE:
        return _distances_numba(positions, idx_a, idx_b)
    return _distances_numpy(positions, idx_a, idx_b)


def bulk_relative_speeds_mps(
    velocities: np.ndarray,
    idx_a: np.ndarray,
    idx_b: np.ndarray,
    use_numba: bool,
) -> np.ndarray:
    if use_numba and NUMBA_AVAILABLE:
        return _relative_speeds_numba(velocities, idx_a, idx_b)
    return _relative_speeds_numpy(velocities, idx_a, idx_b)
