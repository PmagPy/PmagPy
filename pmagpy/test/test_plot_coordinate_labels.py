"""
Tests that plots report the coordinate system their directions are actually in.

MagIC thumbnails made by make_magic_plots.py used to give two different
equal area plots of the same specimen the same title, "Equal Area Plot": one
made by zeq_magic from directions rotated into geographic coordinates, and one
made by eqarea_magic from raw measurement directions, which the MagIC data
model defines as being in specimen coordinates. The latter was additionally
tagged 'CO:_g' in its file name. Nothing on either plot said which frame it
was in.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag, pmag, pmagplotlib


# ---------------------------------------------------------------------------
# naming helpers
# ---------------------------------------------------------------------------

class TestCoordinateSystemNames:
    """Tests for ipmag.coordinate_system_name and ipmag.add_coordinate_system."""

    @pytest.mark.parametrize("crd, expected", [
        ("s", "specimen coordinates"),
        ("g", "geographic coordinates"),
        ("t", "tilt-corrected coordinates"),
    ])
    def test_known_codes_are_spelled_out(self, crd, expected):
        assert ipmag.coordinate_system_name(crd) == expected

    @pytest.mark.parametrize("crd", ["", None, "x", "0"])
    def test_unknown_codes_give_empty_string(self, crd):
        assert ipmag.coordinate_system_name(crd) == ""

    def test_title_gets_the_coordinate_system(self):
        assert ipmag.add_coordinate_system("Equal Area Plot", "g") == \
            "Equal Area Plot (geographic coordinates)"

    def test_title_unchanged_when_frame_is_unknown(self):
        """An unrecognized code must not produce an empty parenthetical."""
        assert ipmag.add_coordinate_system("Equal Area Plot", "") == \
            "Equal Area Plot"

    def test_tilt_correction_codes_match_magic_values(self):
        """dir_tilt_correction values map onto the crd codes."""
        assert ipmag.TILT_CORRECTION_CODES == {"-1": "s", "0": "g", "100": "t"}


# ---------------------------------------------------------------------------
# transform_to_geographic
# ---------------------------------------------------------------------------

def _meas_df(decs, incs):
    return pd.DataFrame({"dir_dec": decs, "dir_inc": incs})


def _samp_df(sample, azimuth=None, dip=None, bed_dip_direction=None, bed_dip=None):
    row = {"sample": sample}
    if azimuth is not None:
        row["azimuth"] = azimuth
        row["dip"] = dip
    if bed_dip_direction is not None:
        row["bed_dip_direction"] = bed_dip_direction
        row["bed_dip"] = bed_dip
    df = pd.DataFrame([row])
    df.index = df["sample"]
    return df


class TestTransformToGeographic:
    """transform_to_geographic reports the frame it was able to produce."""

    def test_oriented_sample_reaches_geographic(self):
        meas = _meas_df([0., 90.], [0., 0.])
        samp = _samp_df("s1", azimuth=90., dip=0.)
        out, used = ipmag.transform_to_geographic(meas, samp, "s1", "0",
                                                  return_coord=True)
        assert used == "0"
        # a horizontal core rotated 90 degrees puts specimen x at due east
        assert out["dir_dec"].tolist() == pytest.approx([90., 180.], abs=1e-6)

    def test_unoriented_sample_stays_in_specimen_coordinates(self):
        """No azimuth means no rotation, and the return value must say so."""
        meas = _meas_df([12.3, 45.6], [34.5, -20.1])
        samp = _samp_df("s1")
        out, used = ipmag.transform_to_geographic(meas, samp, "s1", "0",
                                                  return_coord=True)
        assert used == "-1"
        assert out["dir_dec"].tolist() == [12.3, 45.6]
        assert out["dir_inc"].tolist() == [34.5, -20.1]

    def test_tilt_correction_reached_when_bedding_is_present(self):
        meas = _meas_df([0., 90.], [10., 20.])
        samp = _samp_df("s1", azimuth=30., dip=-50.,
                        bed_dip_direction=90., bed_dip=20.)
        _, used = ipmag.transform_to_geographic(meas, samp, "s1", "100",
                                                return_coord=True)
        assert used == "100"

    def test_tilt_correction_falls_back_to_geographic_without_bedding(self):
        """Requesting tilt correction with no bedding leaves data geographic."""
        meas = _meas_df([0., 90.], [10., 20.])
        samp = _samp_df("s1", azimuth=30., dip=-50.)
        _, used = ipmag.transform_to_geographic(meas, samp, "s1", "100",
                                                return_coord=True)
        assert used == "0"

    def test_default_return_signature_is_unchanged(self):
        """Existing callers get back just the DataFrame."""
        meas = _meas_df([0., 90.], [0., 0.])
        samp = _samp_df("s1", azimuth=90., dip=0.)
        out = ipmag.transform_to_geographic(meas, samp, "s1", "0")
        assert isinstance(out, pd.DataFrame)


# ---------------------------------------------------------------------------
# add_borders title layout
# ---------------------------------------------------------------------------

class TestAddBordersTitle:
    """The server border/title block has to fit the title in the figure."""

    def _centered_texts(self, fig):
        # the title (and subtitle, if any) are the centered texts added by
        # add_borders, top to bottom
        centered = [t for t in fig.axes[-1].texts
                    if t.get_horizontalalignment() == "center"]
        return sorted(centered, key=lambda t: -t.get_position()[1])

    def test_coordinate_system_becomes_a_subtitle(self):
        """A trailing parenthetical is rendered as a smaller subtitle line."""
        fig = plt.figure(figsize=(5, 5))
        fig.add_subplot(111)
        title = ipmag.add_coordinate_system("Equal Area Plot", "s")
        pmagplotlib.add_borders({"eqarea": fig.number}, {"eqarea": title})
        texts = self._centered_texts(fig)
        assert [t.get_text() for t in texts] == \
            ["Equal Area Plot", "specimen coordinates"]
        assert texts[0].get_size() > texts[1].get_size()
        plt.close(fig)

    def test_short_title_keeps_full_size_on_one_line(self):
        fig = plt.figure(figsize=(5, 5))
        fig.add_subplot(111)
        pmagplotlib.add_borders({"eqarea": fig.number}, {"eqarea": "Day Plot"})
        texts = self._centered_texts(fig)
        assert len(texts) == 1
        assert texts[0].get_text() == "Day Plot"
        assert texts[0].get_size() == 15
        plt.close(fig)

    def test_long_title_is_shrunk_to_fit(self):
        """An unbreakable long title shrinks rather than running off the page."""
        fig = plt.figure(figsize=(5, 5))
        fig.add_subplot(111)
        long_title = "A" * 80
        pmagplotlib.add_borders({"eqarea": fig.number}, {"eqarea": long_title})
        assert self._centered_texts(fig)[0].get_size() < 15
        plt.close(fig)

    def test_timestamp_uses_a_24_hour_clock(self):
        """The stamp is labeled UT, so it must not be a 12 hour time."""
        fig = plt.figure(figsize=(5, 5))
        fig.add_subplot(111)
        pmagplotlib.add_borders({"eqarea": fig.number}, {"eqarea": "Day Plot"})
        stamped = [t.get_text() for t in fig.axes[-1].texts
                   if t.get_text().endswith("UT")]
        assert len(stamped) == 1
        # "YYYY-MM-DD HH:MM UT"
        hour = int(stamped[0].split(" ")[1].split(":")[0])
        assert 0 <= hour <= 23
        plt.close(fig)


# ---------------------------------------------------------------------------
# eqarea_magic on the measurements table
# ---------------------------------------------------------------------------

class TestEqareaMagicMeasurements:
    """Measurement directions are plotted, and labeled, in specimen coordinates."""

    @pytest.fixture
    def con(self):
        from pmagpy import contribution_builder as cb
        return cb.Contribution("data_files/eqarea_magic")

    def test_requested_geographic_is_reported_as_specimen(self, con, tmp_path, capsys):
        """crd='g' (the default) must not be echoed into the file name."""
        res, outfiles, recs = ipmag.eqarea_magic(
            save_plots=True, fmt="png", plot_by="sample", crd="g",
            ignore_tilt=True, source_table="measurements", n_plots=2,
            contribution=con, dir_path=str(tmp_path), image_records=True)
        assert res
        assert len(outfiles) == 2
        for f in outfiles:
            assert f.endswith("_s_eqarea.png"), f
        for r in recs:
            assert r["title"].endswith("Equal Area Plot (specimen coordinates)")
        assert "specimen coordinates" in capsys.readouterr().out
        plt.close("all")

    def test_tilt_filter_is_bypassed_for_measurements(self, con, tmp_path):
        """Measurements have no dir_tilt_correction, so ignore_tilt=False used to plot nothing."""
        res, outfiles = ipmag.eqarea_magic(
            save_plots=True, fmt="png", plot_by="sample", crd="s",
            ignore_tilt=False, source_table="measurements", n_plots=2,
            contribution=con, dir_path=str(tmp_path))
        assert res
        assert len(outfiles) == 2
        plt.close("all")


# ---------------------------------------------------------------------------
# frame derivation from dir_tilt_correction, and the anisotropy titles
# ---------------------------------------------------------------------------

class TestTiltCorrectionCrd:
    """tilt_correction_crd reports a frame only when the records agree."""

    @pytest.mark.parametrize("values, expected", [
        ([0, 0, 0], "g"),
        (["100", 100.0], "t"),
        ([-1, np.nan, None], "s"),
        ([0, 100], ""),          # mixed provenance
        ([], ""),                # nothing to go on
        (["bad", 0], ""),        # unparseable value counts as unknown
    ])
    def test_frame(self, values, expected):
        assert ipmag.tilt_correction_crd(values) == expected


class TestAnisoServerTitles:
    """Only the direction-dependent anisotropy plots carry a frame."""

    def test_eigenvalue_cdf_is_frame_independent(self):
        figs = {"data": 1, "tcdf": 2, "conf": 3, "extra": 4}
        titles = ipmag.aniso_server_titles(figs, "t")
        assert titles["data"] == "Eigenvectors (tilt-corrected coordinates)"
        assert titles["conf"] == "Confidence Ellipses (tilt-corrected coordinates)"
        assert titles["tcdf"] == "Eigenvalue Confidence"
        assert titles["extra"] == "extra"
