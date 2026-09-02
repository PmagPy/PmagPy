"""
Anisotropy tensors from a MagIC specimens table: eigenparameters, shape
parameters, coordinate frames and the Hext / bootstrap statistics of a group.

The tensor algebra is ``pmagpy.pmag``'s (``doseigs``, ``dosgeo``, ``dostilt``,
``sbar``, ``dohext``, ``s_boot``, ``sbootpars``); this module puts it over the
tables — the six-element ``aniso_s`` strings of ``specimens.txt``, the
orientations of ``samples.txt`` — and returns plain dictionaries and
DataFrames, so that an application, a notebook and a test see the same
numbers without a figure being drawn. The plotting programs
(``ipmag.aniso_magic``, ``ipmag.plot_aniso``) keep their own path.

Conventions (Tauxe, Essentials of Paleomagnetism, chapter 13): a tensor is
``s = [s11, s22, s33, s12, s23, s13]``, normalised to trace 1 in MagIC;
eigenvalues ``tau1 >= tau2 >= tau3`` sum to 1; eigenvectors V1, V2, V3 are
reported in the lower hemisphere. ``aniso_tilt_correction`` names the frame:
-1 specimen, 0 geographic, 100 tilt-corrected.
"""
from __future__ import annotations

import json
from typing import Optional

import numpy as np
import pandas as pd

from pmagpy import pmag

# MagIC's aniso_tilt_correction value for each frame, and the frame's name
COORDINATES = {'s': -1, 'g': 0, 't': 100}
COORDINATE_NAMES = {'s': 'specimen', 'g': 'geographic', 't': 'tilt-corrected'}
S_ELEMENTS = ['s11', 's22', 's33', 's12', 's23', 's13']
SHAPE_COLUMNS = ['aniso_p', 'aniso_pp', 'aniso_t', 'aniso_l', 'aniso_f', 'aniso_ll', 'aniso_ff', 'aniso_fl',
                 'aniso_vg', 'aniso_perc', 'aniso_total']
EIGEN_COLUMNS = ['tau1', 'tau2', 'tau3', 'v1_dec', 'v1_inc', 'v2_dec', 'v2_inc', 'v3_dec', 'v3_inc']


# ----------------------------------------------------------------------------- one tensor
def parse_s(text) -> np.ndarray:
    """The six tensor elements of an ``aniso_s`` cell.

    Args:
        text: colon-delimited ``s11:s22:s33:s12:s23:s13``; spaces around the
            colons (as some converters wrote them) are allowed. A sequence of
            six numbers is returned as an array.

    Returns:
        A float array of length 6.

    Raises:
        ValueError: when the cell does not hold six numbers.
    """
    if isinstance(text, str):
        parts = [p.strip() for p in text.split(':')]
    else:
        parts = list(text)
    if len(parts) != 6:
        raise ValueError(f"an anisotropy tensor has six elements, got {len(parts)}: {text!r}")
    try:
        return np.array([float(p) for p in parts], dtype=float)
    except (TypeError, ValueError) as ex:
        raise ValueError(f"could not read the tensor {text!r}: {ex}") from None


def format_s(s, precision: int = 8) -> str:
    """The ``aniso_s`` cell for a six-element tensor."""
    return ':'.join(f'{float(v):.{precision}f}' for v in s)


def shape_parameters(tau) -> dict:
    """The anisotropy shape parameters of three eigenvalues, under their MagIC column names.

    Args:
        tau: eigenvalues ``tau1 >= tau2 >= tau3`` (any positive scale; every
            parameter is a ratio).

    Returns:
        ``aniso_p`` (P = tau1/tau3), ``aniso_pp`` (Jelinek's corrected degree
        P'), ``aniso_t`` (Jelinek's shape T, -1 prolate to +1 oblate),
        ``aniso_l`` (L = tau1/tau2), ``aniso_f`` (F = tau2/tau3), ``aniso_ll``
        and ``aniso_ff`` (ln L, ln F), ``aniso_fl`` (F/L), ``aniso_vg`` (Graham's
        V in degrees, sin V = sqrt((tau2-tau3)/(tau1-tau3))), ``aniso_perc``
        (100 (tau1-tau3)/(tau1+tau2+tau3)) and ``aniso_total``
        (100 (tau1-tau3)/mean). T and V are NaN for an isotropic tensor.
    """
    t1, t2, t3 = (float(t) for t in tau)
    if min(t1, t2, t3) <= 0:
        raise ValueError(f"eigenvalues must be positive to take their ratios, got {tau}")
    eta = np.log([t1, t2, t3])
    L, F = t1 / t2, t2 / t3
    params = {'aniso_p': t1 / t3,
              'aniso_pp': float(np.exp(np.sqrt(2 * np.sum((eta - eta.mean()) ** 2)))),
              'aniso_l': L, 'aniso_f': F, 'aniso_ll': float(np.log(L)), 'aniso_ff': float(np.log(F)),
              'aniso_fl': F / L,
              'aniso_perc': 100 * (t1 - t3) / (t1 + t2 + t3),
              'aniso_total': 100 * (t1 - t3) / ((t1 + t2 + t3) / 3)}
    if t1 > t3:
        params['aniso_t'] = float((2 * eta[1] - eta[0] - eta[2]) / (eta[0] - eta[2]))
        params['aniso_vg'] = float(np.degrees(np.arcsin(np.sqrt((t2 - t3) / (t1 - t3)))))
    else:
        params['aniso_t'] = np.nan
        params['aniso_vg'] = np.nan
    return params


def eigen(s):
    """Eigenvalues (descending) and lower-hemisphere eigenvector directions of a tensor.

    The same decomposition as ``pmag.doseigs`` in double precision
    (``numpy.linalg.eigh`` on the symmetric matrix).

    Returns:
        ``(tau, directions)``: a length-3 array and a ``(3, 2)`` array of
        declination, inclination.
    """
    s = parse_s(s) if isinstance(s, str) else np.asarray(s, dtype=float)
    a = np.array([[s[0], s[3], s[5]], [s[3], s[1], s[4]], [s[5], s[4], s[2]]], dtype=float)
    tau, vectors = np.linalg.eigh(a)
    order = np.argsort(tau)[::-1]
    tau, vectors = tau[order], vectors[:, order]
    directions = []
    for i in range(3):
        v = vectors[:, i]
        if v[2] < 0:
            v = -v
        dec, inc, _ = pmag.cart2dir(v)
        directions.append((float(dec), float(inc)))
    return tau, np.array(directions)


def eigenparameters(s) -> dict:
    """Eigenvalues, eigenvector directions and shape parameters of one tensor.

    Args:
        s: six-element tensor (array or ``aniso_s`` string).

    Returns:
        ``tau1..tau3``, ``v1_dec``, ``v1_inc`` … ``v3_inc`` (lower hemisphere)
        and the :func:`shape_parameters`.
    """
    tau, V = eigen(s)
    out = {'tau1': float(tau[0]), 'tau2': float(tau[1]), 'tau3': float(tau[2])}
    for i, (dec, inc) in enumerate(V, start=1):
        out[f'v{i}_dec'], out[f'v{i}_inc'] = dec, inc
    out.update(shape_parameters(tau))
    return out


