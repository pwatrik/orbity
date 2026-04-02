from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import SystemConfig


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping in {path}")
    return data


def load_system_config(config_path: str | Path) -> SystemConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = _read_yaml(path)

    extends = raw.get("extends")
    if extends:
        base_path = (path.parent / str(extends)).resolve()
        base_raw = _read_yaml(base_path)
        raw = _deep_merge(base_raw, raw)
        raw.pop("extends", None)

    return SystemConfig.from_dict(raw)
