from __future__ import annotations

from pathlib import Path

from orbity import Universe


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    default_cfg = root / "orbity" / "config" / "defaults" / "solar_system.yaml"

    universe = Universe(default_cfg)

    print("Simulation time:", universe.clock.current_time.isoformat())
    print("Earth-Mars distance (km):", f"{universe.distance_km('earth', 'mars'):,.0f}")
    print("Earth-Moon distance (km):", f"{universe.distance_km('earth', 'moon'):,.0f}")
    print("Earth-Mars relative speed (m/s):", f"{universe.relative_speed_mps('earth', 'mars'):,.2f}")

    universe.fast_forward(60 * 60 * 24 * 30)
    print("\nAfter 30 days:")
    print("Simulation time:", universe.clock.current_time.isoformat())
    print("Earth-Mars distance (km):", f"{universe.distance_km('earth', 'mars'):,.0f}")
    print("Earth-Moon distance (km):", f"{universe.distance_km('earth', 'moon'):,.0f}")


if __name__ == "__main__":
    main()
