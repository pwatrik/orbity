from __future__ import annotations

from pathlib import Path
import time

from orbity import Universe


def main() -> None:
    cfg = Path(__file__).resolve().parents[1] / "orbity" / "config" / "defaults" / "solar_system.yaml"
    universe = Universe(cfg)

    pairs = [
        ("earth", "mars"),
        ("earth", "moon"),
        ("jupiter", "saturn"),
        ("ceres", "earth"),
    ]

    iterations = 20000
    t0 = time.perf_counter()
    for i in range(iterations):
        a, b = pairs[i % len(pairs)]
        universe.distance_km(a, b)
        if i % 500 == 0:
            universe.fast_forward(60.0)
    elapsed = time.perf_counter() - t0

    print(f"Distance calls: {iterations}")
    print(f"Elapsed: {elapsed:.4f}s")
    print(f"Calls/sec: {iterations / elapsed:,.0f}")


if __name__ == "__main__":
    main()