def _real(params: dict) -> dict:
    """``pmag.dohext`` works in complex64; the imaginary parts of a symmetric tensor's statistics are zero."""
    out = {}
    for key, value in params.items():
        if isinstance(value, (complex, np.complexfloating)):
            value = float(np.real(value))
        elif isinstance(value, np.floating):
            value = float(value)
        out[key] = value
    return out


def rotate_s(s, azimuth: float, dip: float, bed_dip_direction: Optional[float] = None,
             bed_dip: Optional[float] = None, coordinates: str = 'g') -> np.ndarray:
    """A specimen-frame tensor in geographic or tilt-corrected coordinates.

    Args:
        s: six-element tensor in specimen coordinates.
        azimuth, dip: the sample's orientation (``samples.txt`` ``azimuth``,
            ``dip``: azimuth and plunge of the specimen x axis).
        bed_dip_direction, bed_dip: bedding, needed for ``coordinates='t'``.
        coordinates: ``'g'`` geographic or ``'t'`` tilt-corrected.

    Returns:
        The rotated six-element tensor (``pmag.dosgeo``, then ``pmag.dostilt``).
    """
    s = parse_s(s) if isinstance(s, str) else np.asarray(s, dtype=float)
    if coordinates not in ('g', 't'):
        raise ValueError("coordinates must be 'g' (geographic) or 't' (tilt-corrected)")
    if not (np.isfinite(azimuth) and np.isfinite(dip)):
        raise ValueError("the sample's azimuth and dip are needed to rotate a tensor out of specimen coordinates")
    geo = np.asarray(pmag.dosgeo(list(s), float(azimuth), float(dip)), dtype=float)
    if coordinates == 'g':
        return geo
    if bed_dip_direction is None or bed_dip is None or not (np.isfinite(bed_dip_direction) and np.isfinite(bed_dip)):
        raise ValueError("bed_dip_direction and bed_dip are needed for tilt-corrected coordinates")
    return np.asarray(pmag.dostilt(list(geo), float(bed_dip_direction), float(bed_dip)), dtype=float)


# ----------------------------------------------------------------------------- the table
def tensor_table(specimens: pd.DataFrame, samples: Optional[pd.DataFrame] = None,
                 coordinates: str = 's') -> pd.DataFrame:
    """Every specimen's tensor in one coordinate frame, with its eigenparameters.

    A specimens table may hold a specimen's tensor in several frames (one row
    each, told apart by ``aniso_tilt_correction``); a row in the requested
    frame is used as it is. A specimen with only a specimen-frame row is
    rotated with its sample's orientation when `samples` gives one
    (:func:`rotate_s`); otherwise it is left out. Rows without ``aniso_s`` are
    ignored.

    Args:
        specimens: MagIC specimens table (``aniso_s`` and, where present,
            ``aniso_tilt_correction``, ``aniso_type``, ``aniso_s_sigma``,
            ``aniso_s_n_measurements``, ``sample``, ``site``, ``location``).
        samples: MagIC samples table with ``azimuth``, ``dip`` and, for tilt
            correction, ``bed_dip_direction``, ``bed_dip``.
        coordinates: ``'s'``, ``'g'`` or ``'t'``.

    Returns:
        One row per specimen: ``specimen``, ``sample``, ``site``, ``location``,
        ``aniso_type``, ``aniso_s_sigma``, ``aniso_s_n_measurements``,
        ``coordinates``, ``source`` (``'table'`` when the row was in the frame,
        ``'rotated'`` when it was rotated here), ``s`` (the six-element array),
        the :data:`S_ELEMENTS` as columns, and the :func:`eigenparameters`.
    """
    if coordinates not in COORDINATES:
        raise ValueError(f"coordinates must be one of {sorted(COORDINATES)}")
    columns = (['specimen', 'sample', 'site', 'location', 'aniso_type', 'aniso_s_sigma', 'aniso_s_n_measurements',
                'coordinates', 'source', 's'] + S_ELEMENTS + EIGEN_COLUMNS + SHAPE_COLUMNS)
    if specimens is None or 'aniso_s' not in specimens.columns:
        return pd.DataFrame(columns=columns)
    rows = specimens[specimens['aniso_s'].notna() & (specimens['aniso_s'].astype(str).str.strip() != '')].copy()
    if not len(rows):
        return pd.DataFrame(columns=columns)
    for column in ('sample', 'site', 'location', 'aniso_type', 'aniso_s_sigma', 'aniso_s_n_measurements'):
        if column not in rows.columns:
            rows[column] = np.nan
    frame = pd.to_numeric(rows['aniso_tilt_correction'], errors='coerce') if 'aniso_tilt_correction' in rows.columns \
        else pd.Series(np.nan, index=rows.index)
    frame = frame.fillna(COORDINATES['s'])                # a row without a frame is taken as the specimen's
    rows['_frame'] = frame

    orientation = None
    if samples is not None and 'sample' in samples.columns:
        orientation = samples.drop_duplicates('sample').set_index('sample')
        for column in ('azimuth', 'dip', 'bed_dip_direction', 'bed_dip'):
            orientation[column] = pd.to_numeric(orientation[column], errors='coerce') \
                if column in orientation.columns else np.nan

    wanted = COORDINATES[coordinates]
    out = []
    for specimen, group in rows.groupby('specimen', sort=False):
        in_frame = group[group['_frame'] == wanted]
        if len(in_frame):
            row = in_frame.iloc[0]
            s, source = parse_s(row['aniso_s']), 'table'
        else:
            own = group[group['_frame'] == COORDINATES['s']]
            if coordinates == 's' or not len(own) or orientation is None:
                continue
            row = own.iloc[0]
            if row['sample'] not in orientation.index:
                continue
            o = orientation.loc[row['sample']]
            try:
                s = rotate_s(parse_s(row['aniso_s']), o['azimuth'], o['dip'], o['bed_dip_direction'], o['bed_dip'],
                             coordinates=coordinates)
            except ValueError:
                continue
            source = 'rotated'
        record = {'specimen': specimen, 'sample': row['sample'], 'site': row['site'], 'location': row['location'],
                  'aniso_type': row['aniso_type'],
                  'aniso_s_sigma': pd.to_numeric(row['aniso_s_sigma'], errors='coerce'),
                  'aniso_s_n_measurements': pd.to_numeric(row['aniso_s_n_measurements'], errors='coerce'),
                  'coordinates': coordinates, 'source': source, 's': s}
        record.update(dict(zip(S_ELEMENTS, s)))
        record.update(eigenparameters(s))
        out.append(record)
    return pd.DataFrame(out, columns=columns)


def specimen_index(specimens: pd.DataFrame) -> pd.DataFrame:
    """One row per specimen with a tensor: ``specimen``, ``sample``, ``site``, ``location``, ``aniso_type``
    and ``frames`` — the frames its rows are in, as ``'s'``, ``'g'``, ``'t'`` letters joined (``'sg'``)."""
    columns = ['specimen', 'sample', 'site', 'location', 'aniso_type', 'frames']
    if specimens is None or 'aniso_s' not in specimens.columns:
        return pd.DataFrame(columns=columns)
    rows = specimens[specimens['aniso_s'].notna() & (specimens['aniso_s'].astype(str).str.strip() != '')]
    if not len(rows):
        return pd.DataFrame(columns=columns)
    rows = rows.reindex(columns=['specimen', 'sample', 'site', 'location', 'aniso_type', 'aniso_tilt_correction'])
    frame = pd.to_numeric(rows['aniso_tilt_correction'], errors='coerce').fillna(COORDINATES['s'])
    letters = {value: key for key, value in COORDINATES.items()}
    rows = rows.assign(_letter=frame.map(letters).fillna(''))
    out = []
    for specimen, group in rows.groupby('specimen', sort=False):
        first = group.iloc[0]
        out.append({'specimen': specimen, 'sample': first['sample'], 'site': first['site'],
                    'location': first['location'], 'aniso_type': first['aniso_type'],
                    'frames': ''.join(key for key in COORDINATES if key in set(group['_letter']))})
    return pd.DataFrame(out, columns=columns)


