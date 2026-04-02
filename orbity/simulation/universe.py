from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np

from orbity.config.loader import load_system_config
from orbity.config.models import BodyConfig, SystemConfig
from orbity.simulation.acceleration import (
    NUMBA_AVAILABLE,
    bulk_distances_m,
    bulk_relative_speeds_mps,
)
from orbity.simulation.clock import SimulationClock
from orbity.simulation.propagator import StateVector, propagate_body


@dataclass(slots=True)
class Universe:
    """Universe holds loaded bodies and cached per-tick state vectors."""

    config: SystemConfig
    clock: SimulationClock
    _state_cache: dict[str, StateVector] = field(init=False, repr=False)
    _cache_time: datetime | None = field(init=False, default=None, repr=False)
    _body_index: dict[str, int] = field(init=False, repr=False)
    _index_body: list[str] = field(init=False, repr=False)
    _position_matrix: np.ndarray = field(init=False, repr=False)
    _velocity_matrix: np.ndarray = field(init=False, repr=False)
    _use_numba: bool = field(init=False, repr=False)

    def __init__(self, config_path: str | Path, use_numba: bool = False):
        self.config = load_system_config(config_path)
        epoch = str(self.config.metadata.get("epoch", "2000-01-01T12:00:00Z"))
        self.clock = SimulationClock.from_iso8601(epoch)
        self._use_numba = bool(use_numba)

        self._state_cache: dict[str, StateVector] = {}
        self._cache_time: datetime | None = None
        self._body_index: dict[str, int] = {}
        self._index_body: list[str] = []
        self._position_matrix = np.zeros((0, 3), dtype=np.float64)
        self._velocity_matrix = np.zeros((0, 3), dtype=np.float64)
        self._update_cache()

    @property
    def numba_available(self) -> bool:
        return NUMBA_AVAILABLE

    @property
    def numba_enabled(self) -> bool:
        return self._use_numba and NUMBA_AVAILABLE

    def set_time_iso8601(self, iso8601_time: str) -> None:
        self.clock = SimulationClock.from_iso8601(iso8601_time)
        self._update_cache()

    def fast_forward(self, seconds: float) -> None:
        self.clock.fast_forward(seconds)
        self._update_cache()

    def position_m(self, body_id: str) -> np.ndarray:
        return self._state_cache[body_id].position_m

    def velocity_mps(self, body_id: str) -> np.ndarray:
        return self._state_cache[body_id].velocity_mps

    def distance_m(self, body_a: str, body_b: str) -> float:
        delta = self.position_m(body_a) - self.position_m(body_b)
        return float(np.linalg.norm(delta))

    def relative_speed_mps(self, body_a: str, body_b: str) -> float:
        delta_v = self.velocity_mps(body_a) - self.velocity_mps(body_b)
        return float(np.linalg.norm(delta_v))

    def distance_km(self, body_a: str, body_b: str) -> float:
        return self.distance_m(body_a, body_b) / 1000.0

    def distance_au(self, body_a: str, body_b: str) -> float:
        au_m = self.config.constants.get("AU_m", 149_597_870_700.0)
        return self.distance_m(body_a, body_b) / au_m

    def bulk_distances_m(self, pairs: Iterable[tuple[str, str]]) -> np.ndarray:
        idx_a, idx_b = self._pair_indices(pairs)
        return bulk_distances_m(
            self._position_matrix,
            idx_a,
            idx_b,
            use_numba=self._use_numba,
        )

    def bulk_distances_km(self, pairs: Iterable[tuple[str, str]]) -> np.ndarray:
        return self.bulk_distances_m(pairs) / 1000.0

    def bulk_relative_speeds_mps(self, pairs: Iterable[tuple[str, str]]) -> np.ndarray:
        idx_a, idx_b = self._pair_indices(pairs)
        return bulk_relative_speeds_mps(
            self._velocity_matrix,
            idx_a,
            idx_b,
            use_numba=self._use_numba,
        )

    def distance_matrix_m(self, body_ids: list[str] | None = None) -> np.ndarray:
        ids = body_ids if body_ids is not None else self._index_body
        n = len(ids)
        matrix = np.zeros((n, n), dtype=np.float64)
        if n <= 1:
            return matrix

        upper_i: list[int] = []
        upper_j: list[int] = []
        for i in range(n):
            for j in range(i + 1, n):
                upper_i.append(self._body_index[ids[i]])
                upper_j.append(self._body_index[ids[j]])

        idx_a = np.array(upper_i, dtype=np.int64)
        idx_b = np.array(upper_j, dtype=np.int64)
        d = bulk_distances_m(self._position_matrix, idx_a, idx_b, use_numba=self._use_numba)

        k = 0
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i, j] = d[k]
                matrix[j, i] = d[k]
                k += 1
        return matrix

    def body_ids(self) -> list[str]:
        return list(self.config.bodies.keys())

    def _body_absolute_state(self, body: BodyConfig) -> StateVector:
        au_m = self.config.constants.get("AU_m", 149_597_870_700.0)
        local_state = propagate_body(body, self.clock.current_time, au_m)
        if body.parent is None:
            return local_state

        parent_state = self._state_cache[body.parent]
        return StateVector(
            position_m=parent_state.position_m + local_state.position_m,
            velocity_mps=parent_state.velocity_mps + local_state.velocity_mps,
        )

    def _update_cache(self) -> None:
        if self._cache_time == self.clock.current_time:
            return

        self._state_cache = {}

        unresolved = set(self.config.bodies.keys())
        while unresolved:
            progressed = False
            for body_id in list(unresolved):
                body = self.config.bodies[body_id]
                if body.parent is None or body.parent in self._state_cache:
                    self._state_cache[body_id] = self._body_absolute_state(body)
                    unresolved.remove(body_id)
                    progressed = True
            if not progressed:
                raise RuntimeError("Could not resolve parent-child body order")

        self._index_body = sorted(self._state_cache.keys())
        self._body_index = {body_id: idx for idx, body_id in enumerate(self._index_body)}
        self._position_matrix = np.array(
            [self._state_cache[body_id].position_m for body_id in self._index_body],
            dtype=np.float64,
        )
        self._velocity_matrix = np.array(
            [self._state_cache[body_id].velocity_mps for body_id in self._index_body],
            dtype=np.float64,
        )

        self._cache_time = self.clock.current_time

    def _pair_indices(self, pairs: Iterable[tuple[str, str]]) -> tuple[np.ndarray, np.ndarray]:
        idx_a: list[int] = []
        idx_b: list[int] = []
        for body_a, body_b in pairs:
            idx_a.append(self._body_index[body_a])
            idx_b.append(self._body_index[body_b])
        return np.array(idx_a, dtype=np.int64), np.array(idx_b, dtype=np.int64)
