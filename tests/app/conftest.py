import pytest
from PySide6.QtCore import QCoreApplication

from kondor.app.startup.stagedbuild import PROJECT_VERSION


@pytest.fixture
def app_identity(qapp: object) -> None:
    QCoreApplication.setApplicationVersion(PROJECT_VERSION)
