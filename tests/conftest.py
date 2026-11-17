import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QResource, QStandardPaths, Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from PySide6.QtWidgets import QApplication

from kondor.app.startup.appidentity import use_bundled_icons
from kondor.core.database.database import Database
from kondor.site.sitesettings import SiteSettings
from tests.kondortypes import qmltypes_modules

STAGED_BUILD = Path(__file__).resolve().parent.parent / "build" / "python"
DESKTOP_STYLE = "org.kde.desktop"
XDG_FOLDERS = {"XDG_CONFIG_HOME": "config", "XDG_DATA_HOME": "data", "XDG_CACHE_HOME": "cache"}
DICTIONARIES_VARIABLE = "QTWEBENGINE_DICTIONARIES_PATH"
SANDBOX_VARIABLE = "QTWEBENGINE_DISABLE_SANDBOX"
CHROMIUM_FLAGS_VARIABLE = "QTWEBENGINE_CHROMIUM_FLAGS"
NO_GPU_FLAG = "--disable-gpu"
NO_KWALLET_VARIABLE = "KONDOR_NO_KWALLET"
NO_DESKTOP_SERVICES = {"QT_QPA_PLATFORMTHEME": "", "QT_NO_XDG_DESKTOP_PORTAL": "1"}

os.environ.update(NO_DESKTOP_SERVICES)


@pytest.fixture(scope="session", autouse=True)
def isolated_profile(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    profile = tmp_path_factory.mktemp("profile")
    with pytest.MonkeyPatch.context() as patch:
        for variable, folder in XDG_FOLDERS.items():
            patch.setenv(variable, str(profile / folder))
        patch.delenv(DICTIONARIES_VARIABLE, raising=False)
        patch.setenv(SANDBOX_VARIABLE, "1")
        patch.setenv(NO_KWALLET_VARIABLE, "1")
        patch.setenv(CHROMIUM_FLAGS_VARIABLE, NO_GPU_FLAG)
        yield profile


@pytest.fixture(scope="session")
def qapp_cls(isolated_profile: Path) -> type[QApplication]:
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QtWebEngineQuick.initialize()
    return QApplication


@pytest.fixture(scope="session")
def kondor_types(qapp: object, isolated_profile: Path) -> None:
    for module in qmltypes_modules():
        module.register_types()


@pytest.fixture(scope="session")
def staged_build() -> Path:
    if not (STAGED_BUILD / "qml" / "Kondor" / "qmldir").exists():
        pytest.fail("run python3 scripts/build.py first")
    return STAGED_BUILD


@pytest.fixture(scope="session")
def desktop_style() -> None:
    QQuickStyle.setStyle(DESKTOP_STYLE)


@pytest.fixture(scope="session")
def staged_resources(staged_build: Path, desktop_style: None) -> None:
    assert QResource.registerResource(str(staged_build / "kondor.rcc"))
    use_bundled_icons()


def staged_engine(staged_build: Path) -> QQmlEngine:
    engine = QQmlEngine()
    engine.addImportPath(str(staged_build / "qml"))
    return engine


@pytest.fixture
def qml_engine(qapp: object, staged_build: Path, staged_resources: None) -> Iterator[QQmlEngine]:
    engine = staged_engine(staged_build)
    yield engine
    engine.deleteLater()


@pytest.fixture(scope="session")
def kondor_engine(kondor_types: None, staged_build: Path, staged_resources: None) -> QQmlEngine:
    return staged_engine(staged_build)


@pytest.fixture
def site_settings(qapp: object) -> Iterator[SiteSettings]:
    Database.reset_instance()
    folder = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    (folder / "kondor.sqlite").unlink(missing_ok=True)
    yield SiteSettings.instance()
    Database.reset_instance()
    (folder / "kondor.sqlite").unlink(missing_ok=True)
