from kondor.app.krunner.opentabs import open_tabs
from tests.app.krunner.runnerfakes import FakeTab, FakeWindow


def titles(windows: list[FakeWindow]) -> list[str]:
    return [tab.title for tab in open_tabs(windows)]


def test_private_windows_are_skipped(qapp: object) -> None:
    private = FakeWindow([FakeTab("Secret", "https://secret.example")], is_private=True)

    assert titles([private]) == []


def test_private_tabs_are_skipped(qapp: object) -> None:
    window = FakeWindow(
        [FakeTab("Secret", "https://s.example", True), FakeTab("A", "https://a.io")]
    )

    assert titles([window]) == ["A"]


def test_new_tab_page_and_empty_url_tabs_are_skipped(qapp: object) -> None:
    window = FakeWindow([FakeTab("New Tab", ""), FakeTab("A", "https://a.io")])

    assert titles([window]) == ["A"]


def test_window_and_tab_order_is_kept(qapp: object) -> None:
    first = FakeWindow([FakeTab("A", "https://a.io"), FakeTab("B", "https://b.io")])
    second = FakeWindow([FakeTab("C", "https://c.io")])

    assert titles([first, second]) == ["A", "B", "C"]
