"""Tests for the toolkit's foundations: the shell, the session's directory, the runtime, the launcher.

    pytest programs/pmagpy_panel/test_shell.py -q
"""
import asyncio
import json
import os

import param
import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel import AppInfo, datasets, launch, runtime, shell  # noqa: E402

INFO = AppInfo(name="Test App", app_id="test_app", env_prefixes=("TEST_APP_",))
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(os.path.dirname(HERE), "pmagpy_directions", "assets", "pmagpy_logo_white.png")


class FakeSession(param.Parameterized):
    status = param.String(default="loaded")


def _body(**kw):
    return shell.Body(info=INFO, main=pn.Column(pn.pane.HTML("main")), **kw)


class TestShell:
    def test_template_wraps_a_body_and_wires_the_modal(self):
        """The host owns the modal; the body only asks for it to open and close."""
        modal = pn.Column(pn.pane.HTML("choose"))
        body = _body(side=pn.Column(pn.pane.HTML("side")), modal=modal,
                     header=shell.status_line(FakeSession()))
        tmpl = shell.template(body, logo=LOGO)
        assert tmpl.title == "Test App"
        assert tmpl.logo.startswith("data:image/png;base64,")
        assert tmpl.favicon == "/test_app_assets/favicon.png"
        assert modal in list(tmpl.modal)
        assert body.open_modal == tmpl.open_modal and body.close_modal == tmpl.close_modal
        assert tmpl.body is body and tmpl.workspace.side_area is not None

    def test_show_side_hides_the_column_and_its_handle_together(self):
        body = _body(side=pn.Column(pn.pane.HTML("side")))
        tmpl = shell.template(body, logo=LOGO)
        body.show_side(False)
        assert tmpl.workspace.side_area.visible is False
        body.show_side(True)
        assert tmpl.workspace.side_area.visible is True

    def test_a_body_without_a_side_column_takes_the_full_width(self):
        body = _body()
        tmpl = shell.template(body, logo=LOGO)
        assert tmpl.workspace.side_area is None
        assert len(tmpl.workspace.layout) == 1
        body.show_side(False)                      # nothing to hide; must not raise

    def test_status_line_follows_the_session(self):
        s = FakeSession()
        line = shell.status_line(s)
        assert "loaded" in line.object
        s.status = "1034 specimens"
        assert "1034 specimens" in line.object

    def test_back_link_only_under_a_hub(self):
        body = _body()
        assert len(shell.template(body, logo=LOGO).header) == 0
        under_hub = shell.template(_body(), logo=LOGO, hub_url="http://localhost:5010/")
        assert len(under_hub.header) == 1 and 'href="http://localhost:5010/"' in under_hub.header[0].object


class TestSessionDirectory:
    def test_query_string_then_environment_then_default(self, monkeypatch, tmp_path):
        monkeypatch.delenv("TEST_APP_DIR", raising=False)
        monkeypatch.setattr(datasets, "query_param", lambda name, default="": default)
        assert datasets.session_directory(INFO.env_prefixes, "/default") == "/default"
        monkeypatch.setenv("TEST_APP_DIR", str(tmp_path))
        assert datasets.session_directory(INFO.env_prefixes, "/default") == str(tmp_path)
        monkeypatch.setattr(datasets, "query_param", lambda name, default="": "~/from_url" if name == "dir" else default)
        assert datasets.session_directory(INFO.env_prefixes, "/default") == os.path.expanduser("~/from_url")

    def test_query_param_is_empty_outside_a_server_session(self):
        assert runtime.query_param("dir") == ""
        assert runtime.query_param("dir", "x") == "x"

    def test_example_dir_finds_the_shipped_dataset(self):
        assert datasets.example_dir("McMurdo").endswith(os.path.join("3_0", "McMurdo"))
        assert datasets.example_dir("no_such_dataset") == ""


class TestSharedRecentFile:
    def test_seeded_once_from_the_per_application_lists(self, monkeypatch, tmp_path):
        shared = tmp_path / ".pmagpy" / "recent_magic_dirs.json"
        monkeypatch.setattr(datasets, "SHARED_RECENT_FILE", str(shared))
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir(); b.mkdir()
        old = tmp_path / ".old_recent.json"
        old.write_text(json.dumps([str(a), str(b), str(tmp_path / "gone")]))
        path = datasets.shared_recent_file(migrate_from=[str(old)])
        assert path == str(shared)
        assert datasets.load_recent(path) == [str(a), str(b)]      # missing directories dropped
        # a second application's old list does not overwrite what is already shared
        other = tmp_path / ".other_recent.json"
        other.write_text(json.dumps([str(b)]))
        datasets.shared_recent_file(migrate_from=[str(other)])
        assert datasets.load_recent(path) == [str(a), str(b)]
        # and remembering writes to the shared file, creating its directory if need be
        datasets.remember_recent(path, str(b))
        assert datasets.load_recent(path) == [str(b), str(a)]

    def test_without_anything_to_migrate_the_path_is_just_returned(self, monkeypatch, tmp_path):
        shared = tmp_path / ".pmagpy" / "recent_magic_dirs.json"
        monkeypatch.setattr(datasets, "SHARED_RECENT_FILE", str(shared))
        assert datasets.shared_recent_file() == str(shared)
        assert not shared.exists()


class TestRuntime:
    def test_no_dialog_on_an_unknown_platform(self, monkeypatch):
        monkeypatch.setattr(runtime.sys, "platform", "unknown-os")
        assert runtime.native_choose_directory("/nonexistent") is None
        assert runtime.native_chooser_available() is False
        assert asyncio.run(runtime.choose_directory("/nonexistent")) is None

    def test_stub_answers_both_forms_of_the_dialog(self):
        assert runtime.native_choose_directory(stub="/stub") == "/stub"
        assert asyncio.run(runtime.choose_directory(stub="/stub")) == "/stub"
        assert runtime.native_chooser_available(stub="/stub") is True

    def test_hub_url_comes_from_the_environment(self, monkeypatch):
        monkeypatch.delenv(runtime.HUB_URL_VAR, raising=False)
        assert runtime.hub_url() == ""
        monkeypatch.setenv(runtime.HUB_URL_VAR, "http://localhost:5010/")
        assert runtime.hub_url() == "http://localhost:5010/"

    def test_datasets_still_exports_the_chooser_names(self):
        assert datasets.native_choose_directory is runtime.native_choose_directory
        assert datasets.native_chooser_available is runtime.native_chooser_available


class TestLaunch:
    def test_serve_command_for_one_application(self):
        app = os.path.join(os.path.dirname(HERE), "pmagpy_directions", "pmagpy_directions.py")
        cmd = launch.serve_command([app], 5100)
        assert cmd[cmd.index("serve") + 1] == app and "--index" not in cmd and "--dev" in cmd
        assets = cmd[cmd.index("--static-dirs") + 1]
        assert assets.startswith("pmagpy_directions_assets=") and assets.endswith(os.path.join("pmagpy_directions", "assets"))

    def test_serve_command_for_the_family(self):
        hub = os.path.join(os.path.dirname(HERE), "pmagpy_apps", "pmagpy_apps.py")
        app = os.path.join(os.path.dirname(HERE), "pmagpy_directions", "pmagpy_directions.py")
        cmd = launch.serve_command([hub, app], 5010, dev=False, index=True)
        assert cmd[cmd.index("--index") + 1] == "pmagpy_apps" and "--dev" not in cmd
        i = cmd.index("--static-dirs")
        assert cmd[i + 1].startswith("pmagpy_apps_assets=") and cmd[i + 2].startswith("pmagpy_directions_assets=")
