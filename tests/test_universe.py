from pathlib import Path

from orbity import Universe


def _default_path() -> Path:
    return Path(__file__).resolve().parents[1] / "orbity" / "config" / "defaults" / "solar_system.yaml"


def test_load_default_system() -> None:
    universe = Universe(_default_path())
    assert "earth" in universe.body_ids()
    assert "moon" in universe.body_ids()


def test_distance_changes_over_time() -> None:
    universe = Universe(_default_path())
    d1 = universe.distance_km("earth", "mars")
    universe.fast_forward(86400 * 10)
    d2 = universe.distance_km("earth", "mars")
    assert d1 != d2


def test_moon_parent_transform() -> None:
    universe = Universe(_default_path())
    d = universe.distance_km("earth", "moon")
    assert 250000 <= d <= 500000
