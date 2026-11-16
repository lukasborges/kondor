from collections.abc import Iterator

import pytest
from PySide6.QtCore import QCoreApplication, QEvent

from kondor.browser.tabs.tabmodel import TabModel
from tests.bookmarks.bar.barharness import release_created_objects, release_profiles


@pytest.fixture
def tabs(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    release_created_objects()
    tab_model.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    release_profiles()


@pytest.fixture(autouse=True)
def released_objects() -> Iterator[None]:
    yield
    release_created_objects()
