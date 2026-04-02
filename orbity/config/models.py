from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _parse_iso8601(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(slots=True)
class OrbitalElements:
    epoch: str
    semi_major_axis_au: float
    eccentricity: float
    inclination_deg: float
    longitude_ascending_node_deg: float
    argument_periapsis_deg: float
    mean_anomaly_deg: float
    orbital_period_days: float

    def validate(self) -> None:
        if self.semi_major_axis_au <= 0:
            raise ValueError("semi_major_axis_au must be > 0")
        if not (0 <= self.eccentricity < 1):
            raise ValueError("eccentricity must be in [0, 1)")
        if self.orbital_period_days <= 0:
            raise ValueError("orbital_period_days must be > 0")
        _parse_iso8601(self.epoch)


@dataclass(slots=True)
class BodyConfig:
    id: str
    name: str
    type: str
    parent: str | None
    mass_kg: float
    radius_m: float | None = None
    orbital_elements: OrbitalElements | None = None
    source: str | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BodyConfig":
        orbit_raw = data.get("orbital_elements")
        orbital_elements = OrbitalElements(**orbit_raw) if orbit_raw else None
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            type=str(data["type"]),
            parent=data.get("parent"),
            mass_kg=float(data["mass_kg"]),
            radius_m=float(data["radius_m"]) if data.get("radius_m") is not None else None,
            orbital_elements=orbital_elements,
            source=data.get("source"),
            notes=data.get("notes"),
        )

    def validate(self) -> None:
        if self.mass_kg <= 0:
            raise ValueError(f"Body '{self.id}' mass_kg must be > 0")
        if self.radius_m is not None and self.radius_m <= 0:
            raise ValueError(f"Body '{self.id}' radius_m must be > 0")
        if self.orbital_elements is not None:
            self.orbital_elements.validate()


@dataclass(slots=True)
class SystemConfig:
    version: str
    metadata: dict[str, Any]
    constants: dict[str, float]
    root_frame: str
    bodies: dict[str, BodyConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SystemConfig":
        bodies_raw = raw.get("bodies", {})
        bodies = {key: BodyConfig.from_dict(value) for key, value in bodies_raw.items()}

        cfg = cls(
            version=str(raw.get("version", "1.0")),
            metadata=dict(raw.get("metadata", {})),
            constants={k: float(v) for k, v in dict(raw.get("constants", {})).items()},
            root_frame=str(raw.get("root_frame", "sun")),
            bodies=bodies,
        )
        cfg.validate()
        return cfg

    def validate(self) -> None:
        if not self.bodies:
            raise ValueError("Config must include at least one body")
        if self.root_frame not in self.bodies:
            raise ValueError(f"root_frame '{self.root_frame}' must exist in bodies")

        for body in self.bodies.values():
            body.validate()

        for body in self.bodies.values():
            if body.parent and body.parent not in self.bodies:
                raise ValueError(f"Body '{body.id}' parent '{body.parent}' not found")
            if body.id == body.parent:
                raise ValueError(f"Body '{body.id}' cannot parent itself")

        self._validate_no_cycles()

    def _validate_no_cycles(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                raise ValueError(f"Cycle detected at '{node_id}'")
            visiting.add(node_id)
            parent = self.bodies[node_id].parent
            if parent is not None:
                dfs(parent)
            visiting.remove(node_id)
            visited.add(node_id)

        for body_id in self.bodies:
            dfs(body_id)
