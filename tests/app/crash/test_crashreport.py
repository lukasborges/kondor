from urllib.parse import parse_qs, urlparse

from kondor.app.crash.crashreport import CLIPBOARD_NOTE, CrashReport

CRASH = "Fatal Python error: Segmentation fault\n\nCurrent thread 0x1 (most recent call first):"


def query_of(address: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(address).query)


def test_titleNamesTheSignalAndVersion() -> None:
    report = CrashReport(CRASH, "10:00:00 window opened", "0.15.1")
    assert report.title() == "Crash: Segmentation fault in Kondor 0.15.1"


def test_bodyHasAllSections() -> None:
    body = CrashReport(CRASH, "10:00:00 window opened", "0.15.1").body()
    for heading in ("### What were you doing?", "### Environment", "### Last actions", "### Crash"):
        assert heading in body
    assert "10:00:00 window opened" in body


def test_addressPointsToPrefilledIssue() -> None:
    address = CrashReport(CRASH, "", "0.15.1").address()
    assert address.startswith("https://github.com/lukasborges/kondor-browser/issues/new?labels=bug")
    assert "Fatal Python error" in query_of(address)["body"][0]


def test_longReportKeepsOnlyEnvironmentInAddress() -> None:
    report = CrashReport(CRASH, "x" * 9000, "0.15.1")
    assert report.is_too_long()
    body = query_of(report.address())["body"][0]
    assert CLIPBOARD_NOTE in body
    assert "xxxx" not in body
    assert "### Environment" in body
