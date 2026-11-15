import os
import subprocess
import sys
from pathlib import Path

from .tools import locate

CONVERT_TOOL = "qwebengine_convert_dict"
HUNSPELL_DIRECTORIES = ("/usr/share/hunspell", "/app/share/hunspell")
DEFAULT_LANGUAGES = ("en_US", "pt_BR")
MISSING_TOOL = f"{CONVERT_TOOL} not found: spell checking dictionaries are not built"
MISSING_DICTIONARY = "Hunspell dictionary {} not found: no {} spell checking"


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def find_hunspell_dictionary(language: str) -> Path | None:
    candidates = (Path(directory) / f"{language}.dic" for directory in HUNSPELL_DIRECTORIES)
    return next((path for path in candidates if path.exists()), None)


def convert_language(tool: str, language: str, target_directory: Path) -> None:
    source = find_hunspell_dictionary(language)
    if source is None:
        warn(MISSING_DICTIONARY.format(Path(HUNSPELL_DIRECTORIES[0]) / f"{language}.dic", language))
        return
    target = target_directory / f"{language.replace('_', '-')}.bdic"
    environment = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    subprocess.run(
        [tool, str(source), str(target)], env=environment, check=True, capture_output=True
    )


def convert_dictionaries(out_dir: Path, languages: tuple[str, ...]) -> None:
    tool = locate(CONVERT_TOOL)
    if tool is None:
        warn(MISSING_TOOL)
        return
    target_directory = out_dir / "qtwebengine_dictionaries"
    target_directory.mkdir(parents=True, exist_ok=True)
    for language in languages:
        convert_language(tool, language, target_directory)
