#!/usr/bin/env python3
"""Renderiza os protótipos QML (prototypes/*.qml) em PNG com o estilo Breeze real.

Uso:
    python3 prototypes/render.py            # todos
    python3 prototypes/render.py 05-find     # só os que contêm "05-find" no nome

Requer: python3-pyqt6 (mesma versão de Qt do sistema), kf6-kirigami,
kf6-qqc2-desktop-style, plasma-integration e breeze-icon-theme.
Os PNGs vão para prototypes/screenshots/.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_PLATFORMTHEME", "kde")          # ícones/cores do Plasma
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PyQt6.QtCore import QTimer, QUrl, QEventLoop            # noqa: E402
from PyQt6.QtGui import QGuiApplication, QIcon               # noqa: E402
from PyQt6.QtQuick import QQuickView                         # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "screenshots"


def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main():
    app = QGuiApplication(sys.argv[:1])
    QIcon.setThemeName(QIcon.themeName() or "breeze")
    OUT.mkdir(exist_ok=True)
    filt = sys.argv[1] if len(sys.argv) > 1 else ""
    files = sorted(p for p in HERE.glob("*.qml") if filt in p.name)
    failed = 0
    for qml in files:
        view = QQuickView()
        view.engine().addImportPath(str(HERE))
        view.setResizeMode(QQuickView.ResizeMode.SizeViewToRootObject)
        view.setSource(QUrl.fromLocalFile(str(qml)))
        if view.status() == QQuickView.Status.Error:
            for e in view.errors():
                print(f"{qml.name}: {e.toString()}", file=sys.stderr)
            failed += 1
            continue
        view.show()
        wait(900)   # popups/menus abrem em Component.onCompleted
        img = view.grabWindow()
        dest = OUT / (qml.stem + ".png")
        img.save(str(dest))
        print(f"{dest.relative_to(HERE.parent)}  {img.width()}x{img.height()}")
        view.close()
        view.deleteLater()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
