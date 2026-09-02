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
def specimen_hext(s, sigma: float, n_measurements: int) -> dict:
    """Hext statistics of one specimen's tensor from its own measurement scatter.

    Args:
        s: the six-element tensor.
        sigma: ``aniso_s_sigma``, the standard deviation of the fit.
        n_measurements: ``aniso_s_n_measurements``; the degrees of freedom are
            ``3 n - 6`` (three components measured in each of n positions).

    Returns:
        ``pmag.dohext``'s dictionary: eigenvalues ``t1..t3``, eigenvector
        directions, the F statistics with their critical values and the
        confidence-ellipse semi-angles ``e12``, ``e23``, ``e13`` in degrees.
    """
    s = parse_s(s) if isinstance(s, str) else np.asarray(s, dtype=float)
    nf = 3 * int(n_measurements) - 6
    if nf <= 0:
        raise ValueError("Hext statistics need more than two measurement positions")
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


def mean_record(stats: dict, aniso_type: str, coordinates: str) -> dict:
    """The MagIC sample/site columns for a group mean (:func:`group_statistics`).

    Returns ``aniso_type``, ``aniso_tilt_correction``, ``aniso_v1..v3``
    (``tau:dec:inc`` of the mean tensor), the shape parameters, and — when
    the Hext statistics were computed — ``aniso_ftest``, ``aniso_ftest12``,
    ``aniso_ftest23`` and ``aniso_ftest_quality`` (``g`` when F exceeds its
    critical value). ``aniso_n_specimens`` is not a data-model column and is
    left to the caller's description.
    """
    record = {'aniso_type': aniso_type, 'aniso_tilt_correction': COORDINATES[coordinates]}
    for i in (1, 2, 3):
        record[f'aniso_v{i}'] = eigenparameter_cell(stats[f'tau{i}'], stats[f'v{i}_dec'], stats[f'v{i}_inc'])
    record.update({key: stats[key] for key in SHAPE_COLUMNS})
    h = stats.get('hext')
    if h is not None:
        record.update({'aniso_ftest': h['F'], 'aniso_ftest12': h['F12'], 'aniso_ftest23': h['F23'],
                       'aniso_ftest_quality': 'g' if float(h['F']) > float(h['F_crit']) else 'b'})
    return record
