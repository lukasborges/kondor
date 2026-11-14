from pathlib import Path

from .tools import run_tool


def compile_translations(i18n_root: Path, out_dir: Path) -> list[Path]:
    target_dir = out_dir / "i18n"
    target_dir.mkdir(parents=True)
    compiled = []
    for source in sorted(i18n_root.glob("kondor_*.ts")):
        target = target_dir / f"{source.stem}.qm"
        run_tool("pyside6-lrelease", [source, "-qm", target])
        compiled.append(target)
    return compiled