def frames_present(specimens: pd.DataFrame) -> dict:
    """How many specimens have a tensor row in each frame: ``{'s': n, 'g': n, 't': n}``."""
    counts = {key: 0 for key in COORDINATES}
    if specimens is None or 'aniso_s' not in specimens.columns:
        return counts
    rows = specimens[specimens['aniso_s'].notna()]
    frame = pd.to_numeric(rows['aniso_tilt_correction'], errors='coerce').fillna(-1) \
        if 'aniso_tilt_correction' in rows.columns else pd.Series(-1.0, index=rows.index)
    for key, value in COORDINATES.items():
        counts[key] = int(rows.loc[frame == value, 'specimen'].nunique())
    return counts


# ----------------------------------------------------------------------------- statistics
def degrees_of_freedom(n_measurements: int, aniso_type: str = '') -> int:
    """The degrees of freedom of a specimen's tensor fit: ``n - 6`` for AMS, whose
    Kappabridge positions each measure one scalar susceptibility (``pmag.dok15_s``,
    the legacy ``aniso_magic``), ``3 n - 6`` for a remanence anisotropy, whose
    positions each measure a three-component moment (``ipmag.aarm_magic``,
    ``atrm_magic``)."""
    n = int(n_measurements)
    return n - 6 if str(aniso_type).upper() == 'AMS' else 3 * n - 6


def specimen_hext(s, sigma: float, n_measurements: int, aniso_type: str = '') -> dict:
    """Hext statistics of one specimen's tensor from its own measurement scatter.

    Args:
        s: the six-element tensor.
        sigma: ``aniso_s_sigma``, the standard deviation of the fit.
        n_measurements: ``aniso_s_n_measurements``, the positions measured.
        aniso_type: ``aniso_type``; decides the degrees of freedom
            (:func:`degrees_of_freedom`): ``n - 6`` for AMS, else ``3 n - 6``.

    Returns:
        ``pmag.dohext``'s dictionary: eigenvalues ``t1..t3``, eigenvector
        directions, the F statistics with their critical values and the
        confidence-ellipse semi-angles ``e12``, ``e23``, ``e13`` in degrees.
    """
    s = parse_s(s) if isinstance(s, str) else np.asarray(s, dtype=float)
    nf = degrees_of_freedom(n_measurements, aniso_type)
    if nf <= 0:
        raise ValueError("Hext statistics need more positions than the six a tensor has elements")
    return _real(pmag.dohext(nf, float(sigma), list(s)))


def group_statistics(Ss, hext: bool = True, bootstrap: bool = False, parametric: bool = False,
                     n_bootstraps: int = 1000, random_seed=None) -> dict:
    """The mean tensor of a group of specimens and its confidence estimates.

    Args:
        Ss: sequence of six-element tensors (at least two).
        hext: Hext (1963) statistics of the mean — F tests and the confidence
            ellipses about the mean eigenvectors, from the scatter of the
            tensors (``pmag.sbar`` and ``pmag.dohext``).
        bootstrap: bootstrap the tensors (``pmag.s_boot``) for the eigenvalue
            distributions and the ellipses of ``pmag.sbootpars``.
        parametric: draw each bootstrap tensor from a normal distribution
            about the resampled tensor (Tauxe's parametric bootstrap) rather
            than resampling alone.
        n_bootstraps: number of bootstrap draws.
        random_seed: seed (or Generator) for a reproducible bootstrap.

    Returns:
        ``n``, ``s`` (the mean six-element tensor), ``sigma`` and ``nf`` from
        ``sbar``, the mean's :func:`eigenparameters`, ``hext`` (``dohext``'s
        dictionary, or None) and ``bootstrap`` (None, or ``params`` from
        ``sbootpars``, ``taus`` — an ``(n_bootstraps, 3)`` array of eigenvalues
        — and ``vectors`` — ``(n_bootstraps, 3, 2)`` dec/inc of the bootstrap
        eigenvectors — with ``parametric`` and ``n_bootstraps``).
    """
    Ss = np.asarray([parse_s(s) if isinstance(s, str) else s for s in Ss], dtype=float)
    if Ss.ndim != 2 or Ss.shape[1] != 6:
        raise ValueError("Ss must be a sequence of six-element tensors")
    if len(Ss) < 2:
        raise ValueError("the statistics of a group need at least two tensors")
    nf, sigma, avs = pmag.sbar(Ss)
    mean_s = np.asarray(avs, dtype=float)
    result = {'n': int(len(Ss)), 's': mean_s, 'sigma': float(sigma), 'nf': int(nf)}
    result.update(eigenparameters(mean_s))
    result['hext'] = _real(pmag.dohext(nf, sigma, list(mean_s))) if hext else None
    result['bootstrap'] = None
    if bootstrap:
        _, _, taus, vectors = pmag.s_boot(Ss, 1 if parametric else 0, int(n_bootstraps), random_seed=random_seed)
        taus, vectors = np.real(np.asarray(taus)).astype(float), np.real(np.asarray(vectors)).astype(float)
        result['bootstrap'] = {'params': _real(pmag.sbootpars(taus, vectors)), 'taus': taus, 'vectors': vectors,
                               'parametric': bool(parametric), 'n_bootstraps': int(n_bootstraps)}
    return result


def bootstrap_eigenvalue_bounds(taus, level: float = 0.95) -> dict:
    """The bootstrap confidence bounds of the three eigenvalues: ``{'tau1': (lo, hi), ...}``."""
    taus = np.asarray(taus, dtype=float)
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    return {f'tau{i + 1}': (float(np.quantile(taus[:, i], lo)), float(np.quantile(taus[:, i], hi))) for i in range(3)}


# ----------------------------------------------------------------------------- ellipses
def ellipse(pdec, pinc, beta, bdec, binc, gamma, gdec, ginc, n: int = 201) -> np.ndarray:
    """Points (dec, inc) on the confidence ellipse about a direction.

    Args:
        pdec, pinc: the direction at the centre.
        beta, bdec, binc: the semi-angle (degrees) and direction of one axis.
        gamma, gdec, ginc: the semi-angle and direction of the other axis.
        n: number of points around the ellipse.

    Returns:
        An ``(n, 2)`` array of declination, inclination; the inclination is
        negative where the ellipse crosses into the upper hemisphere.
    """
    rad = np.pi / 180
    if beta > 90 or gamma > 90:                     # as pmagplotlib.plot_ell: fold an over-wide ellipse
        beta, gamma, pdec, pinc = 180 - beta, 180 - gamma, pdec - 180, -pinc
    axes = []
    for dec, inc in ((bdec, binc), (gdec, ginc), (pdec, pinc)):
        x = np.asarray(pmag.dir2cart([dec, inc, 1.0]), dtype=float)
        if x[2] < 0:
            x = -x
        axes.append(x)
    t = np.column_stack(axes)                       # columns: beta axis, gamma axis, centre
    psi = np.linspace(0, 2 * np.pi, n)
    v = np.column_stack([np.sin(beta * rad) * np.cos(psi), np.sin(gamma * rad) * np.sin(psi)])
    v = np.column_stack([v, np.sqrt(np.clip(1 - v[:, 0] ** 2 - v[:, 1] ** 2, 0, None))])
    xyz = v @ t.T
    return np.asarray(pmag.cart2dir(xyz), dtype=float)[:, :2]


