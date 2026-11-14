from pathlib import Path
from xml.sax.saxutils import quoteattr

from .resources import ResourceEntry, static_resource_entries
from .tools import run_tool


def translation_entries(compiled: list[Path]) -> list[ResourceEntry]:
    return [ResourceEntry(f"/i18n/{path.name}", str(path)) for path in compiled]


def qrc_line(entry: ResourceEntry, repository: Path) -> str:
    source = Path(entry.source_path)
    absolute = source if source.is_absolute() else repository / source
    alias = entry.resource_path.removeprefix("/")
    return f"        <file alias={quoteattr(alias)}>{absolute}</file>"


def qrc_text(entries: list[ResourceEntry], repository: Path) -> str:
    lines = ['<RCC>', '    <qresource prefix="/">']
    lines += [qrc_line(entry, repository) for entry in entries]
    return "\n".join([*lines, "    </qresource>", "</RCC>"]) + "\n"


def write_bundle(repository: Path, out_dir: Path, compiled: list[Path]) -> Path:
    entries = static_resource_entries() + translation_entries(compiled)
    qrc = out_dir / "kondor.qrc"
    qrc.write_text(qrc_text(entries, repository), encoding="utf-8")
    rcc = out_dir / "kondor.rcc"
    run_tool("pyside6-rcc", ["--binary", qrc, "-o", rcc])
    return rcc
