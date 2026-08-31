"""Tests for the orthographic pole-map geometry (pure numpy)."""
import numpy as np
import pytest

import pmagpy.demag_geo as geo


def test_centre_projects_to_origin_and_antipode_is_hidden():
    x, y, vis = geo.orthographic_xy([10, 190, 100], [20, -20, 20], 10, 20)
    assert abs(x[0]) < 1e-12 and abs(y[0]) < 1e-12 and vis[0]
    assert not vis[1]                       # the antipode of the centre
    assert vis[2]


def test_point_ninety_degrees_away_lies_on_the_rim():
    x, y, vis = geo.orthographic_xy([90, 0], [0, 90], 0, 0)
    assert np.allclose(np.hypot(x, y), 1.0)
    assert vis.all()                        # exactly on the horizon counts as visible
    assert abs(x[0] - 1.0) < 1e-12 and abs(y[1] - 1.0) < 1e-12   # east is +x, north is +y


def test_lon_lat_round_trip():
    lon, lat = np.array([10.0, 200.0, 359.0]), np.array([-80.0, 0.0, 45.0])
    lo, la = geo.lon_lat(geo.unit_vectors(lon, lat))
    assert np.allclose(lo, lon) and np.allclose(la, lat)


def test_small_circle_has_constant_radius():
    pts = geo.small_circle(30, 40, 10)
    d = [geo.angular_distance(30, 40, lo, la) for lo, la in pts]
    assert np.allclose(d, 10.0)
    pts = geo.small_circle(0, 89, 5)        # near the pole the helper axis switches
    assert np.allclose([geo.angular_distance(0, 89, lo, la) for lo, la in pts], 5.0)


def test_paleolatitude_sign():
    assert geo.paleolatitude(0, 90, 45, 30) == pytest.approx(30.0)
    assert geo.paleolatitude(0, 90, 45, -30) == pytest.approx(-30.0)
    assert geo.paleolatitude(180, -90, 45, -30) == pytest.approx(30.0)   # a south pole seen as north


def test_project_lines_cuts_at_the_horizon():
    meridian = np.column_stack([np.zeros(181), np.linspace(-90, 90, 181)])
    runs = geo.project_lines([meridian], 90, 0)          # meridian 0 seen from lon 90: it is the left rim
    assert len(runs) == 1
    x, y = runs[0]
    assert np.allclose(np.hypot(x, y), 1.0, atol=1e-6)
    runs = geo.project_lines([meridian], 180, 0)         # from the far side: nothing visible
    assert runs == []
    runs = geo.project_lines([meridian], 45, 0)          # partly visible: ends on the rim
    x, y = runs[0]
    assert (np.hypot(x, y) <= 1 + 1e-9).all()


def test_clip_polygon_cases():
    square = [[-10, -10], [10, -10], [10, 10], [-10, 10]]
    assert geo.clip_polygon(square, 180, 0) is None                        # fully hidden
    x, y = geo.clip_polygon(square, 0, 0)                                  # fully visible: 4 vertices
    assert len(x) == 4
    x, y = geo.clip_polygon(square, 95, 0)                                 # cut by the horizon (lon -10 is 105° away)
    assert len(x) > 4 and (np.hypot(x, y) <= 1 + 1e-9).all()
    assert (np.isclose(np.hypot(x, y), 1.0)).sum() >= 2                  # rim points were inserted


def test_bundled_land_and_coast_project_inside_the_disc():
    for lon0, lat0 in ((0, 90), (110, 18), (-70, -80), (181.6, 85.4)):
        outers, holes = geo.land_patches(lon0, lat0)
        assert outers
        for x, y in outers + holes + geo.coast_lines(lon0, lat0) + geo.graticule(lon0, lat0):
            assert (np.hypot(x, y) <= 1 + 1e-6).all()
    assert any(hole for hole, _ in geo.land())            # the Caspian Sea is a hole in the Eurasia ring


def _truth_and_render(lon0, lat0, n=120):
    """Land masks over the disc: pixel ground truth (inverse projection + lon/lat point-in-ring)
    versus the clipped, projected rings that are drawn."""
    from matplotlib.path import Path
    g = np.linspace(-0.995, 0.995, n)
    X, Y = np.meshgrid(g, g)
    inside = X ** 2 + Y ** 2 < 1
    view, east, north = geo.view_basis(lon0, lat0)
    Z = np.sqrt(np.clip(1 - X ** 2 - Y ** 2, 0, 1))
    V = X[..., None] * east + Y[..., None] * north + Z[..., None] * view
    lon, lat = geo.lon_lat(V.reshape(-1, 3))
    lonlat = np.column_stack([np.where(lon > 180, lon - 360, lon), lat])
    xy = np.column_stack([X.ravel(), Y.ravel()])
    truth = np.zeros(len(xy), bool)
    drawn = np.zeros(len(xy), bool)
    for is_hole, ring in geo.land():
        m = Path(ring).contains_points(lonlat)
        truth = truth & ~m if is_hole else truth | m
    outers, holes = geo.land_patches(lon0, lat0)
    for x, y in outers:
        drawn |= Path(np.column_stack([x, y])).contains_points(xy)
    for x, y in holes:
        drawn &= ~Path(np.column_stack([x, y])).contains_points(xy)
    return truth.reshape(n, n) & inside, drawn.reshape(n, n) & inside, inside


@pytest.mark.parametrize("lon0,lat0", [(195, 0), (180, -30), (210, 30), (225, -60), (0, 90), (110, 18), (-70, -80),
                                       (60, 30), (330, 60)])
def test_land_fill_matches_pixel_ground_truth(lon0, lat0):
    # the rim arc replacing a hidden stretch must be the one inside the polygon;
    # the old sweep heuristic painted up to 90 % of Pacific-centred globes as land
    truth, drawn, inside = _truth_and_render(lon0, lat0)
    mismatch = (truth ^ drawn).sum() / inside.sum()
    assert mismatch < 0.01, f"{mismatch:.3f} of the disc differs at centre {lon0}, {lat0}"


def test_point_in_ring_even_odd():
    square = [[-10, -10], [10, -10], [10, 10], [-10, 10]]
    assert geo.point_in_ring(square, 0, 0) and not geo.point_in_ring(square, 20, 0)
    assert geo.point_in_ring(square, 355, 0)               # longitudes above 180 are wrapped