def hext_ellipses(hpars: dict) -> dict:
    """The Hext confidence ellipses about V1, V2 and V3 as (dec, inc) point arrays.

    The ellipse about each eigenvector has its axes along the other two, with
    the semi-angles ``e12``, ``e13``, ``e23`` of ``pmag.dohext`` — the same
    pairing ``ipmag.plot_aniso`` draws.
    """
    h = hpars
    return {'v1': ellipse(h['v1_dec'], h['v1_inc'], h['e12'], h['v2_dec'], h['v2_inc'], h['e13'], h['v3_dec'], h['v3_inc']),
            'v2': ellipse(h['v2_dec'], h['v2_inc'], h['e23'], h['v3_dec'], h['v3_inc'], h['e12'], h['v1_dec'], h['v1_inc']),
            'v3': ellipse(h['v3_dec'], h['v3_inc'], h['e13'], h['v1_dec'], h['v1_inc'], h['e23'], h['v2_dec'], h['v2_inc'])}


def bootstrap_ellipses(hpars: dict, bpars: dict) -> dict:
    """The bootstrap (Kent) ellipses about the mean eigenvectors as (dec, inc) point arrays.

    Centred on the mean tensor's eigenvectors (`hpars`, from ``dohext``) with
    the zeta/eta semi-angles and directions of ``pmag.sbootpars`` (`bpars`), as
    ``ipmag.plot_aniso`` draws them.
    """
    out = {}
    for v in ('v1', 'v2', 'v3'):
        out[v] = ellipse(hpars[f'{v}_dec'], hpars[f'{v}_inc'], bpars[f'{v}_zeta'], bpars[f'{v}_zeta_dec'],
                         bpars[f'{v}_zeta_inc'], bpars[f'{v}_eta'], bpars[f'{v}_eta_dec'], bpars[f'{v}_eta_inc'])
    return out


# ----------------------------------------------------------------------------- MagIC rows
def eigenparameter_cell(tau: float, dec: float, inc: float) -> str:
    """An ``aniso_v1``/``v2``/``v3`` cell: ``tau:dec:inc``."""
    return f'{tau:.6f}:{dec:.1f}:{inc:.1f}'


# the lab protocol behind each anisotropy type, for the method codes of a mean's row
TYPE_METHOD_CODES = {'AMS': 'LP-AN-MS', 'AARM': 'LP-AN-ARM', 'ATRM': 'LP-AN-TRM', 'AIRM': 'LP-AN-IRM'}
MEAN_COLUMNS = ['aniso_type', 'aniso_tilt_correction', 'aniso_v1', 'aniso_v2', 'aniso_v3', *SHAPE_COLUMNS,
                'aniso_ftest', 'aniso_ftest12', 'aniso_ftest23', 'aniso_ftest_quality', 'method_codes',
                'description', 'specimens']              # what a mean writes on its row


def mean_record(stats: dict, aniso_type: str, coordinates: str, specimens=None) -> dict:
    """The MagIC sample/site columns for a group mean (:func:`group_statistics`).

    Returns ``aniso_type``, ``aniso_tilt_correction``, ``aniso_v1..v3``
    (``tau:dec:inc`` of the mean tensor), the shape parameters, and — when
    the Hext statistics were computed — ``aniso_ftest``, ``aniso_ftest12``,
    ``aniso_ftest23`` and ``aniso_ftest_quality`` (``g`` when F exceeds its
    critical value); ``method_codes`` name the protocol (``LP-AN-ARM`` for
    AARM) and the estimation (``AE-H`` Hext, ``AE-BS``/``AE-BS-P`` bootstrap).
    The tables have no column for the mean tensor itself, the number of
    specimens or the bootstrap parameters, so those go into ``description``
    as ``text | {json}`` (the convention of the rock-magnetic writers):
    ``s``, ``n_specimens``, ``nf``, ``sigma``, ``hext`` (F, its critical
    value, the semi-angles) and ``bootstrap`` (draws, parametric, ζ/η about
    each axis, the 95% eigenvalue bounds).

    Args:
        stats: :func:`group_statistics`'s result.
        aniso_type: AMS, AARM, ATRM ...
        coordinates: 's', 'g' or 't' — the frame the tensors were in.
        specimens: names of the specimens in the mean, for the ``specimens`` column.
    """
    record = {'aniso_type': aniso_type, 'aniso_tilt_correction': COORDINATES[coordinates]}
    for i in (1, 2, 3):
        record[f'aniso_v{i}'] = eigenparameter_cell(stats[f'tau{i}'], stats[f'v{i}_dec'], stats[f'v{i}_inc'])
    record.update({key: round(float(stats[key]), 6) for key in SHAPE_COLUMNS})
    codes = [TYPE_METHOD_CODES[aniso_type]] if aniso_type in TYPE_METHOD_CODES else ['LP-AN']
    detail = {'s': [round(float(x), 8) for x in stats['s']], 'n_specimens': int(stats['n'])}
    for key in ('nf', 'sigma'):
        if key in stats:
            detail[key] = round(float(stats[key]), 8) if key == 'sigma' else int(stats[key])
    h = stats.get('hext')
    if h is not None:
        record.update({'aniso_ftest': round(float(h['F']), 4), 'aniso_ftest12': round(float(h['F12']), 4),
                       'aniso_ftest23': round(float(h['F23']), 4),
                       'aniso_ftest_quality': 'g' if float(h['F']) > float(h['F_crit']) else 'b'})
        codes.append('AE-H')
        detail['hext'] = {'F': round(float(h['F']), 4), 'F_crit': float(h['F_crit']),
                          'F12': round(float(h['F12']), 4), 'F23': round(float(h['F23']), 4),
                          'F12_crit': float(h['F12_crit']),
                          'e12': round(float(h['e12']), 2), 'e13': round(float(h['e13']), 2),
                          'e23': round(float(h['e23']), 2)}
    b = stats.get('bootstrap')
    if b is not None:
        codes.append('AE-BS-P' if b['parametric'] else 'AE-BS')
        p = b['params']
        bounds = bootstrap_eigenvalue_bounds(b['taus'])
        detail['bootstrap'] = {'n_bootstraps': int(b['n_bootstraps']), 'parametric': bool(b['parametric']),
                               **{f'{v}_{k}': round(float(p[f'{v}_{k}']), 2) for v in ('v1', 'v2', 'v3')
                                  for k in ('zeta', 'eta')},
                               **{f'tau{i}_95': [round(x, 6) for x in bounds[f'tau{i}']] for i in (1, 2, 3)}}
    record['method_codes'] = ':'.join(codes)
    record['description'] = f"mean {aniso_type} tensor of {stats['n']} specimens | {json.dumps(detail)}"
    if specimens is not None:
        record['specimens'] = ':'.join(str(name) for name in specimens)
    return record


