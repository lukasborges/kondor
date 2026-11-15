from collections.abc import Iterator

import pytest
from PySide6.QtCore import QLocale, QObject
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile import profilesetup
from tests.browser.profile.profilesupport import restored_settings

pytestmark = pytest.mark.no_qt_log


@pytest.fixture
def profile(qapp: object) -> Iterator[QQuickWebEngineProfile]:
    owner = QObject()
    profile = QQuickWebEngineProfile(owner)
    profilesetup.apply(profile)
    yield profile
    owner.deleteLater()


def test_user_agent_names_kondor(profile: QQuickWebEngineProfile) -> None:
    assert "Kondor/0.1" in profile.httpUserAgent()
    assert "QtWebEngine/" not in profile.httpUserAgent()


def test_accept_language_is_the_locale(profile: QQuickWebEngineProfile) -> None:
    assert profile.httpAcceptLanguage() == QLocale().bcp47Name()


def test_download_path_and_spell_check_follow_settings(profile: QQuickWebEngineProfile) -> None:
    names = ("spellCheckEnabled", "spellCheckLanguages", "downloadDirectory")
    with restored_settings(*names) as settings:
        settings.setProperty("spellCheckEnabled", False)
        settings.setProperty("spellCheckLanguages", ["en-US"])
        profilesetup.apply(profile)
        assert profile.downloadPath() == settings.property("downloadDirectory")
        assert not profile.isSpellCheckEnabled()
        assert profile.spellCheckLanguages() == ["en-US"]
