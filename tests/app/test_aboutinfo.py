import tomllib
from pathlib import Path

import pytest

from kondor.app import aboutinfo
from kondor.app.aboutinfo import AboutInfo
from kondor.app.startup.stagedbuild import PROJECT_VERSION

REPOSITORY = Path(__file__).resolve().parents[2]


@pytest.fixture
def info(app_identity: None) -> AboutInfo:
    return AboutInfo()


def test_version_matches_project_version(info: AboutInfo) -> None:
    assert info.application_version() == PROJECT_VERSION


@pytest.mark.usefixtures("staged_resources")
def test_license_text_is_embedded(info: AboutInfo) -> None:
    assert info.license_text().startswith("GNU GENERAL PUBLIC LICENSE")


def test_runtime_versions_are_filled(info: AboutInfo) -> None:
    assert info.qt_runtime_version()
    assert info.chromium_version()


def test_project_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((REPOSITORY / "pyproject.toml").read_text())
    assert pyproject["project"]["version"] == PROJECT_VERSION


@pytest.mark.parametrize(
    ("platform", "expected"),
    [("wayland-egl", "Wayland"), ("xcb", "X11"), ("offscreen", "offscreen")],
)
def test_windowing_system_names(platform: str, expected: str) -> None:
    assert aboutinfo.windowing_system_name(platform) == expected
