#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks import module_failure, record_dbus, style_failure
from proofstate import ProofState
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlError, qmlRegisterSingletonInstance
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from results import CHECKS, TIMEOUT_SECONDS, Results

QML_ROOT = Path(__file__).resolve().parent / "qml"


class Proof:
    def __init__(self, engine: QQmlApplicationEngine, state: ProofState) -> None:
        self.engine = engine
        self.state = state
        self.results = Results()
        self.warnings: list[str] = []
        engine.warnings.connect(self.collect_warnings)
        state.reported.connect(self.on_reported)
        state.interceptor.blocked.connect(self.on_blocked)
        engine.objectCreationFailed.connect(self.on_load_failed)

    def collect_warnings(self, warnings: list[QQmlError]) -> None:
        self.warnings += [warning.toString() for warning in warnings]

    def on_blocked(self) -> None:
        self.results.record("interceptor", None)
        self.finish_if_complete()

    def on_load_failed(self) -> None:
        reason = "Proof.qml failed to load: " + "; ".join(self.warnings)
        for name in CHECKS:
            self.results.record(name, reason)
        self.finish_if_complete()

    def on_reported(self, name: str, passed: bool, reason: str) -> None:
        if name == "style":
            self.results.record(name, style_failure(passed, reason, self.warnings))
        elif name == "module":
            self.results.record(name, module_failure(passed, self.is_same_singleton()))
        else:
            self.results.record(name, None if passed else reason)
        self.finish_if_complete()

    def is_same_singleton(self) -> bool:
        return self.engine.singletonInstance("Kondor", "ProofState") is self.state

    def finish_if_complete(self) -> None:
        if self.results.is_complete():
            self.finish()

    def finish(self) -> None:
        print("\n".join([*self.results.lines(), self.results.summary()]), flush=True)
        QCoreApplication.exit(0 if self.results.passed() else 1)

    def start(self) -> None:
        self.engine.addImportPath(str(QML_ROOT))
        self.engine.loadFromModule("Kondor", "Proof")
        QTimer.singleShot(0, lambda: record_dbus(self.results))
        QTimer.singleShot(0, self.finish_if_complete)
        QTimer.singleShot(TIMEOUT_SECONDS * 1000, self.finish)


def main() -> int:
    QtWebEngineQuick.initialize()
    QQuickStyle.setStyle("org.kde.desktop")
    app = QGuiApplication(sys.argv)
    state = ProofState.instance()
    qmlRegisterSingletonInstance(ProofState, "Kondor", 1, 0, "ProofState", state)
    engine = QQmlApplicationEngine()
    proof = Proof(engine, state)
    proof.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
