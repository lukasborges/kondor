from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QResource
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuickControls2 import QQuickStyle

STAGED_BUILD = Path(__file__).resolve().parent.parent / "build" / "python"
DESKTOP_STYLE = "org.kde.desktop"


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


@pytest.fixture
def qml_engine(qapp: object, staged_build: Path, staged_resources: None) -> Iterator[QQmlEngine]:
    engine = QQmlEngine()
    engine.addImportPath(str(staged_build / "qml"))
    yield engine
    engine.deleteLater()
