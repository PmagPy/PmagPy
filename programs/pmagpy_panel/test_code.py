"""The "show code" support: the text a view emits must be Python that runs and says what the view did.

    pytest programs/pmagpy_panel/test_code.py -q
"""
import os

import numpy as np
import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel import code  # noqa: E402


class TestCall:
    def test_arguments_are_written_as_python_literals(self):
        text = code.call("rmag.f", code.Name("df"), "sp 1", 3, 0.1, np.float64(2.5), deg=np.int64(3),
                         rng=(60, 250), flags=[True, None])
        assert text == "rmag.f(df, 'sp 1', 3, 0.1, 2.5, deg=3, rng=(60, 250), flags=[True, None])"
        assert eval(text, {"rmag": type("M", (), {"f": staticmethod(lambda *a, **k: (a, k))}), "df": "D"}) == \
            (("D", "sp 1", 3, 0.1, 2.5), {"deg": 3, "rng": (60, 250), "flags": [True, None]})

    def test_a_long_call_wraps_one_argument_per_line_and_keeps_keyword_order(self):
        text = code.call("rockmag.plot_mpms_dc", *(code.Name(n) for n in ("fc", "zfc", "cool", "warm")),
                         interactive=True, plot_derivative=True, drop_first=True, width=60)
        assert text.splitlines()[0] == "rockmag.plot_mpms_dc("
        assert text.splitlines()[-1] == ")"
        assert [l.strip().rstrip(",") for l in text.splitlines()[1:-1]] == \
            ["fc", "zfc", "cool", "warm", "interactive=True", "plot_derivative=True", "drop_first=True"]

    def test_assign_and_script(self):
        assert code.assign(["a", "b"], "f()") == "a, b = f()"
        assert code.assign("a", "f()") == "a = f()"
        text = code.script(["x = 1", "y = 2"], app="PmagPy Test", what="plot.pdf")
        assert text.startswith("# written by PmagPy Test — the calls that made plot.pdf\n")
        assert text.endswith("y = 2\n")
        assert code.script(["x = 1"]) == "x = 1\n"                    # no header when no app is named


class TestPane:
    def test_the_pane_is_closed_until_asked_and_shows_the_current_text(self):
        pane = code.CodePane()
        pane.set(["import x", "x.f(1)"])
        assert pane.text == "import x\nx.f(1)" and not pane.code.visible
        assert pane.code.object == "```python\nimport x\nx.f(1)\n```"
        pane.toggle.value = True
        assert pane.code.visible
        pane.set("x.f(2)")
        assert "x.f(2)" in pane.code.object

    def test_write_beside_puts_a_py_file_next_to_the_export(self, tmp_path):
        target = code.write_beside(str(tmp_path / "figure.pdf"), "x = 1\n")
        assert target == str(tmp_path / "figure.py") and open(target).read() == "x = 1\n"
