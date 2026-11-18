from typing import Any

import pytest

from kondor.app.mcp.protocol.toolresult import ToolFailureError
from kondor.app.mcp.tools import inspection, interaction, navigation, pagetools
from tests.app.mcp.fakes import WORLD_REPLIES, FakeBrowser, FakeSession

CENTER_X = 40.0
CENTER = {"result": {"value": {"x": CENTER_X, "y": 50.0}}}
CTRL_BIT = 2
WORLD_CONTEXT = 7


def clicking_session() -> FakeSession:
    return FakeSession({**WORLD_REPLIES, "Runtime.evaluate": CENTER})


def mouse_types(session: FakeSession) -> list[Any]:
    return [params["type"] for params in session.params_of("Input.dispatchMouseEvent")]


def test_lists_pages_as_json() -> None:
    result = pagetools.list_pages(FakeBrowser(FakeSession()), {})

    assert '"current": true' in result["content"][0]["text"]
    assert "kde.org" in result["content"][0]["text"]


def test_opens_a_new_tab() -> None:
    browser = FakeBrowser(FakeSession())

    pagetools.new_tab(browser, {"url": "https://kde.org"})

    assert browser.opened == ["https://kde.org"]


def test_navigates_and_waits_for_the_load_event() -> None:
    session = FakeSession()

    navigation.navigate(FakeBrowser(session), {"url": "https://kde.org"})

    assert session.methods() == ["Page.enable", "Page.navigate"]
    assert session.params_of("Page.navigate") == [{"url": "https://kde.org"}]


def test_reports_a_page_that_never_finishes_loading() -> None:
    session = FakeSession()
    session.events.clear()

    with pytest.raises(ToolFailureError):
        navigation.reload(FakeBrowser(session), {})


def test_goes_back_to_the_previous_history_entry() -> None:
    history = {"currentIndex": 1, "entries": [{"id": 10}, {"id": 11}]}
    session = FakeSession({"Page.getNavigationHistory": history})

    navigation.go_back(FakeBrowser(session), {})

    assert session.params_of("Page.navigateToHistoryEntry") == [{"entryId": 10}]


def test_refuses_to_go_back_from_the_first_entry() -> None:
    history = {"currentIndex": 0, "entries": [{"id": 10}]}

    with pytest.raises(ToolFailureError):
        navigation.go_back(FakeBrowser(FakeSession({"Page.getNavigationHistory": history})), {})


def test_clicks_with_real_mouse_events_at_the_element_center() -> None:
    session = clicking_session()

    interaction.click(FakeBrowser(session), {"uid": "3"})

    assert mouse_types(session) == ["mouseMoved", "mousePressed", "mouseReleased"]
    assert session.params_of("Input.dispatchMouseEvent")[1]["x"] == CENTER_X


def test_hovers_with_a_mouse_move_only() -> None:
    session = clicking_session()

    interaction.hover(FakeBrowser(session), {"uid": "3"})

    assert mouse_types(session) == ["mouseMoved"]


def test_rejects_an_unknown_element() -> None:
    session = FakeSession({**WORLD_REPLIES, "Runtime.evaluate": {"result": {"value": None}}})

    with pytest.raises(ToolFailureError):
        interaction.click(FakeBrowser(session), {"uid": "9"})


def test_types_text_after_clicking_and_presses_enter_to_submit() -> None:
    session = clicking_session()

    interaction.type_text(FakeBrowser(session), {"uid": "1", "text": "kde", "submit": True})

    assert session.params_of("Input.insertText") == [{"text": "kde"}]
    assert [p["key"] for p in session.params_of("Input.dispatchKeyEvent")] == ["Enter", "Enter"]


def test_presses_a_combination_with_modifiers() -> None:
    session = FakeSession()

    interaction.press_key(FakeBrowser(session), {"key": "Ctrl+A"})

    first = session.params_of("Input.dispatchKeyEvent")[0]
    assert first["modifiers"] == CTRL_BIT
    assert first["key"] == "A"
    assert "text" not in first


def test_rejects_an_unknown_key() -> None:
    with pytest.raises(ToolFailureError):
        interaction.press_key(FakeBrowser(FakeSession()), {"key": "Hyper"})


def test_scrolls_with_the_mouse_wheel_at_the_viewport_center() -> None:
    session = clicking_session()

    interaction.scroll(FakeBrowser(session), {"direction": "up", "amount": 100})

    wheel = session.params_of("Input.dispatchMouseEvent")[0]
    assert (wheel["type"], wheel["deltaY"], wheel["x"]) == ("mouseWheel", -100, CENTER_X)


def test_returns_the_screenshot_as_png_image_content() -> None:
    session = FakeSession({"Page.captureScreenshot": {"data": "QUJD"}})

    result = inspection.screenshot(FakeBrowser(session), {})

    assert result["content"] == [{"type": "image", "data": "QUJD", "mimeType": "image/png"}]


def test_evaluates_in_the_main_world_by_value() -> None:
    session = FakeSession({"Runtime.evaluate": {"result": {"value": 4}}})

    result = inspection.evaluate(FakeBrowser(session), {"expression": "2+2"})

    assert result["content"][0]["text"] == "4"
    assert session.params_of("Runtime.evaluate")[0]["returnByValue"] is True
    assert "contextId" not in session.params_of("Runtime.evaluate")[0]


def test_reports_a_failing_expression() -> None:
    details = {"exceptionDetails": {"exception": {"description": "ReferenceError: x"}}}

    result = inspection.evaluate(
        FakeBrowser(FakeSession({"Runtime.evaluate": details})), {"expression": "x"}
    )

    assert result["isError"] is True


def test_takes_a_snapshot_in_an_isolated_world() -> None:
    session = FakeSession(
        {**WORLD_REPLIES, "Runtime.evaluate": {"result": {"value": "Title: KDE"}}}
    )

    result = inspection.snapshot(FakeBrowser(session), {})

    assert result["content"][0]["text"] == "Title: KDE"
    assert session.params_of("Runtime.evaluate")[0]["contextId"] == WORLD_CONTEXT


def test_uses_the_requested_page() -> None:
    browser = FakeBrowser(FakeSession({"Page.captureScreenshot": {"data": ""}}))

    inspection.screenshot(browser, {"page": "B"})

    assert browser.requested_page == "B"


def test_announces_the_move_and_press_of_a_click_but_not_the_release() -> None:
    session = clicking_session()

    interaction.click(FakeBrowser(session), {"uid": "1"})

    assert session.announcements == [("move", (CENTER_X, 50.0)), ("press", (CENTER_X, 50.0))]


def test_announces_a_hover_as_a_move() -> None:
    session = clicking_session()

    interaction.hover(FakeBrowser(session), {"uid": "1"})

    assert session.announcements == [("move", (CENTER_X, 50.0))]


def test_does_not_announce_a_scroll() -> None:
    session = clicking_session()

    interaction.scroll(FakeBrowser(session), {"direction": "down"})

    assert session.announcements == []
