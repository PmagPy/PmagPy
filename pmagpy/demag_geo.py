"""
Spherical geometry for pole maps: an orthographic (globe) projection with
hemisphere clipping, graticules, small circles and coastline/land assets.

Pure numpy — no cartopy, no shapely — so the same code serves the Bokeh
views, the matplotlib publication figures, scripts, and a Pyodide build.
Coordinates are longitude/latitude in degrees; projected coordinates are in
units of the globe radius (the visible hemisphere is the unit disc).

Natural Earth 1:110m coastlines and land polygons (public domain) are bundled
as compact JSON in ``pmagpy/maps``.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Iterable, Optional

import numpy as np

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
_EPS = 1e-9


# ---------------------------------------------------------------------------
# unit vectors
# ---------------------------------------------------------------------------
def unit_vectors(lon, lat) -> np.ndarray:
    """(n, 3) unit vectors for arrays of longitude/latitude in degrees."""
    lon = np.radians(np.atleast_1d(np.asarray(lon, dtype=float)))
    lat = np.radians(np.atleast_1d(np.asarray(lat, dtype=float)))
    return np.column_stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])


def lon_lat(vectors) -> tuple[np.ndarray, np.ndarray]:
    """Longitude (0–360) and latitude in degrees of (n, 3) vectors."""
    v = np.atleast_2d(np.asarray(vectors, dtype=float))
    norm = np.linalg.norm(v, axis=1)
    norm[norm == 0] = 1.0
    v = v / norm[:, None]
    lon = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360.0
    lat = np.degrees(np.arcsin(np.clip(v[:, 2], -1.0, 1.0)))
    return lon, lat


def angular_distance(lon1, lat1, lon2, lat2) -> float:
    """Great-circle distance in degrees between two points."""
    a = unit_vectors(lon1, lat1)[0]
    b = unit_vectors(lon2, lat2)[0]
    return float(np.degrees(np.arccos(np.clip(a @ b, -1.0, 1.0))))


def paleolatitude(pole_lon, pole_lat, site_lon, site_lat) -> float:
    """Paleolatitude of a site for a pole: 90° minus the site–pole distance (negative = southern)."""
    return 90.0 - angular_distance(pole_lon, pole_lat, site_lon, site_lat)


# ---------------------------------------------------------------------------
# orthographic projection
# ---------------------------------------------------------------------------
def view_basis(lon0: float, lat0: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(view, east, north) unit vectors for a globe centred on lon0/lat0."""
    view = unit_vectors(lon0, lat0)[0]
    lon, lat = np.radians(lon0), np.radians(lat0)
    east = np.array([-np.sin(lon), np.cos(lon), 0.0])
    north = np.array([-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)])
    return view, east, north


def orthographic_xy(lon, lat, lon0: float, lat0: float):
    """Project points onto the plane of a globe centred on lon0/lat0.

    Returns:
        x, y (units of the globe radius) and a boolean ``visible`` mask for the
        near hemisphere. Hidden points still get coordinates (of their mirror
        position) so that callers can mask or draw them faintly.
    """
    view, east, north = view_basis(lon0, lat0)
    v = unit_vectors(lon, lat)
    return v @ east, v @ north, (v @ view) >= -_EPS


def _project_vectors(v, basis):
    view, east, north = basis
    return v @ east, v @ north


def project_lines(lines: Iterable, lon0: float, lat0: float, min_points: int = 2) -> list[tuple[np.ndarray, np.ndarray]]:
    """Project polylines (lists of [lon, lat]) and cut them at the horizon.

    Each returned item is an (x, y) pair for one visible run; the horizon
    crossing point is added so that lines reach the rim of the disc.
    """
    basis = view_basis(lon0, lat0)
    view = basis[0]
    out = []
    for line in lines:
        pts = np.asarray(line, dtype=float)
        if len(pts) < 2:
            continue
        v = unit_vectors(pts[:, 0], pts[:, 1])
        d = v @ view
        runs, cur = [], []
        for i in range(len(v)):
            if d[i] >= 0:
                if not cur and i > 0:
                    cur.append(_horizon_point(v[i - 1], v[i], d[i - 1], d[i]))
                cur.append(v[i])
            elif cur:
                cur.append(_horizon_point(v[i - 1], v[i], d[i - 1], d[i]))
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        for run in runs:
            if len(run) >= min_points:
                x, y = _project_vectors(np.array(run), basis)
                out.append((x, y))
    return out


def _horizon_point(a, b, da, db):
    """Point on the horizon between vectors a (depth da) and b (depth db)."""
    t = da / (da - db) if da != db else 0.5
    p = a + t * (b - a)
    n = np.linalg.norm(p)
    return p / n if n else a


def clip_polygon(ring: Iterable, lon0: float, lat0: float, rim_step_deg: float = 2.0) -> Optional[tuple[np.ndarray, np.ndarray]]:
    """Clip a lon/lat ring to the visible hemisphere and project it.

    Where the ring dives behind the globe, the hidden stretch is replaced by
    the arc of the horizon that lies *inside* the polygon (decided by testing
    the arc's midpoint against the original ring), so continents cut by the
    horizon keep the correct outline instead of a chord or the wrong arc.
    Returns (x, y) or None when nothing is visible.
    """
    basis = view_basis(lon0, lat0)
    view, east, north = basis
    pts = np.asarray(ring, dtype=float)
    if len(pts) < 3:
        return None
    if np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]
    v = unit_vectors(pts[:, 0], pts[:, 1])
    d = v @ view
    vis = d >= 0
    if not vis.any():
        return None
    if vis.all():
        x, y = _project_vectors(v, basis)
        return x, y
    # start on a visible vertex so that every hidden stretch is enclosed
    start = int(np.argmax(vis))
    v, d, vis = np.roll(v, -start, axis=0), np.roll(d, -start), np.roll(vis, -start)
    n = len(v)
    out = []
    i = 0
    while i < n:
        if vis[i]:
            out.append(v[i])
            i += 1
            continue
        j = i
        while j < n and not vis[j]:
            j += 1
        exit_pt = _horizon_point(v[i - 1], v[i], d[i - 1], d[i])
        nxt = j % n
        entry_pt = _horizon_point(v[nxt], v[j - 1], d[nxt], d[j - 1])
        out.append(exit_pt)
        out.extend(_rim_arc(exit_pt, entry_pt, pts, basis, rim_step_deg))
        out.append(entry_pt)
        i = j
    x, y = _project_vectors(np.array(out), basis)
    return x, y