def add_mean_to_table(table: Optional[pd.DataFrame], level: str, name: str, record: dict,
                      parent: Optional[dict] = None) -> pd.DataFrame:
    """Put a group mean (:func:`mean_record`) on its row of ``sites`` or ``samples``.

    MagIC tables hold several rows per site or sample (a direction, an
    intensity ...), so the mean gets a row of its own: an existing row of the
    group with the same ``aniso_type`` and ``aniso_tilt_correction`` is
    replaced, otherwise a row is added carrying the group's name, the parent
    column of its first row (``location`` for a site, ``site`` for a sample)
    and ``citations = 'This study'``. Nothing else on the table is touched.

    Args:
        table: the ``sites`` or ``samples`` DataFrame; None or empty starts one.
        level: 'site' or 'sample' — the table's key column.
        name: the group's name.
        record: :func:`mean_record`'s columns.
        parent: extra identifying columns for a new row when the table has no
            row for the group (``{'location': 'McMurdo'}``).

    Returns:
        The table with the mean on it (a new DataFrame).

    Raises:
        ValueError: when `level` is not a column of a non-empty table.
    """
    if level not in ('site', 'sample'):
        raise ValueError(f"a mean belongs to a site or a sample, not {level!r}")
    table = pd.DataFrame(columns=[level]) if table is None or not len(table) else table.copy()
    if level not in table.columns:
        raise ValueError(f"the table has no {level!r} column")
    for column in record:
        if column not in table.columns:
            table[column] = np.nan
    table = table.astype(object)
    group = table[table[level].astype(str) == str(name)]
    frame = pd.to_numeric(group['aniso_tilt_correction'], errors='coerce') if len(group) else pd.Series(dtype=float)
    same = group[(group['aniso_type'].astype(str) == str(record['aniso_type']))
                 & (frame == float(record['aniso_tilt_correction']))] if len(group) else group
    if len(same):
        index = same.index[0]
        for column in MEAN_COLUMNS:                # the whole result, so a re-save without Hext clears the F tests
            if column in table.columns:
                table.at[index, column] = record.get(column, np.nan)
        for column, value in record.items():
            table.at[index, column] = value
        return table.reset_index(drop=True)
    row = {level: name, 'citations': 'This study'}
    parent_column = {'site': 'location', 'sample': 'site'}[level]
    if len(group) and parent_column in group.columns and pd.notna(group.iloc[0][parent_column]):
        row[parent_column] = group.iloc[0][parent_column]
    if parent:
        row.update(parent)
    row.update(record)
    for column in row:
        if column not in table.columns:
            table[column] = np.nan
    return pd.concat([table, pd.DataFrame([row], columns=table.columns)], ignore_index=True).astype(object)


# ----------------------------------------------------------------------------- tensors from measurements
# the standard position schemes (Tauxe, Essentials, Appendix D.2) as (phi, theta) of the applied field
# in specimen coordinates, in measurement order — used when a file does not say where the field was
POSITION_SCHEMES = {
    6: [(0., 0.), (90., 0.), (0., 90.), (180., 0.), (270., 0.), (0., -90.)],
    9: [(315., 0.), (225., 0.), (180., 0.), (90., -45.), (270., -45.), (270., 0.), (180., 45.), (180., -45.),
        (0., -90.)],
    15: [(315., 0.), (225., 0.), (180., 0.), (135., 0.), (45., 0.), (90., -45.), (270., -45.), (270., 0.),
         (270., 45.), (90., 45.), (180., 45.), (180., -45.), (0., -90.), (0., -45.), (0., 45.)],
}
TENSOR_COLUMNS = ['aniso_type', 'aniso_tilt_correction', 'aniso_s', 'aniso_s_mean', 'aniso_s_unit',
                  'aniso_s_n_measurements', 'aniso_s_sigma', 'aniso_v1', 'aniso_v2', 'aniso_v3', *SHAPE_COLUMNS,
                  'aniso_ftest', 'aniso_ftest12', 'aniso_ftest23', 'aniso_ftest_quality', 'aniso_alt',
                  'method_codes', 'description', 'experiments']     # what a specimen's tensor writes on its row
# the remanence acquired in each field step of a protocol, and the zero-field step that is its baseline
PROTOCOLS = {'AARM': {'code': 'LP-AN-ARM', 'in_field': 'LT-AF-I', 'zero_field': 'LT-AF-Z'},
             'ATRM': {'code': 'LP-AN-TRM', 'in_field': 'LT-T-I', 'zero_field': 'LT-T-Z'}}
# a susceptibility anisotropy is one scalar per position: LP-AN-MS rows (in the method codes, or in the
# experiment name as k15_magic writes it) carrying a susceptibility, measured along meas_orient_phi/theta
AMS_CODE = 'LP-AN-MS'
CHI_COLUMNS = ('susc_chi_volume', 'susc_chi_mass', 'susc_chi_qdr_volume', 'susc_chi_qdr_mass')
REDUCIBLE = ('AMS', *PROTOCOLS)          # the aniso_types reduce_measurements knows how to fit


def design_matrix(directions) -> tuple:
    """The least-squares design of an anisotropy experiment.

    A unit field along direction ``i`` gives the moment
    ``M_i = s · H_i`` with ``s`` the symmetric tensor, so each measured
    vector contributes three rows to a design matrix ``A`` over the six
    elements ``[s11, s22, s33, s12, s23, s13]`` (``pmag.design``,
    ``ipmag.get_matrix``). The tensor is ``B · K`` with ``B = (AᵀA)⁻¹Aᵀ`` and
    ``K`` the measured components in order.

    Args:
        directions: ``(n, 2)`` declination, inclination of the applied field
            in each position, in specimen coordinates.

    Returns:
        ``(A, B, H)``: the ``(3n, 6)`` design matrix, its ``(6, 3n)``
        pseudo-inverse and the ``(n, 3)`` unit field vectors.

    Raises:
        ValueError: with fewer than six positions, or with positions that do
            not determine all six elements (e.g. all in one plane).
    """
    directions = np.asarray(directions, dtype=float)
    n = len(directions)
    if n < 6:
        raise ValueError(f"a tensor has six elements: {n} field positions cannot determine it")
    H = np.array([pmag.dir2cart([dec, inc, 1.0]) for dec, inc in directions], dtype=float)
    A = np.zeros((3 * n, 6))
    for i, (a, b, c) in enumerate(H):
        A[3 * i] = [a, 0, 0, b, 0, c]
        A[3 * i + 1] = [0, b, 0, a, c, 0]
        A[3 * i + 2] = [0, 0, c, 0, b, a]
    if np.linalg.matrix_rank(A) < 6:
        raise ValueError("the field positions do not determine all six tensor elements")
    B = np.linalg.inv(A.T @ A) @ A.T
    return A, B, H


