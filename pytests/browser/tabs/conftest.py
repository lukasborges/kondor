from collections.abc import Iterator

import pytest
from PySide6.QtCore import QUrl

from kondor.browser.tabs.tabmodel import TabModel

A_URL = QUrl("https://a.example")


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


def site(name: str) -> QUrl:
    return QUrl(f"https://{name}.example")
