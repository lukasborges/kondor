import pytest
from PySide6.QtCore import QObject

from kondor.app.windows import windowtabs
from kondor.app.windows.windowtabs import show_tab_in
from tests.app.krunner.runnerfakes import FakeTab, FakeWindow


@pytest.fixture
def raised(monkeypatch: pytest.MonkeyPatch) -> list[tuple[QObject, bytes]]:
    calls: list[tuple[QObject, bytes]] = []
    monkeypatch.setattr(windowtabs, "raise_window", lambda w, token: calls.append((w, token)))
    return calls


def test_selects_the_tab_in_its_window(raised: list[tuple[QObject, bytes]], qapp: object) -> None:
    tab = FakeTab("Video", "https://a.example/")
    window = FakeWindow([FakeTab("Other", "https://b.example/"), tab])

    assert show_tab_in([window], tab, b"token")

    assert window.model.current_index == 1
    assert raised == [(window, b"token")]


def test_finds_the_tab_in_a_private_window(
    raised: list[tuple[QObject, bytes]], qapp: object
) -> None:
    tab = FakeTab("Video", "https://a.example/", is_private=True)
    normal = FakeWindow([FakeTab("Other", "https://b.example/")])
    private = FakeWindow([tab], is_private=True)

    assert show_tab_in([normal, private], tab, b"")

    assert private.model.current_index == 0 and normal.model.current_index == -1


def test_does_nothing_for_a_tab_in_no_window(
    raised: list[tuple[QObject, bytes]], qapp: object
) -> None:
    window = FakeWindow([FakeTab("Other", "https://b.example/")])

    assert not show_tab_in([window], FakeTab("Lost", "https://c.example/"), b"")

    assert raised == [] and window.model.current_index == -1