def fit_tensor(moments, directions) -> dict:
    """The best-fit anisotropy tensor of vector moments acquired in unit fields.

    Args:
        moments: ``(n, 3)`` Cartesian moments (baseline already removed).
        directions: ``(n, 2)`` declination, inclination of the field in each
            position, in specimen coordinates.

    Returns:
        ``s`` (the six elements, normalised to trace 1), ``s_mean`` (a third
        of the raw trace: the mean moment, in the units of `moments`),
        ``sigma`` (the standard deviation of the normalised fit; Hext 1963:
        ``sqrt(Σ residual² / nf)``), ``nf`` (``3n − 6``), ``n_positions``,
        the :func:`eigenparameters` and ``hext`` (:func:`specimen_hext`, or
        None when ``nf`` is 0 or the fit is exact).
    """
    moments = np.asarray(moments, dtype=float)
    A, B, H = design_matrix(directions)
    K = moments.reshape(-1)
    if len(K) != A.shape[0]:
        raise ValueError(f"{len(moments)} moments for {A.shape[0] // 3} field positions")
    raw = B @ K
    trace = float(raw[0] + raw[1] + raw[2])
    if trace <= 0:
        raise ValueError("the fitted tensor has a non-positive trace: the moments do not look like an acquisition")
    s = raw / trace
    nf = 3 * len(moments) - 6
    residual = K / trace - A @ s
    sigma = float(np.sqrt(np.sum(residual ** 2) / nf)) if nf > 0 else np.nan
    out = {'s': s, 's_mean': trace / 3, 'sigma': sigma, 'nf': nf, 'n_positions': len(moments)}
    out.update(eigenparameters(s))
    # an exact fit (synthetic moments) has no scatter to test against
    out['hext'] = specimen_hext(s, sigma, len(moments)) if nf > 0 and sigma > 1e-10 else None
    return out


def _has_codes(series: pd.Series, code: str) -> pd.Series:
    return series.fillna('').astype(str).str.split(':').apply(lambda codes: code in [c.strip() for c in codes])


def field_directions(rows: pd.DataFrame) -> np.ndarray:
    """Where the field was in each in-field step: ``treat_dc_field_phi/theta``, or the
    standard scheme for the number of steps when the table does not say.

    Raises:
        ValueError: when the directions are missing and the count matches no
            standard scheme (6, 9, 15).
    """
    n = len(rows)
    if {'treat_dc_field_phi', 'treat_dc_field_theta'} <= set(rows.columns):
        phi = pd.to_numeric(rows['treat_dc_field_phi'], errors='coerce')
        theta = pd.to_numeric(rows['treat_dc_field_theta'], errors='coerce')
        if phi.notna().all() and theta.notna().all() and phi.nunique() + theta.nunique() > 2:
            return np.column_stack([phi.to_numpy(dtype=float), theta.to_numpy(dtype=float)])
    if n not in POSITION_SCHEMES:
        raise ValueError(f"{n} in-field steps without treat_dc_field_phi/theta match no standard scheme (6, 9, 15)")
    return np.array(POSITION_SCHEMES[n], dtype=float)


def susceptibility_design(directions) -> tuple:
    """The least-squares design of a susceptibility-anisotropy experiment.

    Susceptibility measured along a unit direction ``h`` is the scalar
    ``k = hᵀ K h``, so each position contributes one row
    ``[h1², h2², h3², 2h1h2, 2h2h3, 2h1h3]`` over the six elements
    ``[s11, s22, s33, s12, s23, s13]`` — Jelinek's (1977) design;
    ``pmag.design(15)`` is this matrix for the Kappabridge's fifteen
    positions in their standard order (:data:`POSITION_SCHEMES`).

    Args:
        directions: ``(n, 2)`` declination, inclination of each measurement
            direction in specimen coordinates.

    Returns:
        ``(A, B, H)``: the ``(n, 6)`` design matrix, its ``(6, n)``
        pseudo-inverse and the ``(n, 3)`` unit direction vectors.

    Raises:
        ValueError: with fewer than six positions, or with positions that do
            not determine all six elements.
    """
    directions = np.asarray(directions, dtype=float)
    n = len(directions)
    if n < 6:
        raise ValueError(f"a tensor has six elements: {n} measurement positions cannot determine it")
    H = np.array([pmag.dir2cart([dec, inc, 1.0]) for dec, inc in directions], dtype=float)
    A = np.column_stack([H[:, 0] ** 2, H[:, 1] ** 2, H[:, 2] ** 2,
                         2 * H[:, 0] * H[:, 1], 2 * H[:, 1] * H[:, 2], 2 * H[:, 0] * H[:, 2]])
    if np.linalg.matrix_rank(A) < 6:
        raise ValueError("the measurement positions do not determine all six tensor elements")
    B = np.linalg.inv(A.T @ A) @ A.T
    return A, B, H


def fit_susceptibility_tensor(chi, directions) -> dict:
    """The best-fit susceptibility tensor of scalar susceptibilities measured along directions.

    :func:`fit_tensor` for a Kappabridge: the same output, with ``nf`` the
    ``n - 6`` of one scalar per position and ``s_mean`` the bulk
    susceptibility (a third of the trace, in the units of `chi`). Reproduces
    ``pmag.dok15_s`` for the fifteen-position scheme.

    Args:
        chi: ``(n,)`` susceptibilities.
        directions: ``(n, 2)`` declination, inclination of each measurement.
    """
    chi = np.asarray(chi, dtype=float).reshape(-1)
    A, B, H = susceptibility_design(directions)
    if len(chi) != A.shape[0]:
        raise ValueError(f"{len(chi)} susceptibilities for {A.shape[0]} measurement positions")
    raw = B @ chi
    trace = float(raw[0] + raw[1] + raw[2])
    if trace <= 0:
        raise ValueError("the fitted tensor has a non-positive trace: the values do not look like susceptibilities")
    s = raw / trace
    nf = len(chi) - 6
    residual = chi / trace - A @ s
    sigma = float(np.sqrt(np.sum(residual ** 2) / nf)) if nf > 0 else np.nan
    out = {'s': s, 's_mean': trace / 3, 'sigma': sigma, 'nf': nf, 'n_positions': len(chi)}
    out.update(eigenparameters(s))
    out['hext'] = specimen_hext(s, sigma, len(chi), 'AMS') if nf > 0 and sigma > 1e-10 else None
    return out


def susceptibility_values(rows: pd.DataFrame) -> pd.Series:
    """Each row's susceptibility: the first of :data:`CHI_COLUMNS` with a value (NaN when none)."""
    out = pd.Series(np.nan, index=rows.index, dtype=float)
    for column in CHI_COLUMNS:
        if column in rows.columns:
            values = pd.to_numeric(rows[column], errors='coerce')
            out = out.where(out.notna(), values)
    return out


def ams_rows(measurements: pd.DataFrame) -> pd.DataFrame:
    """The susceptibility-anisotropy rows of a measurements table: ``LP-AN-MS`` in the method
    codes or the experiment name, with a susceptibility (a Kappabridge bulk value without
    the code is not one)."""
    blank = pd.Series('', index=measurements.index)
    codes = measurements['method_codes'] if 'method_codes' in measurements.columns else blank
    experiment = measurements['experiment'] if 'experiment' in measurements.columns else blank
    is_ams = _has_codes(codes, AMS_CODE) | experiment.fillna('').astype(str).str.contains(AMS_CODE, regex=False)
    return measurements[is_ams & susceptibility_values(measurements).notna()]


