# Orbity

Config-driven orbital simulation for game scenarios where performance and believable motion matter more than mission-grade ephemeris precision.

## What this project implements

- Approximate orbital propagation from orbital elements (no n-body interactions)
- Time abstraction with fast-forward controls
- Distance between any two bodies using center points
- Relative speed queries from propagated velocity vectors
- Bulk distance and bulk relative-speed query APIs
- Parent-child hierarchy support for moons
- Built-in NASA/JPL-derived defaults in YAML
- Config overlays for fictional systems
- Optional Numba acceleration mode for heavy query workloads

## Project layout

- `orbity/config/defaults/solar_system.yaml`: default Lean data pack
- Default pack now includes 20 major asteroids for belt gameplay scenarios
- `config_examples/fictional_overlay.yaml`: fictional augmentation example
- `config_examples/fictional_full.yaml`: full fictional replacement example
- `orbity/config/`: schema + loader + merge behavior
- `orbity/simulation/`: clock, propagator, and universe runtime
- `scripts/demo.py`: minimal runnable example

## Install

```bash
pip install -r requirements.txt
```

## Run demo

```bash
python scripts/demo.py
```

## Use in code

```python
from pathlib import Path
from orbity import Universe

cfg = Path("orbity/config/defaults/solar_system.yaml")
universe = Universe(cfg)

universe.fast_forward(3600)
d_km = universe.distance_km("earth", "mars")
v_rel = universe.relative_speed_mps("earth", "mars")
print(d_km, v_rel)
```

## Bulk queries

```python
pairs = [("earth", "mars"), ("earth", "moon"), ("jupiter", "saturn")]

d_m = universe.bulk_distances_m(pairs)
d_km = universe.bulk_distances_km(pairs)
v_rel = universe.bulk_relative_speeds_mps(pairs)
```

## Optional Numba acceleration

Install optional dependency:

```bash
pip install .[speed]
```

Enable at runtime:

```python
universe = Universe(cfg, use_numba=True)
print(universe.numba_available, universe.numba_enabled)
```

## Data model notes

- All distances are center-to-center.
- `orbital_elements` are interpreted relative to each body's parent.
- `extends` can be used in YAML to augment or replace defaults.
- Default data values are NASA/JPL-derived and intentionally coarse for gameplay.

## Next expansion ideas

- Add larger asteroid packs (100/500 selectable profiles)
- Add vectorized bulk distance query API
- Add optional Numba acceleration
