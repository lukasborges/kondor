from PySide6.QtCore import QLoggingCategory, qSetMessagePattern

SHOWN_CATEGORIES = ("kondor.extensions", "kondor.krunner")
MESSAGE_PATTERN = "%{message}"


def build_logging_rules() -> str:
    rules = ["*.debug=false", "*.info=false"]
    for category in SHOWN_CATEGORIES:
        rules += [f"{category}*.debug=true", f"{category}*.info=true"]
    return "\n".join(rules)


def install_logging_rules() -> None:
    QLoggingCategory.setFilterRules(build_logging_rules())
    qSetMessagePattern(MESSAGE_PATTERN)
