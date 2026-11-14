import shutil
from pathlib import Path

MODULE_NAME = "Kondor"
SOURCE_SUFFIXES = (".qml", ".js")


class DuplicateBaseNameError(Exception):
    pass


def qml_sources(qml_root: Path) -> list[Path]:
    return sorted(path for path in qml_root.rglob("*") if path.suffix in SOURCE_SUFFIXES)


def component_files(sources: list[Path]) -> list[Path]:
    return [path for path in sources if path.suffix == ".qml"]


def check_unique_base_names(qml_root: Path, components: list[Path]) -> None:
    seen: dict[str, Path] = {}
    for path in components:
        if path.stem in seen:
            first = seen[path.stem].relative_to(qml_root)
            second = path.relative_to(qml_root)
            raise DuplicateBaseNameError(
                f"two QML files share the base name {path.stem}: {first} and {second}"
            )
        seen[path.stem] = path


def qmldir_text(qml_root: Path, components: list[Path]) -> str:
    lines = [f"module {MODULE_NAME}"]
    for path in sorted(components, key=lambda item: item.relative_to(qml_root).as_posix()):
        lines.append(f"{path.stem} 1.0 {path.relative_to(qml_root).as_posix()}")
    return "\n".join(lines) + "\n"


def copy_sources(qml_root: Path, sources: list[Path], module_dir: Path) -> None:
    for path in sources:
        target = module_dir / path.relative_to(qml_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def stage_qml_module(qml_root: Path, out_dir: Path) -> Path:
    sources = qml_sources(qml_root)
    components = component_files(sources)
    check_unique_base_names(qml_root, components)
    module_dir = out_dir / "qml" / MODULE_NAME
    module_dir.mkdir(parents=True)
    copy_sources(qml_root, sources, module_dir)
    (module_dir / "qmldir").write_text(qmldir_text(qml_root, components), encoding="utf-8")
    return module_dir
