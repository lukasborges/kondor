import os

from PySide6.QtCore import QCoreApplication, QDir, Qt
from PySide6.QtWebEngineQuick import QtWebEngineQuick

from kondor.app.startup.stagedbuild import staged_build_directory

DICTIONARIES_VARIABLE = "QTWEBENGINE_DICTIONARIES_PATH"
PORTAL_VARIABLE = "PLASMA_INTEGRATION_USE_PORTAL"


def dictionary_candidates(staged: str) -> list[str]:
    return [
        f"{staged}/../share/kondor/qtwebengine_dictionaries",
        f"{staged}/qtwebengine_dictionaries",
    ]


def find_dictionaries(staged: str) -> None:
    if DICTIONARIES_VARIABLE in os.environ:
        return
    for candidate in dictionary_candidates(staged):
        if QDir(candidate).exists():
            os.environ[DICTIONARIES_VARIABLE] = QDir.cleanPath(candidate)
            return


def use_portal_inside_app_image() -> None:
    if "APPIMAGE" in os.environ and PORTAL_VARIABLE not in os.environ:
        os.environ[PORTAL_VARIABLE] = "1"


def prepare_environment() -> None:
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    find_dictionaries(str(staged_build_directory()))
    QtWebEngineQuick.initialize()
    use_portal_inside_app_image()
