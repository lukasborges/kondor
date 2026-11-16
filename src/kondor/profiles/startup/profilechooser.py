from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtWidgets import QApplication

from kondor.app.startup.appidentity import set_up_language_and_style
from kondor.app.startup.stagedbuild import staged_build_directory
from kondor.core.qmlregistration import register
from kondor.profiles.qmltypes import QML_TYPES


def create_window(engine: QQmlApplicationEngine) -> QObject | None:
    component = QQmlComponent(engine, "Kondor", "ProfileChooserWindow")
    return None if component.isError() else component.create()


def ask_for_profile(app: QApplication) -> str | None:
    set_up_language_and_style(app)
    register(QML_TYPES)
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(staged_build_directory() / "qml"))
    window = create_window(engine)
    if window is None:
        return None
    app.exec()
    return str(window.property("chosenProfileId")) or None
