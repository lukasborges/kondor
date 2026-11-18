from pathlib import Path

from PySide6.QtCore import QUrl

from kondor.adblock.adblockinterceptor import VIEWER_SCHEMES

DESKTOP_FILE = Path(__file__).parents[2] / "packaging" / "kondor.desktop"


def test_viewer_schemes_are_chrome_internal() -> None:
    assert QUrl("chrome-extension://abc/index.html").scheme() in VIEWER_SCHEMES
    assert QUrl("chrome://print/").scheme() in VIEWER_SCHEMES


def test_desktop_file_lists_pdf_in_open_with() -> None:
    mime_line = next(
        line for line in DESKTOP_FILE.read_text().splitlines() if line.startswith("MimeType=")
    )
    assert "application/pdf;" in mime_line
