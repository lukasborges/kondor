from kondor.app.aboutinfo import AboutInfo
from kondor.app.commandline.startupargs import StartupArgs
from kondor.app.windows.windowmanager import WindowManager
from kondor.core.qmlregistration import QmlKind, QmlType, register

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(AboutInfo, "AboutInfo", QmlKind.SINGLETON),
    QmlType(StartupArgs, "StartupArgs", QmlKind.SINGLETON),
    QmlType(WindowManager, "WindowManager", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
