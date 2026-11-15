import os

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QTranslator
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from kondor.app.startup.stagedbuild import PROJECT_VERSION

DESKTOP_STYLE = "org.kde.desktop"
FALLBACK_STYLE = "Fusion"


def install_translator(app: QApplication, name: str, directory: str) -> None:
    translator = QTranslator(app)
    if translator.load(QLocale(), name, "_", directory):
        app.installTranslator(translator)


def set_display_name() -> None:
    #: Application display name: translate "Browser", keep "Kondor"
    QGuiApplication.setApplicationDisplayName(
        QCoreApplication.translate("Kondor", "Kondor Browser")
    )


def use_desktop_style() -> None:
    QQuickStyle.setStyle(DESKTOP_STYLE)
    if QQuickStyle.name() != DESKTOP_STYLE:
        QQuickStyle.setStyle(FALLBACK_STYLE)


def desktop_file_name() -> str:
    return os.environ.get("FLATPAK_ID") or "kondor"


def set_up_identity() -> None:
    QCoreApplication.setOrganizationName("KDE")
    QCoreApplication.setApplicationName("Kondor")
    QCoreApplication.setApplicationVersion(PROJECT_VERSION)
    QGuiApplication.setDesktopFileName(desktop_file_name())
    QGuiApplication.setWindowIcon(QIcon(":/packaging/kondor.png"))


def set_up_language_and_style(app: QApplication) -> None:
    install_translator(app, "kondor", ":/i18n")
    install_translator(app, "qt", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    set_display_name()
    use_desktop_style()
