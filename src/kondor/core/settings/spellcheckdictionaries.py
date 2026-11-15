import os
from collections.abc import Callable
from functools import cmp_to_key
from typing import Any

from PySide6.QtCore import QCollator, QDir, QLocale

DICTIONARIES_VARIABLE = "QTWEBENGINE_DICTIONARIES_PATH"
DICTIONARY_PATTERN = "*.bdic"


def capitalized(text: str) -> str:
    return text[:1].upper() + text[1:]


def display_name(code: str) -> str:
    locale = QLocale(code.replace("-", "_"))
    language = capitalized(locale.nativeLanguageName())
    if not language:
        return code
    territory = locale.nativeTerritoryName()
    return f"{language} ({territory})" if territory else language


def language_entry(code: str) -> dict[str, str]:
    return {"code": code, "name": display_name(code)}


def dictionaries_path() -> str:
    return os.environ.get(DICTIONARIES_VARIABLE, "")


def dictionary_codes() -> list[str]:
    path = dictionaries_path()
    if not path:
        return []
    files = QDir(path).entryInfoList([DICTIONARY_PATTERN], QDir.Filter.Files)
    return [file.completeBaseName() for file in files]


def name_order(collator: QCollator) -> Callable[[dict[str, str]], Any]:
    return cmp_to_key(lambda first, second: int(collator.compare(first["name"], second["name"])))


def available_languages() -> list[dict[str, str]]:
    entries = [language_entry(code) for code in dictionary_codes()]
    return sorted(entries, key=name_order(QCollator()))
