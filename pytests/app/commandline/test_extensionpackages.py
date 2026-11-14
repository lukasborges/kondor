from PySide6.QtCore import QUrl

from kondor.app.commandline.extensionpackages import take_extension_packages


def test_takes_local_packages_out_of_the_urls() -> None:
    urls = [
        QUrl.fromLocalFile("/tmp/a.kondorext"),
        QUrl("https://kde.org"),
        QUrl.fromLocalFile("/tmp/B.KONDOREXT"),
    ]

    packages = take_extension_packages(urls)

    assert packages == ["/tmp/a.kondorext", "/tmp/B.KONDOREXT"]
    assert urls == [QUrl("https://kde.org")]


def test_keeps_remote_urls_that_look_like_packages() -> None:
    urls = [QUrl("https://example.com/a.kondorext")]

    assert take_extension_packages(urls) == []
    assert len(urls) == 1
