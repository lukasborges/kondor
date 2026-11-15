from collections.abc import Iterator

import pytest

from kondor.browser.tabs.tabmodel import TabModel


@pytest.fixture
def tabs(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()
