"""
Tests for the shared directory chooser.

They use a stub session rather than either application's, which is the point:
the toolkit must not know what a demagnetization step or a Thellier step is,
and a test that needs one of the applications to run would prove it did.

Adapted from Yiming Zhang's tests on the intensity branch; the system dialog is
now a coroutine, so the native-chooser tests run it with ``asyncio.run``.

    pytest programs/pmagpy_panel/test_chooser.py -q
"""
import asyncio
import os
import shutil

import param
import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel.chooser import DirectoryChooser, shorten   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(REPO, "data_files", "thellier_magic")


class StubSession(param.Parameterized):
    """The whole interface the chooser needs: four attributes and load()."""
    directory = param.String(default="")
    output_dir = param.String(default="")
    status = param.String(default="")

    def __init__(self, directory="", **params):
        super().__init__(**params)
        self.directory = directory
        self.loads = []
        self.refuse = False

    def load(self, path):
        self.loads.append(path)
        if self.refuse:
            self.status = "refused on purpose"
            return False
        self.directory = path
        self.status = f"loaded {os.path.basename(path)}"
        return True


@pytest.fixture
def magic_dir(tmp_path):
    directory = tmp_path / "study"
    directory.mkdir()
    shutil.copy(os.path.join(DATA, "measurements.txt"), directory)
    return str(directory)


@pytest.fixture
def chooser(tmp_path, magic_dir):
    session = StubSession(magic_dir)
    view = DirectoryChooser(session, recent_file=str(tmp_path / "recent.json"),
                            chooser=lambda start=None: None, chooser_available=True,
                            count=lambda s: "3 things")
    return session, view


def test_the_sidebar_names_the_dataset_and_what_is_in_it(chooser):
    session, view = chooser
    assert "study" in view.summary.object
    assert "3 things" in view.summary.object
    assert view.sidebar() is not None


def test_the_path_field_starts_at_the_open_directory(chooser):
    session, view = chooser
    assert view.path.value == session.directory


def test_loading_a_magic_directory_calls_the_session(chooser, tmp_path):
    session, view = chooser
    other = tmp_path / "other"
    other.mkdir()
    shutil.copy(os.path.join(DATA, "measurements.txt"), other)
    view.path.value = str(other)
    assert view._load() is True
    assert session.loads == [str(other)]
    assert "loaded" in view.message.object


def test_a_directory_without_measurements_is_refused_before_the_session_sees_it(chooser, tmp_path):
    session, view = chooser
    empty = tmp_path / "empty"
    empty.mkdir()
    view.path.value = str(empty)
    assert view._load() is False
    assert session.loads == []
    assert "measurements.txt" in view.message.object


def test_a_session_that_refuses_is_reported(chooser, magic_dir):
    session, view = chooser
    session.refuse = True
    view.path.value = magic_dir
    assert view._load() is False
    assert "refused on purpose" in view.message.object


def test_the_native_chooser_loads_what_it_returns(tmp_path, magic_dir):
    session = StubSession(magic_dir)
    other = tmp_path / "other"
    other.mkdir()
    shutil.copy(os.path.join(DATA, "measurements.txt"), other)
    view = DirectoryChooser(session, recent_file=str(tmp_path / "recent.json"),
                            chooser=lambda start=None: str(other), chooser_available=True)
    asyncio.run(view._browse_native())
    assert session.directory == str(other)
    assert view.path.value == str(other)


def test_a_cancelled_chooser_leaves_the_session_alone(chooser, magic_dir):
    session, view = chooser
    asyncio.run(view._browse_native())
    assert session.directory == magic_dir
    assert "No folder chosen" in view.message.object


def test_the_hub_may_open_any_directory_at_all(tmp_path):
    """Home starts empty directories on their way; require_measurements=False lets them in."""
    session = StubSession(str(tmp_path))
    view = DirectoryChooser(session, recent_file=str(tmp_path / "recent.json"),
                            chooser_available=False, require_measurements=False)
    empty = tmp_path / "new_study"
    empty.mkdir()
    view.path.value = str(empty)
    assert view.load() is True and session.loads == [str(empty)]
    assert "measurements.txt" not in view.path.name
    view.path.value = str(tmp_path / "nowhere")
    assert view.load() is False and "is not a directory" in view.message.object


def test_the_button_is_disabled_where_no_dialog_can_be_shown(tmp_path, magic_dir):
    view = DirectoryChooser(StubSession(magic_dir), recent_file=str(tmp_path / "recent.json"),
                            chooser_available=False)
    assert view.native_btn.disabled


def test_the_in_page_browser_fills_the_path_field(chooser, magic_dir):
    session, view = chooser
    view.browser.value = [magic_dir]
    assert view.path.value == magic_dir


def test_on_loaded_is_called_so_the_application_can_close_the_dialog(chooser, tmp_path):
    session, view = chooser
    seen = []
    view.on_loaded = lambda: seen.append(True)
    other = tmp_path / "other"
    other.mkdir()
    shutil.copy(os.path.join(DATA, "measurements.txt"), other)
    view.path.value = str(other)
    view._load()
    assert seen == [True]


def test_the_modal_takes_whatever_the_application_adds(chooser):
    session, view = chooser
    plain = view.modal()
    extended = view.modal(pn.pane.HTML("<b>an importer</b>"))
    assert len(extended) > len(plain)


def test_the_summary_follows_a_directory_change(chooser, tmp_path):
    session, view = chooser
    other = tmp_path / "renamed"
    other.mkdir()
    shutil.copy(os.path.join(DATA, "measurements.txt"), other)
    session.directory = str(other)
    assert "renamed" in view.summary.object


def test_shorten_keeps_the_end_that_identifies_a_path():
    assert shorten("/short/path") == "/short/path"
    long = "/very/long/path/that/goes/on/and/on/and/on/to/the/study"
    assert shorten(long, 20).endswith("study")
    assert len(shorten(long, 20)) == 20


def test_the_toolkit_knows_nothing_about_either_science():
    """The contract: nothing in pmagpy_panel may know what a step is.

    Prose may name an application as an example; *code* may not, so the
    docstrings and comments are stripped before the scan.
    """
    import ast
    import io
    import tokenize
    source = open(os.path.join(HERE, "chooser.py"), encoding="utf-8").read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                source = source.replace(doc, "")
    code = "".join(line.split("#")[0] for line in source.splitlines(keepends=True))
    for word in ("demag", "thellier", "arai", "specimen", "paleointensity", "zijderveld"):
        assert word not in code.lower(), f"chooser.py's code mentions {word}"
