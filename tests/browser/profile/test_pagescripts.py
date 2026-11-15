from collections.abc import Iterator

import pytest
from PySide6.QtCore import QFile, QObject
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile import pagescripts
from tests.browser.profile.profilesupport import scripts_named

pytestmark = pytest.mark.no_qt_log

RESOURCES = (
    pagescripts.WEB_CHANNEL_RESOURCE,
    pagescripts.CHANNEL_RESOURCE,
    pagescripts.USERNAME_FIELD_RESOURCE,
    pagescripts.PASSWORDS_RESOURCE,
)
InjectionPoint = QWebEngineScript.InjectionPoint
APPLICATION_WORLD = QWebEngineScript.ScriptWorldId.ApplicationWorld.value


@pytest.fixture
def owner(qapp: object, staged_resources: None) -> Iterator[QObject]:
    owner = QObject()
    yield owner
    owner.deleteLater()


def installed_profile(owner: QObject, storage_name: str | None) -> QQuickWebEngineProfile:
    if storage_name is None:
        profile = QQuickWebEngineProfile(owner)
    else:
        profile = QQuickWebEngineProfile(storage_name, owner)
    pagescripts.install(profile)
    return profile


def assert_single_script(scripts: list[QWebEngineScript], point: InjectionPoint) -> None:
    assert len(scripts) == 1
    assert scripts[0].injectionPoint() == point
    assert scripts[0].worldId() == APPLICATION_WORLD
    assert scripts[0].runsOnSubFrames()


@pytest.mark.parametrize("path", RESOURCES)
def test_resources_are_available(owner: QObject, path: str) -> None:
    assert QFile.exists(path)


def test_persistent_profile_gets_channel_and_passwords_scripts(owner: QObject) -> None:
    profile = installed_profile(owner, "pagescripts-test")
    assert not profile.isOffTheRecord()
    channel = scripts_named(profile, pagescripts.CHANNEL_SCRIPT)
    assert_single_script(channel, InjectionPoint.DocumentCreation)
    passwords = scripts_named(profile, pagescripts.PASSWORDS_SCRIPT)
    assert_single_script(passwords, InjectionPoint.DocumentReady)


def test_private_profile_gets_only_the_channel_script(owner: QObject) -> None:
    profile = installed_profile(owner, None)
    assert profile.isOffTheRecord()
    channel = scripts_named(profile, pagescripts.CHANNEL_SCRIPT)
    assert_single_script(channel, InjectionPoint.DocumentCreation)
    assert scripts_named(profile, pagescripts.PASSWORDS_SCRIPT) == []
