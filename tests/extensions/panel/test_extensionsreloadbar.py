import pytest

from tests.extensions.panel.panelfixture import PanelFixture
from tests.extensions.panel.panelitems import click_center_of

pytestmark = pytest.mark.no_qt_log

SAMPLE = "sample"


def test_reload_button_requests_reload(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    reloads: list[bool] = []
    panel.tab.reloadRequested.connect(lambda: reloads.append(True))
    panel.toggle_run_on_site()
    panel.wait_for(lambda: panel.item_with_text(panel.item("bar"), "Reload"))
    click_center_of(panel.item_with_text(panel.item("bar"), "Reload"))
    assert len(reloads) == 1


def test_starting_to_load_hides_reload_bar(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    panel.toggle_run_on_site()
    panel.tab.setLoading(True)
    assert not panel.item("bar").isVisible()


def test_toggling_back_hides_reload_bar(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    panel.toggle_run_on_site()
    panel.toggle_run_on_site()
    assert not panel.item("bar").isVisible()