def _rim_arc(exit_pt, entry_pt, ring_lonlat, basis, rim_step_deg):
    """Interior points of the horizon arc from exit to entry that lies inside the ring."""
    view, east, north = basis
    a0, a1 = _rim_angle(exit_pt, basis), _rim_angle(entry_pt, basis)
    ccw = (a1 - a0) % (2 * np.pi)                 # counter-clockwise sweep, in (0, 2π]
    candidates = [ccw, ccw - 2 * np.pi]           # and the clockwise alternative

    def rim_point(angle):
        return np.cos(angle) * east + np.sin(angle) * north

    inside = []
    for sweep in candidates:
        lon, lat = lon_lat(rim_point(a0 + sweep / 2))
        inside.append(point_in_ring(ring_lonlat, float(lon[0]), float(lat[0])))
    if inside[0] != inside[1]:
        sweep = candidates[0] if inside[0] else candidates[1]
    else:                                         # both or neither (degenerate): the shorter arc
        sweep = min(candidates, key=abs)
    steps = max(2, int(abs(np.degrees(sweep)) / rim_step_deg))
    return [rim_point(a0 + t * sweep) for t in np.linspace(0, 1, steps + 1)[1:-1]]


def point_in_ring(ring_lonlat, lon: float, lat: float) -> bool:
    """Even-odd test of a point against a lon/lat ring (longitudes in −180…180, as in Natural Earth)."""
    ring = np.asarray(ring_lonlat, dtype=float)
    if lon > 180.0:
        lon -= 360.0
    x, y = ring[:, 0], ring[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    crosses = (y > lat) != (y2 > lat)
    with np.errstate(divide="ignore", invalid="ignore"):
        x_at = x + (lat - y) * (x2 - x) / (y2 - y)
    return bool(np.count_nonzero(crosses & (lon < x_at)) % 2)


def _rim_angle(vec, basis):
    view, east, north = basis
    return float(np.arctan2(vec @ north, vec @ east))


# ---------------------------------------------------------------------------
# graticule and small circles
# ---------------------------------------------------------------------------
def graticule(lon0: float, lat0: float, step: float = 30.0, resolution: float = 2.0) -> list[tuple[np.ndarray, np.ndarray]]:
    """Projected meridians and parallels every ``step`` degrees."""
    lines = []
    lats = np.arange(-90.0, 90.0 + resolution / 2, resolution)
    for lon in np.arange(0.0, 360.0, step):
        lines.append(np.column_stack([np.full_like(lats, lon), lats]))
    lons = np.arange(0.0, 360.0 + resolution / 2, resolution)
    for lat in np.arange(-90.0 + step, 90.0, step):
        lines.append(np.column_stack([lons, np.full_like(lons, lat)]))
    return project_lines(lines, lon0, lat0)


def small_circle(lon: float, lat: float, radius_deg: float, npts: int = 181) -> np.ndarray:
    """Lon/lat points (npts, 2) of the circle at angular ``radius_deg`` around a point."""
    c = unit_vectors(lon, lat)[0]
    helper = np.array([0.0, 0.0, 1.0]) if abs(c[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(c, helper)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(c, e1)
    r = np.radians(radius_deg)
    t = np.linspace(0, 2 * np.pi, npts)
    pts = np.cos(r) * c + np.sin(r) * (np.cos(t)[:, None] * e1 + np.sin(t)[:, None] * e2)
    lo, la = lon_lat(pts)
    return np.column_stack([lo, la])


def circle_outline(npts: int = 361) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, 2 * np.pi, npts)
    return np.cos(t), np.sin(t)


# ---------------------------------------------------------------------------
# bundled Natural Earth assets
# ---------------------------------------------------------------------------
@lru_cache(maxsize=None)
def coastlines(path: Optional[str] = None) -> tuple:
    """Natural Earth 110m coastline polylines as a tuple of (n, 2) arrays."""
    path = path or os.path.join(ASSET_DIR, "ne_110m_coastline.json")
    with open(path) as fh:
        return tuple(np.asarray(line, dtype=float) for line in json.load(fh)["lines"])


@lru_cache(maxsize=None)
def land(path: Optional[str] = None) -> tuple:
    """Natural Earth 110m land rings as a tuple of (is_hole, (n, 2) array)."""
    path = path or os.path.join(ASSET_DIR, "ne_110m_land.json")
    with open(path) as fh:
        return tuple((bool(r["hole"]), np.asarray(r["points"], dtype=float)) for r in json.load(fh)["rings"])


def land_patches(lon0: float, lat0: float) -> tuple[list, list]:
    """Projected (outer rings, hole rings) of the visible land for a globe centre."""
    outers, holes = [], []
    for is_hole, ring in land():
        clipped = clip_polygon(ring, lon0, lat0)
        if clipped is None:
            continue
        (holes if is_hole else outers).append(clipped)
    return outers, holes


def coast_lines(lon0: float, lat0: float) -> list[tuple[np.ndarray, np.ndarray]]:
    return project_lines(coastlines(), lon0, lat0)
