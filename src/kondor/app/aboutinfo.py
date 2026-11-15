from typing import ClassVar

import PySide6
from PySide6.QtCore import Property, QCoreApplication, QFile, QIODevice, QObject, QSysInfo, qVersion
from PySide6.QtGui import QGuiApplication
from PySide6.QtWebEngineCore import qWebEngineChromiumVersion, qWebEngineVersion

LICENSE_RESOURCE = ":/LICENSE"


def windowing_system_name(platform: str) -> str:
    if platform.startswith("wayland"):
        return "Wayland"
    return "X11" if platform == "xcb" else platform


def read_license_text() -> str:
    license_file = QFile(LICENSE_RESOURCE)
    if not license_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        return ""
    return bytes(license_file.readAll()).decode("utf-8").strip()


class AboutInfo(QObject):
    _instance: ClassVar["AboutInfo | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._license_text: str | None = None

    @classmethod
    def instance(cls) -> "AboutInfo":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def application_version(self) -> str:
        return str(QCoreApplication.applicationVersion())

    def qt_runtime_version(self) -> str:
        return str(qVersion())

    def qt_build_version(self) -> str:
        return str(PySide6.QtCore.__version__)

    def web_engine_version(self) -> str:
        return str(qWebEngineVersion())

    def chromium_version(self) -> str:
        return str(qWebEngineChromiumVersion())

    def windowing_system(self) -> str:
        return windowing_system_name(QGuiApplication.platformName())

    def operating_system(self) -> str:
        return str(QSysInfo.prettyProductName())

    def license_text(self) -> str:
        if self._license_text is None:
            self._license_text = read_license_text()
        return self._license_text

    version = Property(str, application_version, constant=True)
    qtRuntimeVersion = Property(str, qt_runtime_version, constant=True)
    qtBuildVersion = Property(str, qt_build_version, constant=True)
    webEngineVersion = Property(str, web_engine_version, constant=True)
    chromiumVersion = Property(str, chromium_version, constant=True)
    windowingSystem = Property(str, windowing_system, constant=True)
    operatingSystem = Property(str, operating_system, constant=True)
    licenseText = Property(str, license_text, constant=True)
