from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class SimulationClock:
    """Simple simulation clock with fast-forward controls."""

    current_time: datetime

    @classmethod
    def from_iso8601(cls, iso8601_time: str) -> "SimulationClock":
        dt = datetime.fromisoformat(iso8601_time.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return cls(current_time=dt)

    def set_time(self, dt: datetime) -> None:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        self.current_time = dt

    def fast_forward(self, seconds: float) -> datetime:
        self.current_time += timedelta(seconds=seconds)
        return self.current_time
