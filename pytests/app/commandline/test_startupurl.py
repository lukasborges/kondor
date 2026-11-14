from pathlib import Path

import pytest
from PySide6.QtCore import QUrl

from kondor.app.commandline.startupurl import (
    StartupContext,
    startup_url_for_argument,
    startup_urls_for_arguments,
)

HOME_PAGE = QUrl("https://home.example/")
SEARCH_TEMPLATE = "https://duckduckgo.com/?q=%1"


def encoded(url: QUrl) -> str:
    return url.toString(QUrl.ComponentFormattingOption.FullyEncoded)


@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        pytest.param("https://kde.org", "https://kde.org", id="explicit url"),
        pytest.param("kde.org", "https://kde.org", id="naked domain"),
        pytest.param("about:blank", "about:blank", id="about scheme"),
        pytest.param(
            "some words", "https://duckduckgo.com/?q=some%20words", id="free text searches"
        ),
        pytest.param("kde", "https://duckduckgo.com/?q=kde", id="single word searches"),
        pytest.param("   ", "", id="blank arguments are ignored"),
    ],
)
def test_converts_arguments(argument: str, expected: str) -> None:
    context = StartupContext("/tmp", HOME_PAGE, SEARCH_TEMPLATE)

    assert encoded(startup_url_for_argument(argument, context)) == expected


def test_resolves_relative_files_against_working_directory(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    page.write_text("<html></html>")
    context = StartupContext(str(tmp_path), HOME_PAGE, SEARCH_TEMPLATE)
    expected = encoded(QUrl.fromLocalFile(str(page)))

    for argument in ("./page.html", "page.html", str(page)):
        assert encoded(startup_url_for_argument(argument, context)) == expected


@pytest.mark.usefixtures("qapp")
def test_skips_empty_arguments() -> None:
    urls = startup_urls_for_arguments(["", "   ", "https://kde.org"])

    assert urls == [QUrl("https://kde.org")]
