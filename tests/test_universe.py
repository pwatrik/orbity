from pathlib import Path

import numpy as np

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


def test_bulk_distance_matches_scalar() -> None:
    universe = Universe(_default_path())
    pairs = [("earth", "mars"), ("earth", "moon"), ("jupiter", "saturn")]

    bulk = universe.bulk_distances_m(pairs)
    scalar = np.array([universe.distance_m(a, b) for a, b in pairs])

    assert np.allclose(bulk, scalar)


def test_bulk_relative_speed_matches_scalar() -> None:
    universe = Universe(_default_path())
    pairs = [("earth", "mars"), ("earth", "moon"), ("jupiter", "saturn")]

    bulk = universe.bulk_relative_speeds_mps(pairs)
    scalar = np.array([universe.relative_speed_mps(a, b) for a, b in pairs])

    assert np.allclose(bulk, scalar)


def test_distance_matrix_is_symmetric() -> None:
    universe = Universe(_default_path())
    ids = ["earth", "mars", "moon", "jupiter"]
    matrix = universe.distance_matrix_m(ids)

    assert matrix.shape == (4, 4)
    assert np.allclose(matrix, matrix.T)
    assert np.allclose(np.diag(matrix), 0.0)


def test_default_catalog_has_20_plus_asteroids() -> None:
    universe = Universe(_default_path())
    asteroid_count = sum(
        1 for body in universe.config.bodies.values() if body.type == "asteroid"
    )
    assert asteroid_count >= 20


def test_numba_toggle_does_not_break_queries() -> None:
    universe = Universe(_default_path(), use_numba=True)
    d = universe.bulk_distances_km([("earth", "mars")])
    assert d.shape == (1,)
    assert d[0] > 0