def measurement_directions(rows: pd.DataFrame) -> np.ndarray:
    """Where each susceptibility was measured: ``meas_orient_phi/theta``, or the fifteen-position
    scheme when the table does not say and there are fifteen rows.

    Raises:
        ValueError: when the directions are missing and the count is not fifteen.
    """
    if {'meas_orient_phi', 'meas_orient_theta'} <= set(rows.columns):
        phi = pd.to_numeric(rows['meas_orient_phi'], errors='coerce')
        theta = pd.to_numeric(rows['meas_orient_theta'], errors='coerce')
        if phi.notna().all() and theta.notna().all() and phi.nunique() + theta.nunique() > 2:
            return np.column_stack([phi.to_numpy(dtype=float), theta.to_numpy(dtype=float)])
    if len(rows) != 15:
        raise ValueError(f"{len(rows)} susceptibility positions without meas_orient_phi/theta; "
                         "only the fifteen-position Kappabridge scheme is assumed")
    return np.array(POSITION_SCHEMES[15], dtype=float)


def specimen_susceptibility_tensor(measurements: pd.DataFrame) -> dict:
    """One specimen's AMS tensor from its Kappabridge positions (:func:`ams_rows`).

    The rows are taken in ``treat_step_num`` order, else by a numeric
    ``measurement`` name (``k15_magic`` numbers the positions 1–15), else as
    they stand. Returns :func:`fit_susceptibility_tensor`'s dictionary plus
    ``specimen``, ``experiments``, ``n_baselines`` (0) and ``alteration``
    (NaN), the keys :func:`specimen_tensor` returns.

    Raises:
        ValueError: with no AMS rows, fewer than six, or directions that cannot
            be told.
    """
    rows = ams_rows(measurements)
    if not len(rows):
        raise ValueError(f"no {AMS_CODE} susceptibility measurements")
    for column in ('treat_step_num', 'measurement'):
        if column in rows.columns:
            order = pd.to_numeric(rows[column], errors='coerce')
            if order.notna().all():
                rows = rows.iloc[np.argsort(order.to_numpy(), kind='stable')]
                break
    if len(rows) < 6:
        raise ValueError(f"{len(rows)} susceptibility positions; a tensor needs at least six")
    fit = fit_susceptibility_tensor(susceptibility_values(rows).to_numpy(), measurement_directions(rows))
    fit['specimen'] = str(rows['specimen'].iloc[0]) if 'specimen' in rows.columns else ''
    fit['experiments'] = ':'.join(sorted(rows['experiment'].dropna().astype(str).unique())) \
        if 'experiment' in rows.columns else ''
    fit['n_baselines'] = 0
    fit['alteration'] = np.nan
    return fit


def protocol_counts(measurements: Optional[pd.DataFrame]) -> dict:
    """Specimens with measurements of each reducible anisotropy type, ``{'AMS': n, 'AARM': n, ...}``
    in :data:`REDUCIBLE` order — an AMS specimen needs six positions to count."""
    out = {}
    if measurements is None or not len(measurements) or 'specimen' not in measurements.columns:
        return out
    ams = ams_rows(measurements)
    if len(ams):
        n = int((ams.groupby(ams['specimen'].astype(str)).size() >= 6).sum())
        if n:
            out['AMS'] = n
    if 'method_codes' in measurements.columns:
        for kind, protocol in PROTOCOLS.items():
            n = int(measurements.loc[_has_codes(measurements['method_codes'], protocol['code']), 'specimen'].nunique())
            if n:
                out[kind] = n
    return out


def specimen_tensor(measurements: pd.DataFrame, aniso_type: str, baseline: bool = True) -> dict:
    """One specimen's anisotropy tensor from its remanence-acquisition steps.

    Each in-field step (``LT-AF-I`` for AARM, ``LT-T-I`` for ATRM) gives a
    moment vector; the last zero-field step measured before it (``LT-AF-Z``,
    ``LT-T-Z``) is its baseline and is subtracted when `baseline` is True and
    there is one — each AARM step is AF-demagnetised before it, an ATRM
    sequence has one zero-field heating that serves every step. The field
    direction of each step comes from ``treat_dc_field_phi/theta``
    (:func:`field_directions`). ``ipmag.aarm_magic`` pairs the rows by order
    and ``ipmag.atrm_magic`` never subtracts a baseline; with a table in the
    standard order both give the same tensor as this when `baseline` matches.

    Args:
        measurements: the specimen's rows of the measurements table (any
            experiment; the protocol's rows are picked by method code).
        aniso_type: 'AARM' or 'ATRM'; 'AMS' hands the rows to
            :func:`specimen_susceptibility_tensor` (`baseline` does not apply).
        baseline: subtract the preceding zero-field step from each in-field step.

    Returns:
        :func:`fit_tensor`'s dictionary plus ``specimen``, ``experiments``,
        ``n_baselines`` (how many steps had one) and, for ATRM with an
        alteration check (``LT-PTRM-I``), ``alteration`` — the percent
        difference between the repeated step and its first measurement
        (``aniso_alt``).

    Raises:
        ValueError: when the protocol's rows are missing or cannot be fit.
    """
    if aniso_type == 'AMS':
        return specimen_susceptibility_tensor(measurements)
    if aniso_type not in PROTOCOLS:
        raise ValueError(f"tensors are reduced for {list(REDUCIBLE)}, not {aniso_type!r}")
    protocol = PROTOCOLS[aniso_type]
    codes = measurements['method_codes'] if 'method_codes' in measurements.columns else pd.Series('', index=measurements.index)
    rows = measurements[_has_codes(codes, protocol['code'])]
    if 'treat_step_num' in rows.columns and pd.to_numeric(rows['treat_step_num'], errors='coerce').notna().all():
        rows = rows.iloc[np.argsort(pd.to_numeric(rows['treat_step_num']).to_numpy(), kind='stable')]
    if not len(rows):
        raise ValueError(f"no {protocol['code']} measurements")
    in_field = _has_codes(rows['method_codes'], protocol['in_field']).to_numpy()
    zero_field = _has_codes(rows['method_codes'], protocol['zero_field']).to_numpy()
    if in_field.sum() < 6:
        raise ValueError(f"{int(in_field.sum())} {protocol['in_field']} steps; a tensor needs at least six")
    xyz = np.array([pmag.dir2cart([d, i, m]) for d, i, m in
                    rows[['dir_dec', 'dir_inc', 'magn_moment']].to_numpy(dtype=float)], dtype=float)
    moments, n_baselines = [], 0
    last_zero = None
    for k in range(len(rows)):
        if zero_field[k] and not in_field[k]:
            last_zero = xyz[k]
        elif in_field[k]:
            if baseline and last_zero is not None:   # a baseline serves the in-field steps until the next one
                moments.append(xyz[k] - last_zero)      # (each AARM step has its own; one heating for ATRM)
                n_baselines += 1
            else:
                moments.append(xyz[k])
    steps = rows[in_field]
    fit = fit_tensor(np.array(moments), field_directions(steps))
    fit['specimen'] = str(rows['specimen'].iloc[0]) if 'specimen' in rows.columns else ''
    fit['experiments'] = ':'.join(sorted(rows['experiment'].dropna().astype(str).unique())) \
        if 'experiment' in rows.columns else ''
    fit['n_baselines'] = n_baselines
    fit['alteration'] = np.nan
    if aniso_type == 'ATRM':
        checks = measurements[_has_codes(codes, 'LT-PTRM-I') & _has_codes(codes, protocol['code'])]
        if len(checks) and {'treat_dc_field_phi', 'treat_dc_field_theta'} <= set(steps.columns):
            check = checks.iloc[-1]
            phi, theta = float(check['treat_dc_field_phi']), float(check['treat_dc_field_theta'])
            first = steps[(pd.to_numeric(steps['treat_dc_field_phi'], errors='coerce') == phi)
                          & (pd.to_numeric(steps['treat_dc_field_theta'], errors='coerce') == theta)]
            if len(first):
                m1, m2 = float(first['magn_moment'].iloc[0]), float(check['magn_moment'])
                fit['alteration'] = 100 * abs(m1 - m2) / np.mean([m1, m2])
    return fit


