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


class TestSidePanels:
    def test_a_panel_joins_the_page_when_first_shown_and_then_only_its_visibility_changes(self):
        panels = {0: pn.Column(name="steps"), 1: pn.Column(name="fits"), 2: pn.Column(name="means")}
        side = shell.SidePanels(panels)
        assert side.column.objects == [panels[0]]            # only the first tab's panel at the start

        side.show(1)
        assert side.column.objects == [panels[0], panels[1]]
        assert [p.visible for p in side.column.objects] == [False, True]

        side.show(0)                                          # back: nothing added, visibility swapped
        assert side.column.objects == [panels[0], panels[1]]
        assert [p.visible for p in side.column.objects] == [True, False]

        side.show(1)
        side.show(1)                                          # the same tab twice adds nothing
        assert side.column.objects == [panels[0], panels[1]]

    def test_a_tab_without_a_panel_shows_the_default(self):
        panels = {0: pn.Column(name="steps"), 1: pn.Column(name="fits")}
        side = shell.SidePanels(panels)
        side.show(1)
        side.show(4)
        assert [p.visible for p in side.column.objects] == [True, False]


class TestLazyTabs:
    def test_a_tab_joins_the_page_when_first_shown_and_stays(self):
        a, b, c = pn.pane.Markdown("a"), pn.pane.Markdown("b"), pn.pane.Markdown("c")
        tabs = shell.lazy_tabs(("A", a), ("B", b), ("C", c))
        assert tabs.dynamic is False
        assert tabs._names == ["A", "B", "C"]
        assert tabs[0] is a and tabs[1] is not b and tabs[2] is not c      # placeholders until opened

        tabs.active = 2
        assert tabs[2] is c and tabs[1] is not b
        tabs.active = 0
        tabs.active = 2                                    # back again: nothing replaced a second time
        assert tabs[0] is a and tabs[2] is c and tabs._names == ["A", "B", "C"]

    def test_the_content_is_added_before_the_applications_own_watchers(self):
        """The tab appears at once, however long the application's watcher then computes."""
        b = pn.pane.Markdown("")
        tabs = shell.lazy_tabs(("A", pn.pane.Markdown("a")), ("B", b))
        seen = []
        tabs.param.watch(lambda e: seen.append(tabs[1] is b), "active")
        tabs.active = 1
        assert seen == [True]

    def test_another_tab_can_be_on_show_first(self):
        a, b = pn.pane.Markdown("a"), pn.pane.Markdown("b")
        tabs = shell.lazy_tabs(("A", a), ("B", b), active=1)
        assert tabs[1] is b and tabs[0] is not a


class TestShell:
    def test_the_busy_spinner_stays_on_only_briefly_after_quick_work(self):
        """Panel keeps it on for at least 500 ms, which made every tab switch look slow."""
        first, second = shell.template(_body(), logo=LOGO), shell.template(_body(), logo=LOGO)
        assert first.busy_indicator.throttle == shell.BUSY_MIN_MS < 500
        assert first.busy_indicator is not second.busy_indicator        # each page has its own

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

    def test_the_header_wears_the_applications_colour(self):
        """Each application's header is its own colour — the same as its door on the hub."""
        from pmagpy_panel import APP_COLORS, FAMILY_COLOR, AppInfo, text_on
        assert AppInfo("PmagPy Directions", "pmagpy_directions").color == APP_COLORS["pmagpy_directions"] == "#00A8C8"
        assert INFO.color == FAMILY_COLOR                                    # no colour of its own: the family's
        body = shell.Body(info=AppInfo("D", "pmagpy_directions"), main=pn.pane.HTML("x"))
        tmpl = shell.template(body, logo=LOGO)
        assert tmpl.header_background == "#00A8C8" and tmpl.header_color == "#ffffff"
        assert tmpl.accent_base_color == FAMILY_COLOR                       # buttons look alike everywhere
        assert text_on(APP_COLORS["pmagpy_forc"]) == "#1b1b1b"              # dark ink on amber and lime
        assert text_on(APP_COLORS["pmagpy_rockmag"]) == "#1b1b1b"
        assert text_on(APP_COLORS["pmagpy_intensity"]) == "#ffffff"

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
        # the way back carries the open directory (the page's ?dir=) so the hub reopens it
        assert "window.location.search" in under_hub.header[0].object
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


class TestDeferredTemplate:
    def test_the_page_fills_in_when_the_body_is_built(self):
        built = []

        def build():
            built.append(True)
            return shell.Body(info=INFO, main=pn.Column(pn.pane.HTML("the main pane")),
                              side=pn.Column(pn.pane.HTML("the side column")), header=pn.pane.HTML("status"),
                              modal=pn.pane.HTML("the modal"))
        tmpl = shell.deferred_template(INFO, LOGO, build, loading="Loading X …")
        assert built == [True]                                   # outside a served session: at once
        body = tmpl.body
        assert isinstance(body, shell.Body)
        assert tmpl.workspace.main_area.objects[0].objects[0] is body.main and not tmpl.workspace.main_area.objects[0].loading
        assert tmpl.workspace.side_area.visible
        assert tmpl.header[0].objects[0] is body.header
        assert tmpl.modal[0].objects[0] is body.modal
        assert body.open_modal == tmpl.open_modal and body.close_modal == tmpl.close_modal
        body.show_side(False)
        assert not tmpl.workspace.side_area.visible

    def test_a_message_instead_of_a_body_takes_the_main_pane(self):
        tmpl = shell.deferred_template(INFO, LOGO, lambda: pn.pane.Markdown("## could not open"))
        assert tmpl.body is None
        assert tmpl.workspace.main_area.objects[0].objects[0].object == "## could not open"
        assert not tmpl.workspace.side_area.visible

    def test_a_failing_build_leaves_a_message_not_a_blank_page(self):
        def build():
            raise ValueError("boom")
        tmpl = shell.deferred_template(INFO, LOGO, build)
        shown = tmpl.workspace.main_area.objects[0].objects[0]
        assert "boom" in shown.object and not tmpl.workspace.main_area.objects[0].loading
