"""Tests for the forms the conversion registry's Fields generate.

    pytest programs/pmagpy_panel/test_forms.py -q
"""
import pytest

pn = pytest.importorskip("panel")

from pmagpy.convert_registry import FORMATS, Field, build_kwargs  # noqa: E402
from pmagpy_panel.forms import Form  # noqa: E402


class TestWidgets:
    def test_each_kind_gets_its_widget_and_reads_back(self):
        fields = (
            Field("location", "text", "Location", default="unknown"),
            Field("specnum", "int", "Specimen characters", default=1),
            Field("volume", "float", "Volume", default=12),
            Field("lat", "float", "Latitude"),                                   # no default: left blank
            Field("noave", "bool", "Keep replicates", default=False),
            Field("experiment", "choice", "Experiment", choices=(("Demag", "demagnetization"), ("PI", "paleointensity")),
                  default="PI", required=True),
            Field("codelist", "codes", "Protocols", choices=(("AF", "AF"), ("T", "thermal")), required=True),
            Field("samp_con", "naming", "Naming", default="1"),
        )
        form = Form(fields)
        w = form.widgets
        assert isinstance(w["location"], pn.widgets.TextInput) and w["location"].value == "unknown"
        assert isinstance(w["specnum"], pn.widgets.IntInput) and w["specnum"].value == 1
        assert isinstance(w["volume"], pn.widgets.FloatInput) and w["volume"].value == 12
        assert isinstance(w["lat"], pn.widgets.TextInput) and w["lat"].value == ""
        assert isinstance(w["noave"], pn.widgets.Checkbox)
        assert isinstance(w["experiment"], pn.widgets.Select) and w["experiment"].value == "PI"
        assert list(w["experiment"].options) == ["demagnetization", "paleointensity"]     # labels shown, values kept
        assert isinstance(w["codelist"], pn.widgets.MultiChoice) and w["codelist"].value == []
        assert w["experiment"].name == "Experiment *"                                        # required is marked
        values = form.values()
        assert values["lat"] == "" and values["samp_con"] == "1" and values["experiment"] == "PI"
        assert form.missing() == ["Protocols"]
        w["codelist"].value = ["AF", "T"]
        assert form.missing() == [] and form.values()["codelist"] == ["AF", "T"]

    def test_a_required_choice_without_a_default_starts_blank(self):
        form = Form(FORMATS["generic"].fields)
        experiment = form.widgets["experiment"]
        assert experiment.value == "" and list(experiment.options)[0] == "—"
        assert "Experiment" in form.missing()
        experiment.value = "Demag"
        assert "Experiment" not in form.missing()

    def test_naming_convention_asks_for_z_only_when_it_matters(self):
        form = Form((Field("samp_con", "naming", "Naming", default="4-2"),))
        select, z = form.widgets["samp_con"], form.extras["samp_con"]
        assert select.value == "4" and z.value == 2 and z.visible is True
        assert form.values()["samp_con"] == "4-2"
        select.value = "3"
        assert z.visible is False and form.values()["samp_con"] == "3"
        select.value = "7"
        z.value = 3
        assert z.visible is True and form.values()["samp_con"] == "7-3"

    def test_switching_fields_keeps_values_that_carry_over(self):
        form = Form(FORMATS["sio"].fields)
        form.widgets["location"].value = "Hawaii"
        form.widgets["specnum"].value = 2
        form.set_fields(FORMATS["cit"].fields)
        assert form.widgets["location"].value == "Hawaii" and form.widgets["specnum"].value == 2
        assert "sitename" in form.widgets and "codelist" not in form.widgets
        assert len(form.panel()) == len(FORMATS["cit"].fields)

    def test_every_registered_format_builds_a_form_the_registry_accepts(self, tmp_path):
        for key, fmt in FORMATS.items():
            form = Form(fmt.fields)
            values = form.values()
            kwargs = build_kwargs(fmt, values, str(tmp_path / "in.dat"), str(tmp_path))
            assert fmt.output_dir_kw in kwargs, key
