from PySide6.QtCore import QLocale


def language_name(code: str) -> str:
    language = QLocale(code).language()
    if language in (QLocale.Language.AnyLanguage, QLocale.Language.C):
        return code
    return str(QLocale.languageToString(language))
