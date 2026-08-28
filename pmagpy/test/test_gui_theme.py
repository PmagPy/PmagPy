import pytest

from dialogs import gui_theme


SEMANTIC_ROLES = (
    gui_theme.SUCCESS,
    gui_theme.ERROR,
    gui_theme.WARNING,
    gui_theme.ACTION,
    gui_theme.ANALYSIS,
    gui_theme.UPLOAD,
    gui_theme.NEUTRAL,
)


@pytest.mark.parametrize("dark", (False, True))
@pytest.mark.parametrize("role", SEMANTIC_ROLES)
def test_semantic_colours_have_readable_contrast(role, dark):
    background, foreground = gui_theme.get_control_colours(role, dark=dark)

    assert gui_theme.contrast_ratio(background, foreground) >= 4.5


def test_role_aliases_match_their_semantic_roles():
    assert gui_theme.get_control_colours("pass", dark=True) == \
        gui_theme.get_control_colours(gui_theme.SUCCESS, dark=True)
    assert gui_theme.get_control_colours("fail", dark=False) == \
        gui_theme.get_control_colours(gui_theme.ERROR, dark=False)


def test_unknown_role_is_rejected():
    with pytest.raises(ValueError, match="Unknown GUI colour role"):
        gui_theme.get_control_colours("not-a-role")


def test_semantic_colours_do_not_require_wx(monkeypatch):
    def fail_if_wx_is_loaded():
        pytest.fail("semantic colours should not load wxPython")

    monkeypatch.setattr(gui_theme, "_get_wx", fail_if_wx_is_loaded)

    assert gui_theme.get_control_colours(
        gui_theme.WARNING, dark=True
    ) == ("#4A3A0B", "#FFF0B3")


class FakeControl:
    def __init__(self):
        self.background = None
        self.foreground = None
        self.refresh_count = 0

    def SetBackgroundColour(self, colour):
        self.background = colour

    def SetForegroundColour(self, colour):
        self.foreground = colour

    def Refresh(self):
        self.refresh_count += 1


def test_style_control_sets_both_colours_and_remembers_role():
    control = FakeControl()

    background, foreground = gui_theme.style_control(
        control, gui_theme.WARNING, dark=True
    )

    assert control.background == background
    assert control.foreground == foreground
    assert control._pmag_theme_role == gui_theme.WARNING
    assert control.refresh_count == 1
    assert background.startswith("#")
    assert foreground.startswith("#")


class FakeListControl:
    def __init__(self, item_count=1):
        self.item_count = item_count
        self.backgrounds = {}
        self.foregrounds = {}
        self.refreshed_items = []

    def SetItemBackgroundColour(self, index, colour):
        self.backgrounds[index] = colour

    def SetItemTextColour(self, index, colour):
        self.foregrounds[index] = colour

    def RefreshItem(self, index):
        self.refreshed_items.append(index)

    def GetItemCount(self):
        return self.item_count


def test_style_list_item_sets_both_colours_and_remembers_role():
    list_control = FakeListControl()

    background, foreground = gui_theme.style_list_item(
        list_control, 0, gui_theme.ANALYSIS, dark=True
    )

    assert list_control.backgrounds[0] == background
    assert list_control.foregrounds[0] == foreground
    assert list_control._pmag_item_theme_roles[0] == gui_theme.ANALYSIS
    assert list_control.refreshed_items == [0]
    assert gui_theme.contrast_ratio(background, foreground) >= 4.5
