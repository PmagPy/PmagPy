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

    def test_the_content_goes_in_after_the_applications_watchers_have_drawn_it(self, monkeypatch):
        """Served, a tab says it is loading at once, the application draws it while it is out of the
        page, and it goes in on the next tick, filled: a table built with its data works in every
        browser (WebKit loses data sent to a Tabulator it is still building)."""
        from pmagpy_panel import runtime
        queued = []
        monkeypatch.setattr(runtime, "locked", queued.append)       # a served session's next tick
        b = pn.pane.Markdown("")
        tabs = shell.lazy_tabs(("A", pn.pane.Markdown("a")), ("B", b), loading="Loading B")
        seen = []

        def draw(event):
            seen.append(tabs[1] is b)
            b.object = "drawn"
        tabs.param.watch(draw, "active")
        tabs.active = 1
        assert seen == [False] and len(queued) == 1
        assert "Loading B" in tabs[1].objects[0].object            # the tab says so meanwhile
        queued.pop()()
        assert tabs[1] is b and b.object == "drawn"
        tabs.active = 0
        tabs.active = 1                                             # added once
        assert not queued and tabs[1] is b

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

    def test_the_busy_spinner_raises_no_warning(self):
        """param's 'busy_indicator ... valid parameter reference' warning is filtered, nothing else."""
        import warnings
        with warnings.catch_warnings(record=True) as caught:      # the filters as shell left them
            shell.template(_body(), logo=LOGO)
            warnings.warn("Parameter 'other' on <class 'panel.template.base.BasicTemplate'> ...", FutureWarning)
        messages = [str(w.message) for w in caught]
        assert not [m for m in messages if "busy_indicator" in m]
        assert any("Parameter 'other'" in m for m in messages)            # the filter is that warning's only

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

    def test_a_long_status_is_cut_at_two_lines_and_kept_whole_on_hover(self):
        s = FakeSession()
        line = shell.status_line(s)
        s.status = "1034 specimens; " + "demag_gui.redo (2458 fits) was not read & kept " * 6
        assert "-webkit-line-clamp:2" in line.object
        assert f'title="{s.status.replace("&", "&amp;")}"' in line.object

    def test_back_link_only_under_a_hub(self):
        body = _body()
        assert len(shell.template(body, logo=LOGO).header) == 0
        under_hub = shell.template(_body(), logo=LOGO, hub_url="http://localhost:5010/")
        # the way back carries the open directory (the page's ?dir=) so the hub reopens it
        assert "window.location.search" in under_hub.header[0].object
        assert len(under_hub.header) == 1 and 'href="http://localhost:5010/"' in under_hub.header[0].object

    def test_layout_hold_brackets_a_batch_once_and_is_mounted_by_the_workspace(self):
        """Several layout changes go to the browser as one bracketed batch, however deeply nested."""
        from pmagpy_panel.widgets import LayoutHold
        hold = LayoutHold.of_session()
        assert LayoutHold.of_session() is hold                  # one per session
        b0, e0 = hold.begin, hold.end
        with LayoutHold.batch():
            assert (hold.begin, hold.end) == (b0 + 1, e0)       # open ...
            with LayoutHold.batch():                            # ... nesting does not bump again
                pass
            assert (hold.begin, hold.end) == (b0 + 1, e0)
        assert (hold.begin, hold.end) == (b0 + 1, e0 + 1)       # ... closed once
        with pytest.raises(ValueError):
            with LayoutHold.batch():
                raise ValueError("a callback that fails must still release the hold")
        assert hold.begin == hold.end == b0 + 2 and hold._depth == 0
        # every page mounts the session's hold, so the batches reach the browser
        tmpl = shell.template(_body(), logo=LOGO)
        assert hold in list(tmpl.workspace.main_area)


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


    NETSTAT = """
Active Connections

  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       1012
  TCP    0.0.0.0:5010           0.0.0.0:0              LISTENING       4242
  TCP    127.0.0.1:5010         127.0.0.1:61000        ESTABLISHED     4242
  TCP    127.0.0.1:61000        127.0.0.1:5010         ESTABLISHED     9999
  TCP    0.0.0.0:50100          0.0.0.0:0              LISTENING       7777
  TCP    [::]:5010              [::]:0                 LISTENING       4243
  UDP    0.0.0.0:5010           *:*                                    5555
"""

    def test_windows_netstat_finds_the_servers_listening_on_the_port(self):
        """Only the listening TCP sockets of exactly that port (IPv4 and IPv6): not 50100, not a client's
        connection to it, not UDP."""
        assert launch._listening_pids_in_netstat(self.NETSTAT, 5010) == [4242, 4243]
        assert launch._listening_pids_in_netstat(self.NETSTAT, 135) == [1012]
        assert launch._listening_pids_in_netstat(self.NETSTAT, 501) == []

    def test_windows_netstat_in_another_language(self):
        """Windows translates the state column; a listening socket is told by its foreign address."""
        for state in ("ABHÖREN", "ESCUCHANDO", "EN ÉCOUTE", "LISTENING"):     # one word or two
            assert launch._listening_pids_in_netstat(self.NETSTAT.replace("LISTENING", state), 5010) == [4242, 4243]

    def test_windows_runs_netstat_for_both_ip_versions(self, monkeypatch):
        calls = []
        monkeypatch.setattr(launch.sys, "platform", "win32")
        monkeypatch.setattr(launch.subprocess, "run",
                            lambda cmd, **kw: calls.append((cmd, kw)) or type("Out", (), {"stdout": self.NETSTAT})())
        assert launch.pids_on_port(5010) == [4242, 4243]
        cmd, kw = calls[0]
        assert cmd == ["netstat", "-ano"] and kw.get("errors") == "replace"    # no -p TCP: that is IPv4 only

    def test_the_hub_serves_without_dev_mode_unless_asked(self, monkeypatch):
        """Dev mode builds every served application before the server answers: off for the hub,
        on for one application; --reload and --no-reload turn it either way, not both at once."""
        commands = []

        class Done:
            def poll(self):
                return 0

            def wait(self):
                return 0
        monkeypatch.setattr(launch.subprocess, "Popen", lambda cmd, **kw: commands.append(cmd) or Done())
        monkeypatch.setattr(launch, "stop_previous", lambda port: 0)
        app = os.path.join(os.path.dirname(HERE), "pmagpy_directions", "pmagpy_directions.py")

        def dev(argv, **kw):
            launch.main([app], "PMAGPY_X_", 5999, argv=["--no-show", *argv], **kw)
            return "--dev" in commands[-1]
        assert dev([]) and not dev(["--no-reload"])
        assert not dev([], reload=False) and dev(["--reload"], reload=False)
        with pytest.raises(SystemExit):
            launch.main([app], "PMAGPY_X_", 5999, argv=["--reload", "--no-reload"])


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
