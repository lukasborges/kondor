import shutil
from pathlib import Path

from .bundle import write_bundle
from .qmlmodule import stage_qml_module
from .tools import find_tool
from .translations import compile_translations


def clear(out_dir: Path) -> None:
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)


def stage(repository: Path, out_dir: Path) -> None:
    find_tool("pyside6-rcc")
    find_tool("pyside6-lrelease")
    clear(out_dir)
    stage_qml_module(repository / "qml", out_dir)
    compiled = compile_translations(repository / "i18n", out_dir)
    write_bundle(repository, out_dir, compiled)
