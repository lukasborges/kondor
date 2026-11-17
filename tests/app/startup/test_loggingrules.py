import pytest
from PySide6.QtCore import QLoggingCategory

from kondor.app.startup.loggingrules import build_logging_rules


@pytest.fixture
def rules() -> str:
    return build_logging_rules()


def test_silences_debug_and_info_of_every_category(rules: str) -> None:
    assert "*.debug=false" in rules.splitlines()
    assert "*.info=false" in rules.splitlines()


@pytest.mark.parametrize("category", ["kondor.extensions", "kondor.krunner"])
def test_shows_debug_and_info_of_kondor_categories(rules: str, category: str) -> None:
    assert f"{category}*.debug=true" in rules.splitlines()
    assert f"{category}*.info=true" in rules.splitlines()


def test_keeps_the_kondor_rules_after_the_catch_all_rules(rules: str) -> None:
    lines = rules.splitlines()

    assert lines.index("*.info=false") < lines.index("kondor.extensions*.info=true")


def test_rules_are_valid_for_qt() -> None:
    previous = QLoggingCategory.defaultCategory().isDebugEnabled()
    QLoggingCategory.setFilterRules(build_logging_rules())
    try:
        assert not QLoggingCategory("qt.qml.propertyCache").isDebugEnabled()
        assert QLoggingCategory("kondor.krunner").isDebugEnabled()
    finally:
        QLoggingCategory.setFilterRules(f"*.debug={str(previous).lower()}")