def tensor_record(fit: dict, aniso_type: str, unit: Optional[str] = None) -> dict:
    """The specimens-table columns for one specimen's tensor (:func:`specimen_tensor`).
    `unit` is ``aniso_s_unit``: 'SI' for AMS and 'Am^2' for a remanence unless given."""
    if unit is None:
        unit = 'SI' if aniso_type == 'AMS' else 'Am^2'
    record = {'aniso_type': aniso_type, 'aniso_tilt_correction': -1, 'aniso_s': format_s(fit['s']),
              'aniso_s_mean': float(fit['s_mean']), 'aniso_s_unit': unit,
              'aniso_s_n_measurements': int(fit['n_positions']),
              'aniso_s_sigma': round(float(fit['sigma']), 8) if np.isfinite(fit['sigma']) else np.nan}
    for i in (1, 2, 3):
        record[f'aniso_v{i}'] = eigenparameter_cell(fit[f'tau{i}'], fit[f'v{i}_dec'], fit[f'v{i}_inc'])
    record.update({key: round(float(fit[key]), 6) for key in SHAPE_COLUMNS})
    codes = [TYPE_METHOD_CODES.get(aniso_type, 'LP-AN')]
    h = fit.get('hext')
    if h is not None:
        record.update({'aniso_ftest': round(float(h['F']), 4), 'aniso_ftest12': round(float(h['F12']), 4),
                       'aniso_ftest23': round(float(h['F23']), 4),
                       'aniso_ftest_quality': 'g' if float(h['F']) > float(h['F_crit']) else 'b',
                       'description': f"Critical F: {float(h['F_crit']):.4f}"})
        codes.append('AE-H')
    if np.isfinite(fit.get('alteration', np.nan)):
        record['aniso_alt'] = round(float(fit['alteration']), 2)
    record['method_codes'] = ':'.join(codes)
    if fit.get('experiments'):
        record['experiments'] = fit['experiments']
    return record


def reduce_measurements(measurements: pd.DataFrame, aniso_type: str, baseline: bool = True,
                        specimens=None) -> tuple:
    """Every specimen's tensor from a measurements table.

    Args:
        measurements: the MagIC measurements table.
        aniso_type: 'AMS', 'AARM' or 'ATRM' (:data:`REDUCIBLE`) — which rows to reduce.
        baseline: see :func:`specimen_tensor`; ignored for AMS.
        specimens: names to reduce, or None for every specimen with the protocol's rows.

    Returns:
        ``(tensors, problems)``: a DataFrame with one :func:`tensor_record`
        row per specimen (``specimen`` first, in natural table order, then
        ``sample`` when the measurements name it) and a ``{specimen: reason}``
        dict for the specimens that could not be reduced.
    """
    if aniso_type == 'AMS':
        rows = ams_rows(measurements)
    elif aniso_type in PROTOCOLS:
        rows = measurements[_has_codes(measurements['method_codes'], PROTOCOLS[aniso_type]['code'])] \
            if 'method_codes' in measurements.columns else measurements.iloc[0:0]
    else:
        raise ValueError(f"tensors are reduced for {list(REDUCIBLE)}, not {aniso_type!r}")
    names = list(dict.fromkeys(rows['specimen'].astype(str))) if len(rows) else []
    if specimens is not None:
        wanted = [str(name) for name in specimens]
        names = [name for name in names if name in wanted]
    records, problems = [], {}
    for name in names:
        mine = rows[rows['specimen'].astype(str) == name]
        try:
            fit = specimen_tensor(mine, aniso_type, baseline=baseline)
        except ValueError as ex:
            problems[name] = str(ex)
            continue
        sample = mine['sample'].dropna() if 'sample' in mine.columns else pd.Series(dtype=object)
        records.append({'specimen': name, 'sample': str(sample.iloc[0]) if len(sample) else np.nan,
                        **tensor_record(fit, aniso_type)})
    columns = ['specimen', 'sample', *TENSOR_COLUMNS]
    tensors = pd.DataFrame(records, columns=columns) if records else pd.DataFrame(columns=columns)
    return tensors.dropna(axis=1, how='all') if len(tensors) else tensors, problems


def add_tensors_to_specimens_table(specimens: Optional[pd.DataFrame], tensors: pd.DataFrame,
                                   samples: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Put reduced tensors (:func:`reduce_measurements`) on the specimens table.

    A specimen's row that already carries a tensor of the same ``aniso_type``
    in specimen coordinates is replaced (its tensor columns cleared first);
    a specimen with rows but no such tensor gets a row of its own, copying
    ``sample`` from its first row; a specimen the table does not know gets a
    new row with the ``sample`` the tensors carry (from the measurements) or,
    failing that, looked up in `samples` (by specimen name when the samples
    table lists its specimens). Rows carry ``citations = 'This study'``.
    Nothing else on the table is touched.

    Returns:
        The table with the tensors on it (a new, object-dtype DataFrame).
    """
    table = pd.DataFrame(columns=['specimen']) if specimens is None or not len(specimens) else specimens.copy()
    if 'specimen' not in table.columns:
        raise ValueError("the specimens table has no 'specimen' column")
    for column in ['specimen', 'sample', 'citations', *TENSOR_COLUMNS]:
        if column not in table.columns:
            table[column] = np.nan
    table = table.astype(object)
    new_rows = []
    for _, tensor in tensors.iterrows():
        record = {k: v for k, v in tensor.items()
                  if k not in ('specimen', 'sample') and not (isinstance(v, float) and np.isnan(v))}
        name = str(tensor['specimen'])
        mine = table[table['specimen'].astype(str) == name]
        frame = pd.to_numeric(mine['aniso_tilt_correction'], errors='coerce') if len(mine) else pd.Series(dtype=float)
        same = mine[(mine['aniso_type'].astype(str) == str(record['aniso_type'])) & (frame == -1)] if len(mine) else mine
        if len(same):
            index = same.index[0]
            for column in TENSOR_COLUMNS:
                table.at[index, column] = record.get(column, np.nan)
            table.at[index, 'citations'] = table.at[index, 'citations'] if pd.notna(table.at[index, 'citations']) \
                else 'This study'
            continue
        row = {'specimen': name, 'citations': 'This study'}
        if len(mine) and pd.notna(mine.iloc[0]['sample']):
            row['sample'] = mine.iloc[0]['sample']
        elif 'sample' in tensor.index and pd.notna(tensor['sample']):
            row['sample'] = tensor['sample']
        elif samples is not None and 'specimens' in samples.columns and 'sample' in samples.columns:
            listed = samples[samples['specimens'].fillna('').astype(str).str.split(':')
                             .apply(lambda names: name in [n.strip() for n in names])]
            if len(listed):
                row['sample'] = listed.iloc[0]['sample']
        row.update(record)
        new_rows.append(row)
    if new_rows:
        table = pd.concat([table, pd.DataFrame(new_rows, columns=table.columns)], ignore_index=True)
    return table.astype(object)
