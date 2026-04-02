# Orbity

Config-driven orbital simulation for game scenarios where performance and believable motion matter more than mission-grade ephemeris precision.

## What this project implements

- Approximate orbital propagation from orbital elements (no n-body interactions)
- Time abstraction with fast-forward controls
- Distance between any two bodies using center points
- Relative speed queries from propagated velocity vectors
- Parent-child hierarchy support for moons
- Built-in NASA/JPL-derived defaults in YAML
- Config overlays for fictional systems

## Project layout

- `orbity/config/defaults/solar_system.yaml`: default Lean data pack
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

## Data model notes

- All distances are center-to-center.
- `orbital_elements` are interpreted relative to each body's parent.
- `extends` can be used in YAML to augment or replace defaults.
- Default data values are NASA/JPL-derived and intentionally coarse for gameplay.

## Next expansion ideas

- Add larger asteroid packs (100/500 selectable profiles)
- Add vectorized bulk distance query API
- Add optional Numba acceleration
