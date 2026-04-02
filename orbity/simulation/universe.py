from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from orbity.config.loader import load_system_config
from orbity.config.models import BodyConfig, SystemConfig
from orbity.simulation.clock import SimulationClock
from orbity.simulation.propagator import StateVector, propagate_body


@dataclass(slots=True)
class Universe:
    """Universe holds loaded bodies and cached per-tick state vectors."""

    config: SystemConfig
    clock: SimulationClock
    _state_cache: dict[str, StateVector] = field(init=False, repr=False)
    _cache_time: datetime | None = field(init=False, default=None, repr=False)

    def __init__(self, config_path: str | Path):
        self.config = load_system_config(config_path)
        epoch = str(self.config.metadata.get("epoch", "2000-01-01T12:00:00Z"))
        self.clock = SimulationClock.from_iso8601(epoch)

        self._state_cache: dict[str, StateVector] = {}
        self._cache_time: datetime | None = None
        self._update_cache()

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

        self._cache_time = self.clock.current_time
