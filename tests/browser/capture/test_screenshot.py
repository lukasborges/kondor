from PySide6.QtCore import QDate, QDateTime, QTime

from kondor.browser.capture.screenshot import screenshot_file_name

MOMENT = QDateTime(QDate(2026, 11, 18), QTime(9, 5, 7))


def test_name_is_title_then_timestamp() -> None:
    assert screenshot_file_name("KDE", MOMENT) == "KDE 2026-11-18 09.05.07.png"


def test_name_drops_characters_not_allowed_in_file_names() -> None:
    assert screenshot_file_name("a/b: c", MOMENT) == "a_b_ c 2026-11-18 09.05.07.png"
