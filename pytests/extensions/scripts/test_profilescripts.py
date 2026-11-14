from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.extensions.extensionmanager import ExtensionManager
from pytests.browser.profile.profilesupport import scripts_named
from pytests.extensions.extensionsharness import (
    allow_in_private_windows,
    install_sample,
    remove_every_extension,
)

pytestmark = pytest.mark.no_qt_log
SCRIPT_NAME = "kondor-ext:sample:0"


@pytest.fixture
def owner(qapp: object, staged_resources: None) -> Iterator[QObject]:
    owner = QObject()
    yield owner
    owner.deleteLater()
    remove_every_extension()


def private_profile(owner: QObject) -> QQuickWebEngineProfile:
    profile = QQuickWebEngineProfile(owner)
    ExtensionManager.instance().register_profile(profile)
    return profile


def test_registered_profile_gets_the_scripts(owner: QObject, tmp_path: Path) -> None:
    assert install_sample(str(tmp_path))
    allow_in_private_windows("sample")
    profile = private_profile(owner)
    assert len(scripts_named(profile, SCRIPT_NAME)) == 1


def test_rebuild_replaces_instead_of_adding(owner: QObject, tmp_path: Path, qtbot: Any) -> None:
    assert install_sample(str(tmp_path))
    allow_in_private_windows("sample")
    profile = private_profile(owner)
    manager = ExtensionManager.instance()
    manager.setEnabled("sample", False)
    manager.setEnabled("sample", True)
    qtbot.wait(50)
    assert len(scripts_named(profile, SCRIPT_NAME)) == 1


def test_private_profile_skips_extensions_not_allowed(owner: QObject, tmp_path: Path) -> None:
    assert install_sample(str(tmp_path))
    profile = private_profile(owner)
    assert scripts_named(profile, SCRIPT_NAME) == []
