from kondor.app.aboutinfo import AboutInfo
from kondor.app.commandline.startupargs import StartupArgs
from kondor.app.crash.actionlog import ActionLog
from kondor.app.crash.crashreporter import CrashReporter
from kondor.app.remotecontrol.remotecontrol import RemoteControl
from kondor.app.restart.apprestart import AppRestart
from kondor.app.windows.windowmanager import WindowManager
from kondor.core.qmlregistration import QmlKind, QmlType, register

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(ActionLog, "ActionLog", QmlKind.SINGLETON),
    QmlType(AboutInfo, "AboutInfo", QmlKind.SINGLETON),
    QmlType(AppRestart, "AppRestart", QmlKind.SINGLETON),
    QmlType(CrashReporter, "CrashReporter", QmlKind.SINGLETON),
    QmlType(RemoteControl, "RemoteControl", QmlKind.SINGLETON),
    QmlType(StartupArgs, "StartupArgs", QmlKind.SINGLETON),
    QmlType(WindowManager, "WindowManager", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
